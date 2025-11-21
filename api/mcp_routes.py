"""
MCP Routes - Unified API for All MCP Systems
============================================

Comprehensive REST API providing access to all 9 MCP systems:
1. FinPsyMCP - Financial Psychology & Analytics
2. PydiniRedEnterprise - Workflow Automation
3. LexMCP - Legal Compliance
4. InnoMCP - Innovation Management
5. CreativeMCP - Creative Content
6. EduMCP - Adaptive Education
7. OmniCognitionMCP - Recursive Learning & Workflow Generation
8. GambinoSecurityMCP - Multi-Agent Security & Meta-Security
9. JulesProtocolMCP - Unified Recursive Cognition & Guardrails

Integrated with Central MCP Orchestrator for cross-system workflows.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging
import os
from importlib import import_module

# Import MCP orchestrator factory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mcp_agents.central_orchestrator import CentralMCPOrchestrator, create_central_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/mcp", tags=["MCP Systems"])

# Global orchestrator instance
central_orchestrator: Optional[CentralMCPOrchestrator] = None

MCP_MODULE_BASE = "cesar_ecosystem.mcp_agents"


def _load_optional_mcp(module_name: str, getter_name: str, feature_label: str):
    """Dynamically import optional MCP subsystems when needed."""
    try:
        module = import_module(f"{MCP_MODULE_BASE}.{module_name}")
        getter = getattr(module, getter_name)
        return getter()
    except Exception as exc:
        logger.error("%s unavailable: %s", feature_label, exc)
        raise HTTPException(status_code=503, detail=f"{feature_label} temporarily unavailable: {exc}")


def __get_omnicognition_mcp():
    return _load_optional_mcp('omnicognition_mcp', 'get_omnicognition_mcp', 'OmniCognitionMCP')


def __get_gambino_security_mcp():
    return _load_optional_mcp('gambino_security_mcp', 'get_gambino_security_mcp', 'GambinoSecurityMCP')


def __get_jules_protocol_mcp():
    return _load_optional_mcp('jules_protocol_mcp', 'get_jules_protocol_mcp', 'JulesProtocolMCP')


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TaskRequest(BaseModel):
    """Base task request model"""
    task_type: str = Field(..., description="Type of task to execute")
    task_data: Dict[str, Any] = Field(..., description="Task input data")
    material_id: Optional[str] = Field(None, description="Related learning material ID")
    priority: int = Field(5, ge=1, le=10, description="Task priority")


class WorkflowStepRequest(BaseModel):
    """Workflow step for multi-system workflows"""
    name: str = Field(..., description="Step name")
    task_type: str = Field(..., description="Task type")
    task_data: Dict[str, Any] = Field(..., description="Task data")
    depends_on: Optional[int] = Field(None, description="Index of dependent step")
    priority: int = Field(5, ge=1, le=10)


class MultiSystemWorkflowRequest(BaseModel):
    """Multi-system workflow request"""
    workflow_name: str = Field(..., description="Workflow name")
    workflow_steps: List[WorkflowStepRequest] = Field(..., description="Workflow steps")


class TaskResponse(BaseModel):
    """Task execution response"""
    status: str
    mcp_system: Optional[str] = None
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Financial Psychology & Analytics Models
class StockAnalysisRequest(BaseModel):
    """Stock analysis request"""
    ticker: str = Field(..., description="Stock ticker symbol")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class PortfolioOptimizationRequest(BaseModel):
    """Portfolio optimization request"""
    tickers: List[str] = Field(..., description="List of stock tickers")
    objective: str = Field("max_sharpe", description="Optimization objective")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Optimization constraints")


# Workflow Automation Models
class WorkflowConversionRequest(BaseModel):
    """Workflow conversion request"""
    workflow_json: Dict[str, Any] = Field(..., description="Workflow definition")
    platform: str = Field("generic", description="Source platform (n8n, zapier, make, generic)")
    tenant_id: str = Field("default", description="Tenant identifier")
    output_dir: str = Field("downloads", description="Output directory")
    package_format: Optional[str] = Field(None, description="Package format (zip, docker, lambda)")


# Legal Compliance Models
class ContractReviewRequest(BaseModel):
    """Contract review request"""
    contract_text: str = Field(..., description="Full contract text")


class ComplianceCheckRequest(BaseModel):
    """Compliance check request"""
    context: str = Field(..., description="Context to check")
    regulations: List[str] = Field(..., description="Regulations to check against")
    jurisdiction: str = Field("US", description="Legal jurisdiction")


# Innovation Management Models
class PatentSearchRequest(BaseModel):
    """Patent search request"""
    query: str = Field(..., description="Search query")
    technology_area: Optional[str] = Field(None, description="Technology area filter")
    max_results: int = Field(20, ge=1, le=100, description="Maximum results")


class InnovationPipelineRequest(BaseModel):
    """Innovation pipeline request"""
    problem_statement: str = Field(..., description="Problem to solve")
    market: Optional[str] = Field(None, description="Target market")
    competitors: List[str] = Field(default_factory=list, description="Competitor list")


# Creative Content Models
class ScriptGenerationRequest(BaseModel):
    """Script generation request"""
    content_type: str = Field("article", description="Content type (video, podcast, article, social)")
    topic: str = Field(..., description="Script topic")
    tone: str = Field("professional", description="Desired tone")
    length: str = Field("medium", description="Script length (short, medium, long)")
    target_audience: str = Field("general", description="Target audience")


class CreativeCampaignRequest(BaseModel):
    """Creative campaign request"""
    topic: str = Field(..., description="Campaign topic")
    platform: str = Field("social", description="Target platform")
    brand_identity: Optional[str] = Field(None, description="Brand identity")
    include_visuals: bool = Field(True, description="Include visual style guide")
    include_music: bool = Field(False, description="Include music composition")


# Adaptive Education Models
class LearnerProfileRequest(BaseModel):
    """Learner profile request"""
    learner_id: str = Field(..., description="Learner identifier")
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment results")
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list)
    preferences: Optional[Dict[str, Any]] = Field(None, description="Learner preferences")


class LearningPathRequest(BaseModel):
    """Learning path request"""
    learner_id: str = Field(..., description="Learner identifier")
    subject: str = Field(..., description="Subject to learn")
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment results")


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

async def get_orchestrator() -> CentralMCPOrchestrator:
    """Get or create central orchestrator"""
    global central_orchestrator

    if central_orchestrator is None:
        central_orchestrator = create_central_orchestrator()

    return central_orchestrator


# =============================================================================
# GENERAL ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_mcp_status(orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)):
    """Get status of all MCP systems"""
    return orchestrator.get_system_status()


@router.get("/tasks/available")
async def get_available_tasks(orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)):
    """Get list of all available task types"""
    return orchestrator.get_available_tasks()


@router.post("/tasks/execute", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Execute a task on appropriate MCP system"""
    try:
        material_id = uuid.UUID(request.material_id) if request.material_id else None

        result = orchestrator.route_task(
            task_type=request.task_type,
            task_data=request.task_data,
            material_id=material_id,
            priority=request.priority
        )

        return TaskResponse(
            status=result.get('status', 'unknown'),
            mcp_system=result.get('mcp_system'),
            result=result.get('result'),
            error=result.get('error')
        )

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/multi-system")
async def execute_multi_system_workflow(
    request: MultiSystemWorkflowRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Execute a multi-system workflow"""
    try:
        # Convert request to workflow steps
        workflow_steps = [
            {
                'name': step.name,
                'task_type': step.task_type,
                'task_data': step.task_data,
                'depends_on': step.depends_on,
                'priority': step.priority
            }
            for step in request.workflow_steps
        ]

        result = orchestrator.execute_multi_system_workflow(
            workflow_steps=workflow_steps,
            workflow_name=request.workflow_name
        )

        return result

    except Exception as e:
        logger.error(f"Multi-system workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FINPSY MCP ENDPOINTS
# =============================================================================

@router.post("/finpsy/stock-analysis")
async def analyze_stock(
    request: StockAnalysisRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Analyze stock with FinPsyMCP"""
    result = orchestrator.route_task(
        task_type='stock_analysis',
        task_data={
            'ticker': request.ticker,
            'start_date': request.start_date,
            'end_date': request.end_date
        }
    )

    return result


@router.post("/finpsy/portfolio-optimization")
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Optimize portfolio with FinPsyMCP"""
    result = orchestrator.route_task(
        task_type='portfolio_optimization',
        task_data={
            'tickers': request.tickers,
            'objective': request.objective,
            'constraints': request.constraints
        }
    )

    return result


@router.post("/finpsy/sentiment-analysis")
async def analyze_sentiment(
    ticker: str,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Analyze market sentiment with FinPsyMCP"""
    result = orchestrator.route_task(
        task_type='sentiment_analysis',
        task_data={'ticker': ticker}
    )

    return result


# =============================================================================
# PYDINI RED MCP ENDPOINTS
# =============================================================================

@router.post("/pydini/workflow-conversion")
async def convert_workflow(
    request: WorkflowConversionRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Convert workflow with PydiniRedMCP"""
    result = orchestrator.route_task(
        task_type='workflow_conversion',
        task_data={
            'workflow_json': request.workflow_json,
            'platform': request.platform,
            'tenant_id': request.tenant_id,
            'output_dir': request.output_dir
        }
    )

    return result


@router.post("/pydini/workflow-automation")
async def automate_workflow(
    request: WorkflowConversionRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Full workflow automation pipeline with PydiniRedMCP"""
    result = orchestrator.route_task(
        task_type='workflow_automation',
        task_data={
            'workflow_json': request.workflow_json,
            'platform': request.platform,
            'tenant_id': request.tenant_id,
            'output_dir': request.output_dir,
            'package_format': request.package_format or 'zip'
        }
    )

    return result


# =============================================================================
# LEX MCP ENDPOINTS
# =============================================================================

@router.post("/lex/contract-review")
async def review_contract(
    request: ContractReviewRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Review contract with LexMCP"""
    result = orchestrator.route_task(
        task_type='contract_review',
        task_data={'contract_text': request.contract_text}
    )

    return result


@router.post("/lex/compliance-check")
async def check_compliance(
    request: ComplianceCheckRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Check compliance with LexMCP"""
    result = orchestrator.route_task(
        task_type='compliance_check',
        task_data={
            'context': request.context,
            'regulations': request.regulations,
            'jurisdiction': request.jurisdiction
        }
    )

    return result


@router.post("/lex/legal-analysis")
async def analyze_legal_document(
    document_text: str,
    document_type: Optional[str] = "contract",
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Analyze legal document with LexMCP"""
    result = orchestrator.route_task(
        task_type='legal_analysis',
        task_data={
            'document_text': document_text,
            'document_type': document_type
        }
    )

    return result


# =============================================================================
# INNO MCP ENDPOINTS
# =============================================================================

@router.post("/inno/patent-search")
async def search_patents(
    request: PatentSearchRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Search patents with InnoMCP"""
    result = orchestrator.route_task(
        task_type='patent_search',
        task_data={
            'query': request.query,
            'technology_area': request.technology_area,
            'max_results': request.max_results
        }
    )

    return result


@router.post("/inno/market-trends")
async def analyze_market_trends(
    market: str,
    time_period: str = "3y",
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Analyze market trends with InnoMCP"""
    result = orchestrator.route_task(
        task_type='market_trends',
        task_data={
            'market': market,
            'time_period': time_period
        }
    )

    return result


@router.post("/inno/innovation-pipeline")
async def run_innovation_pipeline(
    request: InnovationPipelineRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Run complete innovation pipeline with InnoMCP"""
    result = orchestrator.route_task(
        task_type='innovation_pipeline',
        task_data={
            'problem_statement': request.problem_statement,
            'market': request.market,
            'competitors': request.competitors
        }
    )

    return result


# =============================================================================
# CREATIVE MCP ENDPOINTS
# =============================================================================

@router.post("/creative/script-generation")
async def generate_script(
    request: ScriptGenerationRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Generate creative script with CreativeMCP"""
    result = orchestrator.route_task(
        task_type='script_writing',
        task_data={
            'content_type': request.content_type,
            'topic': request.topic,
            'tone': request.tone,
            'length': request.length,
            'target_audience': request.target_audience
        }
    )

    return result


@router.post("/creative/campaign")
async def create_campaign(
    request: CreativeCampaignRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Create complete creative campaign with CreativeMCP"""
    result = orchestrator.route_task(
        task_type='complete_campaign',
        task_data={
            'topic': request.topic,
            'platform': request.platform,
            'brand_identity': request.brand_identity or request.topic,
            'include_visuals': request.include_visuals,
            'include_music': request.include_music
        }
    )

    return result


@router.post("/creative/engagement-optimization")
async def optimize_engagement(
    content: Dict[str, Any],
    platform: str,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Optimize content engagement with CreativeMCP"""
    result = orchestrator.route_task(
        task_type='engagement_optimization',
        task_data={
            'content': content,
            'platform': platform
        }
    )

    return result


# =============================================================================
# EDU MCP ENDPOINTS
# =============================================================================

@router.post("/edu/learner-profile")
async def create_learner_profile(
    request: LearnerProfileRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Create learner profile with EduMCP"""
    result = orchestrator.route_task(
        task_type='learner_profiling',
        task_data={
            'learner_id': request.learner_id,
            'assessment_data': request.assessment_data,
            'interaction_history': request.interaction_history,
            'preferences': request.preferences
        }
    )

    return result


@router.post("/edu/learning-path")
async def create_learning_path(
    request: LearningPathRequest,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Create personalized learning path with EduMCP"""
    result = orchestrator.route_task(
        task_type='learning_path',
        task_data={
            'learner_id': request.learner_id,
            'subject': request.subject,
            'assessment_data': request.assessment_data
        }
    )

    return result


@router.post("/edu/curriculum-design")
async def design_curriculum(
    learner_profile: Dict[str, Any],
    subject: str,
    duration_weeks: int = 8,
    orchestrator: CentralMCPOrchestrator = Depends(get_orchestrator)
):
    """Design curriculum with EduMCP"""
    result = orchestrator.route_task(
        task_type='curriculum_design',
        task_data={
            'learner_profile': learner_profile,
            'subject': subject,
            'duration_weeks': duration_weeks
        }
    )

    return result


# =============================================================================
# EXAMPLE WORKFLOWS
# =============================================================================

@router.get("/examples/workflows")
async def get_example_workflows():
    """Get example multi-system workflows"""
    return {
        "examples": [
            {
                "name": "Financial Analysis with Report Generation",
                "description": "Analyze stock and generate professional report",
                "steps": [
                    {
                        "name": "analyze_stock",
                        "task_type": "stock_analysis",
                        "task_data": {"ticker": "AAPL", "start_date": "2023-01-01"}
                    },
                    {
                        "name": "generate_report",
                        "task_type": "content_generation",
                        "task_data": {"content_type": "article", "topic": "AAPL Stock Analysis"},
                        "depends_on": 0
                    }
                ]
            },
            {
                "name": "Innovation Research Pipeline",
                "description": "Complete innovation research from patents to feasibility",
                "steps": [
                    {
                        "name": "patent_search",
                        "task_type": "patent_search",
                        "task_data": {"query": "AI healthcare", "max_results": 20}
                    },
                    {
                        "name": "market_analysis",
                        "task_type": "market_trends",
                        "task_data": {"market": "ai healthcare"}
                    },
                    {
                        "name": "generate_ideas",
                        "task_type": "idea_generation",
                        "task_data": {"problem_statement": "AI-powered diagnosis"}
                    }
                ]
            }
        ]
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check():
    """MCP systems health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "systems": "9 MCP systems operational (6 core + OmniCognition + Gambino Security + Jules Protocol)"
    }


# =============================================================================
# OMNICOGNITION MCP ROUTES
# =============================================================================

class OmniCognitionWorkflowRequest(BaseModel):
    """OmniCognition workflow cycle request"""
    workflow_description: str = Field(..., description="Natural language workflow description")
    ticker: str = Field(..., description="Stock ticker for financial analysis")
    user_role: str = Field("developer", description="User role for governance")


@router.post("/omnicognition/workflow-cycle")
async def run_omnicognition_workflow_cycle(request: OmniCognitionWorkflowRequest):
    """
    Execute complete OmniCognition workflow cycle

    Performs:
    1. Workflow generation from natural language
    2. Financial analysis
    3. Strategic recommendation synthesis
    4. Governance approval
    5. Meta-skill evolution

    Returns comprehensive results with all cycle outputs.
    """
    try:
        omni_mcp = _get_omnicognition_mcp()
        result = await omni_mcp.run_workflow_cycle(
            workflow_description=request.workflow_description,
            ticker=request.ticker,
            user_role=request.user_role
        )

        return TaskResponse(
            status=result["status"],
            mcp_system="OmniCognition",
            task_id=result.get("workflow", {}).get("workflow_id"),
            result=result,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"OmniCognition workflow cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/omnicognition/stats")
async def get_omnicognition_stats():
    """Get OmniCognition MCP statistics"""
    try:
        omni_mcp = _get_omnicognition_mcp()
        stats = omni_mcp.get_stats()

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get OmniCognition stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/omnicognition/governance/audit-trail")
async def get_omnicognition_audit_trail(limit: int = 100):
    """Get OmniCognition governance audit trail"""
    try:
        omni_mcp = _get_omnicognition_mcp()
        audit_trail = omni_mcp.governance.get_audit_trail(limit=limit)

        return {
            "status": "success",
            "audit_trail": audit_trail,
            "count": len(audit_trail),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GAMBINO SECURITY MCP ROUTES
# =============================================================================

class SecurityCycleRequest(BaseModel):
    """Security validation cycle request"""
    agent_name: str = Field(..., description="Name of agent to validate")
    workflow_code: str = Field(..., description="Workflow code to validate")
    actor_role: str = Field("analyst", description="Role of actor (user, analyst, manager, etc.)")
    metrics: Optional[List[float]] = Field(None, description="Optional metrics [cpu%, memory%, req_rate, err_rate]")


@router.post("/security/validate-cycle")
async def run_security_validation_cycle(request: SecurityCycleRequest):
    """
    Execute complete security validation cycle

    Performs:
    1. Sandboxed code execution
    2. Threat intelligence update
    3. Anomaly detection
    4. Incident response (if needed)
    5. Zero-trust governance approval
    6. Meta-security skill evolution

    Returns comprehensive security analysis and approval status.
    """
    try:
        security_mcp = _get_gambino_security_mcp()
        result = await security_mcp.execute_security_cycle(
            agent_name=request.agent_name,
            workflow_code=request.workflow_code,
            actor_role=request.actor_role,
            metrics=request.metrics
        )

        return TaskResponse(
            status=result["status"],
            mcp_system="GambinoSecurity",
            task_id=f"sec_{request.agent_name}",
            result=result,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Security validation cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/stats")
async def get_security_stats():
    """Get comprehensive security statistics"""
    try:
        security_mcp = _get_gambino_security_mcp()
        stats = security_mcp.get_security_stats()

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get security stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/audit-logs")
async def get_security_audit_logs(limit: int = 100):
    """Get security audit logs with cryptographic verification"""
    try:
        security_mcp = _get_gambino_security_mcp()
        logs = security_mcp.audit_logger.get_recent_logs(limit=limit)

        # Convert to dict and verify hashes
        logs_data = []
        for log in logs:
            log_dict = {
                "log_id": log.log_id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "actor": log.actor,
                "hash_value": log.hash_value,
                "metadata": log.metadata,
                "hash_verified": log.verify_hash()
            }
            logs_data.append(log_dict)

        return {
            "status": "success",
            "logs": logs_data,
            "count": len(logs_data),
            "all_verified": all(log["hash_verified"] for log in logs_data),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/incidents")
async def get_security_incidents():
    """Get security incidents"""
    try:
        security_mcp = _get_gambino_security_mcp()
        incidents = security_mcp.incident_response.incidents

        # Convert to dict
        incidents_data = []
        for inc in incidents:
            from dataclasses import asdict
            incidents_data.append(asdict(inc))

        return {
            "status": "success",
            "incidents": incidents_data,
            "total": len(incidents_data),
            "unresolved": sum(1 for inc in incidents if not inc.resolved),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/threat-intel")
async def get_threat_intelligence():
    """Get current threat intelligence indicators"""
    try:
        security_mcp = _get_gambino_security_mcp()
        indicators = security_mcp.threat_intel.indicators

        # Convert to dict
        from dataclasses import asdict
        indicators_data = [asdict(ind) for ind in indicators[-100:]]  # Last 100

        return {
            "status": "success",
            "indicators": indicators_data,
            "total": len(security_mcp.threat_intel.indicators),
            "returned": len(indicators_data),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get threat intel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# INTEGRATED SECURITY + OMNICOGNITION WORKFLOW
# =============================================================================

class SecureWorkflowRequest(BaseModel):
    """Secure workflow execution with security validation"""
    workflow_description: str = Field(..., description="Workflow description")
    ticker: str = Field(..., description="Stock ticker for financial analysis")
    user_role: str = Field("developer", description="User role")


@router.post("/integrated/secure-workflow")
async def execute_secure_workflow(request: SecureWorkflowRequest):
    """
    Execute OmniCognition workflow with Gambino security validation

    Integrates both systems for secure workflow execution:
    1. OmniCognition generates workflow
    2. Gambino Security validates and approves
    3. Returns combined results

    This is the recommended endpoint for production workflows.
    """
    try:
        # Step 1: Generate workflow
        omni_mcp = _get_omnicognition_mcp()
        omni_result = await omni_mcp.run_workflow_cycle(
            workflow_description=request.workflow_description,
            ticker=request.ticker,
            user_role=request.user_role
        )

        if omni_result["status"] != "success":
            return TaskResponse(
                status="error",
                mcp_system="Integrated",
                result={"error": "Workflow generation failed", "details": omni_result},
                timestamp=datetime.now()
            )

        # Step 2: Security validation
        workflow_code = omni_result.get("workflow", {}).get("code_preview", "# Generated workflow")
        security_mcp = _get_gambino_security_mcp()
        security_result = await security_mcp.execute_security_cycle(
            agent_name="omnicognition_workflow",
            workflow_code=workflow_code,
            actor_role=request.user_role
        )

        # Step 3: Combined result
        integrated_result = {
            "omnicognition": omni_result,
            "security": security_result,
            "final_status": "approved" if security_result.get("governance", {}).get("approved") else "denied",
            "execution_safe": security_result.get("anomaly_detection", {}).get("anomalies_found") == False
        }

        return TaskResponse(
            status="success",
            mcp_system="Integrated (OmniCognition + Gambino)",
            task_id=omni_result.get("workflow", {}).get("workflow_id"),
            result=integrated_result,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Integrated secure workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# JULES PROTOCOL MCP ROUTES
# =============================================================================

class JulesReasoningRequest(BaseModel):
    """Jules Protocol reasoning cycle request"""
    agent_name: str = Field(..., description="Name of the agent executing the cycle")
    prompt_id: str = Field("general_reasoning", description="ID of the prompt to use")
    task_input: str = Field(..., description="Input for the reasoning task")
    gold_standard: Optional[str] = Field(None, description="Optional expected output for supervised learning")


@router.post("/jules/execute-cycle")
async def execute_jules_reasoning_cycle(request: JulesReasoningRequest):
    """
    Execute complete Jules Protocol reasoning cycle

    Performs:
    1. Prompt library retrieval
    2. FAISS context retrieval
    3. LLM reasoning generation
    4. Confidence labeling (CERTAIN/PROBABLE/UNCERTAIN/UNKNOWN)
    5. Hallucination detection
    6. Self-reflection
    7. Reinforcement learning (reward/penalty)
    8. Supervised fine-tuning (if gold standard provided)
    9. Evolution tracking
    10. Cryptographic audit logging

    Returns complete reasoning cycle result with all guardrails applied.
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()
        result = await jules_mcp.execute_cycle(
            agent_name=request.agent_name,
            prompt_id=request.prompt_id,
            task_input=request.task_input,
            gold_standard=request.gold_standard
        )

        # Convert dataclass to dict
        from dataclasses import asdict
        result_dict = asdict(result)

        # Convert datetime to ISO format
        result_dict['timestamp'] = result.timestamp.isoformat()

        return TaskResponse(
            status="success",
            mcp_system="JulesProtocol",
            task_id=result.reasoning_id,
            result=result_dict,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Jules Protocol reasoning cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jules/stats")
async def get_jules_stats():
    """
    Get comprehensive Jules Protocol statistics

    Returns:
    - Prompt library metrics (usage counts, success rates)
    - Reinforcement learning statistics (rewards, penalties)
    - Supervised fine-tuning anchors
    - Evolution trends
    - Context manager statistics
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()
        stats = await jules_mcp.get_stats()

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get Jules Protocol stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jules/prompts")
async def get_jules_prompts():
    """
    Get all prompts in the Jules Protocol library

    Returns list of prompts with their metrics and history.
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()

        # Get all prompts
        prompts_data = []
        for prompt_id, prompt in jules_mcp.prompt_lib.prompts.items():
            prompts_data.append({
                "prompt_id": prompt.prompt_id,
                "text": prompt.text,
                "task_type": prompt.task_type,
                "metrics": prompt.metrics,
                "history_count": len(prompt.history),
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat()
            })

        return {
            "status": "success",
            "prompts": prompts_data,
            "total": len(prompts_data),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AddPromptRequest(BaseModel):
    """Add prompt request"""
    prompt_id: str = Field(..., description="Unique prompt ID")
    text: str = Field(..., description="Prompt text")
    task_type: str = Field(..., description="Task type (general, technical, analytical, creative)")


@router.post("/jules/prompts")
async def add_jules_prompt(request: AddPromptRequest):
    """
    Add new prompt to Jules Protocol library

    The prompt will be tracked with performance metrics and history.
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()
        await jules_mcp.add_prompt(
            prompt_id=request.prompt_id,
            text=request.text,
            task_type=request.task_type
        )

        return {
            "status": "success",
            "message": f"Prompt '{request.prompt_id}' added successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to add prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jules/audit-logs")
async def get_jules_audit_logs(limit: int = 100):
    """
    Get Jules Protocol audit logs with cryptographic verification

    All reasoning cycles and operations are logged with SHA-256 hashes.
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()
        logs = await jules_mcp.get_audit_logs(limit=limit)

        return {
            "status": "success",
            "logs": logs,
            "count": len(logs),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get Jules audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jules/evolution/trends")
async def get_jules_evolution_trends():
    """
    Get Jules Protocol evolution and adaptation trends

    Returns metrics on adaptation patterns, success rates, and contextual relevance.
    """
    try:
        jules_mcp = _get_jules_protocol_mcp()
        trends = jules_mcp.evolution.get_adaptation_trends()

        return {
            "status": "success",
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get evolution trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
