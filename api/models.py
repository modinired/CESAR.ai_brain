"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class SourceType(str, Enum):
    article = "article"
    video = "video"
    course = "course"
    paper = "paper"
    book = "book"
    podcast = "podcast"
    financial_data = "financial_data"
    research = "research"

class FetchStatus(str, Enum):
    pending = "pending"
    fetched = "fetched"
    failed = "failed"
    archived = "archived"

class AgentType(str, Enum):
    scraper = "scraper"
    analyzer = "analyzer"
    curator = "curator"
    reflector = "reflector"
    coordinator = "coordinator"
    specialist = "specialist"

# ============================================================================
# LEARNING SOURCES & MATERIALS
# ============================================================================

class LearningSourceCreate(BaseModel):
    url: str
    source_type: SourceType
    category: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    metadata: Dict[str, Any] = {}

class LearningSource(BaseModel):
    id: str
    url: str
    source_type: str
    category: Optional[str]
    priority: int
    fetch_status: str
    last_fetched: Optional[datetime]
    created_at: datetime

class LearningMaterialResponse(BaseModel):
    id: str
    source_id: Optional[str]
    title: str
    description: Optional[str]
    content: str
    processed: bool
    quality_score: float
    relevance_score: float
    tags: List[str]
    fetched_at: datetime

class LearningReflection(BaseModel):
    id: str
    material_id: str
    agent_id: str
    reflection_text: str
    reflection_type: str
    reflection_score: float
    key_insights: List[str]
    created_at: datetime

# ============================================================================
# AGENTS
# ============================================================================

class AgentProfileResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    agent_type: str
    description: Optional[str]
    specialization: List[str]
    status: str
    performance_score: float
    total_tasks_completed: int
    success_rate: float

class AgentSkill(BaseModel):
    id: str
    agent_id: str
    skill_name: str
    skill_category: Optional[str]
    skill_level: float
    proficiency: str
    practice_count: int
    last_practiced: Optional[datetime]

# ============================================================================
# WORKFLOWS
# ============================================================================

class WorkflowResponse(BaseModel):
    id: str
    workflow_name: str
    workflow_run_id: Optional[str]
    agent_id: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    tasks_total: int
    tasks_completed: int
    tasks_failed: int

class WorkflowTriggerRequest(BaseModel):
    workflow_name: str
    parameters: Dict[str, Any] = {}
