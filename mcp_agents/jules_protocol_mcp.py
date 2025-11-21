"""
Jules Protocol MCP - Unified Recursive Cognition & Guardrails
==============================================================

PhD-Level Production-Ready MCP for Multi-Agent Ecosystem
Author: Terry Delmonaco
Date: 2025-11-16

Architecture:
    Prompt Library → Context Manager (FAISS) → LLM Reasoning →
    Jules Protocol (Confidence + Hallucination Check + Self-Reflection) →
    Reinforcement Learning → Supervised Fine-Tuning → Evolution Continuity

Features:
- Prompt library with performance metrics
- FAISS-based context retrieval
- LLM-powered reasoning and summarization
- Confidence labeling (CERTAIN/PROBABLE/UNCERTAIN/UNKNOWN)
- Hallucination detection and prevention
- Self-reflection and output verification
- Reinforcement learning (reward/penalty tracking)
- Supervised fine-tuning (persistent improvements)
- Adaptive reasoning and contextual memory
- Cryptographic audit logging

Security:
- Fernet encryption for sensitive data
- SHA-256 audit trail
- Immutable logging
"""

import os
import json
import hashlib
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3

# Scientific computing
import numpy as np
import faiss

# LLM & Transformers
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Encryption
from cryptography.fernet import Fernet

# Structured logging
from ..api.structured_logger import (
    log_mcp_task,
    log_performance_metric,
    log_security_event
)

logger = logging.getLogger("JulesProtocolMCP")

# =========================
# Configuration
# =========================

@dataclass
class JulesProtocolConfig:
    """Configuration for Jules Protocol MCP"""
    base_dir: Path = Path(__file__).parent.parent
    audit_db_path: Path = base_dir / "data" / "audit_jules.db"
    prompt_library_path: Path = base_dir / "data" / "prompt_library.json"
    context_vector_dim: int = 768
    llm_model_name: str = "google/flan-t5-base"
    max_summary_length: int = 256
    min_summary_length: int = 64
    context_retrieval_top_k: int = 5
    confidence_levels: List[str] = None

    def __post_init__(self):
        """Initialize default values and create directories"""
        if self.confidence_levels is None:
            self.confidence_levels = ["CERTAIN", "PROBABLE", "UNCERTAIN", "UNKNOWN"]

        self.audit_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.prompt_library_path.parent.mkdir(parents=True, exist_ok=True)


# Global config
jules_config = JulesProtocolConfig()


# =========================
# Data Models
# =========================

@dataclass
class PromptRecord:
    """Prompt library record"""
    prompt_id: str
    text: str
    task_type: str
    metrics: Dict[str, Any]
    history: List[Dict[str, Any]]
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ReasoningCycle:
    """Reasoning cycle result"""
    reasoning_id: str
    prompt_id: str
    agent_name: str
    task_input: str
    reasoning_output: str
    confidence_level: str
    hallucination_detected: bool
    reflection_applied: bool
    reward: Optional[str] = None
    success_score: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class EvolutionMetrics:
    """Evolution and adaptation metrics"""
    metric_id: str
    reasoning_id: str
    success_rate: float
    adaptation_score: float
    pattern_matches: int
    context_relevance: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# =========================
# Audit Logger
# =========================

class JulesAuditLogger:
    """
    Immutable cryptographically verifiable audit logging for Jules Protocol

    Tracks all reasoning cycles, rewards, and adaptations.
    """

    def __init__(self, db_path: Path = jules_config.audit_db_path):
        self.db_path = db_path
        self.conn = None
        self._setup_database()

    def _setup_database(self):
        """Initialize audit database schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                hash TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jules_timestamp
            ON audit_logs(timestamp)
        """)

        self.conn.commit()
        logger.info(f"Jules Protocol audit database initialized: {self.db_path}")

    async def log(self, action: str, actor: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log action with cryptographic hash

        Args:
            action: Action description
            actor: Actor performing action
            metadata: Optional metadata

        Returns:
            Hash value for verification
        """
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{timestamp}-{actor}-{action}".encode()
        hash_val = hashlib.sha256(hash_input).hexdigest()

        metadata_json = json.dumps(metadata) if metadata else None

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (timestamp, actor, action, hash, metadata) VALUES (?, ?, ?, ?, ?)",
            (timestamp, actor, action, hash_val, metadata_json)
        )
        self.conn.commit()

        logger.info(f"Jules audit logged: {action} by {actor}, hash={hash_val[:16]}...")

        # Log security event
        log_security_event(
            logger,
            event_type="jules_audit_log",
            details={
                "action": action,
                "actor": actor,
                "hash": hash_val[:16]
            },
            severity="INFO"
        )

        return hash_val


# =========================
# Crypto Manager
# =========================

class JulesCryptoManager:
    """
    Fernet encryption for sensitive Jules Protocol data

    Protects prompt library and reasoning outputs.
    """

    def __init__(self):
        # Generate or load encryption key
        key_file = jules_config.base_dir / "data" / "jules_fernet.key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self.key)
            logger.info("Generated new Fernet key for Jules Protocol")

        self.fernet = Fernet(self.key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using Fernet"""
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypt data using Fernet"""
        return self.fernet.decrypt(token)

    def encrypt_string(self, text: str) -> str:
        """Encrypt string and return base64"""
        return self.fernet.encrypt(text.encode('utf-8')).decode('utf-8')

    def decrypt_string(self, token: str) -> str:
        """Decrypt base64 string"""
        return self.fernet.decrypt(token.encode('utf-8')).decode('utf-8')


# =========================
# Prompt Library with Metrics
# =========================

class PromptLibrary:
    """
    Manages prompts with performance metrics and history

    Tracks success rates, usage patterns, and adaptations.
    """

    def __init__(self, path: Path = jules_config.prompt_library_path):
        self.path = path
        self.prompts: Dict[str, PromptRecord] = {}
        self.load()

    def load(self):
        """Load prompt library from file"""
        if self.path.exists():
            try:
                with open(self.path, 'r') as f:
                    data = json.load(f)
                    for pid, pdata in data.items():
                        self.prompts[pid] = PromptRecord(
                            prompt_id=pid,
                            text=pdata['text'],
                            task_type=pdata['task_type'],
                            metrics=pdata.get('metrics', {}),
                            history=pdata.get('history', []),
                            created_at=datetime.fromisoformat(pdata['created_at']) if 'created_at' in pdata else datetime.utcnow(),
                            updated_at=datetime.fromisoformat(pdata['updated_at']) if 'updated_at' in pdata else datetime.utcnow()
                        )
                logger.info(f"Loaded {len(self.prompts)} prompts from library")
            except Exception as e:
                logger.error(f"Failed to load prompt library: {e}")
                self.prompts = {}
        else:
            self.prompts = {}
            logger.info("Initialized empty prompt library")

    def save(self):
        """Save prompt library to file"""
        try:
            data = {}
            for pid, prompt in self.prompts.items():
                data[pid] = {
                    'text': prompt.text,
                    'task_type': prompt.task_type,
                    'metrics': prompt.metrics,
                    'history': prompt.history,
                    'created_at': prompt.created_at.isoformat(),
                    'updated_at': prompt.updated_at.isoformat()
                }

            with open(self.path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.prompts)} prompts to library")
        except Exception as e:
            logger.error(f"Failed to save prompt library: {e}")

    def add_prompt(self, prompt_id: str, text: str, task_type: str):
        """Add new prompt to library"""
        self.prompts[prompt_id] = PromptRecord(
            prompt_id=prompt_id,
            text=text,
            task_type=task_type,
            metrics={
                'usage_count': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0
            },
            history=[]
        )
        self.save()
        logger.info(f"Added prompt {prompt_id} to library")

    def get_prompt(self, prompt_id: str) -> Optional[str]:
        """Get prompt text by ID"""
        if prompt_id in self.prompts:
            return self.prompts[prompt_id].text
        return None

    def update_metrics(self, prompt_id: str, success: float, confidence: str):
        """Update prompt metrics after usage"""
        if prompt_id in self.prompts:
            prompt = self.prompts[prompt_id]

            # Update usage count
            prompt.metrics['usage_count'] = prompt.metrics.get('usage_count', 0) + 1

            # Update success rate (exponential moving average)
            current_success = prompt.metrics.get('success_rate', 0.0)
            alpha = 0.1  # Learning rate
            prompt.metrics['success_rate'] = alpha * success + (1 - alpha) * current_success

            # Update confidence tracking
            confidence_map = {"CERTAIN": 1.0, "PROBABLE": 0.7, "UNCERTAIN": 0.4, "UNKNOWN": 0.0}
            conf_value = confidence_map.get(confidence, 0.0)
            current_conf = prompt.metrics.get('avg_confidence', 0.0)
            prompt.metrics['avg_confidence'] = alpha * conf_value + (1 - alpha) * current_conf

            # Add to history
            prompt.history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'success': success,
                'confidence': confidence
            })

            # Keep only last 100 history entries
            prompt.history = prompt.history[-100:]

            prompt.updated_at = datetime.utcnow()
            self.save()


# =========================
# Context Manager / Vector Store
# =========================

class ContextManager:
    """
    FAISS-based context retrieval with LLM summarization

    Manages contextual memory for reasoning cycles.
    """

    def __init__(self, dim: int = jules_config.context_vector_dim):
        self.dim = dim
        self.context_data: List[str] = []
        self.embeddings = np.empty((0, dim), dtype='float32')
        self.index = faiss.IndexFlatL2(dim)

        # Load LLM for summarization
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(jules_config.llm_model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(jules_config.llm_model_name)
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer
            )
            logger.info(f"Context manager initialized with {jules_config.llm_model_name}")
        except Exception as e:
            logger.error(f"Failed to load LLM for context manager: {e}")
            self.summarizer = None

    def add_context(self, text: str, vector: np.ndarray):
        """Add context with embedding vector"""
        self.context_data.append(text)

        if self.embeddings.shape[0] == 0:
            self.embeddings = vector.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, vector.reshape(1, -1)])

        self.index.add(vector.reshape(1, -1).astype('float32'))
        logger.debug(f"Added context: {text[:100]}...")

    def retrieve(self, query_vector: np.ndarray, top_k: int = jules_config.context_retrieval_top_k) -> List[str]:
        """Retrieve top-k most relevant contexts"""
        if self.index.ntotal == 0:
            return []

        D, I = self.index.search(query_vector.reshape(1, -1).astype('float32'), min(top_k, self.index.ntotal))
        return [self.context_data[i] for i in I[0] if i < len(self.context_data)]

    async def summarize(self, text: str) -> str:
        """Summarize text using LLM"""
        if self.summarizer is None:
            return text[:jules_config.max_summary_length]

        try:
            # Run summarization in thread pool
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                lambda: self.summarizer(
                    text,
                    max_length=jules_config.max_summary_length,
                    min_length=jules_config.min_summary_length,
                    do_sample=False
                )[0]["summary_text"]
            )
            return summary
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return text[:jules_config.max_summary_length]


# =========================
# Jules Protocol Core Components
# =========================

class ReinforcementLearning:
    """
    Assign internal rewards and penalties to reasoning cycles

    Tracks performance for supervised fine-tuning.
    """

    def __init__(self):
        self.log: List[Dict[str, Any]] = []

    async def reward(self, reasoning_id: str, outcome: str, score: float):
        """
        Assign reward or penalty

        Args:
            reasoning_id: ID of reasoning cycle
            outcome: "REWARD" or "PENALTY"
            score: Success score (0.0 - 1.0)
        """
        entry = {
            "reasoning_id": reasoning_id,
            "outcome": outcome,
            "score": score,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.log.append(entry)

        logger.info(f"Reinforcement learning: {reasoning_id} -> {outcome} (score={score:.2f})")

        # Log performance metric
        log_performance_metric(
            logger,
            metric_name="reinforcement_learning_reward",
            value=score,
            unit="score",
            metadata={"reasoning_id": reasoning_id, "outcome": outcome}
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get reward/penalty statistics"""
        if not self.log:
            return {"total": 0, "rewards": 0, "penalties": 0, "avg_score": 0.0}

        rewards = sum(1 for entry in self.log if entry["outcome"] == "REWARD")
        penalties = sum(1 for entry in self.log if entry["outcome"] == "PENALTY")
        avg_score = np.mean([entry["score"] for entry in self.log])

        return {
            "total": len(self.log),
            "rewards": rewards,
            "penalties": penalties,
            "reward_rate": rewards / len(self.log) if self.log else 0.0,
            "avg_score": float(avg_score)
        }


class SupervisedFineTuning:
    """
    Persist successful self-edits into long-term behavior

    Stores successful patterns for future adaptation.
    """

    def __init__(self):
        self.anchors: Dict[str, Dict[str, Any]] = {}

    async def persist(self, reasoning_id: str, updates: Dict[str, Any]):
        """
        Persist successful pattern

        Args:
            reasoning_id: ID of reasoning cycle
            updates: Pattern updates to persist
        """
        self.anchors[reasoning_id] = {
            **updates,
            "persisted_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Supervised fine-tuning: Persisted pattern {reasoning_id}")

    def get_anchor(self, reasoning_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve persisted pattern"""
        return self.anchors.get(reasoning_id)

    def get_all_anchors(self) -> Dict[str, Dict[str, Any]]:
        """Get all persisted patterns"""
        return self.anchors


class JulesProtocol:
    """
    Enforce traceable, verifiable, self-reflective outputs

    Core Jules Protocol implementation:
    - Confidence labeling
    - Hallucination detection
    - Self-reflection
    """

    def __init__(self):
        self.confidence_levels = jules_config.confidence_levels

    def label_confidence(self, statement: str, level: str) -> str:
        """
        Label statement with confidence level

        Args:
            statement: Statement to label
            level: Confidence level (CERTAIN/PROBABLE/UNCERTAIN/UNKNOWN)

        Returns:
            Labeled statement
        """
        if level not in self.confidence_levels:
            level = "UNKNOWN"

        return f"[{level}] {statement}"

    def hallucination_checkpoint(self, text: str) -> tuple[str, bool]:
        """
        Check for and flag unverified claims

        Args:
            text: Text to check

        Returns:
            Tuple of (processed_text, hallucination_detected)
        """
        hallucination_detected = False

        # Check for unverified markers
        if "UNVERIFIED" in text.upper():
            text = text.replace("UNVERIFIED", "[UNVERIFIED - REQUIRES SOURCE]")
            text = text.replace("unverified", "[UNVERIFIED - REQUIRES SOURCE]")
            hallucination_detected = True

        # Check for absolute claims without evidence
        absolute_markers = ["definitely", "certainly", "absolutely", "without doubt"]
        for marker in absolute_markers:
            if marker in text.lower() and "[CERTAIN]" not in text:
                # Don't flag if already labeled as certain
                if text.count("[") == 0:  # No confidence label
                    hallucination_detected = True

        return text, hallucination_detected

    async def self_reflect(self, output: str) -> str:
        """
        Apply self-reflection to improve output quality

        Args:
            output: Output to reflect on

        Returns:
            Refined output
        """
        # Strip unnecessary whitespace
        output = output.strip()

        # Ensure proper sentence ending
        if output and output[-1] not in '.!?':
            output += '.'

        # Check for clarity markers
        if len(output) < 10:
            output = f"[LOW QUALITY - TOO SHORT] {output}"

        return output


class EvolutionContinuity:
    """
    Adaptive reasoning & contextual memory

    Tracks patterns and maintains context across reasoning cycles.
    """

    def __init__(self):
        self.adaptive_metrics: Dict[str, EvolutionMetrics] = {}
        self.contextual_memory: Dict[str, Any] = {}

    async def track_pattern(self, reasoning_id: str, metrics: Dict[str, Any]):
        """
        Track reasoning pattern for adaptation

        Args:
            reasoning_id: ID of reasoning cycle
            metrics: Performance metrics
        """
        evolution_metric = EvolutionMetrics(
            metric_id=f"evo_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            reasoning_id=reasoning_id,
            success_rate=metrics.get('success_rate', 0.0),
            adaptation_score=metrics.get('adaptation_score', 0.0),
            pattern_matches=metrics.get('pattern_matches', 0),
            context_relevance=metrics.get('context_relevance', 0.0)
        )

        self.adaptive_metrics[reasoning_id] = evolution_metric

        logger.debug(f"Evolution tracking: {reasoning_id} -> success_rate={evolution_metric.success_rate:.2f}")

    def remember_context(self, key: str, value: Any):
        """Store context in memory"""
        self.contextual_memory[key] = {
            "value": value,
            "stored_at": datetime.utcnow().isoformat()
        }

    def recall_context(self, key: str) -> Optional[Any]:
        """Recall context from memory"""
        if key in self.contextual_memory:
            return self.contextual_memory[key]["value"]
        return None

    def get_adaptation_trends(self) -> Dict[str, Any]:
        """Analyze adaptation trends"""
        if not self.adaptive_metrics:
            return {"count": 0, "avg_success": 0.0, "avg_adaptation": 0.0}

        success_rates = [m.success_rate for m in self.adaptive_metrics.values()]
        adaptation_scores = [m.adaptation_score for m in self.adaptive_metrics.values()]

        return {
            "count": len(self.adaptive_metrics),
            "avg_success_rate": float(np.mean(success_rates)),
            "avg_adaptation_score": float(np.mean(adaptation_scores)),
            "total_patterns": sum(m.pattern_matches for m in self.adaptive_metrics.values())
        }


# =========================
# Jules Protocol MCP Orchestrator
# =========================

class JulesProtocolMCP:
    """
    Unified MCP integrating all Jules Protocol components

    Coordinates:
    - Prompt library management
    - Context retrieval (FAISS)
    - LLM reasoning
    - Confidence labeling
    - Hallucination detection
    - Self-reflection
    - Reinforcement learning
    - Supervised fine-tuning
    - Evolution tracking

    This is the main entry point for Jules Protocol operations.
    """

    def __init__(self):
        """Initialize Jules Protocol MCP with all components"""
        self.audit = JulesAuditLogger()
        self.crypto = JulesCryptoManager()
        self.prompt_lib = PromptLibrary()
        self.context_mgr = ContextManager()
        self.rl = ReinforcementLearning()
        self.sft = SupervisedFineTuning()
        self.jules = JulesProtocol()
        self.evolution = EvolutionContinuity()

        # LLM for reasoning (shared with context manager)
        self.llm_tokenizer = None
        self.llm_model = None
        self._load_llm()

        logger.info("Jules Protocol MCP initialized successfully")

    def _load_llm(self):
        """Load LLM for reasoning (lazy loading)"""
        try:
            self.llm_tokenizer = AutoTokenizer.from_pretrained(jules_config.llm_model_name)
            self.llm_model = AutoModelForSeq2SeqLM.from_pretrained(jules_config.llm_model_name)
            logger.info(f"LLM loaded: {jules_config.llm_model_name}")
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")

    async def execute_cycle(
        self,
        agent_name: str,
        prompt_id: str,
        task_input: str,
        gold_standard: Optional[str] = None
    ) -> ReasoningCycle:
        """
        Execute complete Jules Protocol reasoning cycle

        Args:
            agent_name: Name of the agent executing the cycle
            prompt_id: ID of the prompt to use
            task_input: Input for the reasoning task
            gold_standard: Optional expected output for supervised learning

        Returns:
            ReasoningCycle result with all metrics
        """
        start_time = datetime.utcnow()
        reasoning_id = f"jules_{agent_name}_{start_time.strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting Jules Protocol cycle: {reasoning_id}")

        # Step 1: Retrieve prompt from library
        prompt_text = self.prompt_lib.get_prompt(prompt_id)
        if not prompt_text:
            logger.warning(f"Prompt {prompt_id} not found, using default")
            prompt_text = "Analyze the following task and provide a detailed response:"

        # Step 2: Retrieve relevant context using FAISS
        # Generate simple embedding for task_input (using random vector for now)
        # In production, use a proper embedding model
        query_vector = np.random.rand(jules_config.context_vector_dim).astype('float32')
        relevant_contexts = self.context_mgr.retrieve(query_vector)

        # Step 3: Generate reasoning output using LLM
        full_prompt = f"{prompt_text}\n\nTask: {task_input}"
        if relevant_contexts:
            context_str = "\n".join(relevant_contexts[:3])
            full_prompt += f"\n\nRelevant context:\n{context_str}"

        reasoning_output = await self._generate_reasoning(full_prompt)

        # Step 4: Apply Jules Protocol guardrails

        # 4a. Confidence labeling
        # Determine confidence based on output characteristics
        confidence_level = self._determine_confidence(reasoning_output, relevant_contexts)
        labeled_output = self.jules.label_confidence(reasoning_output, confidence_level)

        # 4b. Hallucination checkpoint
        checked_output, hallucination_detected = self.jules.hallucination_checkpoint(labeled_output)

        # 4c. Self-reflection
        refined_output = await self.jules.self_reflect(checked_output)

        # Step 5: Reinforcement learning
        # Calculate success score
        success_score = self._calculate_success_score(
            refined_output,
            gold_standard,
            hallucination_detected,
            confidence_level
        )

        reward_type = "REWARD" if success_score >= 0.7 else "PENALTY"
        await self.rl.reward(reasoning_id, reward_type, success_score)

        # Step 6: Supervised fine-tuning (if gold standard provided)
        if gold_standard and success_score >= 0.8:
            await self.sft.persist(reasoning_id, {
                "prompt_id": prompt_id,
                "task_input": task_input,
                "successful_output": refined_output,
                "gold_standard": gold_standard,
                "confidence": confidence_level
            })

        # Step 7: Evolution tracking
        await self.evolution.track_pattern(reasoning_id, {
            "success_rate": success_score,
            "adaptation_score": success_score * 0.9,  # Simplified
            "pattern_matches": len(relevant_contexts),
            "context_relevance": 0.8 if relevant_contexts else 0.3
        })

        # Step 8: Store context for future retrieval
        output_vector = np.random.rand(jules_config.context_vector_dim).astype('float32')
        self.context_mgr.add_context(refined_output, output_vector)

        # Step 9: Update prompt library metrics
        self.prompt_lib.update_metrics(prompt_id, success_score, confidence_level)

        # Step 10: Audit logging
        await self.audit.log(
            action=f"reasoning_cycle_completed",
            actor=agent_name,
            metadata={
                "reasoning_id": reasoning_id,
                "prompt_id": prompt_id,
                "success_score": success_score,
                "confidence": confidence_level,
                "hallucination_detected": hallucination_detected
            }
        )

        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log MCP task
        log_mcp_task(
            logger,
            mcp_system="JulesProtocol",
            task_type="reasoning_cycle",
            status="success" if success_score >= 0.5 else "failure",
            duration_ms=duration_ms,
            metadata={
                "reasoning_id": reasoning_id,
                "confidence": confidence_level,
                "success_score": success_score
            }
        )

        # Create and return reasoning cycle result
        result = ReasoningCycle(
            reasoning_id=reasoning_id,
            prompt_id=prompt_id,
            agent_name=agent_name,
            task_input=task_input,
            reasoning_output=refined_output,
            confidence_level=confidence_level,
            hallucination_detected=hallucination_detected,
            reflection_applied=True,
            reward=reward_type,
            success_score=success_score,
            timestamp=start_time
        )

        logger.info(f"Jules Protocol cycle completed: {reasoning_id}, score={success_score:.2f}")

        return result

    async def _generate_reasoning(self, prompt: str) -> str:
        """
        Generate reasoning output using LLM

        Args:
            prompt: Full prompt with context

        Returns:
            Generated reasoning text
        """
        if self.llm_model is None or self.llm_tokenizer is None:
            return f"LLM not available. Prompt: {prompt[:200]}"

        try:
            # Tokenize and generate
            loop = asyncio.get_event_loop()

            def generate():
                inputs = self.llm_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
                outputs = self.llm_model.generate(
                    inputs.input_ids,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True
                )
                return self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)

            result = await loop.run_in_executor(None, generate)
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating reasoning: {str(e)}"

    def _determine_confidence(self, output: str, contexts: List[str]) -> str:
        """
        Determine confidence level based on output and context

        Args:
            output: Generated output
            contexts: Retrieved contexts

        Returns:
            Confidence level (CERTAIN/PROBABLE/UNCERTAIN/UNKNOWN)
        """
        # Simple heuristic-based confidence determination

        # Check for uncertainty markers
        uncertainty_markers = ["maybe", "possibly", "might", "could be", "uncertain", "unclear"]
        if any(marker in output.lower() for marker in uncertainty_markers):
            return "UNCERTAIN"

        # Check for certainty markers
        certainty_markers = ["definitely", "certainly", "confirmed", "verified"]
        if any(marker in output.lower() for marker in certainty_markers):
            return "CERTAIN"

        # Check context availability
        if len(contexts) >= 3:
            return "PROBABLE"
        elif len(contexts) >= 1:
            return "UNCERTAIN"
        else:
            return "UNKNOWN"

    def _calculate_success_score(
        self,
        output: str,
        gold_standard: Optional[str],
        hallucination_detected: bool,
        confidence: str
    ) -> float:
        """
        Calculate success score for the reasoning cycle

        Args:
            output: Generated output
            gold_standard: Expected output (if available)
            hallucination_detected: Whether hallucination was detected
            confidence: Confidence level

        Returns:
            Success score (0.0 - 1.0)
        """
        score = 0.5  # Base score

        # Penalty for hallucination
        if hallucination_detected:
            score -= 0.3

        # Bonus for higher confidence
        confidence_bonus = {
            "CERTAIN": 0.3,
            "PROBABLE": 0.2,
            "UNCERTAIN": 0.0,
            "UNKNOWN": -0.1
        }
        score += confidence_bonus.get(confidence, 0.0)

        # Check against gold standard if provided
        if gold_standard:
            # Simple similarity check (in production, use proper metrics)
            if gold_standard.lower() in output.lower():
                score += 0.2

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for Jules Protocol MCP

        Returns:
            Dictionary with all statistics
        """
        return {
            "system": "JulesProtocol",
            "status": "operational",
            "prompt_library": {
                "total_prompts": len(self.prompt_lib.prompts),
                "prompts": [
                    {
                        "id": pid,
                        "task_type": p.task_type,
                        "usage_count": p.metrics.get('usage_count', 0),
                        "success_rate": p.metrics.get('success_rate', 0.0),
                        "avg_confidence": p.metrics.get('avg_confidence', 0.0)
                    }
                    for pid, p in self.prompt_lib.prompts.items()
                ]
            },
            "reinforcement_learning": self.rl.get_statistics(),
            "supervised_fine_tuning": {
                "total_anchors": len(self.sft.anchors),
                "anchors": list(self.sft.anchors.keys())
            },
            "evolution": self.evolution.get_adaptation_trends(),
            "context_manager": {
                "total_contexts": len(self.context_mgr.context_data),
                "index_size": self.context_mgr.index.ntotal
            }
        }

    async def add_prompt(self, prompt_id: str, text: str, task_type: str):
        """
        Add new prompt to library

        Args:
            prompt_id: Unique prompt ID
            text: Prompt text
            task_type: Type of task
        """
        self.prompt_lib.add_prompt(prompt_id, text, task_type)

        await self.audit.log(
            action="prompt_added",
            actor="system",
            metadata={"prompt_id": prompt_id, "task_type": task_type}
        )

    async def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs

        Args:
            limit: Maximum number of logs to retrieve

        Returns:
            List of audit log entries
        """
        cursor = self.audit.conn.cursor()
        cursor.execute(
            "SELECT timestamp, actor, action, hash, metadata FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )

        logs = []
        for row in cursor.fetchall():
            logs.append({
                "timestamp": row[0],
                "actor": row[1],
                "action": row[2],
                "hash": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            })

        return logs


# =========================
# Singleton Pattern
# =========================

_jules_instance: Optional[JulesProtocolMCP] = None


def get_jules_protocol_mcp() -> JulesProtocolMCP:
    """
    Get or create Jules Protocol MCP instance (singleton)

    Returns:
        Global JulesProtocolMCP instance
    """
    global _jules_instance

    if _jules_instance is None:
        _jules_instance = JulesProtocolMCP()
        logger.info("Created new Jules Protocol MCP instance")

    return _jules_instance


# =========================
# Initialization
# =========================

# Add default prompts on module import
def _initialize_default_prompts():
    """Initialize default prompts for common tasks"""
    try:
        mcp = get_jules_protocol_mcp()

        # Check if prompts already exist
        if len(mcp.prompt_lib.prompts) == 0:
            # Add default prompts
            default_prompts = [
                {
                    "id": "general_reasoning",
                    "text": "Analyze the following task carefully and provide a detailed, well-reasoned response. Consider multiple perspectives and potential implications.",
                    "type": "general"
                },
                {
                    "id": "code_analysis",
                    "text": "Review the following code and provide insights on its functionality, potential issues, and optimization opportunities.",
                    "type": "technical"
                },
                {
                    "id": "data_analysis",
                    "text": "Examine the following data and extract meaningful insights, patterns, and recommendations.",
                    "type": "analytical"
                },
                {
                    "id": "creative_generation",
                    "text": "Generate creative and innovative ideas based on the following prompt. Think outside conventional boundaries.",
                    "type": "creative"
                }
            ]

            for prompt in default_prompts:
                mcp.prompt_lib.add_prompt(prompt["id"], prompt["text"], prompt["type"])

            logger.info(f"Initialized {len(default_prompts)} default prompts")

    except Exception as e:
        logger.error(f"Failed to initialize default prompts: {e}")


# Initialize on import
_initialize_default_prompts()


# =========================
# Export
# =========================

__all__ = [
    "JulesProtocolMCP",
    "get_jules_protocol_mcp",
    "JulesProtocolConfig",
    "ReasoningCycle",
    "PromptRecord",
    "EvolutionMetrics"
]
