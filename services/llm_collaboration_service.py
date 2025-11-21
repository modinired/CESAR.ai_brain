"""
CESAR.ai Collaborative LLM Orchestration Service

Manages multi-LLM collaboration with automatic learning capture.
Every user interaction benefits both local and cloud models.

Key Features:
- 7 collaboration strategies (hierarchical, parallel, teacher-student, etc.)
- Automatic learning example capture when cloud outperforms local
- Intelligent routing based on task complexity and model capabilities
- Performance tracking and quality assessment
- Cost optimization through progressive escalation

Author: CESAR.ai Development Team
Date: November 19, 2025
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import aioredis
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import (
    LLM,
    LLMCollaboration,
    LocalLLMLearningExample,
    RoutingRule,
    Session as DBSession,
)
from ..models import (
    LLMCollaborationStrategy,
    LLMResponse,
    Message,
    MessageType,
)
from .ollama_service import OllamaService


class CollaborationStrategy(str, Enum):
    """LLM collaboration strategies"""
    PARALLEL = "parallel"  # All LLMs process simultaneously
    SEQUENTIAL = "sequential"  # LLMs refine each other's outputs
    HIERARCHICAL = "hierarchical"  # Local first, escalate to cloud
    VOTING = "voting"  # Multiple LLMs vote on best response
    ENSEMBLE = "ensemble"  # Combine outputs from multiple LLMs
    TEACHER_STUDENT = "teacher_student"  # Cloud teaches local
    PEER_REVIEW = "peer_review"  # LLMs review each other


class TaskComplexity(str, Enum):
    """Task complexity levels for routing"""
    SIMPLE = "simple"  # Local LLM sufficient
    MODERATE = "moderate"  # Local with cloud fallback
    COMPLEX = "complex"  # Cloud required, local learns
    EXPERT = "expert"  # Cloud only


class LLMCollaborationService:
    """
    Orchestrates collaborative processing across multiple LLMs.
    Ensures every user interaction benefits both local and cloud models.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        redis_client: aioredis.Redis,
        anthropic_client: Optional[AsyncAnthropic] = None,
        openai_client: Optional[AsyncOpenAI] = None,
        ollama_service: Optional[OllamaService] = None,
    ):
        self.db = db_session
        self.redis = redis_client
        self.anthropic = anthropic_client
        self.openai = openai_client
        self.ollama = ollama_service or OllamaService()

        # Cache for LLM configurations
        self._llm_cache: Dict[str, LLM] = {}

    async def process_user_query(
        self,
        session_id: UUID,
        user_query: str,
        tags: Optional[List[str]] = None,
        strategy: Optional[CollaborationStrategy] = None,
        force_collaboration: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process user query with collaborative LLM orchestration.

        Every query:
        1. Attempts local LLM first (fast, free, private)
        2. Evaluates quality of local response
        3. Escalates to cloud if needed
        4. Captures learning examples when cloud provides better answer
        5. Returns best response to user

        Args:
            session_id: Current session UUID
            user_query: User's input message
            tags: Optional tags for routing (e.g., ['code', 'complex'])
            strategy: Override collaboration strategy
            force_collaboration: Force multi-LLM collaboration even for simple tasks

        Returns:
            Tuple of (final_response_text, collaboration_metadata)
        """
        start_time = datetime.now()

        # Step 1: Determine task complexity and strategy
        complexity = await self._assess_task_complexity(user_query, tags)
        strategy = strategy or await self._select_strategy(complexity, tags)

        # Step 2: Select participating LLMs
        llm_ids = await self._select_llms_for_task(user_query, tags, complexity, strategy)

        # Step 3: Create collaboration record
        collab_id = await self._create_collaboration(
            session_id=session_id,
            user_query=user_query,
            strategy=strategy,
            llm_ids=llm_ids,
        )

        # Step 4: Execute collaboration strategy
        try:
            result = await self._execute_strategy(
                collab_id=collab_id,
                user_query=user_query,
                strategy=strategy,
                llm_ids=llm_ids,
                tags=tags,
            )

            # Step 5: Record completion and return
            await self._complete_collaboration(
                collab_id=collab_id,
                result=result,
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

            return result["final_response"], result["metadata"]

        except Exception as e:
            await self._mark_collaboration_failed(collab_id, str(e))
            raise

    async def _assess_task_complexity(
        self, user_query: str, tags: Optional[List[str]] = None
    ) -> TaskComplexity:
        """
        Assess task complexity to determine optimal LLM routing.

        Factors:
        - Query length and structure
        - Technical keywords (code, analysis, etc.)
        - Explicit complexity tags
        - Historical performance data
        """
        tags = tags or []

        # Explicit complexity override
        if "simple" in tags:
            return TaskComplexity.SIMPLE
        if "expert" in tags or "complex" in tags:
            return TaskComplexity.COMPLEX

        # Code generation heuristics
        if any(tag in tags for tag in ["code", "programming", "implementation"]):
            # Simple code tasks (< 100 chars, basic keywords)
            if len(user_query) < 100 and not any(
                kw in user_query.lower()
                for kw in ["algorithm", "optimize", "architecture", "design pattern"]
            ):
                return TaskComplexity.SIMPLE
            # Complex code tasks
            elif any(
                kw in user_query.lower()
                for kw in ["refactor", "optimize", "algorithm", "architecture", "concurrent"]
            ):
                return TaskComplexity.COMPLEX
            else:
                return TaskComplexity.MODERATE

        # Analysis tasks
        if any(tag in tags for tag in ["analysis", "research", "investigation"]):
            return TaskComplexity.COMPLEX

        # Default: simple for short queries, moderate for longer
        if len(user_query) < 50:
            return TaskComplexity.SIMPLE
        elif len(user_query) < 200:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.COMPLEX

    async def _select_strategy(
        self, complexity: TaskComplexity, tags: Optional[List[str]] = None
    ) -> CollaborationStrategy:
        """
        Select optimal collaboration strategy based on task.

        Strategy Selection:
        - SIMPLE tasks: HIERARCHICAL (local first, cloud fallback)
        - MODERATE tasks: TEACHER_STUDENT (local attempts, cloud refines)
        - COMPLEX tasks: PARALLEL (best of breed selection)
        - EXPERT tasks: SEQUENTIAL (progressive refinement)
        """
        tags = tags or []

        # Learning-focused tasks
        if "learning" in tags or "training" in tags:
            return CollaborationStrategy.TEACHER_STUDENT

        # Match complexity to strategy
        strategy_map = {
            TaskComplexity.SIMPLE: CollaborationStrategy.HIERARCHICAL,
            TaskComplexity.MODERATE: CollaborationStrategy.TEACHER_STUDENT,
            TaskComplexity.COMPLEX: CollaborationStrategy.PARALLEL,
            TaskComplexity.EXPERT: CollaborationStrategy.SEQUENTIAL,
        }

        return strategy_map.get(complexity, CollaborationStrategy.HIERARCHICAL)

    async def _select_llms_for_task(
        self,
        user_query: str,
        tags: Optional[List[str]],
        complexity: TaskComplexity,
        strategy: CollaborationStrategy,
    ) -> List[UUID]:
        """
        Select LLMs to participate in collaboration.

        Selection Logic:
        - Always include local LLM for learning (Qwen or Llama)
        - Add cloud LLM based on task type and complexity
        - Limit to 2-3 LLMs to control cost and latency
        """
        tags = tags or []
        selected_llms = []

        # Step 1: Select local LLM (always included)
        if any(tag in tags for tag in ["code", "programming", "python", "javascript"]):
            # Prefer Qwen for code
            local_llm = await self._get_llm_by_name("Qwen 2.5 Coder 7B (Local)")
        else:
            # Prefer Llama for general tasks
            local_llm = await self._get_llm_by_name("Llama 3 8B (Local)")

        if local_llm:
            selected_llms.append(local_llm.id)

        # Step 2: Select cloud LLM (based on task requirements)
        if complexity in [TaskComplexity.SIMPLE]:
            # Simple tasks: local only, no cloud needed
            return selected_llms

        # Code tasks -> Claude Sonnet
        if any(tag in tags for tag in ["code", "programming"]):
            cloud_llm = await self._get_llm_by_name("Claude Sonnet 4.5")
            if cloud_llm:
                selected_llms.append(cloud_llm.id)

        # Analysis tasks -> GPT-4o
        elif any(tag in tags for tag in ["analysis", "research"]):
            cloud_llm = await self._get_llm_by_name("GPT-4o")
            if cloud_llm:
                selected_llms.append(cloud_llm.id)

        # Default -> Claude Sonnet (best general purpose)
        else:
            cloud_llm = await self._get_llm_by_name("Claude Sonnet 4.5")
            if cloud_llm:
                selected_llms.append(cloud_llm.id)

        return selected_llms

    async def _execute_strategy(
        self,
        collab_id: UUID,
        user_query: str,
        strategy: CollaborationStrategy,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the selected collaboration strategy."""

        if strategy == CollaborationStrategy.HIERARCHICAL:
            return await self._execute_hierarchical(collab_id, user_query, llm_ids, tags)

        elif strategy == CollaborationStrategy.TEACHER_STUDENT:
            return await self._execute_teacher_student(collab_id, user_query, llm_ids, tags)

        elif strategy == CollaborationStrategy.PARALLEL:
            return await self._execute_parallel(collab_id, user_query, llm_ids, tags)

        elif strategy == CollaborationStrategy.SEQUENTIAL:
            return await self._execute_sequential(collab_id, user_query, llm_ids, tags)

        elif strategy == CollaborationStrategy.PEER_REVIEW:
            return await self._execute_peer_review(collab_id, user_query, llm_ids, tags)

        else:
            # Default to hierarchical
            return await self._execute_hierarchical(collab_id, user_query, llm_ids, tags)

    async def _execute_hierarchical(
        self,
        collab_id: UUID,
        user_query: str,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Hierarchical strategy: Local first, escalate to cloud if needed.

        Process:
        1. Try local LLM first (fast, free, private)
        2. Evaluate response quality
        3. If quality insufficient, escalate to cloud
        4. Capture learning example if cloud was needed
        """
        individual_responses = []
        local_llm_id = llm_ids[0]  # First LLM is local
        local_llm = await self._get_llm_by_id(local_llm_id)

        # Step 1: Try local LLM
        local_start = datetime.now()
        local_response = await self._call_llm(local_llm, user_query, tags)
        local_duration = int((datetime.now() - local_start).total_seconds() * 1000)

        individual_responses.append({
            "llm_id": str(local_llm_id),
            "llm_name": local_llm.name,
            "text": local_response.content,
            "duration_ms": local_duration,
            "tokens_input": local_response.tokens_input,
            "tokens_output": local_response.tokens_output,
            "cost_usd": 0.00,  # Local is free
        })

        # Step 2: Evaluate local response quality
        quality_score = await self._evaluate_response_quality(
            user_query, local_response.content, tags
        )

        # Step 3: Decide if cloud escalation needed
        needs_escalation = quality_score < 0.7 or len(llm_ids) > 1

        if needs_escalation and len(llm_ids) > 1:
            # Escalate to cloud LLM
            cloud_llm_id = llm_ids[1]
            cloud_llm = await self._get_llm_by_id(cloud_llm_id)

            cloud_start = datetime.now()
            cloud_response = await self._call_llm(cloud_llm, user_query, tags)
            cloud_duration = int((datetime.now() - cloud_start).total_seconds() * 1000)

            # Calculate cloud cost
            cloud_cost = (
                (cloud_response.tokens_input / 1000.0) * cloud_llm.cost_per_1k_input +
                (cloud_response.tokens_output / 1000.0) * cloud_llm.cost_per_1k_output
            )

            individual_responses.append({
                "llm_id": str(cloud_llm_id),
                "llm_name": cloud_llm.name,
                "text": cloud_response.content,
                "duration_ms": cloud_duration,
                "tokens_input": cloud_response.tokens_input,
                "tokens_output": cloud_response.tokens_output,
                "cost_usd": cloud_cost,
            })

            # Step 4: Capture learning example
            await self._capture_learning_example(
                collab_id=collab_id,
                local_llm_id=local_llm_id,
                teacher_llm_id=cloud_llm_id,
                user_query=user_query,
                local_output=local_response.content,
                teacher_output=cloud_response.content,
                quality_score=quality_score,
                tags=tags,
            )

            # Return cloud response (better quality)
            final_response = cloud_response.content
            selected_llm_id = cloud_llm_id
            confidence = 0.9

        else:
            # Local response sufficient
            final_response = local_response.content
            selected_llm_id = local_llm_id
            confidence = quality_score

        return {
            "final_response": final_response,
            "selected_llm_id": selected_llm_id,
            "confidence_score": confidence,
            "individual_responses": individual_responses,
            "metadata": {
                "escalated_to_cloud": needs_escalation and len(llm_ids) > 1,
                "quality_score": quality_score,
                "strategy": "hierarchical",
            },
        }

    async def _execute_teacher_student(
        self,
        collab_id: UUID,
        user_query: str,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Teacher-Student strategy: Local attempts, cloud refines and teaches.

        Process:
        1. Local LLM generates initial response (student)
        2. Cloud LLM reviews and refines response (teacher)
        3. Capture improvement delta as learning example
        4. Return refined response
        """
        individual_responses = []

        # Step 1: Student (local) attempts task
        local_llm_id = llm_ids[0]
        local_llm = await self._get_llm_by_id(local_llm_id)

        local_start = datetime.now()
        local_response = await self._call_llm(local_llm, user_query, tags)
        local_duration = int((datetime.now() - local_start).total_seconds() * 1000)

        individual_responses.append({
            "llm_id": str(local_llm_id),
            "llm_name": local_llm.name,
            "text": local_response.content,
            "duration_ms": local_duration,
            "tokens_input": local_response.tokens_input,
            "tokens_output": local_response.tokens_output,
            "cost_usd": 0.00,
            "role": "student",
        })

        # Step 2: Teacher (cloud) refines
        if len(llm_ids) > 1:
            cloud_llm_id = llm_ids[1]
            cloud_llm = await self._get_llm_by_id(cloud_llm_id)

            # Create teacher prompt that reviews student work
            teacher_prompt = f"""Review and improve this response:

ORIGINAL QUESTION:
{user_query}

STUDENT RESPONSE (from local LLM):
{local_response.content}

TASK:
1. Identify any errors or areas for improvement
2. Provide a refined, superior answer
3. Explain what was improved

Please provide the refined response:"""

            cloud_start = datetime.now()
            cloud_response = await self._call_llm(cloud_llm, teacher_prompt, tags)
            cloud_duration = int((datetime.now() - cloud_start).total_seconds() * 1000)

            cloud_cost = (
                (cloud_response.tokens_input / 1000.0) * cloud_llm.cost_per_1k_input +
                (cloud_response.tokens_output / 1000.0) * cloud_llm.cost_per_1k_output
            )

            individual_responses.append({
                "llm_id": str(cloud_llm_id),
                "llm_name": cloud_llm.name,
                "text": cloud_response.content,
                "duration_ms": cloud_duration,
                "tokens_input": cloud_response.tokens_input,
                "tokens_output": cloud_response.tokens_output,
                "cost_usd": cloud_cost,
                "role": "teacher",
            })

            # Step 3: Capture learning example with improvement delta
            await self._capture_learning_example(
                collab_id=collab_id,
                local_llm_id=local_llm_id,
                teacher_llm_id=cloud_llm_id,
                user_query=user_query,
                local_output=local_response.content,
                teacher_output=cloud_response.content,
                quality_score=0.6,  # Student needs improvement
                improvement_delta="Teacher refined and improved student response",
                tags=tags,
            )

            final_response = cloud_response.content
            selected_llm_id = cloud_llm_id

        else:
            final_response = local_response.content
            selected_llm_id = local_llm_id

        return {
            "final_response": final_response,
            "selected_llm_id": selected_llm_id,
            "confidence_score": 0.85,
            "individual_responses": individual_responses,
            "metadata": {
                "strategy": "teacher_student",
                "learning_occurred": len(llm_ids) > 1,
            },
        }

    async def _execute_parallel(
        self,
        collab_id: UUID,
        user_query: str,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Parallel strategy: All LLMs process simultaneously, best selected.

        Process:
        1. Send query to all LLMs in parallel
        2. Collect all responses
        3. Select best response (via voting or quality scoring)
        4. Capture learning examples from superior responses
        """
        # Execute all LLM calls in parallel
        tasks = []
        for llm_id in llm_ids:
            llm = await self._get_llm_by_id(llm_id)
            tasks.append(self._call_llm_with_timing(llm, user_query, tags))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        individual_responses = []
        valid_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue

            llm_id = llm_ids[i]
            llm = await self._get_llm_by_id(llm_id)
            response, duration_ms = result

            cost = 0.00
            if llm.provider != "ollama":
                cost = (
                    (response.tokens_input / 1000.0) * llm.cost_per_1k_input +
                    (response.tokens_output / 1000.0) * llm.cost_per_1k_output
                )

            response_data = {
                "llm_id": str(llm_id),
                "llm_name": llm.name,
                "text": response.content,
                "duration_ms": duration_ms,
                "tokens_input": response.tokens_input,
                "tokens_output": response.tokens_output,
                "cost_usd": cost,
            }

            individual_responses.append(response_data)
            valid_results.append((llm_id, response, cost))

        # Select best response
        if valid_results:
            best_llm_id, best_response, _ = await self._select_best_response(
                user_query, valid_results
            )

            # Capture learning if local LLM didn't win
            local_llm_ids = [
                lid for lid in llm_ids
                if (await self._get_llm_by_id(lid)).provider == "ollama"
            ]

            if local_llm_ids and best_llm_id not in local_llm_ids:
                # Find local response
                local_llm_id = local_llm_ids[0]
                local_result = next(
                    (r for r in valid_results if r[0] == local_llm_id), None
                )

                if local_result:
                    await self._capture_learning_example(
                        collab_id=collab_id,
                        local_llm_id=local_llm_id,
                        teacher_llm_id=best_llm_id,
                        user_query=user_query,
                        local_output=local_result[1].content,
                        teacher_output=best_response.content,
                        quality_score=0.7,
                        tags=tags,
                    )

            return {
                "final_response": best_response.content,
                "selected_llm_id": best_llm_id,
                "confidence_score": 0.9,
                "individual_responses": individual_responses,
                "metadata": {
                    "strategy": "parallel",
                    "responses_collected": len(valid_results),
                },
            }

        # Fallback
        return {
            "final_response": "Error: No valid responses received",
            "selected_llm_id": llm_ids[0],
            "confidence_score": 0.0,
            "individual_responses": individual_responses,
            "metadata": {"strategy": "parallel", "error": "no_valid_responses"},
        }

    async def _execute_sequential(
        self,
        collab_id: UUID,
        user_query: str,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sequential strategy: Each LLM refines the previous output.

        Process:
        1. Local LLM generates initial response
        2. Cloud LLM refines and improves
        3. Each step captured as learning example
        """
        individual_responses = []
        current_response = user_query

        for i, llm_id in enumerate(llm_ids):
            llm = await self._get_llm_by_id(llm_id)

            # First LLM gets original query, subsequent ones refine
            if i == 0:
                prompt = user_query
            else:
                prompt = f"Improve this response:\n\nQUERY: {user_query}\n\nCURRENT RESPONSE:\n{current_response}\n\nProvide an improved version:"

            start = datetime.now()
            response = await self._call_llm(llm, prompt, tags)
            duration = int((datetime.now() - start).total_seconds() * 1000)

            cost = 0.00
            if llm.provider != "ollama":
                cost = (
                    (response.tokens_input / 1000.0) * llm.cost_per_1k_input +
                    (response.tokens_output / 1000.0) * llm.cost_per_1k_output
                )

            individual_responses.append({
                "llm_id": str(llm_id),
                "llm_name": llm.name,
                "text": response.content,
                "duration_ms": duration,
                "tokens_input": response.tokens_input,
                "tokens_output": response.tokens_output,
                "cost_usd": cost,
                "sequence_position": i,
            })

            # Capture learning if this was an improvement step
            if i > 0:
                prev_llm_id = llm_ids[i - 1]
                prev_llm = await self._get_llm_by_id(prev_llm_id)

                if prev_llm.provider == "ollama" and llm.provider != "ollama":
                    await self._capture_learning_example(
                        collab_id=collab_id,
                        local_llm_id=prev_llm_id,
                        teacher_llm_id=llm_id,
                        user_query=user_query,
                        local_output=current_response,
                        teacher_output=response.content,
                        quality_score=0.65,
                        improvement_delta=f"Sequential refinement step {i}",
                        tags=tags,
                    )

            current_response = response.content

        return {
            "final_response": current_response,
            "selected_llm_id": llm_ids[-1],  # Last LLM in chain
            "confidence_score": 0.88,
            "individual_responses": individual_responses,
            "metadata": {
                "strategy": "sequential",
                "refinement_steps": len(llm_ids),
            },
        }

    async def _execute_peer_review(
        self,
        collab_id: UUID,
        user_query: str,
        llm_ids: List[UUID],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Peer Review strategy: LLMs review each other's outputs.

        Process:
        1. All LLMs generate initial responses
        2. Each LLM reviews others' responses
        3. Consensus or best response selected
        """
        # Step 1: Initial responses from all LLMs
        initial_tasks = []
        for llm_id in llm_ids:
            llm = await self._get_llm_by_id(llm_id)
            initial_tasks.append(self._call_llm_with_timing(llm, user_query, tags))

        initial_results = await asyncio.gather(*initial_tasks, return_exceptions=True)
        initial_responses = []

        for i, result in enumerate(initial_results):
            if isinstance(result, Exception):
                continue

            llm_id = llm_ids[i]
            llm = await self._get_llm_by_id(llm_id)
            response, duration_ms = result

            initial_responses.append({
                "llm_id": llm_id,
                "llm_name": llm.name,
                "response": response,
                "duration_ms": duration_ms,
            })

        # Step 2: Select best via simple quality assessment
        # (Full peer review would be expensive, use simplified version)
        if initial_responses:
            best = max(
                initial_responses,
                key=lambda x: len(x["response"].content),  # Simple heuristic
            )

            individual_responses = [
                {
                    "llm_id": str(r["llm_id"]),
                    "llm_name": r["llm_name"],
                    "text": r["response"].content,
                    "duration_ms": r["duration_ms"],
                    "tokens_input": r["response"].tokens_input,
                    "tokens_output": r["response"].tokens_output,
                    "cost_usd": 0.00
                    if (await self._get_llm_by_id(r["llm_id"])).provider == "ollama"
                    else (
                        r["response"].tokens_input / 1000.0
                        * (await self._get_llm_by_id(r["llm_id"])).cost_per_1k_input
                        + r["response"].tokens_output / 1000.0
                        * (await self._get_llm_by_id(r["llm_id"])).cost_per_1k_output
                    ),
                }
                for r in initial_responses
            ]

            return {
                "final_response": best["response"].content,
                "selected_llm_id": best["llm_id"],
                "confidence_score": 0.85,
                "individual_responses": individual_responses,
                "metadata": {
                    "strategy": "peer_review",
                    "responses_reviewed": len(initial_responses),
                },
            }

        # Fallback
        return {
            "final_response": "Error: No valid responses",
            "selected_llm_id": llm_ids[0],
            "confidence_score": 0.0,
            "individual_responses": [],
            "metadata": {"strategy": "peer_review", "error": "no_responses"},
        }

    async def _call_llm(
        self, llm: LLM, prompt: str, tags: Optional[List[str]] = None
    ) -> LLMResponse:
        """Call specific LLM and return response."""
        if llm.provider == "ollama":
            return await self.ollama.generate(
                model=llm.model_id, prompt=prompt, max_tokens=llm.max_output_tokens
            )

        elif llm.provider == "anthropic":
            response = await self.anthropic.messages.create(
                model=llm.model_id,
                max_tokens=llm.max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return LLMResponse(
                content=response.content[0].text,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
            )

        elif llm.provider == "openai":
            response = await self.openai.chat.completions.create(
                model=llm.model_id,
                max_tokens=llm.max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_input=response.usage.prompt_tokens,
                tokens_output=response.usage.completion_tokens,
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {llm.provider}")

    async def _call_llm_with_timing(
        self, llm: LLM, prompt: str, tags: Optional[List[str]] = None
    ) -> Tuple[LLMResponse, int]:
        """Call LLM and return response with duration."""
        start = datetime.now()
        response = await self._call_llm(llm, prompt, tags)
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        return response, duration_ms

    async def _evaluate_response_quality(
        self, query: str, response: str, tags: Optional[List[str]] = None
    ) -> float:
        """
        Evaluate response quality (0.0 - 1.0).

        Simple heuristics:
        - Length appropriateness
        - Keyword coverage
        - Structure quality
        """
        score = 0.5  # Base score

        # Length check
        if len(response) > 50:
            score += 0.2
        if len(response) > 200:
            score += 0.1

        # Contains code if code requested
        if tags and "code" in tags:
            if "```" in response or "def " in response or "function " in response:
                score += 0.2

        # Not too short
        if len(response) < 20:
            score -= 0.3

        return max(0.0, min(1.0, score))

    async def _select_best_response(
        self, query: str, results: List[Tuple[UUID, LLMResponse, float]]
    ) -> Tuple[UUID, LLMResponse, float]:
        """Select best response from multiple LLM outputs."""
        # Simple heuristic: longest response (could be improved with actual quality model)
        best = max(results, key=lambda x: len(x[1].content))
        return best

    async def _capture_learning_example(
        self,
        collab_id: UUID,
        local_llm_id: UUID,
        teacher_llm_id: UUID,
        user_query: str,
        local_output: str,
        teacher_output: str,
        quality_score: float,
        tags: Optional[List[str]] = None,
        improvement_delta: Optional[str] = None,
    ) -> None:
        """Capture learning example for local LLM improvement."""
        task_category = None
        if tags:
            if "code" in tags:
                task_category = "code_generation"
            elif "analysis" in tags:
                task_category = "analysis"
            else:
                task_category = tags[0] if tags else "general"

        # Determine difficulty
        difficulty = "medium"
        if quality_score < 0.5:
            difficulty = "hard"
        elif quality_score > 0.8:
            difficulty = "easy"

        example = LocalLLMLearningExample(
            id=uuid4(),
            collaboration_id=collab_id,
            local_llm_id=local_llm_id,
            teacher_llm_id=teacher_llm_id,
            input_prompt=user_query,
            local_llm_output=local_output,
            teacher_llm_output=teacher_output,
            improvement_delta=improvement_delta
            or "Teacher model provided superior response",
            quality_score=quality_score,
            task_category=task_category,
            difficulty_level=difficulty,
        )

        self.db.add(example)
        await self.db.flush()

    async def _create_collaboration(
        self, session_id: UUID, user_query: str, strategy: CollaborationStrategy, llm_ids: List[UUID]
    ) -> UUID:
        """Create collaboration record."""
        query_hash = hashlib.md5(user_query.encode()).hexdigest()

        collab = LLMCollaboration(
            id=uuid4(),
            session_id=session_id,
            user_query=user_query,
            query_hash=query_hash,
            strategy=strategy.value,
            participating_llms=llm_ids,
            primary_llm_id=llm_ids[0],
            status="in_progress",
        )

        self.db.add(collab)
        await self.db.flush()

        return collab.id

    async def _complete_collaboration(
        self, collab_id: UUID, result: Dict[str, Any], duration_ms: int
    ) -> None:
        """Mark collaboration as completed with results."""
        await self.db.execute(
            update(LLMCollaboration)
            .where(LLMCollaboration.id == collab_id)
            .values(
                status="completed",
                final_response=result["final_response"],
                selected_llm_id=result["selected_llm_id"],
                confidence_score=result["confidence_score"],
                individual_responses=result["individual_responses"],
                total_duration_ms=duration_ms,
                completed_at=datetime.now(),
                metadata=result.get("metadata", {}),
            )
        )
        await self.db.commit()

    async def _mark_collaboration_failed(self, collab_id: UUID, error: str) -> None:
        """Mark collaboration as failed."""
        await self.db.execute(
            update(LLMCollaboration)
            .where(LLMCollaboration.id == collab_id)
            .values(status="failed", metadata={"error": error})
        )
        await self.db.commit()

    async def _get_llm_by_id(self, llm_id: UUID) -> LLM:
        """Get LLM by ID (cached)."""
        cache_key = str(llm_id)
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        result = await self.db.execute(select(LLM).where(LLM.id == llm_id))
        llm = result.scalar_one()
        self._llm_cache[cache_key] = llm
        return llm

    async def _get_llm_by_name(self, name: str) -> Optional[LLM]:
        """Get LLM by name (cached)."""
        if name in self._llm_cache:
            return self._llm_cache[name]

        result = await self.db.execute(select(LLM).where(LLM.name == name))
        llm = result.scalar_one_or_none()
        if llm:
            self._llm_cache[name] = llm
        return llm
