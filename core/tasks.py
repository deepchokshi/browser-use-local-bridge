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
            
            # Setup browser configuration
            task.add_step("browser_init", "Initializing browser session")
            try:
                browser_profile = await self._create_browser_profile(task, user_id)
                task.add_step("profile_created", "Browser profile created")
                browser_session = BrowserSession(profile=browser_profile)
                task.add_step("session_created", "Browser session created")
            except Exception as e:
                task.add_step("browser_error", f"Browser setup failed: {e}", error=str(e))
                raise
            
            # Store browser session for potential control operations
            self.browser_sessions[task_id] = browser_session
            
            # Create and configure agent
            agent = Agent(
                task=task.task,
                llm=llm,
                browser_session=browser_session
            )
            self.task_agents[task_id] = agent
            
            # Setup progress tracking
            task.add_step("execution_start", "Starting task execution")
            task.update_progress(10)
            
            # Execute task with timeout
            timeout_seconds = settings.TASK_TIMEOUT_MINUTES * 60
            result = await asyncio.wait_for(
                self._run_agent_with_monitoring(agent, task, user_id),
                timeout=timeout_seconds
            )
            
            # Process results
            task.result = result.final_result() if result else None
            if result and hasattr(result, 'history'):
                task.history = [h.model_dump() for h in result.history]
            
            # Take final screenshot
            if task.browser_config.enable_screenshots:
                await self._take_final_screenshot(browser_session, task, user_id)
            
            # Extract cookies if requested
            await self._extract_cookies(browser_session, task)
            
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
            task.error = str(e)
            task.set_status(TaskStatus.FAILED)
            task.add_step("error", f"Task failed with error: {str(e)}", error=str(e))
            logger.error(f"Task failed: {task_id} - {e}")
            
        finally:
            # Cleanup resources
            await self._cleanup_task_resources(task_id, browser_session, agent)
    
    async def _run_agent_with_monitoring(self, agent: Agent, task: Task, user_id: str):
        """Run agent with progress monitoring and screenshot capture"""
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
            
            # Execute the agent
            result = await agent.run()
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise
    
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

# Global task manager instance
task_manager = TaskManager(task_storage)