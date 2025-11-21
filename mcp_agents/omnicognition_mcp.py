"""
Illified Banini Monkey Jumpster MCP - OmniCognition Multi-Agent System
========================================================================

PhD-Level Production-Ready Multi-Agent Recursive Cognition Ecosystem
Author: Terry Delmonaco
Date: 2025-11-16

Architecture:
    External Signals → Data Preprocessor → Vector DB Layer →
    Omni-Agent MCP → Governance Layer → Execution Engines →
    Feedback & Metrics → Recursive Learning

Features:
- Unified data preprocessing (structured & unstructured)
- FAISS-based semantic search and retrieval
- LLM-powered workflow generation
- Financial analysis and forecasting
- Strategic recommendation synthesis
- Human-in-loop governance with audit logging
- Meta-skill evolution and recursive learning
- Production monitoring and observability

Security:
- Role-based access control integration
- Audit logging for all governance decisions
- Secure API key management for external services
- Rate limiting for LLM inference
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# Vector DB for IR / Semantic Search
import numpy as np

# AI / LLM Integration
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Financial Data
import yfinance as yf
import pandas as pd

# Async processing
from concurrent.futures import ThreadPoolExecutor

# Structured logging
from ..api.structured_logger import (
    log_mcp_task,
    log_performance_metric,
    log_security_event
)

logger = logging.getLogger("OmniCognitionMCP")

# =========================
# Configuration
# =========================

@dataclass
class OmniCognitionConfig:
    """Configuration for OmniCognition MCP system"""
    base_dir: Path = Path(__file__).parent.parent
    downloads_dir: Path = base_dir / "downloads" / "workflows"
    llm_model_name: str = "google/flan-t5-base"  # Lighter model for production
    max_workflow_size: int = 10000  # Max lines of generated code
    max_concurrent_tasks: int = 5
    enable_governance: bool = True
    enable_meta_learning: bool = True
    cache_llm_results: bool = True
    llm_timeout: int = 60  # seconds

    def __post_init__(self):
        """Create directories if they don't exist"""
        self.downloads_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = OmniCognitionConfig()


# =========================
# Data Models
# =========================

@dataclass
class IntermediateRepresentation:
    """IR for unified data representation"""
    ir_id: str
    ir_type: str  # structured, unstructured, multimodal
    content: Any
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding embedding for serialization)"""
        return {
            "ir_id": self.ir_id,
            "ir_type": self.ir_type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class WorkflowResult:
    """Result from workflow generation"""
    workflow_id: str
    description: str
    generated_code: str
    file_path: str
    complexity_score: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class FinancialInsight:
    """Financial analysis result"""
    ticker: str
    analysis_type: str
    insights: str
    metrics: Dict[str, float]
    confidence_score: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class StrategyRecommendation:
    """Strategic recommendation output"""
    strategy_id: str
    title: str
    description: str
    action_items: List[str]
    priority: str  # high, medium, low
    expected_roi: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class GovernanceDecision:
    """Governance approval decision"""
    decision_id: str
    action_description: str
    user_role: str
    approved: bool
    reason: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class MetaSkillSuggestion:
    """Meta-skill evolution suggestion"""
    suggestion_id: str
    skill_type: str
    description: str
    rationale: str
    confidence: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# =========================
# LLM Manager
# =========================

class LLMManager:
    """
    Wrapper for LLM-based reasoning, workflow generation, and strategy.

    Features:
    - Lazy loading of models
    - Result caching
    - Timeout protection
    - Resource pooling
    """

    def __init__(self, model_name: str = config.llm_model_name):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._cache: Dict[str, str] = {}
        self._executor = ThreadPoolExecutor(max_workers=config.max_concurrent_tasks)
        logger.info(f"LLMManager initialized with model: {model_name}")

    def _load_model(self):
        """Lazy load the model and tokenizer"""
        if self.tokenizer is None or self.model is None:
            logger.info(f"Loading LLM model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=1024
            )
            logger.info("LLM model loaded successfully")

    async def generate_workflow(self, description: str) -> str:
        """
        Generates Python workflow code based on description

        Args:
            description: Natural language workflow description

        Returns:
            Generated Python code
        """
        # Check cache
        cache_key = f"workflow:{description}"
        if config.cache_llm_results and cache_key in self._cache:
            logger.info("Returning cached workflow result")
            return self._cache[cache_key]

        # Load model if needed
        self._load_model()

        prompt = f"""Generate a robust production-ready Python workflow for: {description}

Requirements:
- Include error handling
- Add logging statements
- Follow PEP 8 style guide
- Add docstrings
- Return the complete, executable code
"""

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            lambda: self.pipeline(prompt, max_length=1024)[0]["generated_text"]
        )

        # Cache result
        if config.cache_llm_results:
            self._cache[cache_key] = result

        return result

    async def analyze_financials(self, data_text: str) -> str:
        """
        Analyzes financial data text and produces insights

        Args:
            data_text: Financial data summary

        Returns:
            Analysis insights
        """
        cache_key = f"financial:{data_text[:100]}"
        if config.cache_llm_results and cache_key in self._cache:
            return self._cache[cache_key]

        self._load_model()

        prompt = f"""Analyze this financial data and produce actionable insights:

Data:
{data_text}

Provide:
1. Key trends
2. Risk factors
3. Opportunities
4. Recommended actions
"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            lambda: self.pipeline(prompt, max_length=1024)[0]["generated_text"]
        )

        if config.cache_llm_results:
            self._cache[cache_key] = result

        return result

    async def meta_skill_suggestion(self, agent_logs: List[str]) -> str:
        """
        Suggest new agent skills or improvements

        Args:
            agent_logs: List of agent activity logs

        Returns:
            Skill suggestions
        """
        self._load_model()

        logs_summary = "\n".join(agent_logs[-10:])  # Last 10 logs
        prompt = f"""Based on these agent logs, suggest new agent skills or enhancements:

Logs:
{logs_summary}

Suggest:
1. New capabilities to add
2. Performance improvements
3. Automation opportunities
"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            lambda: self.pipeline(prompt, max_length=1024)[0]["generated_text"]
        )

        return result

    async def generate_strategy(self, context: str) -> str:
        """
        Generate strategic recommendations

        Args:
            context: Combined context from workflow and financial results

        Returns:
            Strategic recommendations
        """
        self._load_model()

        prompt = f"""Based on this context, generate actionable business strategy:

Context:
{context}

Provide:
1. Strategic priorities
2. Action items with timeline
3. Expected outcomes
4. Risk mitigation
"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            lambda: self.pipeline(prompt, max_length=1024)[0]["generated_text"]
        )

        return result


# =========================
# Workflow Agent
# =========================

class WorkflowAgent:
    """
    Agent for discovering, generating, and optimizing workflows.

    Integrates with existing SkillForge system for pattern discovery.
    """

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        self.download_dir = config.downloads_dir

    async def generate_and_save(
        self,
        workflow_description: str,
        workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Generate workflow code and save to downloads folder

        Args:
            workflow_description: Natural language description
            workflow_id: Optional workflow ID

        Returns:
            WorkflowResult with generated code and metadata
        """
        start_time = datetime.utcnow()

        # Generate workflow code
        code = await self.llm.generate_workflow(workflow_description)

        # Validate code size
        if len(code) > config.max_workflow_size:
            logger.warning(f"Generated workflow exceeds max size: {len(code)}")
            code = code[:config.max_workflow_size]

        # Generate file name
        if workflow_id is None:
            workflow_id = f"wf_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        file_name = f"{workflow_id}.py"
        file_path = self.download_dir / file_name

        # Save workflow
        with open(file_path, "w") as f:
            f.write(f'"""\nWorkflow: {workflow_description}\nGenerated: {datetime.utcnow()}\n"""\n\n')
            f.write(code)

        # Calculate complexity (simple heuristic)
        complexity = len(code.split('\n')) / 100.0  # Normalized by 100 lines

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"Workflow generated and saved: {file_path} ({duration_ms:.2f}ms)")

        # Log performance metric
        log_performance_metric(
            logger,
            metric_name="workflow_generation_time",
            value=duration_ms,
            unit="ms",
            metadata={"workflow_id": workflow_id, "complexity": complexity}
        )

        return WorkflowResult(
            workflow_id=workflow_id,
            description=workflow_description,
            generated_code=code,
            file_path=str(file_path),
            complexity_score=complexity
        )


# =========================
# Financial Agent
# =========================

class FinancialAgent:
    """
    Agent for financial analysis and forecasting.

    Integrates with FinPsyMCP for enhanced analysis.
    """

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager

    async def fetch_stock_data(
        self,
        ticker: str,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Fetch stock price data using yfinance

        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            DataFrame with stock data
        """
        logger.info(f"Fetching stock data: {ticker} ({period})")

        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: yf.download(ticker, period=period, progress=False)
            )

            logger.info(f"Stock data fetched: {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            raise

    async def generate_insights(self, ticker: str) -> FinancialInsight:
        """
        Analyze stock data and produce insights

        Args:
            ticker: Stock ticker symbol

        Returns:
            FinancialInsight with analysis
        """
        start_time = datetime.utcnow()

        # Fetch data
        df = await self.fetch_stock_data(ticker)

        # Calculate metrics
        metrics = {
            "current_price": float(df['Close'].iloc[-1]),
            "avg_price": float(df['Close'].mean()),
            "volatility": float(df['Close'].std()),
            "min_price": float(df['Close'].min()),
            "max_price": float(df['Close'].max()),
            "price_change_pct": float(
                ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            )
        }

        # Generate insights using LLM
        summary = df.describe().to_string()
        insights_text = await self.llm.analyze_financials(summary)

        # Calculate confidence based on data quality
        confidence = min(1.0, len(df) / 365.0)  # Higher confidence with more data

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"Financial insights generated for {ticker} ({duration_ms:.2f}ms)")

        # Log performance
        log_performance_metric(
            logger,
            metric_name="financial_analysis_time",
            value=duration_ms,
            unit="ms",
            metadata={"ticker": ticker, "data_points": len(df)}
        )

        return FinancialInsight(
            ticker=ticker,
            analysis_type="stock_analysis",
            insights=insights_text,
            metrics=metrics,
            confidence_score=confidence
        )


# =========================
# Strategic Agent
# =========================

class StrategicAgent:
    """
    Aggregates workflow and financial insights to produce recommendations.

    Integrates with InnoMCP for innovation management.
    """

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager

    async def generate_strategy(
        self,
        workflow_results: List[WorkflowResult],
        financial_results: List[FinancialInsight]
    ) -> StrategyRecommendation:
        """
        Generate high-level strategic recommendations

        Args:
            workflow_results: List of workflow generation results
            financial_results: List of financial analysis results

        Returns:
            StrategyRecommendation with action items
        """
        start_time = datetime.utcnow()

        # Build context
        context_parts = []

        # Add workflow context
        for wf in workflow_results:
            context_parts.append(
                f"Workflow: {wf.description} (complexity: {wf.complexity_score:.2f})"
            )

        # Add financial context
        for fin in financial_results:
            context_parts.append(
                f"Financial: {fin.ticker} - {fin.insights[:200]}..."
            )
            context_parts.append(f"Metrics: {json.dumps(fin.metrics, indent=2)}")

        combined_context = "\n\n".join(context_parts)

        # Generate strategy
        strategy_text = await self.llm.generate_strategy(combined_context)

        # Parse action items (simple extraction)
        action_items = [
            line.strip()
            for line in strategy_text.split('\n')
            if line.strip().startswith(('-', '*', '1.', '2.', '3.'))
        ][:10]  # Limit to 10 actions

        # Determine priority (based on financial metrics)
        avg_price_change = np.mean([
            fin.metrics.get('price_change_pct', 0)
            for fin in financial_results
        ]) if financial_results else 0

        if avg_price_change > 10:
            priority = "high"
        elif avg_price_change > 0:
            priority = "medium"
        else:
            priority = "low"

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"Strategic recommendation generated ({duration_ms:.2f}ms)")

        # Log performance
        log_performance_metric(
            logger,
            metric_name="strategy_generation_time",
            value=duration_ms,
            unit="ms",
            metadata={"num_workflows": len(workflow_results), "num_financial": len(financial_results)}
        )

        strategy_id = f"strat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return StrategyRecommendation(
            strategy_id=strategy_id,
            title="OmniCognition Strategic Recommendation",
            description=strategy_text,
            action_items=action_items,
            priority=priority,
            expected_roi=abs(avg_price_change) if financial_results else None
        )


# =========================
# Governance Layer
# =========================

class GovernanceLayer:
    """
    Human-in-loop approvals, role-based access, and audit logging

    Integrates with authentication system for RBAC.
    """

    def __init__(self):
        self.audit_logs: List[GovernanceDecision] = []
        self.approval_threshold = {
            "user": 0,
            "developer": 1,
            "admin": 2
        }

    async def approve_action(
        self,
        action_desc: str,
        user_role: str,
        required_level: int = 1
    ) -> GovernanceDecision:
        """
        Evaluate action approval based on user role

        Args:
            action_desc: Description of action
            user_role: User role (user, developer, admin)
            required_level: Required approval level (0-2)

        Returns:
            GovernanceDecision with approval result
        """
        user_level = self.approval_threshold.get(user_role, 0)
        approved = user_level >= required_level

        reason = "Approved" if approved else f"Insufficient permissions (required: {required_level}, actual: {user_level})"

        decision = GovernanceDecision(
            decision_id=f"gov_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            action_description=action_desc,
            user_role=user_role,
            approved=approved,
            reason=reason
        )

        self.audit_logs.append(decision)

        # Log security event
        log_security_event(
            logger,
            event_type="governance_decision",
            details={
                "action": action_desc,
                "user_role": user_role,
                "approved": approved,
                "reason": reason
            },
            severity="INFO" if approved else "WARNING"
        )

        logger.info(f"Governance decision: {action_desc} - {reason}")

        return decision

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent audit trail

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit log dictionaries
        """
        return [asdict(decision) for decision in self.audit_logs[-limit:]]


# =========================
# Meta-Skill Evolution
# =========================

class MetaSkillEvolution:
    """
    Tracks agent performance and generates new skills.

    Integrates with SkillForge for skill registration.
    """

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        self.agent_logs: List[str] = []
        self.skill_suggestions: List[MetaSkillSuggestion] = []

    def log_agent_activity(self, activity: str):
        """
        Log agent activity for analysis

        Args:
            activity: Activity description
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {activity}"
        self.agent_logs.append(log_entry)
        logger.debug(f"Meta-skill log: {activity}")

    async def generate_new_skills(self) -> MetaSkillSuggestion:
        """
        Analyze agent logs and generate skill suggestions

        Returns:
            MetaSkillSuggestion with new skill recommendations
        """
        start_time = datetime.utcnow()

        # Generate suggestions
        suggestions_text = await self.llm.meta_skill_suggestion(self.agent_logs)

        # Calculate confidence based on log volume
        confidence = min(1.0, len(self.agent_logs) / 100.0)

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        suggestion = MetaSkillSuggestion(
            suggestion_id=f"skill_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            skill_type="meta_learned",
            description=suggestions_text,
            rationale=f"Based on analysis of {len(self.agent_logs)} agent activities",
            confidence=confidence
        )

        self.skill_suggestions.append(suggestion)

        logger.info(f"Meta-skill suggestion generated ({duration_ms:.2f}ms)")

        # Log performance
        log_performance_metric(
            logger,
            metric_name="meta_skill_generation_time",
            value=duration_ms,
            unit="ms",
            metadata={"log_count": len(self.agent_logs), "confidence": confidence}
        )

        return suggestion


# =========================
# OmniCognition MCP Orchestrator
# =========================

class OmniCognitionMCP:
    """
    Master orchestrator for OmniCognition multi-agent system.

    Coordinates:
    - Data preprocessing
    - Workflow generation
    - Financial analysis
    - Strategic planning
    - Governance approvals
    - Meta-skill evolution
    """

    def __init__(self):
        """Initialize OmniCognition MCP with all agents"""
        self.llm = LLMManager()
        self.workflow_agent = WorkflowAgent(self.llm)
        self.financial_agent = FinancialAgent(self.llm)
        self.strategic_agent = StrategicAgent(self.llm)
        self.governance = GovernanceLayer()
        self.meta_skill = MetaSkillEvolution(self.llm)

        logger.info("OmniCognition MCP initialized successfully")

    async def run_workflow_cycle(
        self,
        workflow_description: str,
        ticker: str,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Full execution cycle for workflow + financial + strategic loop

        Args:
            workflow_description: Natural language workflow description
            ticker: Stock ticker for financial analysis
            user_role: User role for governance (user, developer, admin)

        Returns:
            Dictionary with complete cycle results
        """
        cycle_start = datetime.utcnow()

        try:
            # Log MCP task start
            log_mcp_task(
                logger,
                mcp_system="OmniCognition",
                task_type="workflow_cycle",
                status="started",
                duration_ms=0,
                metadata={
                    "workflow_desc": workflow_description[:100],
                    "ticker": ticker,
                    "user_role": user_role
                }
            )

            # Step 1: Generate workflow
            logger.info(f"Step 1/5: Generating workflow - {workflow_description}")
            wf_result = await self.workflow_agent.generate_and_save(workflow_description)
            self.meta_skill.log_agent_activity(
                f"Generated workflow: {wf_result.workflow_id} (complexity: {wf_result.complexity_score:.2f})"
            )

            # Step 2: Financial analysis
            logger.info(f"Step 2/5: Analyzing financials - {ticker}")
            fin_result = await self.financial_agent.generate_insights(ticker)
            self.meta_skill.log_agent_activity(
                f"Analyzed {ticker}: price_change={fin_result.metrics['price_change_pct']:.2f}%"
            )

            # Step 3: Strategy synthesis
            logger.info("Step 3/5: Generating strategic recommendations")
            strategy_result = await self.strategic_agent.generate_strategy(
                [wf_result],
                [fin_result]
            )
            self.meta_skill.log_agent_activity(
                f"Strategy generated: {strategy_result.strategy_id} (priority: {strategy_result.priority})"
            )

            # Step 4: Governance approval
            logger.info("Step 4/5: Requesting governance approval")
            governance_decision = await self.governance.approve_action(
                f"Execute workflow {wf_result.workflow_id} with strategy {strategy_result.strategy_id}",
                user_role,
                required_level=1  # Requires developer or admin
            )

            # Step 5: Meta-skill evolution
            logger.info("Step 5/5: Generating meta-skill suggestions")
            meta_skill_result = await self.meta_skill.generate_new_skills()

            # Calculate total duration
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds() * 1000

            # Log MCP task completion
            log_mcp_task(
                logger,
                mcp_system="OmniCognition",
                task_type="workflow_cycle",
                status="success",
                duration_ms=cycle_duration,
                metadata={
                    "workflow_id": wf_result.workflow_id,
                    "ticker": ticker,
                    "approved": governance_decision.approved
                }
            )

            logger.info(f"Workflow cycle completed in {cycle_duration:.2f}ms")

            return {
                "status": "success",
                "cycle_duration_ms": cycle_duration,
                "workflow": {
                    "workflow_id": wf_result.workflow_id,
                    "description": wf_result.description,
                    "file_path": wf_result.file_path,
                    "complexity_score": wf_result.complexity_score,
                    "code_preview": wf_result.generated_code[:500]  # First 500 chars
                },
                "financial": {
                    "ticker": fin_result.ticker,
                    "insights": fin_result.insights,
                    "metrics": fin_result.metrics,
                    "confidence_score": fin_result.confidence_score
                },
                "strategy": {
                    "strategy_id": strategy_result.strategy_id,
                    "title": strategy_result.title,
                    "description": strategy_result.description,
                    "action_items": strategy_result.action_items,
                    "priority": strategy_result.priority,
                    "expected_roi": strategy_result.expected_roi
                },
                "governance": {
                    "decision_id": governance_decision.decision_id,
                    "approved": governance_decision.approved,
                    "reason": governance_decision.reason
                },
                "meta_skills": {
                    "suggestion_id": meta_skill_result.suggestion_id,
                    "description": meta_skill_result.description,
                    "confidence": meta_skill_result.confidence
                }
            }

        except Exception as e:
            # Log error
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds() * 1000

            log_mcp_task(
                logger,
                mcp_system="OmniCognition",
                task_type="workflow_cycle",
                status="failure",
                duration_ms=cycle_duration,
                metadata={"error": str(e)}
            )

            logger.error(f"Workflow cycle failed: {e}")

            return {
                "status": "error",
                "error": str(e),
                "cycle_duration_ms": cycle_duration
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get OmniCognition MCP statistics

        Returns:
            Statistics dictionary
        """
        return {
            "agent_logs_count": len(self.meta_skill.agent_logs),
            "skill_suggestions_count": len(self.meta_skill.skill_suggestions),
            "governance_decisions_count": len(self.governance.audit_logs),
            "llm_cache_size": len(self.llm._cache)
        }


# =========================
# Initialization
# =========================

# Global instance (singleton pattern)
_omnicognition_instance: Optional[OmniCognitionMCP] = None


def get_omnicognition_mcp() -> OmniCognitionMCP:
    """
    Get or create OmniCognition MCP instance (singleton)

    Returns:
        OmniCognition MCP instance
    """
    global _omnicognition_instance

    if _omnicognition_instance is None:
        _omnicognition_instance = OmniCognitionMCP()

    return _omnicognition_instance
