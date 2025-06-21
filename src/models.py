from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectPhase(str, Enum):
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TECHNICAL_DESIGN = "technical_design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    ACCEPTANCE = "acceptance"

class TeamMember(BaseModel):
    """团队成员模型"""
    id: str
    name: str
    role: str
    skills: List[str]
    responsibilities: List[str]
    personality: str
    is_available: bool = True

class ProjectTask(BaseModel):
    """项目任务模型"""
    id: str
    name: str
    description: str
    phase: ProjectPhase
    assignee: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: str = ""
    dependencies: List[str] = []
    estimated_duration: str = "1天"

class Project(BaseModel):
    """项目模型"""
    id: str
    name: str
    description: str
    requirements: str
    current_phase: ProjectPhase = ProjectPhase.REQUIREMENT_ANALYSIS
    status: TaskStatus = TaskStatus.PENDING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_members: List[str] = []
    tasks: List[ProjectTask] = []
    deliverables: Dict[str, str] = {}
    budget: Optional[float] = None
    client: Optional[str] = None

class ProjectReport(BaseModel):
    """项目报告模型"""
    project_id: str
    phase: ProjectPhase
    summary: str
    progress: float = Field(ge=0, le=100)
    completed_tasks: List[str] = []
    pending_tasks: List[str] = []
    issues: List[str] = []
    next_steps: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.now)

class LLMResponse(BaseModel):
    """LLM响应模型"""
    role: str
    content: str
    confidence: float = Field(ge=0, le=1)
    reasoning: Optional[str] = None
    suggestions: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now) 