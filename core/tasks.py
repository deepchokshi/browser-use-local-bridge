"""
Advanced Task Manager for Browser Automation
Supports multiple AI providers, comprehensive media handling, and production-ready features
"""

import asyncio
import logging
import os
import psutil
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.browser.browser import Browser

from core.storage import TaskStorage, task_storage
from core.llm_factory import LLMFactory
from core.media_manager import media_manager
from core.config import settings
from models.task import Task, TaskStatus, TaskCreate, BrowserConfig, LLMConfig, TaskStep
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TaskManager:
    """Advanced task manager with comprehensive browser automation capabilities"""
    
    def __init__(self, storage: TaskStorage):
        self.storage = storage
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.browser_sessions: Dict[str, BrowserSession] = {}
        self.task_agents: Dict[str, Agent] = {}
        self.max_concurrent_tasks = settings.MAX_CONCURRENT_TASKS
        # Semaphore to prevent concurrent Agent creation (EventBus conflict)
        self._agent_creation_semaphore = asyncio.Semaphore(1)
        
    def create_task(
        self, 
        task_create: TaskCreate,
        user_id: Optional[str] = None
    ) -> Task:
        """Create a new task with comprehensive configuration"""
        try:
            user_id = user_id or task_create.user_id or settings.DEFAULT_USER_ID
            
            # Create task with enhanced configuration
            task = Task(
                user_id=user_id,
                task=task_create.task,
                browser_config=task_create.browser_config or BrowserConfig(),
                llm_config=task_create.llm_config or LLMConfig(),
                metadata=task_create.metadata
            )
            
            # Validate AI provider configuration
            if not LLMFactory.validate_provider_config(task.llm_config.provider):
                logger.warning(f"Provider {task.llm_config.provider} not properly configured, falling back to default")
                task.llm_config.provider = settings.DEFAULT_LLM_PROVIDER
                task.llm_config.model = settings.DEFAULT_MODEL
            
            # Add initial step
            task.add_step("created", "Task created and initialized")
            
            # Store task
            self.storage.add_task(user_id, task)
            
            logger.info(f"Task created: {task.id} for user {user_id}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    
    async def start_task(self, user_id: str, task_id: str) -> Task:
        """Start task execution in background"""
        try:
            task = self.storage.get_task(user_id, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if task.status != TaskStatus.CREATED:
                raise HTTPException(status_code=400, detail=f"Task cannot be started from status {task.status}")
            
            # Check concurrent task limit
            active_count = len([t for t in self.active_tasks.values() if not t.done()])
            if active_count >= self.max_concurrent_tasks:
                raise HTTPException(status_code=429, detail="Maximum concurrent tasks reached")
            
            # Start task execution
            task_coroutine = asyncio.create_task(
                self._execute_task(user_id, task_id)
            )
            self.active_tasks[task_id] = task_coroutine
            
            # Update task status
            task.set_status(TaskStatus.RUNNING)
            task.add_step("started", "Task execution started")
            
            logger.info(f"Task started: {task_id}")
            return task

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")
    
    async def _execute_task(self, user_id: str, task_id: str):
        """Execute task with comprehensive error handling and monitoring"""
        task = self.storage.get_task(user_id, task_id)
        if not task:
            return

        browser_session = None
        agent = None
        
        try:
            # Initialize performance monitoring
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create LLM instance
            task.add_step("llm_init", f"Initializing {task.llm_config.provider} LLM")
            logger.debug(f"LLM config: provider={task.llm_config.provider}, model={task.llm_config.model}")
            logger.debug(f"LLM custom_config: {task.llm_config.custom_config}")
            
            try:
                llm = LLMFactory.create_llm(
                    provider=task.llm_config.provider,
                    model=task.llm_config.model,
                    temperature=task.llm_config.temperature,
                    max_tokens=task.llm_config.max_tokens,
                    **task.llm_config.custom_config
                )
                task.add_step("llm_created", "LLM created successfully")
            except Exception as e:
                task.add_step("llm_error", f"LLM creation failed: {e}", error=str(e))
                raise
            
            # Create agent with COMPLETE configuration support
            task.add_step("agent_init", "Creating browser agent")
            try:
                # Build comprehensive Agent configuration
                agent_kwargs = {
                    "task": task.task,
                    "llm": llm,
                }
                
                # Core Agent behavior from agent_config
                agent_kwargs["use_vision"] = task.agent_config.use_vision
                
                if task.agent_config.save_conversation_path:
                    agent_kwargs["save_conversation_path"] = task.agent_config.save_conversation_path
                
                if task.agent_config.override_system_message:
                    agent_kwargs["override_system_message"] = task.agent_config.override_system_message
                
                if task.agent_config.extend_system_message:
                    agent_kwargs["extend_system_message"] = task.agent_config.extend_system_message
                
                # Task context and actions
                if task.agent_config.message_context:
                    agent_kwargs["message_context"] = task.agent_config.message_context
                
                if task.agent_config.initial_actions:
                    agent_kwargs["initial_actions"] = task.agent_config.initial_actions
                
                # Agent limits and behavior
                agent_kwargs["max_actions_per_step"] = task.agent_config.max_actions_per_step
                agent_kwargs["max_failures"] = task.agent_config.max_failures
                agent_kwargs["retry_delay"] = task.agent_config.retry_delay
                
                # Media generation
                if task.agent_config.generate_gif:
                    gif_path = task.agent_config.gif_path or f"./media/{task_id}/task.gif"
                    agent_kwargs["generate_gif"] = gif_path
                
                # Planner configuration
                if task.agent_config.planner_llm_provider and task.agent_config.planner_llm_model:
                    planner_llm = LLMFactory.create_llm(
                        provider=task.agent_config.planner_llm_provider,
                        model=task.agent_config.planner_llm_model,
                        **task.llm_config.custom_config
                    )
                    agent_kwargs["planner_llm"] = planner_llm
                    agent_kwargs["use_vision_for_planner"] = task.agent_config.use_vision_for_planner
                    agent_kwargs["planner_interval"] = task.agent_config.planner_interval
                
                # Planner system prompt customization
                if task.agent_config.extend_planner_system_message:
                    agent_kwargs["extend_planner_system_message"] = task.agent_config.extend_planner_system_message
                
                # Sensitive data handling
                if task.agent_config.sensitive_data:
                    # Validate sensitive data domains against allowed domains
                    if browser_profile and browser_profile.allowed_domains:
                        self._validate_sensitive_data_domains(task.agent_config.sensitive_data, browser_profile.allowed_domains, task_id)
                    
                    agent_kwargs["sensitive_data"] = task.agent_config.sensitive_data
                    task.add_step("sensitive_data", f"Configured sensitive data for {len(task.agent_config.sensitive_data)} domains")
                
                # Lifecycle hooks
                lifecycle_hooks = {}
                if task.agent_config.lifecycle_hooks:
                    for hook in task.agent_config.lifecycle_hooks:
                        hook_func = await self._create_lifecycle_hook(hook, task_id)
                        if hook_func:
                            lifecycle_hooks[hook.hook_type] = hook_func
                    
                    if lifecycle_hooks:
                        # Pass hooks to agent.run() later
                        task.add_step("lifecycle_hooks", f"Configured {len(lifecycle_hooks)} lifecycle hooks")
                
                # Browser configuration - COMPLETE BROWSER-USE SUPPORT
                browser_profile = None
                browser_session = None
                
                # Use comprehensive BrowserProfile if provided, otherwise convert legacy BrowserConfig
                if task.browser_profile:
                    browser_profile = task.browser_profile
                elif task.browser_config:
                    browser_profile = task.browser_config.to_browser_profile()
                else:
                    browser_profile = BrowserProfile()  # Use defaults
                
                # Create BrowserSession if connection parameters provided
                if task.browser_session_config:
                    from browser_use import BrowserSession
                    
                    session_kwargs = {"browser_profile": browser_profile}
                    
                    # Add connection parameters
                    if task.browser_session_config.cdp_url:
                        session_kwargs["cdp_url"] = task.browser_session_config.cdp_url
                    elif task.browser_session_config.wss_url:
                        session_kwargs["wss_url"] = task.browser_session_config.wss_url
                    elif task.browser_session_config.browser_pid:
                        session_kwargs["browser_pid"] = task.browser_session_config.browser_pid
                    
                    browser_session = BrowserSession(**session_kwargs)
                    agent_kwargs["browser_session"] = browser_session
                else:
                    # Pass browser profile parameters directly to Agent
                    # Convert BrowserProfile to kwargs that Agent/BrowserSession can use
                    profile_dict = browser_profile.model_dump(exclude_none=True)
                    
                    # Map BrowserProfile fields to Agent/BrowserSession parameters
                    for key, value in profile_dict.items():
                        if key in ["headless", "user_data_dir", "args", "timeout", "viewport", 
                                  "user_agent", "stealth", "allowed_domains", "storage_state"]:
                            agent_kwargs[key] = value
                
                # Controller configuration (structured output + custom functions)
                controller = None
                if task.agent_config.controller_config or task.agent_config.custom_functions:
                    controller = await self._create_controller(task.agent_config.controller_config, task.agent_config.custom_functions, task_id)
                    if controller:
                        agent_kwargs["controller"] = controller
                        custom_func_count = len(task.agent_config.controller_config.custom_functions) if task.agent_config.controller_config else 0
                        legacy_func_count = len(task.agent_config.custom_functions)
                        total_functions = custom_func_count + legacy_func_count
                        task.add_step("controller_created", f"Controller created with {total_functions} custom functions")
                
                # Custom controller/functions would need additional implementation
                # This requires creating a custom Controller class
                
                # Create the Agent with all parameters
                # Use semaphore to prevent EventBus naming conflicts during concurrent creation
                async with self._agent_creation_semaphore:
                    agent = Agent(**agent_kwargs)
                
                self.task_agents[task_id] = agent
                task.add_step("agent_created", "Agent created successfully")
                
                # Store browser session reference
                self.browser_sessions[task_id] = agent_kwargs.get("browser_session")
                
                # Store lifecycle hooks for later use
                if 'lifecycle_hooks' in locals():
                    self._current_lifecycle_hooks = lifecycle_hooks
                else:
                    self._current_lifecycle_hooks = {}
                
            except Exception as e:
                task.add_step("agent_error", f"Agent creation failed: {e}", error=str(e))
                task.set_status(TaskStatus.FAILED)
                task.error = f"Agent creation failed: {str(e)}"
                logger.error(f"Agent creation failed for task {task_id}: {e}")
                return
            
            # Setup progress tracking
            task.add_step("execution_start", "Starting task execution")
            task.update_progress(10)
            
            # Execute task with timeout and proper error handling
            timeout_seconds = settings.TASK_TIMEOUT_MINUTES * 60
            try:
                result = await asyncio.wait_for(
                    self._run_agent_with_monitoring(agent, task, user_id),
                    timeout=timeout_seconds
                )
                
                # Check if result indicates failure
                if result is None:
                    raise Exception("Agent returned no result - likely due to browser failures")
                
                # Process results using the documented AgentHistoryList methods
                if result:
                    # Use the documented methods for extracting results
                    try:
                        # First try final_result() method as documented
                        if hasattr(result, 'final_result') and callable(result.final_result):
                            final_result = result.final_result()
                            
                            # Handle structured output validation
                            if task.agent_config.controller_config and controller:
                                try:
                                    # Try to parse as structured output
                                    import json
                                    if isinstance(final_result, str):
                                        # Try to parse JSON
                                        try:
                                            parsed_result = json.loads(final_result)
                                            task.result = parsed_result
                                            task.add_step("structured_output", "Structured output parsed successfully")
                                        except json.JSONDecodeError:
                                            # Not JSON, store as-is
                                            task.result = final_result
                                            task.add_step("structured_output_warning", "Result is not valid JSON")
                                    else:
                                        task.result = final_result
                                except Exception as e:
                                    logger.warning(f"Failed to process structured output: {e}")
                                    task.result = final_result
                            else:
                                task.result = final_result
                                
                        elif hasattr(result, 'extracted_content') and callable(result.extracted_content):
                            # Fallback to extracted_content() method
                            extracted = result.extracted_content()
                            task.result = extracted if extracted else str(result)
                        else:
                            task.result = str(result)
                    except Exception as e:
                        # Final fallback
                        task.result = str(result)
                        logger.warning(f"Failed to extract result using documented methods: {e}")
                    
                    # Store additional history information using documented methods
                    try:
                        history_data = {}
                        if hasattr(result, 'urls') and callable(result.urls):
                            history_data['urls'] = result.urls()
                        if hasattr(result, 'action_names') and callable(result.action_names):
                            history_data['action_names'] = result.action_names()
                        if hasattr(result, 'is_done') and callable(result.is_done):
                            history_data['is_done'] = result.is_done()
                        if hasattr(result, 'has_errors') and callable(result.has_errors):
                            history_data['has_errors'] = result.has_errors()
                        if hasattr(result, 'errors') and callable(result.errors):
                            history_data['errors'] = result.errors()
                        task.history = history_data
                    except Exception as e:
                        logger.warning(f"Failed to extract history: {e}")
                        task.history = {}
                else:
                    task.result = "No result returned from agent"
                
                # Take final screenshot (skip for simplified approach)
                # Screenshots are handled internally by the Agent
                
                # Extract cookies (skip for simplified approach)
                # Cookies can be extracted separately if needed
                
                # Update final status
                task.set_status(TaskStatus.FINISHED)
                task.add_step("completed", "Task completed successfully")
                task.update_progress(100)
                
                # Calculate performance metrics
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                task.memory_usage_mb = end_memory - start_memory
                
                logger.info(f"Task completed successfully: {task_id}")
                
            except asyncio.TimeoutError:
                task.error = f"Task timed out after {settings.TASK_TIMEOUT_MINUTES} minutes"
                task.set_status(TaskStatus.FAILED)
                task.add_step("timeout", "Task execution timed out", error=task.error)
                logger.error(f"Task timed out: {task_id}")
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle Windows-specific browser errors
                if "NotImplementedError" in error_msg:
                    error_msg = "Browser initialization failed on Windows. Please ensure Playwright browsers are installed and try running in Docker or WSL for better compatibility."
                elif "subprocess" in error_msg.lower():
                    error_msg = "Browser process creation failed. This may be due to Windows security settings or missing dependencies."
                elif "setup_playwright failed" in error_msg:
                    error_msg = "Playwright browser setup failed. This is a known Windows compatibility issue. Consider using Docker or WSL."
                
                task.error = error_msg
                task.set_status(TaskStatus.FAILED)
                task.add_step("error", f"Task failed with error: {error_msg}", error=error_msg)
                logger.error(f"Task failed: {task_id} - {error_msg}")
            
        except Exception as e:
            # Catch any other unexpected errors
            error_msg = f"Unexpected error during task execution: {str(e)}"
            task.error = error_msg
            task.set_status(TaskStatus.FAILED)
            task.add_step("fatal_error", error_msg, error=error_msg)
            logger.error(f"Fatal error in task {task_id}: {e}")
            
        finally:
            # Cleanup resources
            await self._cleanup_task_resources(task_id, None, agent)
    
    async def _run_agent_with_monitoring(self, agent: Agent, task: Task, user_id: str):
        """Run agent with progress monitoring and screenshot capture"""
        browser_failure_detected = False
        original_result = None
        
        try:
            # Setup monitoring callback if available
            if hasattr(agent, 'set_progress_callback'):
                agent.set_progress_callback(
                    lambda progress: self._update_task_progress(task, progress)
                )
            
            # Setup screenshot callback if enabled
            if task.browser_config.enable_screenshots and hasattr(agent, 'set_screenshot_callback'):
                agent.set_screenshot_callback(
                    lambda screenshot_data: self._save_task_screenshot(task, user_id, screenshot_data)
                )
            
            # Execute the agent with better error detection
            logger.info(f"Starting agent execution for task {task.id}")
            
            # Set up a way to capture browser failures
            # We'll monitor the task for signs of browser failures
            task_start_time = time.time()
            
            # Execute the agent with max_steps parameter and lifecycle hooks
            run_kwargs = {"max_steps": task.agent_config.max_steps}
            
            # Add lifecycle hooks if configured
            if hasattr(self, '_current_lifecycle_hooks') and self._current_lifecycle_hooks:
                for hook_type, hook_func in self._current_lifecycle_hooks.items():
                    run_kwargs[hook_type] = hook_func
            
            result = await agent.run(**run_kwargs)
            original_result = result
            
            # With the simplified approach, trust the Agent's result
            execution_time = time.time() - task_start_time
            
            logger.info(f"Agent execution completed successfully for task {task.id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent execution failed for task {task.id}: {error_msg}")
            
            # Check for specific browser-related failures
            if "NotImplementedError" in error_msg or "setup_playwright failed" in error_msg:
                raise Exception(f"Browser automation failed due to Windows compatibility issues: {error_msg}")
            elif "stopping due to" in error_msg.lower() and "consecutive failures" in error_msg.lower():
                raise Exception(f"Agent stopped due to repeated browser failures: {error_msg}")
            elif browser_failure_detected:
                raise Exception(f"Browser automation failed - likely due to Windows Playwright issues. Original result: {original_result}")
            else:
                raise  # Re-raise the original exception
    
    async def _create_browser_profile(self, task: Task, user_id: str) -> BrowserProfile:
        """Create browser profile with task-specific configuration"""
        try:
            # Setup user data directory
            user_data_dir = None
            if task.browser_config.user_data_dir:
                user_data_dir = task.browser_config.user_data_dir
            elif settings.BROWSER_USER_DATA_PERSISTENCE:
                user_data_dir = os.path.join(settings.BROWSER_USER_DATA_DIR, user_id)
                os.makedirs(user_data_dir, exist_ok=True)
            
            # Prepare browser args
            browser_args = []
            
            # Add custom flags
            if task.browser_config.custom_flags:
                browser_args.extend(task.browser_config.custom_flags)
            
            # Disable telemetry if configured
            if not settings.TELEMETRY_ENABLED:
                browser_args.extend([
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection"
                ])
            
            # Create browser profile with minimal configuration first
            try:
                profile_kwargs = {
                    "headless": task.browser_config.headless,
                    "timeout": task.browser_config.timeout / 1000,  # Convert to seconds
                }
                
                # Add user data dir if specified
                if user_data_dir:
                    profile_kwargs["user_data_dir"] = user_data_dir
                
                # Add executable path if specified
                if task.browser_config.chrome_executable_path or settings.CHROME_EXECUTABLE_PATH:
                    profile_kwargs["executable_path"] = task.browser_config.chrome_executable_path or settings.CHROME_EXECUTABLE_PATH
                
                # Add browser args
                if browser_args:
                    profile_kwargs["args"] = browser_args
                
                # Add viewport configuration
                if task.browser_config.viewport_width and task.browser_config.viewport_height:
                    from browser_use.browser.types import ViewportSize
                    profile_kwargs["viewport"] = ViewportSize(
                        width=task.browser_config.viewport_width,
                        height=task.browser_config.viewport_height
                    )
                
                profile = BrowserProfile(**profile_kwargs)
                
            except Exception as e:
                logger.error(f"Failed to create browser profile with full config: {e}")
                # Fallback to minimal profile
                profile = BrowserProfile(headless=True)
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create browser profile: {e}")
            raise
    
    async def _take_final_screenshot(self, browser_session: BrowserSession, task: Task, user_id: str):
        """Take final screenshot of the browser"""
        try:
            if browser_session and browser_session.browser:
                screenshot_data = await browser_session.browser.screenshot()
                if screenshot_data:
                    media = await media_manager.save_screenshot(
                        task.id, user_id, screenshot_data,
                        filename="final_screenshot.png",
                        metadata={"type": "final", "step": "completion"}
                    )
                    task.add_media(
                        media.filename, media.filepath, media.media_type,
                        media.size_bytes, **media.metadata
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to take final screenshot: {e}")
    
    async def _extract_cookies(self, browser_session: BrowserSession, task: Task):
        """Extract cookies from browser session"""
        try:
            if browser_session and browser_session.browser:
                cookies = await browser_session.browser.get_cookies()
                if cookies:
                    task.cookies = cookies
                    logger.info(f"Extracted {len(cookies)} cookies for task {task.id}")
                    
        except Exception as e:
            logger.warning(f"Failed to extract cookies: {e}")
    
    def _update_task_progress(self, task: Task, progress: float):
        """Update task progress"""
        try:
            task.update_progress(progress)
            logger.debug(f"Task {task.id} progress: {progress}%")
        except Exception as e:
            logger.warning(f"Failed to update task progress: {e}")
    
    async def _save_task_screenshot(self, task: Task, user_id: str, screenshot_data: bytes):
        """Save screenshot during task execution"""
        try:
            media = await media_manager.save_screenshot(
                task.id, user_id, screenshot_data,
                metadata={"type": "step", "step": task.current_step}
            )
            task.add_media(
                media.filename, media.filepath, media.media_type,
                media.size_bytes, **media.metadata
            )
        except Exception as e:
            logger.warning(f"Failed to save task screenshot: {e}")
    
    async def _create_controller(self, controller_config, legacy_custom_functions, task_id: str):
        """Create a Controller for structured output and custom functions"""
        try:
            from browser_use import Controller, ActionResult
            from pydantic import BaseModel, create_model
            from typing import get_type_hints
            import json
            import asyncio
            import aiohttp
            
            # Initialize controller
            exclude_actions = []
            if controller_config and controller_config.exclude_actions:
                exclude_actions = controller_config.exclude_actions
            
            controller = Controller(exclude_actions=exclude_actions)
            
            # Create structured output model if provided
            if controller_config and controller_config.output_model_schema:
                try:
                    # Create a dynamic model from the schema
                    model_name = controller_config.output_model_name or "OutputModel"
                    
                    # Convert schema to model fields
                    fields = {}
                    properties = controller_config.output_model_schema.get("properties", {})
                    required = controller_config.output_model_schema.get("required", [])
                    
                    for field_name, field_info in properties.items():
                        field_type = self._schema_type_to_python_type(field_info)
                        default_value = ... if field_name in required else None
                        fields[field_name] = (field_type, default_value)
                    
                    # Create the dynamic model
                    OutputModel = create_model(model_name, **fields)
                    
                    # Update controller with the model
                    controller = Controller(output_model=OutputModel, exclude_actions=exclude_actions)
                    
                    logger.info(f"Created structured output model for task {task_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to create dynamic model from schema: {e}")
            
            # Register custom functions
            functions_registered = 0
            
            # Register new-style custom functions
            if controller_config and controller_config.custom_functions:
                for func_def in controller_config.custom_functions:
                    try:
                        await self._register_custom_function(controller, func_def, task_id)
                        functions_registered += 1
                    except Exception as e:
                        logger.error(f"Failed to register custom function {func_def.name}: {e}")
            
            # Register legacy custom functions
            if legacy_custom_functions:
                for func_def in legacy_custom_functions:
                    try:
                        await self._register_legacy_custom_function(controller, func_def, task_id)
                        functions_registered += 1
                    except Exception as e:
                        logger.error(f"Failed to register legacy custom function: {e}")
            
            if functions_registered > 0:
                logger.info(f"Registered {functions_registered} custom functions for task {task_id}")
            
            return controller
                
        except ImportError:
            logger.warning("Controller not available in browser-use version")
            return None
        except Exception as e:
            logger.error(f"Failed to create controller for task {task_id}: {e}")
            return None
    
    def _schema_type_to_python_type(self, field_info: Dict[str, Any]):
        """Convert JSON schema type to Python type"""
        field_type = field_info.get("type", "string")
        
        if field_type == "string":
            return str
        elif field_type == "integer":
            return int
        elif field_type == "number":
            return float
        elif field_type == "boolean":
            return bool
        elif field_type == "array":
            items_type = self._schema_type_to_python_type(field_info.get("items", {"type": "string"}))
            return List[items_type]
        elif field_type == "object":
            return Dict[str, Any]
        else:
            return str  # Default fallback
    
    def _validate_sensitive_data_domains(self, sensitive_data: Dict[str, Dict[str, str]], allowed_domains: List[str], task_id: str):
        """Validate that sensitive data domains are covered by allowed domains"""
        try:
            import fnmatch
            
            sensitive_domains = set(sensitive_data.keys())
            
            # Check if each sensitive domain is covered by allowed domains
            uncovered_domains = []
            for sensitive_domain in sensitive_domains:
                is_covered = False
                for allowed_domain in allowed_domains:
                    if self._domain_matches_pattern(sensitive_domain, allowed_domain):
                        is_covered = True
                        break
                
                if not is_covered:
                    uncovered_domains.append(sensitive_domain)
            
            if uncovered_domains:
                warning_msg = f"Sensitive data domains not covered by allowed_domains: {uncovered_domains}"
                logger.warning(f"Task {task_id}: {warning_msg}")
                # Don't fail the task, just warn
            else:
                logger.info(f"Task {task_id}: All sensitive data domains are properly restricted")
                
        except Exception as e:
            logger.warning(f"Failed to validate sensitive data domains for task {task_id}: {e}")
    
    def _domain_matches_pattern(self, domain: str, pattern: str) -> bool:
        """Check if a domain matches a pattern (simplified implementation)"""
        import fnmatch
        
        # Remove protocol if present
        if "://" in domain:
            domain = domain.split("://", 1)[1]
        if "://" in pattern:
            pattern = pattern.split("://", 1)[1]
        
        # Handle wildcards
        if pattern.startswith("*."):
            # *.example.com should match example.com and subdomain.example.com
            base_domain = pattern[2:]
            return domain == base_domain or domain.endswith("." + base_domain)
        elif "*" in pattern:
            return fnmatch.fnmatch(domain, pattern)
        else:
            return domain == pattern
    
    async def _register_custom_function(self, controller, func_def, task_id: str):
        """Register a custom function with the controller"""
        from browser_use import ActionResult
        import aiohttp
        import asyncio
        import json
        
        # Create the function implementation
        if func_def.implementation_type == "webhook":
            # Webhook-based function
            async def webhook_function(**kwargs):
                try:
                    # Extract framework parameters
                    framework_params = {}
                    action_params = {}
                    
                    for key, value in kwargs.items():
                        if key in ['page', 'browser_session', 'context', 'page_extraction_llm', 'available_file_paths', 'has_sensitive_data']:
                            framework_params[key] = value
                        else:
                            action_params[key] = value
                    
                    # Call webhook
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "function_name": func_def.name,
                            "parameters": action_params,
                            "task_id": task_id,
                            "framework_context": {
                                "page_url": framework_params.get('page').url if framework_params.get('page') else None,
                                "has_sensitive_data": framework_params.get('has_sensitive_data', False)
                            }
                        }
                        
                        timeout = aiohttp.ClientTimeout(total=func_def.timeout_seconds)
                        async with session.post(func_def.webhook_url, json=payload, timeout=timeout) as response:
                            if response.status == 200:
                                result_data = await response.json()
                                return ActionResult(
                                    extracted_content=result_data.get('content', ''),
                                    include_in_memory=func_def.include_in_memory
                                )
                            else:
                                error_text = await response.text()
                                return ActionResult(
                                    extracted_content=f"Webhook error: {response.status} - {error_text}",
                                    include_in_memory=False
                                )
                
                except Exception as e:
                    logger.error(f"Webhook function {func_def.name} failed: {e}")
                    return ActionResult(
                        extracted_content=f"Function execution failed: {str(e)}",
                        include_in_memory=False
                    )
            
            # Register with controller
            controller.action(
                func_def.description,
                allowed_domains=func_def.allowed_domains
            )(webhook_function)
            
        elif func_def.implementation_type == "code":
            # Python code-based function
            async def code_function(**kwargs):
                try:
                    # Create execution environment
                    exec_globals = {
                        'ActionResult': ActionResult,
                        'logger': logger,
                        'asyncio': asyncio,
                        'json': json,
                        **kwargs  # Include all parameters
                    }
                    
                    # Execute the code
                    if func_def.async_execution:
                        exec(f"async def _custom_func():\n{func_def.python_code}", exec_globals)
                        result = await exec_globals['_custom_func']()
                    else:
                        exec(f"def _custom_func():\n{func_def.python_code}", exec_globals)
                        result = exec_globals['_custom_func']()
                    
                    # Ensure result is ActionResult
                    if isinstance(result, ActionResult):
                        return result
                    else:
                        return ActionResult(
                            extracted_content=str(result),
                            include_in_memory=func_def.include_in_memory
                        )
                
                except Exception as e:
                    logger.error(f"Code function {func_def.name} failed: {e}")
                    return ActionResult(
                        extracted_content=f"Function execution failed: {str(e)}",
                        include_in_memory=False
                    )
            
            # Register with controller
            controller.action(
                func_def.description,
                allowed_domains=func_def.allowed_domains
            )(code_function)
        
        logger.info(f"Registered custom function: {func_def.name}")
    
    async def _register_legacy_custom_function(self, controller, func_def: Dict[str, Any], task_id: str):
        """Register a legacy custom function (simple dict format)"""
        from browser_use import ActionResult
        
        # Extract function details
        name = func_def.get('name', 'unknown_function')
        description = func_def.get('description', name)
        webhook_url = func_def.get('webhook_url')
        
        if webhook_url:
            # Simple webhook function
            async def legacy_webhook_function(**kwargs):
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "function_name": name,
                            "parameters": kwargs,
                            "task_id": task_id
                        }
                        
                        async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                result_data = await response.json()
                                return ActionResult(
                                    extracted_content=result_data.get('content', ''),
                                    include_in_memory=True
                                )
                            else:
                                return ActionResult(
                                    extracted_content=f"Legacy function error: {response.status}",
                                    include_in_memory=False
                                )
                
                except Exception as e:
                    return ActionResult(
                        extracted_content=f"Legacy function failed: {str(e)}",
                        include_in_memory=False
                    )
            
            # Register with controller
            controller.action(description)(legacy_webhook_function)
            logger.info(f"Registered legacy custom function: {name}")
    
    async def _create_lifecycle_hook(self, hook_config, task_id: str):
        """Create a lifecycle hook function"""
        try:
            import aiohttp
            import asyncio
            import json
            import base64
            
            if hook_config.implementation_type == "webhook":
                # Webhook-based hook
                async def webhook_hook(agent):
                    try:
                        # Gather hook data
                        hook_data = {
                            "hook_type": hook_config.hook_type,
                            "task_id": task_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        
                        # Include agent state if requested
                        if hook_config.include_agent_state:
                            hook_data["agent_state"] = {
                                "task": agent.task,
                                "settings": str(agent.settings) if hasattr(agent, 'settings') else None,
                            }
                        
                        # Include history if requested
                        if hook_config.include_history and hasattr(agent, 'state') and agent.state:
                            history = agent.state.history
                            hook_data["history"] = {
                                "urls": history.urls() if hasattr(history, 'urls') else [],
                                "model_thoughts": str(history.model_thoughts()[-1]) if hasattr(history, 'model_thoughts') and history.model_thoughts() else None,
                                "model_actions": str(history.model_actions()[-1]) if hasattr(history, 'model_actions') and history.model_actions() else None,
                                "extracted_content": str(history.extracted_content()[-1]) if hasattr(history, 'extracted_content') and history.extracted_content() else None,
                            }
                        
                        # Include page data if requested
                        if hook_config.include_page_html or hook_config.include_screenshot:
                            try:
                                page = await agent.browser_session.get_current_page()
                                current_url = page.url
                                hook_data["current_url"] = current_url
                                
                                if hook_config.include_page_html:
                                    hook_data["page_html"] = await agent.browser_session.get_page_html()
                                
                                if hook_config.include_screenshot:
                                    screenshot_bytes = await agent.browser_session.take_screenshot()
                                    if screenshot_bytes:
                                        hook_data["screenshot"] = base64.b64encode(screenshot_bytes).decode('utf-8')
                                        
                            except Exception as e:
                                logger.warning(f"Failed to capture page data for hook: {e}")
                        
                        # Call webhook
                        timeout = aiohttp.ClientTimeout(total=hook_config.timeout_seconds)
                        async with aiohttp.ClientSession() as session:
                            async with session.post(hook_config.webhook_url, json=hook_data, timeout=timeout) as response:
                                if response.status != 200:
                                    error_text = await response.text()
                                    logger.warning(f"Hook webhook returned {response.status}: {error_text}")
                                    if not hook_config.continue_on_error:
                                        raise Exception(f"Hook webhook failed: {response.status}")
                    
                    except Exception as e:
                        logger.error(f"Lifecycle hook {hook_config.hook_type} failed: {e}")
                        if not hook_config.continue_on_error:
                            raise
                
                return webhook_hook
                
            elif hook_config.implementation_type == "code":
                # Python code-based hook
                async def code_hook(agent):
                    try:
                        # Create execution environment
                        exec_globals = {
                            'agent': agent,
                            'logger': logger,
                            'asyncio': asyncio,
                            'json': json,
                            'datetime': datetime,
                            'base64': base64,
                            'task_id': task_id
                        }
                        
                        # Execute the code
                        if hook_config.async_execution:
                            exec(f"async def _hook_func(agent):\n{hook_config.python_code}", exec_globals)
                            await exec_globals['_hook_func'](agent)
                        else:
                            exec(f"def _hook_func(agent):\n{hook_config.python_code}", exec_globals)
                            exec_globals['_hook_func'](agent)
                    
                    except Exception as e:
                        logger.error(f"Code lifecycle hook {hook_config.hook_type} failed: {e}")
                        if not hook_config.continue_on_error:
                            raise
                
                return code_hook
            
            else:
                logger.warning(f"Unknown hook implementation type: {hook_config.implementation_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create lifecycle hook {hook_config.hook_type}: {e}")
            return None

    async def _cleanup_task_resources(self, task_id: str, browser_session: Optional[BrowserSession], agent: Optional[Agent]):
        """Clean up task resources"""
        try:
            # Close browser session
            if browser_session:
                await browser_session.close()
                self.browser_sessions.pop(task_id, None)
            
            # Clean up agent
            if agent:
                self.task_agents.pop(task_id, None)
            
            # Remove from active tasks
            self.active_tasks.pop(task_id, None)
            
            logger.debug(f"Cleaned up resources for task {task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup task resources: {e}")
    
    async def stop_task(self, user_id: str, task_id: str) -> Task:
        """Stop a running task"""
        try:
            task = self.storage.get_task(user_id, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if not task.is_active():
                raise HTTPException(status_code=400, detail=f"Task is not active (status: {task.status})")
            
            # Cancel the task
            if task_id in self.active_tasks:
                self.active_tasks[task_id].cancel()
            
            # Update status
            task.set_status(TaskStatus.STOPPING)
            task.add_step("stopping", "Task stop requested")
            
            # Cleanup resources
            browser_session = self.browser_sessions.get(task_id)
            agent = self.task_agents.get(task_id)
            await self._cleanup_task_resources(task_id, browser_session, agent)
            
            # Final status update
            task.set_status(TaskStatus.STOPPED)
            task.add_step("stopped", "Task stopped successfully")
            
            logger.info(f"Task stopped: {task_id}")
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to stop task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop task: {str(e)}")
    
    async def pause_task(self, user_id: str, task_id: str) -> Task:
        """Pause a running task"""
        try:
            task = self.storage.get_task(user_id, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if task.status != TaskStatus.RUNNING:
                raise HTTPException(status_code=400, detail=f"Task cannot be paused from status {task.status}")
            
            if not task.can_pause:
                raise HTTPException(status_code=400, detail="Task cannot be paused")
            
            # Update status
            task.set_status(TaskStatus.PAUSED)
            task.add_step("paused", "Task paused")
            
            # Note: Actual pause implementation would depend on browser-use library capabilities
            logger.info(f"Task paused: {task_id}")
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to pause task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to pause task: {str(e)}")
    
    async def resume_task(self, user_id: str, task_id: str) -> Task:
        """Resume a paused task"""
        try:
            task = self.storage.get_task(user_id, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
                
                if task.status != TaskStatus.PAUSED:
                    raise HTTPException(status_code=400, detail=f"Task cannot be resumed from status {task.status}")
                
                # Update status
                task.set_status(TaskStatus.RUNNING)
                task.add_step("resumed", "Task resumed")
                
                # Note: Actual resume implementation would depend on browser-use library capabilities
                logger.info(f"Task resumed: {task_id}")
            return task

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to resume task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to resume task: {str(e)}")
    
    def get_task_status(self, user_id: str, task_id: str) -> TaskStatus:
        """Get current task status"""
        task = self.storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.status
    
    def list_tasks(self, user_id: str, page: int = 1, page_size: int = 10, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """List tasks with optional filtering"""
        tasks = self.storage.list_tasks(user_id, page, page_size)
        
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        return tasks
    
    async def get_task_media(self, user_id: str, task_id: str) -> List[Dict[str, Any]]:
        """Get media files for a task"""
        task = self.storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        media_files = await media_manager.list_task_media(task_id, user_id)
        return [
            {
                "filename": media.filename,
                "media_type": media.media_type,
                "size_bytes": media.size_bytes,
                "created_at": media.created_at.isoformat(),
                "metadata": media.metadata
            }
            for media in media_files
        ]
    
    async def cleanup_completed_tasks(self, days_old: int = 7) -> int:
        """Clean up old completed tasks and their media"""
        try:
            cleaned_count = 0
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # This would require implementing cleanup in storage
            # For now, just clean up media files
            media_cleaned = await media_manager.cleanup_old_media(days_old)
            
            logger.info(f"Cleaned up {media_cleaned} old media files")
            return media_cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            return 0
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            active_tasks = len([t for t in self.active_tasks.values() if not t.done()])
            
            return {
                "active_tasks": active_tasks,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "total_browser_sessions": len(self.browser_sessions),
                "available_providers": LLMFactory.get_available_providers(),
                "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.cpu_percent()
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}

    async def _create_browser_session(self, browser_config: dict) -> BrowserSession:
        """Create a browser session with proper configuration"""
        try:
            # Create browser profile with Windows-specific optimizations
            browser_profile = BrowserProfile(
                browser_type=browser_config.get("browser_type", "chromium"),
                headless=browser_config.get("headless", False),
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-translate",
                    "--disable-ipc-flooding-protection",
                    # Windows-specific optimizations
                    "--disable-features=TranslateUI,VizDisplayCompositor",
                    "--enable-features=NetworkService,NetworkServiceLogging",
                    "--force-device-scale-factor=1",
                    "--high-dpi-support=1"
                ] + browser_config.get("args", []),
                user_data_dir=browser_config.get("user_data_dir"),
                window_size=browser_config.get("window_size", {"width": 1920, "height": 1080}),
                downloads_path=browser_config.get("downloads_path"),
                keep_open=browser_config.get("keep_open", False)
            )
            
            # Create browser session with retry logic for Windows
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    session = BrowserSession(profile=browser_profile)
                    await asyncio.sleep(0.1)  # Small delay for Windows stability
                    return session
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Browser session creation attempt {attempt + 1} failed, retrying", 
                                 error=str(e))
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            logger.error("Failed to create browser session", error=str(e))
            raise RuntimeError(f"Browser session creation failed: {str(e)}")

    async def _run_task_with_agent(self, task_id: str, task: Task, llm_instance) -> Dict[str, Any]:
        """Run task with browser-use agent with enhanced Windows compatibility"""
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self._update_task_progress(task_id, task.progress, "Starting browser automation...")
            
            # Create browser session with Windows optimizations
            browser_config = {
                "browser_type": "chromium",
                "headless": task.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-translate",
                    "--disable-ipc-flooding-protection",
                    # Windows-specific fixes
                    "--disable-features=TranslateUI,VizDisplayCompositor",
                    "--enable-features=NetworkService,NetworkServiceLogging",
                    "--force-device-scale-factor=1",
                    "--high-dpi-support=1",
                    "--disable-web-security",  # Additional Windows compatibility
                    "--disable-site-isolation-trials"
                ],
                "user_data_dir": os.path.join(settings.BROWSER_USER_DATA_DIR, task_id),
                "window_size": {"width": 1920, "height": 1080},
                "downloads_path": os.path.join(settings.MEDIA_DIR, task_id),
                "keep_open": False
            }
            
            browser_session = await self._create_browser_session(browser_config)
            self.browser_sessions[task_id] = browser_session
            
            await self._update_task_progress(task_id, 10, "Browser session created")
            
            # Create agent with Windows-compatible settings
            agent = Agent(
                task=task.instruction,
                llm=llm_instance,
                browser_session=browser_session,
                use_vision=True,
                save_conversation_path=os.path.join(settings.MEDIA_DIR, task_id, "conversation.json"),
                max_failures=3,  # Increased for Windows stability
                retry_delay=2.0,  # Longer delay for Windows
                validate_output=True
            )
            
            await self._update_task_progress(task_id, 20, "Agent initialized")
            
            # Set up progress tracking
            step_count = 0
            max_steps = 50  # Reasonable limit
            
            async def progress_callback(step_info: dict):
                nonlocal step_count
                step_count += 1
                progress = min(20 + (step_count / max_steps) * 70, 90)
                
                step_description = step_info.get('description', f'Step {step_count}')
                await self._update_task_progress(task_id, progress, step_description)
                
                # Capture screenshot if available
                if 'screenshot' in step_info:
                    try:
                        screenshot_path = os.path.join(settings.MEDIA_DIR, task_id, f"step_{step_count}.png")
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        
                        with open(screenshot_path, 'wb') as f:
                            f.write(step_info['screenshot'])
                        
                        task.media_files.append({
                            "type": "screenshot",
                            "filename": f"step_{step_count}.png",
                            "path": screenshot_path,
                            "timestamp": datetime.utcnow().isoformat(),
                            "step": step_count
                        })
                    except Exception as e:
                        logger.warning("Failed to save screenshot", error=str(e))
            
            # Run the agent with timeout and Windows-specific error handling
            try:
                # Set a reasonable timeout for Windows
                timeout = task.timeout or 300  # 5 minutes default
                
                result = await asyncio.wait_for(
                    agent.run(),
                    timeout=timeout
                )
                
                await self._update_task_progress(task_id, 100, "Task completed successfully")
                
                # Process result
                if hasattr(result, 'extracted_content') and result.extracted_content:
                    task.result = result.extracted_content
                elif hasattr(result, 'final_result'):
                    task.result = result.final_result
                else:
                    task.result = str(result) if result else "Task completed"
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                
                # Capture final screenshot
                try:
                    final_screenshot = await browser_session.get_screenshot()
                    if final_screenshot:
                        screenshot_path = os.path.join(settings.MEDIA_DIR, task_id, "final_screenshot.png")
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        
                        with open(screenshot_path, 'wb') as f:
                            f.write(final_screenshot)
                        
                        task.media_files.append({
                            "type": "screenshot",
                            "filename": "final_screenshot.png",
                            "path": screenshot_path,
                            "timestamp": datetime.utcnow().isoformat(),
                            "step": "final"
                        })
                except Exception as e:
                    logger.warning("Failed to capture final screenshot", error=str(e))
                
                logger.info("Task completed successfully", task_id=task_id)
                
                return {
                    "status": "completed",
                    "result": task.result,
                    "steps_completed": step_count,
                    "media_files": task.media_files
                }
                
            except asyncio.TimeoutError:
                await self._update_task_progress(task_id, task.progress, "Task timed out")
                task.status = TaskStatus.FAILED
                task.error = f"Task timed out after {timeout} seconds"
                task.completed_at = datetime.utcnow()
                
                logger.warning("Task timed out", task_id=task_id, timeout=timeout)
                
                return {
                    "status": "failed",
                    "error": task.error,
                    "steps_completed": step_count
                }
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle Windows-specific browser errors
                if "NotImplementedError" in error_msg:
                    error_msg = "Browser initialization failed on Windows. Please ensure Playwright browsers are installed."
                elif "subprocess" in error_msg.lower():
                    error_msg = "Browser process creation failed. This may be due to Windows security settings or missing dependencies."
                
                await self._update_task_progress(task_id, task.progress, f"Task failed: {error_msg}")
                task.status = TaskStatus.FAILED
                task.error = error_msg
                task.completed_at = datetime.utcnow()
                
                logger.error("Task execution failed", task_id=task_id, error=error_msg)
                
                return {
                    "status": "failed",
                    "error": error_msg,
                    "steps_completed": step_count
                }
                
        except Exception as e:
            error_msg = f"Task setup failed: {str(e)}"
            task.status = TaskStatus.FAILED
            task.error = error_msg
            task.completed_at = datetime.utcnow()
            
            logger.error("Task setup failed", task_id=task_id, error=error_msg)
            
            return {
                "status": "failed",
                "error": error_msg
            }
            
        finally:
            # Cleanup browser session
            if task_id in self.browser_sessions:
                try:
                    await self.browser_sessions[task_id].close()
                    del self.browser_sessions[task_id]
                    logger.debug("Browser session cleaned up", task_id=task_id)
                except Exception as e:
                    logger.warning("Failed to cleanup browser session", task_id=task_id, error=str(e))

# Global task manager instance
task_manager = TaskManager(task_storage)