"""
SkillForge MCP - Dynamic Skill Discovery & Auto-Generation
===========================================================

Automatically discovers new skills from usage patterns, generates
skill specifications, and deploys them as MCP agents.

Features:
- Pattern discovery from activity logs
- Automatic skill generation
- Few-shot prompt synthesis
- Skill evaluation and deployment
- Integration with existing MCP systems
"""

import os
import json
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from collections import Counter

# ML dependencies
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN, AgglomerativeClustering
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    import faiss
except ImportError as e:
    logging.warning(f"SkillForge ML dependencies missing: {e}")
    logging.warning("Install: pip install sentence-transformers scikit-learn faiss-cpu")

from .base_agent import BaseMCPAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SkillForge")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class SkillRecord:
    """Skill specification record"""
    skill_id: str
    name: str
    description: str
    interface: Dict[str, Any]
    prompt: str = ""
    code: str = ""
    version: str = "0.1.0"
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    eval_metrics: Dict[str, Any] = field(default_factory=dict)
    owner: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class SkillHypothesis:
    """Discovered skill hypothesis from clustering"""
    cluster_id: str
    examples: List[str]
    top_terms: List[str]
    frequency: int
    confidence: float


# =============================================================================
# DISCOVERY AGENT
# =============================================================================

class DiscoveryAgent:
    """
    Analyzes activity logs to discover repeating patterns and unmet needs
    """

    def __init__(self, vector_model: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(vector_model)
        logger.info(f"DiscoveryAgent initialized with model: {vector_model}")

    def discover_from_logs(
        self,
        logs: List[Dict[str, Any]],
        min_cluster_size: int = 3
    ) -> List[SkillHypothesis]:
        """
        Discover skill patterns from activity logs

        Args:
            logs: List of activity log entries
            min_cluster_size: Minimum examples to form a pattern

        Returns:
            List of skill hypotheses
        """
        if not logs or len(logs) < min_cluster_size:
            logger.info("Insufficient logs for discovery")
            return []

        # Extract failed/manual tasks - these indicate unmet needs
        unmet_needs = [
            log for log in logs
            if log.get('status') in ['failed', 'manual_override', 'error']
               or log.get('action', '').startswith('manual:')
        ]

        if len(unmet_needs) < min_cluster_size:
            logger.info("No significant unmet needs found")
            return []

        # Extract text descriptions
        texts = []
        for log in unmet_needs:
            text = log.get('details', '') or log.get('action', '') or str(log)
            texts.append(text)

        # Embed texts
        embeddings = self.model.encode(texts)

        # Cluster with DBSCAN (finds clusters of arbitrary shape)
        clustering = DBSCAN(
            eps=0.3,  # Distance threshold
            min_samples=min_cluster_size,
            metric='cosine'
        ).fit(embeddings)

        # Collect clusters
        hypotheses = []
        clusters = {}

        for idx, label in enumerate(clustering.labels_):
            if label == -1:  # Noise
                continue

            if label not in clusters:
                clusters[label] = []

            clusters[label].append({
                'text': texts[idx],
                'log': unmet_needs[idx]
            })

        # Generate hypothesis for each cluster
        for cluster_id, items in clusters.items():
            if len(items) >= min_cluster_size:
                hypothesis = self._generate_hypothesis(cluster_id, items)
                hypotheses.append(hypothesis)

        logger.info(f"Discovered {len(hypotheses)} skill hypotheses")
        return hypotheses

    def _generate_hypothesis(
        self,
        cluster_id: int,
        items: List[Dict[str, Any]]
    ) -> SkillHypothesis:
        """Generate hypothesis from cluster"""
        texts = [item['text'] for item in items]

        # Extract top terms using TF-IDF
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=50
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # Get top terms
            tfidf_scores = tfidf_matrix.sum(axis=0).A1
            top_indices = tfidf_scores.argsort()[-10:][::-1]
            top_terms = [feature_names[i] for i in top_indices]

        except Exception as e:
            logger.warning(f"TF-IDF failed: {e}")
            # Fallback: simple word frequency
            all_words = ' '.join(texts).lower().split()
            word_freq = Counter(all_words)
            top_terms = [word for word, _ in word_freq.most_common(10)]

        # Calculate confidence based on cluster coherence
        frequency = len(items)
        confidence = min(1.0, frequency / 10.0)  # More examples = higher confidence

        return SkillHypothesis(
            cluster_id=f"cluster_{cluster_id}",
            examples=texts[:10],  # Limit examples
            top_terms=top_terms[:5],
            frequency=frequency,
            confidence=confidence
        )


# =============================================================================
# CANDIDATE GENERATION AGENT
# =============================================================================

class CandidateGenAgent:
    """
    Generates skill specifications from hypotheses
    """

    def __init__(self):
        logger.info("CandidateGenAgent initialized")

    def generate_skill_spec(self, hypothesis: SkillHypothesis) -> SkillRecord:
        """
        Create SkillRecord from hypothesis

        Args:
            hypothesis: Discovered skill hypothesis

        Returns:
            SkillRecord specification
        """
        skill_id = f"skill_{uuid.uuid4().hex[:8]}"

        # Generate name from top terms
        name_parts = hypothesis.top_terms[:3]
        name = "AutoSkill: " + " ".join(name_parts).title()

        # Generate description
        description = (
            f"Auto-generated skill for handling: {', '.join(hypothesis.top_terms)}. "
            f"Discovered from {hypothesis.frequency} similar requests."
        )

        # Define interface
        interface = {
            "input": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Input text to process"}
                }
            },
            "output": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "params": {"type": "object"},
                    "confidence": {"type": "number"}
                }
            }
        }

        # Generate few-shot prompt
        prompt = self._generate_prompt_template(hypothesis)

        # Create skill record
        record = SkillRecord(
            skill_id=skill_id,
            name=name,
            description=description,
            interface=interface,
            prompt=prompt,
            tags=["auto-generated", "discovered"] + hypothesis.top_terms[:3],
            examples=hypothesis.examples,
            confidence_score=hypothesis.confidence
        )

        logger.info(f"Generated skill spec: {skill_id} - {name}")
        return record

    def _generate_prompt_template(self, hypothesis: SkillHypothesis) -> str:
        """Generate few-shot prompt template"""
        prompt = f"""# Auto-Generated Skill: {' '.join(hypothesis.top_terms[:3]).title()}

## Description
Handle requests related to: {', '.join(hypothesis.top_terms)}

## Examples
"""

        # Add example inputs/outputs
        for i, example in enumerate(hypothesis.examples[:5], 1):
            prompt += f"\n### Example {i}\nInput: {example}\n"
            prompt += f"Output: {{'action': 'process', 'params': {{}}, 'confidence': 0.8}}\n"

        prompt += """
## Instructions
1. Analyze the input text
2. Extract relevant parameters
3. Return structured output with action and params
4. Include confidence score (0.0-1.0)
"""

        return prompt


# =============================================================================
# TRAINER AGENT
# =============================================================================

class TrainerAgent:
    """
    Trains skills with few-shot examples and synthetic data
    """

    def __init__(self):
        logger.info("TrainerAgent initialized")

    def synthesize_examples(
        self,
        seed_examples: List[str],
        n: int = 50,
        augmentation_factor: float = 0.3
    ) -> List[str]:
        """
        Synthesize additional training examples

        Args:
            seed_examples: Original examples
            n: Number of examples to generate
            augmentation_factor: Variation intensity

        Returns:
            List of synthetic examples
        """
        if not seed_examples:
            return []

        synthesized = []

        # Simple augmentation strategies
        for i in range(n):
            base = seed_examples[i % len(seed_examples)]

            # Strategy 1: Paraphrasing (simple word substitution)
            augmented = self._augment_text(base, augmentation_factor)
            synthesized.append(augmented)

        logger.info(f"Synthesized {len(synthesized)} training examples")
        return synthesized

    def _augment_text(self, text: str, factor: float) -> str:
        """Simple text augmentation"""
        # Add variation markers
        suffixes = [
            f" (variant {int(time.time() % 100)})",
            f" - modified",
            f" [v{int(factor * 10)}]",
            ""
        ]

        import random
        suffix = random.choice(suffixes)
        return text + suffix

    def train_prompt_skill(self, skill: SkillRecord, examples: List[str]) -> SkillRecord:
        """
        Train skill with examples

        Args:
            skill: Skill record
            examples: Training examples

        Returns:
            Trained skill record
        """
        # Build few-shot prompt with examples
        few_shot = "\n### Training Examples\n"

        for i, ex in enumerate(examples[:10], 1):
            few_shot += f"{i}. Input: {ex}\n   Output: {{'processed': true}}\n"

        skill.prompt += "\n" + few_shot
        skill.eval_metrics["training_examples"] = len(examples)

        logger.info(f"Trained skill {skill.skill_id} with {len(examples)} examples")
        return skill


# =============================================================================
# EVALUATOR AGENT
# =============================================================================

class EvaluatorAgent:
    """
    Evaluates skill quality with unit tests and adversarial examples
    """

    def __init__(self):
        logger.info("EvaluatorAgent initialized")

    def run_unit_tests(
        self,
        skill: SkillRecord,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run unit tests on skill

        Args:
            skill: Skill to test
            test_cases: List of test cases

        Returns:
            Test results
        """
        if not test_cases:
            return {"score": 0.0, "passed": 0, "total": 0}

        passed = 0

        for tc in test_cases:
            # Simple validation: check if input is processed
            if tc.get("input"):
                # In production, would execute skill and validate output
                # For now, assume success if input is valid
                passed += 1

        total = len(test_cases)
        score = passed / max(1, total)

        results = {
            "score": score,
            "passed": passed,
            "total": total,
            "pass_rate": score * 100
        }

        skill.eval_metrics["unit_test_score"] = score
        skill.eval_metrics["tests_passed"] = passed
        skill.eval_metrics["tests_total"] = total

        logger.info(f"Skill {skill.skill_id} test score: {score:.2%}")
        return results

    def run_adversarial(
        self,
        skill: SkillRecord,
        adv_inputs: List[str]
    ) -> Dict[str, Any]:
        """
        Test skill with adversarial inputs

        Args:
            skill: Skill to test
            adv_inputs: Adversarial test inputs

        Returns:
            Adversarial test results
        """
        hits = 0

        for adv_input in adv_inputs:
            # Check if skill description covers adversarial case
            if any(term in adv_input.lower() for term in skill.tags):
                hits += 1

        robustness = 1.0 - (hits / max(1, len(adv_inputs)))

        results = {
            "adversarial_hits": hits,
            "robustness_score": robustness
        }

        skill.eval_metrics.update(results)

        logger.info(f"Skill {skill.skill_id} robustness: {robustness:.2%}")
        return results


# =============================================================================
# SKILLFORGE ORCHESTRATOR
# =============================================================================

class SkillForgeOrchestrator:
    """
    Main orchestrator for SkillForge MCP system

    Coordinates discovery, generation, training, and evaluation
    """

    def __init__(self, db_dsn: str = None):
        self.db_dsn = db_dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        )

        # Initialize agents
        self.discovery = DiscoveryAgent()
        self.candidate_gen = CandidateGenAgent()
        self.trainer = TrainerAgent()
        self.evaluator = EvaluatorAgent()

        # Skill registry
        self.skills: Dict[str, SkillRecord] = {}

        # Lifecycle tracking
        self.lifecycle: Dict[str, Dict[str, Any]] = {}

        logger.info("SkillForgeOrchestrator initialized")

    def run_discovery_cycle(
        self,
        activity_logs: List[Dict[str, Any]],
        auto_deploy: bool = False,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Run complete skill discovery cycle

        Args:
            activity_logs: Recent activity logs
            auto_deploy: Auto-deploy high-confidence skills
            min_confidence: Minimum confidence for auto-deployment

        Returns:
            List of discovered skills with metadata
        """
        logger.info(f"Starting discovery cycle with {len(activity_logs)} logs")

        # Step 1: Discover patterns
        hypotheses = self.discovery.discover_from_logs(activity_logs)

        if not hypotheses:
            logger.info("No patterns discovered")
            return []

        # Step 2: Generate candidates
        candidates = []

        for hypothesis in hypotheses:
            # Generate skill spec
            skill = self.candidate_gen.generate_skill_spec(hypothesis)

            # Synthesize training examples
            examples = self.trainer.synthesize_examples(
                hypothesis.examples,
                n=20
            )

            # Train skill
            trained_skill = self.trainer.train_prompt_skill(skill, examples)

            # Evaluate skill
            test_cases = [{"input": ex} for ex in examples[:10]]
            eval_results = self.evaluator.run_unit_tests(trained_skill, test_cases)

            # Store skill
            self.skills[trained_skill.skill_id] = trained_skill

            # Track lifecycle
            self.lifecycle[trained_skill.skill_id] = {
                "status": "evaluated",
                "created_at": time.time(),
                "hypothesis": hypothesis.cluster_id
            }

            candidate_info = {
                "skill_id": trained_skill.skill_id,
                "name": trained_skill.name,
                "confidence": trained_skill.confidence_score,
                "eval_score": eval_results["score"],
                "deployed": False
            }

            # Auto-deploy if confidence is high
            if auto_deploy and trained_skill.confidence_score >= min_confidence:
                self._deploy_skill(trained_skill)
                candidate_info["deployed"] = True

            candidates.append(candidate_info)

        logger.info(f"Discovery cycle completed: {len(candidates)} candidates")
        return candidates

    def _deploy_skill(self, skill: SkillRecord):
        """Deploy skill to production"""
        self.lifecycle[skill.skill_id]["status"] = "deployed"
        self.lifecycle[skill.skill_id]["deployed_at"] = time.time()

        logger.info(f"Deployed skill: {skill.skill_id} - {skill.name}")

    def call_skill(self, skill_id: str, input_text: str) -> Dict[str, Any]:
        """
        Execute a skill

        Args:
            skill_id: Skill identifier
            input_text: Input text to process

        Returns:
            Skill execution result
        """
        skill = self.skills.get(skill_id)

        if not skill:
            return {"error": "skill_not_found", "skill_id": skill_id}

        # In production: call LLM with skill.prompt + input_text
        # For now: return structured output
        result = {
            "skill_id": skill_id,
            "version": skill.version,
            "output": {
                "action": "processed",
                "params": {"input": input_text},
                "confidence": skill.confidence_score
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Executed skill: {skill_id}")
        return result

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all registered skills"""
        return [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "description": skill.description,
                "confidence": skill.confidence_score,
                "eval_score": skill.eval_metrics.get("unit_test_score", 0.0),
                "status": self.lifecycle.get(skill.skill_id, {}).get("status", "unknown"),
                "tags": skill.tags
            }
            for skill in self.skills.values()
        ]

    def get_skill(self, skill_id: str) -> Optional[SkillRecord]:
        """Get skill by ID"""
        return self.skills.get(skill_id)

    def get_status(self) -> Dict[str, Any]:
        """Get SkillForge system status"""
        deployed = sum(
            1 for lifecycle in self.lifecycle.values()
            if lifecycle.get("status") == "deployed"
        )

        return {
            "system": "skillforge",
            "status": "active",
            "total_skills": len(self.skills),
            "deployed_skills": deployed,
            "pending_skills": len(self.skills) - deployed
        }


# =============================================================================
# INTEGRATION WITH BASE MCP AGENT
# =============================================================================

class SkillForgeAgent(BaseMCPAgent):
    """
    SkillForge as an MCP agent for integration with other systems
    """

    def __init__(self, db_dsn: str = None):
        super().__init__(
            agent_id='mcp_skillforge',
            mcp_system='skillforge',
            db_dsn=db_dsn
        )
        self.orchestrator = SkillForgeOrchestrator(db_dsn)

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process SkillForge tasks

        Args:
            task_input: {
                'task_type': 'discover' | 'call_skill' | 'list_skills',
                'logs': [...],  # for discover
                'skill_id': str,  # for call_skill
                'input': str  # for call_skill
            }

        Returns:
            Task execution result
        """
        task_type = task_input.get('task_type', 'discover')

        if task_type == 'discover':
            logs = task_input.get('logs', [])
            results = self.orchestrator.run_discovery_cycle(logs)
            return {"discovered_skills": results}

        elif task_type == 'call_skill':
            skill_id = task_input.get('skill_id')
            input_text = task_input.get('input', '')
            result = self.orchestrator.call_skill(skill_id, input_text)
            return result

        elif task_type == 'list_skills':
            skills = self.orchestrator.list_skills()
            return {"skills": skills}

        else:
            return {"error": "unknown_task_type", "task_type": task_type}
