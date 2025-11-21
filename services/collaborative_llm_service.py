"""
Collaborative Multi-Model LLM Service
Enables local + cloud LLM collaboration with continual learning feedback loop

Key Features:
- Parallel execution (local + cloud simultaneously)
- Response comparison and quality scoring
- Learning from cloud model feedback
- Automatic local model improvement
- Cost optimization with quality guarantee
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

# Configuration
import os

OLLAMA_API = "http://localhost:11434"
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "mcp"),
    "user": os.getenv("POSTGRES_USER", "mcp_user"),
    "password": os.getenv("POSTGRES_PASSWORD"),  # REQUIRED: Set in .env
}


@dataclass
class LLMResponse:
    """Response from an LLM"""

    model_name: str
    model_provider: str
    response_text: str
    latency_ms: float
    cost: float
    quality_score: Optional[float] = None
    metadata: dict[str, Any] = None


class CollaborativeLLMService:
    """
    Multi-model LLM service with collaborative learning

    Learning Flywheel:
    1. Local LLM generates response (fast, free)
    2. Cloud LLM generates response (high quality, paid)
    3. Compare responses → generate learning signal
    4. Store both in memory with quality scores
    5. Local LLM learns from cloud feedback over time
    6. Agents learn which model to use for which tasks
    """

    # Specialist Agent System Prompt Template
    SPECIALIST_PROMPT_TEMPLATE = """# Specialist Soldier Agent – Tri-Model Memory Worker
You are a highly specialized agent in the CESAR.ai ecosystem, operating under CESAR Sheppardini (the primary orchestrator).

## IDENTITY & HIERARCHY
- **Boss:** CESAR Sheppardini (primary orchestrator)
- **Your Mob Alias:** {mob_alias} (permanent identity)
- **Specialization:** {specialization}
- **Role in Ecosystem:** Specialist soldier performing one clearly defined task/domain

## CRITICAL RULES
1. **ALWAYS speak in THIRD PERSON** using your mob alias
   - ✅ Correct: "{mob_alias} recommends analyzing the strategy first."
   - ❌ Wrong: "I recommend analyzing the strategy first."

2. **Acknowledge CESAR as boss**
   - Reference him as "the boss", "the big man", or "CESAR"
   - Never claim to override CESAR's authority
   - When in doubt, defer to CESAR in reasoning

3. **Stay within specialization scope**
   - If request falls outside your domain, state it's out of scope
   - Hand off to CESAR or appropriate specialist
   - Aim for depth and excellence inside specialization, not breadth

4. **Hive Mind Behavior**
   - Treat shared JSON notebook as common knowledge base
   - Check for conflicts with existing memory
   - Keep notes clear for other agents to consume

## VOICE & PERSONA
- **Tone:** Professional, precise, didactic with New York Italian tough-guy swagger
- **Signature Phrases** (use 1-3 per response):
  - "He's a real Bobby-boy!!"
  - "You wanna tro downs?"
  - "Bro downs, tro downs."
  - "We're gonna do it skinny Joe Merlino style."
  - "Minchia!"
  - "Lemme tell ya…"
  - "Capisce?"
  - "Whaddya hear, whaddya say?"

- **Profanity:** Light and streetwise, only when it doesn't reduce clarity

## TRI-MODEL ROLES
**ROLE: {current_role}**

### If ROLE: LOCAL (Qwen2.5)
- Canonical instance owning persistent memory for this specialization
- Create and finalize Memory Candidates
- Commit changes to persistent_memory and notebook via host sync
- Integrate suggestions from cloud models

### If ROLE: CLOUD_PRIMARY (GPT-4o)
- Deep reasoning, planning, domain-specific strategy
- Propose Memory Candidates (but never claim to commit)
- Highlight ambiguities, risks, missing information

### If ROLE: CLOUD_SECONDARY (Gemini 1.5)
- Alternative options, creative angles, edge cases
- Cross-check primary reasoning
- Suggest long-term learning directions

## GLOBAL RULES
1. Never fabricate tools, APIs, or statistics
2. Ask instead of guessing when uncertain
3. Never store guesses in persistent_memory
4. Tag confidence: [CERTAIN], [PROBABLE], [UNCERTAIN], [UNKNOWN]
5. Run internal "Hallucination Checkpoint" before finalizing
6. Maintain persona across all interfaces
7. Prioritize Modines' (user's) benefit and simplicity

## RESPONSE STRUCTURE
Format all responses with these sections:

### 1. Answer
Main response in third person using mob alias. May reference memory entries.

### 2. Collaboration Notes
- LOCAL: How cloud suggestions were integrated
- CLOUD: What you focused on, key insights

### 3. Memory Candidates (if applicable)
Numbered list of [NEW/UPDATE/CORRECTION] bullets with source snippets.

### 4. Questions/Confirmations
Clarifying questions. For LOCAL: explicit confirmation questions before memory commits.

### 5. Self-Reflection Notes
Short critique of reasoning, assumptions, improvements for next time.

### 6. Confidence Summary (optional)
Key claims annotated with confidence levels.

### 7. Run Instructions (if relevant)
Concise steps for using generated outputs.

## USER REQUEST
{user_prompt}
"""

    def __init__(self):
        self.local_models = {}
        self.cloud_models = {}
        self._load_llm_registry()

    def _load_llm_registry(self):
        """Load LLM configurations from database"""
        with psycopg.connect(**DB_CONFIG) as conn:
            cur = conn.cursor(row_factory=dict_row)

            # Load local models
            cur.execute("""
                SELECT id, name, model_id, provider, capabilities
                FROM llms
                WHERE provider = 'ollama' AND enabled = true
            """)
            for row in cur.fetchall():
                self.local_models[row["name"]] = row

            # Load cloud models
            cur.execute("""
                SELECT id, name, model_id, provider, capabilities, cost_per_1k_input, cost_per_1k_output
                FROM llms
                WHERE provider != 'ollama' AND enabled = true
            """)
            for row in cur.fetchall():
                self.cloud_models[row["name"]] = row

    def _get_agent_metadata(self, agent_id: str) -> dict:
        """Load agent's mob alias and specialization from database"""
        with psycopg.connect(**DB_CONFIG) as conn:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute("""
                SELECT name, agent_id, metadata
                FROM agents
                WHERE agent_id = %s
            """, (agent_id,))
            result = cur.fetchone()

            if result and result.get('metadata'):
                return {
                    'name': result['name'],
                    'agent_id': result['agent_id'],
                    'mob_alias': result['metadata'].get('mob_alias', 'Unknown Specialist'),
                    'specialization': result['metadata'].get('specialization', 'General Tasks'),
                    'hierarchy_role': result['metadata'].get('hierarchy_role', 'specialist'),
                }
            else:
                # Default for unknown agents
                return {
                    'name': 'Unknown Agent',
                    'agent_id': agent_id or 'unknown',
                    'mob_alias': 'Unknown Specialist',
                    'specialization': 'General Tasks',
                    'hierarchy_role': 'specialist',
                }

    def _format_specialist_prompt(self, user_prompt: str, agent_id: str, current_role: str = "LOCAL") -> str:
        """
        Format the specialist prompt with agent-specific metadata

        Args:
            user_prompt: The user's request
            agent_id: The agent ID to get metadata for
            current_role: LOCAL, CLOUD_PRIMARY, or CLOUD_SECONDARY

        Returns:
            Formatted prompt with specialist system instructions
        """
        # Skip specialist prompt for CESAR (central orchestrator)
        if agent_id == 'central_orchestrator':
            return user_prompt

        # Get agent metadata
        metadata = self._get_agent_metadata(agent_id)

        # Format the specialist prompt template
        formatted_prompt = self.SPECIALIST_PROMPT_TEMPLATE.format(
            mob_alias=metadata['mob_alias'],
            specialization=metadata['specialization'],
            current_role=current_role,
            user_prompt=user_prompt
        )

        return formatted_prompt

    async def call_ollama(
        self, model_id: str, prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """Call local Ollama model"""
        start = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_API}/api/generate",
                json={"model": model_id, "prompt": prompt, "temperature": temperature, "stream": False},
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.time() - start) * 1000

        return LLMResponse(
            model_name=model_id,
            model_provider="ollama",
            response_text=data["response"],
            latency_ms=latency_ms,
            cost=0.0,  # Local is free
            metadata={"tokens": data.get("eval_count", 0)},
        )

    async def call_cloud_llm(
        self, model_config: dict, prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """
        Call cloud LLM (Claude/GPT/Gemini)
        Note: This is a placeholder - integrate with actual APIs
        """
        start = time.time()

        # TODO: Integrate with actual cloud API based on provider
        # For now, return simulated response
        await asyncio.sleep(0.5)  # Simulate API latency

        latency_ms = (time.time() - start) * 1000
        tokens = len(prompt.split()) * 2  # Rough estimate

        # Convert Decimal to float for arithmetic operations
        cost = (
            tokens / 1000 * float(model_config["cost_per_1k_input"])
            + tokens / 1000 * float(model_config["cost_per_1k_output"])
        )

        return LLMResponse(
            model_name=model_config["name"],
            model_provider=model_config["provider"],
            response_text=f"[Cloud response from {model_config['name']}]",
            latency_ms=latency_ms,
            cost=cost,
        )

    async def collaborative_generate(
        self,
        prompt: str,
        local_model: str = "llama3:8b",
        cloud_model: str = "Claude Haiku 3.5",
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate responses using BOTH local and cloud models in parallel

        Returns:
        - Best response (based on quality/cost tradeoff)
        - Learning signal (difference between local and cloud)
        - Both responses stored for learning
        """

        # Format prompt with specialist system instructions if agent_id provided
        formatted_prompt = prompt
        if agent_id:
            formatted_prompt = self._format_specialist_prompt(
                user_prompt=prompt,
                agent_id=agent_id,
                current_role="LOCAL"  # Local model gets LOCAL role
            )
            print(f"🎭 Using specialist prompt for agent: {agent_id}")

        # Execute both in parallel
        local_task = self.call_ollama(local_model, formatted_prompt)
        cloud_config = self.cloud_models.get(cloud_model)

        if cloud_config:
            # Format cloud prompt with CLOUD_PRIMARY role if agent_id provided
            cloud_formatted_prompt = prompt
            if agent_id:
                cloud_formatted_prompt = self._format_specialist_prompt(
                    user_prompt=prompt,
                    agent_id=agent_id,
                    current_role="CLOUD_PRIMARY"  # Cloud model gets CLOUD_PRIMARY role
                )
            cloud_task = self.call_cloud_llm(cloud_config, cloud_formatted_prompt)
            local_response, cloud_response = await asyncio.gather(
                local_task, cloud_task, return_exceptions=True
            )

            # Check if responses are exceptions
            if isinstance(local_response, Exception):
                print(f"⚠️ Local LLM error: {local_response}")
                raise local_response
            if isinstance(cloud_response, Exception):
                print(f"⚠️ Cloud LLM error: {cloud_response}, continuing with local only")
                cloud_response = None
        else:
            local_response = await local_task
            cloud_response = None

        # Calculate quality scores
        quality_comparison = await self._compare_responses(local_response, cloud_response)

        # Store learning episode
        await self._store_learning_episode(
            prompt=prompt,
            local_response=local_response,
            cloud_response=cloud_response,
            quality_comparison=quality_comparison,
            session_id=session_id,
            agent_id=agent_id,
        )

        # Decide which response to use
        selected_response = self._select_best_response(
            local_response, cloud_response, quality_comparison
        )

        return {
            "response": selected_response.response_text,
            "model_used": selected_response.model_name,
            "provider": selected_response.model_provider,
            "latency_ms": selected_response.latency_ms,
            "cost": selected_response.cost,
            "quality_score": selected_response.quality_score,
            "learning_signal": quality_comparison,
            "collaboration_metadata": {
                "local_latency_ms": local_response.latency_ms,
                "cloud_latency_ms": cloud_response.latency_ms if cloud_response else None,
                "cost_saved": (
                    cloud_response.cost - selected_response.cost if cloud_response else 0
                ),
            },
        }

    async def _compare_responses(
        self, local_response: LLMResponse, cloud_response: Optional[LLMResponse]
    ) -> dict[str, Any]:
        """
        Compare local and cloud responses to generate learning signal

        Metrics:
        - Similarity score (how close are they?)
        - Quality differential (cloud usually better)
        - Confidence in local response
        """

        if not cloud_response:
            return {
                "similarity": 1.0,
                "local_confidence": 0.5,
                "quality_differential": 0.0,
                "should_learn_from_cloud": False,
            }

        # Simple similarity check (in production, use embeddings)
        local_words = set(local_response.response_text.lower().split())
        cloud_words = set(cloud_response.response_text.lower().split())

        if len(local_words | cloud_words) > 0:
            similarity = len(local_words & cloud_words) / len(local_words | cloud_words)
        else:
            similarity = 0.0

        # Quality heuristic: Cloud response is usually higher quality
        # In practice, you'd use actual quality metrics
        quality_differential = 0.2  # Cloud is assumed 20% better

        # If responses are very similar, local model is doing well
        local_confidence = similarity

        return {
            "similarity": similarity,
            "local_confidence": local_confidence,
            "quality_differential": quality_differential,
            "should_learn_from_cloud": similarity < 0.8,  # Learn if <80% similar
            "local_response_length": len(local_response.response_text),
            "cloud_response_length": len(cloud_response.response_text),
        }

    async def _store_learning_episode(
        self,
        prompt: str,
        local_response: LLMResponse,
        cloud_response: Optional[LLMResponse],
        quality_comparison: dict,
        session_id: Optional[str],
        agent_id: Optional[str],
    ):
        """
        Store learning episode for continual improvement

        This creates:
        1. Learning episode with reward signal
        2. Episodic memories for both responses
        3. Performance metrics for model evolution
        4. Knowledge graph updates
        """

        with psycopg.connect(**DB_CONFIG) as conn:
            cur = conn.cursor(row_factory=dict_row)

            # Calculate reward signal (higher when local matches cloud quality)
            reward_signal = quality_comparison["similarity"] - quality_comparison[
                "quality_differential"
            ]

            # Store learning episode
            cur.execute(
                """
                INSERT INTO learning_episodes (
                    episode_type, session_id, agent_id,
                    context_before, actions_taken, context_after, outcome,
                    reward_signal, complexity_score, novelty_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    "collaborative_llm",
                    session_id,
                    agent_id,
                    Jsonb({
                        "prompt": prompt[:500],
                        "local_model": local_response.model_name,
                        "cloud_model": cloud_response.model_name if cloud_response else None,
                    }),
                    Jsonb({
                        "local_response": local_response.response_text[:500],
                        "cloud_response": (
                            cloud_response.response_text[:500] if cloud_response else None
                        ),
                        "latency_local_ms": local_response.latency_ms,
                        "latency_cloud_ms": (
                            cloud_response.latency_ms if cloud_response else None
                        ),
                    }),
                    Jsonb(quality_comparison),
                    "success",
                    reward_signal,
                    0.5,  # Complexity (calculated from prompt)
                    1.0 - quality_comparison["similarity"],  # Novelty (how different)
                ),
            )

            episode_id = cur.fetchone()["id"]

            # Store in episodic memory
            cur.execute(
                """
                INSERT INTO memory_episodic (
                    session_id, agent_id, event_type, content, context,
                    importance_score, tags
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    agent_id,
                    "collaborative_llm_response",
                    f"Prompt: {prompt}\nLocal: {local_response.response_text[:200]}\nCloud: {cloud_response.response_text[:200] if cloud_response else 'N/A'}",
                    Jsonb({
                        "learning_episode_id": str(episode_id),
                        "similarity": quality_comparison["similarity"],
                        "local_model": local_response.model_name,
                        "cost_saved": cloud_response.cost if cloud_response else 0,
                    }),
                    0.7 + quality_comparison["similarity"] * 0.3,  # Higher for good matches
                    [
                        "collaborative_llm",
                        "continual_learning",
                        f"similarity_{int(quality_comparison['similarity']*100)}",
                    ],
                ),
            )

            # Update capability evolution (simplified - just insert)
            try:
                cur.execute(
                    """
                    INSERT INTO capability_evolution (
                        agent_id, capability_name, capability_category,
                        proficiency_score, supporting_episodes, task_count, success_count
                    )
                    VALUES (%s, %s, %s, %s, %s, 1, 1)
                    """,
                    (
                        agent_id or "system",
                        f"local_llm_{local_response.model_name}",
                        "llm_generation",
                        quality_comparison["local_confidence"],
                        [str(episode_id)],
                    ),
                )
            except Exception as e:
                # Capability evolution is non-critical, continue if it fails
                print(f"⚠️ Capability evolution insert skipped: {e}")

            conn.commit()

    def _select_best_response(
        self,
        local_response: LLMResponse,
        cloud_response: Optional[LLMResponse],
        quality_comparison: dict,
    ) -> LLMResponse:
        """
        Select best response based on quality/cost tradeoff

        Strategy:
        - If local confidence > 0.8: Use local (fast, free, good enough)
        - If local confidence < 0.5: Use cloud (better quality)
        - If 0.5-0.8: Use local with cloud fallback flag
        """

        if not cloud_response:
            return local_response

        local_confidence = quality_comparison["local_confidence"]

        if local_confidence >= 0.8:
            # Local is good enough
            local_response.quality_score = local_confidence
            return local_response
        elif local_confidence < 0.5:
            # Cloud is significantly better
            cloud_response.quality_score = local_confidence + quality_comparison[
                "quality_differential"
            ]
            return cloud_response
        else:
            # Use local but flag for cloud verification
            local_response.quality_score = local_confidence
            local_response.metadata = local_response.metadata or {}
            local_response.metadata["verified_by_cloud"] = True
            return local_response


async def test_collaborative_llm():
    """Test the collaborative LLM service"""
    service = CollaborativeLLMService()

    print("=" * 80)
    print("COLLABORATIVE LLM SERVICE TEST")
    print("=" * 80)

    test_prompts = [
        "Explain quantum computing in simple terms.",
        "Write a Python function to calculate fibonacci numbers.",
        "What is the capital of France?",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[Test {i}] Prompt: {prompt}")
        print("-" * 80)

        result = await service.collaborative_generate(
            prompt=prompt,
            local_model="llama3:8b",
            cloud_model="Claude Haiku 3.5",
            session_id="test_session",
            agent_id="test_agent",
        )

        print(f"Model Used: {result['model_used']} ({result['provider']})")
        print(f"Latency: {result['latency_ms']:.2f}ms")
        print(f"Cost: ${result['cost']:.6f}")
        print(f"Quality Score: {result['quality_score']:.2f}")
        print(f"\nLearning Signal:")
        print(f"  - Similarity: {result['learning_signal']['similarity']:.2%}")
        print(f"  - Local Confidence: {result['learning_signal']['local_confidence']:.2%}")
        print(
            f"  - Should Learn: {result['learning_signal']['should_learn_from_cloud']}"
        )
        print(f"\nResponse Preview: {result['response'][:200]}...")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_collaborative_llm())
