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

class BrowserProfile(BaseModel):
    """Complete BrowserProfile configuration matching browser-use documentation"""
    
    # ===== Browser-Use Specific Parameters =====
    keep_alive: Optional[bool] = None
    stealth: bool = False
    allowed_domains: Optional[List[str]] = None
    disable_security: bool = False
    deterministic_rendering: bool = False
    highlight_elements: bool = True
    viewport_expansion: int = 500
    include_dynamic_attributes: bool = True
    minimum_wait_page_load_time: float = 0.25
    wait_for_network_idle_page_load_time: float = 0.5
    maximum_wait_page_load_time: float = 5.0
    wait_between_actions: float = 0.5
    cookies_file: Optional[str] = None  # DEPRECATED - use storage_state
    profile_directory: str = "Default"
    window_position: Optional[Dict[str, int]] = None
    save_recording_path: Optional[str] = None
    trace_path: Optional[str] = None
    
    # ===== Playwright Launch Options =====
    headless: Optional[bool] = None
    channel: str = "chromium"  # chromium, chrome, chrome-beta, etc.
    executable_path: Optional[str] = None
    user_data_dir: Optional[str] = "~/.config/browseruse/profiles/default"
    args: List[str] = Field(default_factory=list)
    ignore_default_args: List[str] = Field(default_factory=lambda: ["--enable-automation", "--disable-extensions"])
    env: Dict[str, str] = Field(default_factory=dict)
    chromium_sandbox: Optional[bool] = None  # Auto-detected based on Docker
    devtools: bool = False
    slow_mo: float = 0
    timeout: float = 30000
    accept_downloads: bool = True
    proxy: Optional[Dict[str, str]] = None
    permissions: List[str] = Field(default_factory=lambda: ["clipboard-read", "clipboard-write", "notifications"])
    storage_state: Optional[str] = None  # Path to storage state file or dict
    
    # ===== Playwright Timing Settings =====
    default_timeout: Optional[float] = None
    default_navigation_timeout: Optional[float] = None
    
    # ===== Playwright Viewport Options =====
    user_agent: Optional[str] = None
    is_mobile: bool = False
    has_touch: bool = False
    geolocation: Optional[Dict[str, float]] = None
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    window_size: Optional[Dict[str, int]] = None
    viewport: Optional[Dict[str, int]] = None
    no_viewport: Optional[bool] = None
    device_scale_factor: Optional[float] = None
    screen: Optional[Dict[str, int]] = None
    color_scheme: str = "light"  # light, dark, no-preference
    contrast: str = "no-preference"  # no-preference, more, null
    reduced_motion: str = "no-preference"  # reduce, no-preference, null
    forced_colors: str = "none"  # active, none, null
    
    # ===== Playwright Security Options =====
    offline: bool = False
    http_credentials: Optional[Dict[str, str]] = None
    extra_http_headers: Dict[str, str] = Field(default_factory=dict)
    ignore_https_errors: bool = False
    bypass_csp: bool = False
    java_script_enabled: bool = True
    service_workers: str = "allow"  # allow, block
    base_url: Optional[str] = None
    strict_selectors: bool = False
    client_certificates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # ===== Playwright Recording Options =====
    record_video_dir: Optional[str] = None
    record_video_size: Optional[Dict[str, int]] = None
    record_har_path: Optional[str] = None
    record_har_content: str = "embed"  # omit, embed, attach
    record_har_mode: str = "full"  # full, minimal
    record_har_omit_content: bool = False
    record_har_url_filter: Optional[str] = None
    downloads_path: Optional[str] = "~/.config/browseruse/downloads"
    traces_dir: Optional[str] = None
    handle_sighup: bool = True
    handle_sigint: bool = False
    handle_sigterm: bool = False

class BrowserSessionConfig(BaseModel):
    """Browser session configuration for connecting to existing browsers"""
    # Session-specific connection parameters (cannot be stored in BrowserProfile)
    wss_url: Optional[str] = None
    cdp_url: Optional[str] = None
    browser_pid: Optional[int] = None
    
    # Session-specific parameters
    browser_profile: Optional[BrowserProfile] = None
    playwright: Optional[str] = None  # Would be handle in implementation
    browser: Optional[str] = None  # Would be handle in implementation
    browser_context: Optional[str] = None  # Would be handle in implementation
    page: Optional[str] = None  # Would be handle in implementation
    human_current_page: Optional[str] = None  # Would be handle in implementation
    initialized: bool = False

# Keep BrowserConfig for backward compatibility
class BrowserConfig(BaseModel):
    """Simplified browser configuration (backward compatibility)"""
    headless: bool = True
    user_data_dir: Optional[str] = None
    chrome_executable_path: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    enable_screenshots: bool = True
    enable_recordings: bool = False
    custom_flags: List[str] = Field(default_factory=list)
    
    def to_browser_profile(self) -> BrowserProfile:
        """Convert to comprehensive BrowserProfile"""
        return BrowserProfile(
            headless=self.headless,
            user_data_dir=self.user_data_dir,
            executable_path=self.chrome_executable_path,
            viewport={"width": self.viewport_width, "height": self.viewport_height},
            timeout=self.timeout,
            record_video_dir=None if not self.enable_recordings else "./media/recordings",
            args=self.custom_flags
        )

class LLMConfig(BaseModel):
    """LLM configuration for a task"""
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    custom_config: Dict[str, Any] = Field(default_factory=dict)

class CustomFunctionParam(BaseModel):
    """Custom function parameter definition"""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type (str, int, float, bool, list, dict)")
    description: Optional[str] = Field(None, description="Parameter description for the LLM")
    required: bool = Field(True, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value if parameter is optional")

class CustomFunction(BaseModel):
    """Custom function definition"""
    name: str = Field(description="Function name")
    description: str = Field(description="Function description for the LLM")
    
    # Function parameters
    parameters: List[CustomFunctionParam] = Field(default_factory=list, description="Function parameters")
    param_model_schema: Optional[Dict[str, Any]] = Field(None, description="Pydantic model schema for parameters")
    
    # Function restrictions
    allowed_domains: Optional[List[str]] = Field(None, description="Domains where this function can be used")
    page_filter_code: Optional[str] = Field(None, description="Python code for page filtering (advanced)")
    
    # Function implementation
    implementation_type: str = Field("webhook", description="Implementation type: webhook, code, builtin")
    webhook_url: Optional[str] = Field(None, description="Webhook URL to call for function execution")
    python_code: Optional[str] = Field(None, description="Python code to execute (if implementation_type=code)")
    
    # Function behavior
    async_execution: bool = Field(True, description="Whether function execution is async")
    timeout_seconds: int = Field(30, description="Function execution timeout")
    include_in_memory: bool = Field(True, description="Include result in agent memory")

class ControllerConfig(BaseModel):
    """Controller configuration for structured output formats and custom functions"""
    # Output format configuration
    output_model_schema: Optional[Dict[str, Any]] = Field(None, description="Pydantic model schema for structured output")
    output_model_name: Optional[str] = Field(None, description="Name of the output model class")
    
    # Controller behavior
    validate_output: bool = Field(True, description="Validate output against the model schema")
    retry_on_validation_error: bool = Field(True, description="Retry if output validation fails")
    max_validation_retries: int = Field(3, description="Maximum retries for validation errors")
    
    # Output format examples
    output_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example outputs for the model")
    
    # Custom instructions for structured output
    output_instructions: Optional[str] = Field(None, description="Additional instructions for generating structured output")
    
    # Custom functions
    custom_functions: List[CustomFunction] = Field(default_factory=list, description="Custom action functions")
    exclude_actions: List[str] = Field(default_factory=list, description="Built-in actions to exclude")

class LifecycleHook(BaseModel):
    """Lifecycle hook configuration"""
    hook_type: str = Field(description="Hook type: on_step_start, on_step_end")
    
    # Hook implementation
    implementation_type: str = Field("webhook", description="Implementation type: webhook, code")
    webhook_url: Optional[str] = Field(None, description="Webhook URL to call for hook execution")
    python_code: Optional[str] = Field(None, description="Python code to execute (if implementation_type=code)")
    
    # Hook behavior
    async_execution: bool = Field(True, description="Whether hook execution is async")
    timeout_seconds: int = Field(30, description="Hook execution timeout")
    continue_on_error: bool = Field(True, description="Continue agent execution if hook fails")
    
    # Data to include in webhook payload
    include_page_html: bool = Field(False, description="Include current page HTML")
    include_screenshot: bool = Field(False, description="Include current page screenshot")
    include_agent_state: bool = Field(True, description="Include agent state data")
    include_history: bool = Field(True, description="Include agent history")

class AgentConfig(BaseModel):
    """Complete Agent configuration matching browser-use documentation"""
    # Core Agent behavior
    use_vision: bool = True
    save_conversation_path: Optional[str] = None
    override_system_message: Optional[str] = None
    extend_system_message: Optional[str] = None
    
    # Planner system prompt customization
    extend_planner_system_message: Optional[str] = Field(None, description="Additional instructions for the planner agent")
    
    # Task context and actions
    message_context: Optional[str] = None
    initial_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent limits and behavior
    max_actions_per_step: int = 10
    max_failures: int = 3
    retry_delay: float = 10.0
    max_steps: int = 100
    
    # Media generation
    generate_gif: bool = False
    gif_path: Optional[str] = None
    
    # Planner configuration
    planner_llm_provider: Optional[str] = None
    planner_llm_model: Optional[str] = None
    use_vision_for_planner: bool = True
    planner_interval: int = 1
    
    # Sensitive data handling
    sensitive_data: Dict[str, Dict[str, str]] = Field(
        default_factory=dict, 
        description="Domain-specific sensitive data mapping. Format: {'domain_pattern': {'placeholder': 'actual_value'}}"
    )
    
    # Lifecycle hooks
    lifecycle_hooks: List[LifecycleHook] = Field(default_factory=list, description="Lifecycle hooks for agent execution monitoring")
    
    # Controller configuration (includes structured output + custom functions)
    controller_config: Optional[ControllerConfig] = Field(None, description="Controller configuration for structured output and custom functions")
    
    # Backward compatibility for simple custom functions
    custom_functions: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy custom functions (use controller_config.custom_functions instead)")

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
    
    # Configuration - COMPLETE BROWSER-USE PARITY
    browser_config: BrowserConfig = Field(default_factory=BrowserConfig)  # Backward compatibility
    browser_profile: BrowserProfile = Field(default_factory=BrowserProfile)  # Complete config
    browser_session_config: Optional[BrowserSessionConfig] = None
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    agent_config: AgentConfig = Field(default_factory=AgentConfig)
    
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
    browser_config: Optional[BrowserConfig] = None  # Backward compatibility
    browser_profile: Optional[BrowserProfile] = None  # Complete configuration
    browser_session_config: Optional[BrowserSessionConfig] = None
    llm_config: Optional[LLMConfig] = None
    agent_config: Optional[AgentConfig] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    status: Optional[TaskStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    browser_config: Optional[BrowserConfig] = None
    llm_config: Optional[LLMConfig] = None