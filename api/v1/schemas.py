from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.task import TaskStatus, Task, TaskCreate, TaskStep, TaskMedia, BrowserConfig, BrowserProfile, BrowserSessionConfig, LLMConfig, AgentConfig

# Task Schemas
class TaskCreateRequest(BaseModel):
    """Request schema for creating a new task"""
    task: str = Field(..., description="Task description")
    user_id: Optional[str] = Field(None, description="User ID (defaults to X-User-ID header)")
    browser_config: Optional[BrowserConfig] = Field(None, description="Browser configuration (backward compatibility)")
    browser_profile: Optional[BrowserProfile] = Field(None, description="Complete browser profile configuration")
    browser_session_config: Optional[BrowserSessionConfig] = Field(None, description="Browser session configuration")
    llm_config: Optional[LLMConfig] = Field(None, description="LLM configuration")
    agent_config: Optional[AgentConfig] = Field(None, description="Agent configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class TaskResponse(BaseModel):
    """Response schema for task operations"""
    id: str
    user_id: str
    task: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: datetime
    steps: List[TaskStep] = Field(default_factory=list)
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    browser_config: BrowserConfig  # Backward compatibility
    browser_profile: BrowserProfile  # Complete configuration
    browser_session_config: Optional[BrowserSessionConfig] = None
    llm_config: LLMConfig
    agent_config: AgentConfig
    media: List[TaskMedia] = Field(default_factory=list)
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    can_pause: bool = True
    can_stop: bool = True
    auto_screenshot: bool = True

class TaskListResponse(BaseModel):
    """Response schema for listing tasks"""
    tasks: List[TaskResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool

class TaskStatusResponse(BaseModel):
    """Response schema for task status"""
    status: TaskStatus
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    execution_time_seconds: Optional[float] = None

class TaskStepResponse(BaseModel):
    """Response schema for task steps"""
    steps: List[TaskStep]
    current_step: Optional[str] = None

# Media Schemas
class MediaFileResponse(BaseModel):
    """Response schema for media files"""
    filename: str
    media_type: str
    size_bytes: int
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MediaListResponse(BaseModel):
    """Response schema for listing media files"""
    media_files: List[MediaFileResponse]
    total_size_bytes: int
    total_count: int

class MediaInfoResponse(BaseModel):
    """Response schema for media file information"""
    filename: str
    size_bytes: int
    created_at: str
    modified_at: str
    media_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None

# System Schemas
class PingResponse(BaseModel):
    """Response schema for ping endpoint"""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

class BrowserConfigResponse(BaseModel):
    """Response schema for browser configuration"""
    headless: bool
    user_data_persistence: bool
    user_data_dir: str
    viewport_width: int
    viewport_height: int
    timeout: int
    chrome_executable_path: Optional[str] = None
    enable_screenshots: bool
    enable_recordings: bool

class LLMProviderResponse(BaseModel):
    """Response schema for LLM provider information"""
    provider: str
    available: bool
    models: List[str] = Field(default_factory=list)
    description: str

class SystemStatsResponse(BaseModel):
    """Response schema for system statistics"""
    active_tasks: int
    max_concurrent_tasks: int
    total_browser_sessions: int
    available_providers: Dict[str, bool]
    memory_usage_mb: float
    cpu_percent: float
    uptime_seconds: Optional[float] = None

class HealthCheckResponse(BaseModel):
    """Response schema for health check"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, bool] = Field(default_factory=dict)

# Configuration Schemas
class ConfigUpdateRequest(BaseModel):
    """Request schema for updating configuration"""
    browser_config: Optional[BrowserConfig] = None
    default_llm_provider: Optional[str] = None
    default_model: Optional[str] = None
    max_concurrent_tasks: Optional[int] = None

class ConfigResponse(BaseModel):
    """Response schema for configuration"""
    browser_config: BrowserConfig
    default_llm_provider: str
    default_model: str
    max_concurrent_tasks: int
    available_providers: Dict[str, bool]

# Error Schemas
class ErrorResponse(BaseModel):
    """Response schema for errors"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors"""
    error: str = "Validation Error"
    details: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Live Monitoring Schemas
class LiveTaskUpdate(BaseModel):
    """Schema for live task updates"""
    task_id: str
    status: TaskStatus
    progress_percentage: float
    current_step: Optional[str] = None
    latest_screenshot: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Cookie Schemas
class CookieResponse(BaseModel):
    """Response schema for cookies"""
    cookies: List[Dict[str, Any]]
    count: int
    extracted_at: datetime

# Cleanup Schemas
class CleanupResponse(BaseModel):
    """Response schema for cleanup operations"""
    cleaned_count: int
    operation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Screenshot Test Schema
class ScreenshotTestResponse(BaseModel):
    """Response schema for screenshot test"""
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    size_bytes: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)