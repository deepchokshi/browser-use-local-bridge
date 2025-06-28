from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime

class TaskStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    STOPPING = "STOPPING"

class TaskStep(BaseModel):
    """Individual step in task execution"""
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    description: str
    status: str = "completed"
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskMedia(BaseModel):
    """Media file associated with a task"""
    filename: str
    filepath: str
    media_type: str  # screenshot, recording, etc.
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BrowserConfig(BaseModel):
    """Browser configuration for a task"""
    headless: bool = True
    user_data_dir: Optional[str] = None
    chrome_executable_path: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    enable_screenshots: bool = True
    enable_recordings: bool = False
    custom_flags: List[str] = Field(default_factory=list)

class LLMConfig(BaseModel):
    """LLM configuration for a task"""
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    custom_config: Dict[str, Any] = Field(default_factory=dict)

class Task(BaseModel):
    # Core task information
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    task: str
    status: TaskStatus = TaskStatus.CREATED
    
    # Execution details
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Task execution tracking
    steps: List[TaskStep] = Field(default_factory=list)
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    
    # Browser and LLM configuration
    browser_config: BrowserConfig = Field(default_factory=BrowserConfig)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    
    # Media and files
    media: List[TaskMedia] = Field(default_factory=list)
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Task history and metadata
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance metrics
    execution_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    
    # Task control
    can_pause: bool = True
    can_stop: bool = True
    auto_screenshot: bool = True
    
    def add_step(self, action: str, description: str, **kwargs) -> TaskStep:
        """Add a new step to the task"""
        step = TaskStep(
            action=action,
            description=description,
            **kwargs
        )
        self.steps.append(step)
        self.current_step = step.step_id
        self.updated_at = datetime.utcnow()
        return step
    
    def update_progress(self, percentage: float):
        """Update task progress percentage"""
        self.progress_percentage = max(0, min(100, percentage))
        self.updated_at = datetime.utcnow()
    
    def add_media(self, filename: str, filepath: str, media_type: str, size_bytes: int, **metadata) -> TaskMedia:
        """Add media file to task"""
        media = TaskMedia(
            filename=filename,
            filepath=filepath,
            media_type=media_type,
            size_bytes=size_bytes,
            metadata=metadata
        )
        self.media.append(media)
        self.updated_at = datetime.utcnow()
        return media
    
    def set_status(self, status: TaskStatus):
        """Update task status with timestamp"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == TaskStatus.RUNNING and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.STOPPED]:
            self.finished_at = datetime.utcnow()
            if self.started_at:
                self.execution_time_seconds = (self.finished_at - self.started_at).total_seconds()
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at:
            end_time = self.finished_at or datetime.utcnow()
            return (end_time - self.started_at).total_seconds()
        return None
    
    def is_active(self) -> bool:
        """Check if task is currently active"""
        return self.status in [TaskStatus.RUNNING, TaskStatus.STOPPING]
    
    def is_completed(self) -> bool:
        """Check if task is completed (finished, failed, or stopped)"""
        return self.status in [TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.STOPPED]
    
    def get_media_by_type(self, media_type: str) -> List[TaskMedia]:
        """Get media files by type"""
        return [m for m in self.media if m.media_type == media_type]
    
    def get_latest_screenshot(self) -> Optional[TaskMedia]:
        """Get the latest screenshot"""
        screenshots = self.get_media_by_type("screenshot")
        return screenshots[-1] if screenshots else None

class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    task: str
    user_id: Optional[str] = None
    browser_config: Optional[BrowserConfig] = None
    llm_config: Optional[LLMConfig] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    status: Optional[TaskStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    browser_config: Optional[BrowserConfig] = None
    llm_config: Optional[LLMConfig] = None