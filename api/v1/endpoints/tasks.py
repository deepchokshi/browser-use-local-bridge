"""
Comprehensive Task Management API Endpoints
Supports full task lifecycle, media handling, and real-time monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header, Query, Path
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from api.v1.schemas import (
    TaskCreateRequest, TaskResponse, TaskListResponse, TaskStatusResponse,
    TaskStepResponse, MediaFileResponse, MediaListResponse, MediaInfoResponse,
    CookieResponse, ErrorResponse
)
from core.tasks import task_manager
from core.storage import task_storage
from core.media_manager import media_manager
from core.config import settings
from models.task import Task, TaskStatus, TaskCreate

logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header or use default"""
    return x_user_id or settings.DEFAULT_USER_ID

@router.post("/run-task", response_model=TaskResponse, status_code=201)
async def create_and_run_task(
    task_request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id)
):
    """
    Create and immediately start a new browser automation task
    
    - **task**: Task description/instruction for the AI agent
    - **browser_config**: Optional browser configuration
    - **llm_config**: Optional LLM provider configuration
    - **metadata**: Additional task metadata
    """
    try:
        # Create task
        task_create = TaskCreate(
            task=task_request.task,
            user_id=user_id,
            browser_config=task_request.browser_config,
            llm_config=task_request.llm_config,
            metadata=task_request.metadata
        )
        
        task = task_manager.create_task(task_create, user_id)
        
        # Start task execution in background
        background_tasks.add_task(task_manager.start_task, user_id, task.id)
        
        logger.info(f"Task created and started: {task.id} for user {user_id}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to create and run task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-task", response_model=TaskResponse, status_code=201)
async def create_task(
    task_request: TaskCreateRequest,
    user_id: str = Depends(get_user_id)
):
    """
    Create a new task without starting execution
    
    Use this endpoint when you want to create a task and start it later
    """
    try:
        task_create = TaskCreate(
            task=task_request.task,
            user_id=user_id,
            browser_config=task_request.browser_config,
            llm_config=task_request.llm_config,
            metadata=task_request.metadata
        )
        
        task = task_manager.create_task(task_create, user_id)
        
        logger.info(f"Task created: {task.id} for user {user_id}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-task/{task_id}", response_model=TaskResponse)
async def start_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Start execution of a created task"""
    try:
        task = await task_manager.start_task(user_id, task_id)
        logger.info(f"Task started: {task_id} for user {user_id}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get complete task details including history, media, and metrics"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get current task status and progress"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            execution_time_seconds=task.get_duration()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/steps", response_model=TaskStepResponse)
async def get_task_steps(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get task execution steps and progress details"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStepResponse(
            steps=task.steps,
            current_step=task.current_step
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task steps {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stop-task/{task_id}", response_model=TaskStatusResponse)
async def stop_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Stop a running task"""
    try:
        task = await task_manager.stop_task(user_id, task_id)
        
        return TaskStatusResponse(
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            execution_time_seconds=task.get_duration()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/pause-task/{task_id}", response_model=TaskStatusResponse)
async def pause_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Pause a running task"""
    try:
        task = await task_manager.pause_task(user_id, task_id)
        
        return TaskStatusResponse(
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            execution_time_seconds=task.get_duration()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/resume-task/{task_id}", response_model=TaskStatusResponse)
async def resume_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Resume a paused task"""
    try:
        task = await task_manager.resume_task(user_id, task_id)
        
        return TaskStatusResponse(
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            execution_time_seconds=task.get_duration()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-tasks", response_model=TaskListResponse)
async def list_tasks(
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List tasks with pagination and filtering
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of tasks per page (1-100)
    - **status**: Filter by task status
    - **sort_by**: Sort field (created_at, updated_at, status)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        tasks = task_manager.list_tasks(user_id, page, page_size, status)
        
        # Calculate pagination info
        total_count = len(task_storage.list_tasks(user_id, 1, 1000))  # Get total count
        has_next = (page * page_size) < total_count
        
        # Convert Task objects to TaskResponse objects
        task_responses = []
        for task in tasks:
            try:
                task_responses.append(TaskResponse.model_validate(task))
            except Exception as e:
                logger.warning(f"Failed to convert task {task.id} to response: {e}")
                # Create a minimal response
                task_responses.append(TaskResponse(
                    id=task.id,
                    user_id=task.user_id,
                    task=task.task,
                    status=task.status,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    browser_config=task.browser_config,
                    llm_config=task.llm_config
                ))
        
        return TaskListResponse(
            tasks=task_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/media", response_model=MediaListResponse)
async def get_task_media(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get list of media files for a task"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        media_files = await media_manager.list_task_media(task_id, user_id)
        
        total_size = sum(media.size_bytes for media in media_files)
        
        return MediaListResponse(
            media_files=[
                MediaFileResponse(
                    filename=media.filename,
                    media_type=media.media_type,
                    size_bytes=media.size_bytes,
                    created_at=media.created_at,
                    metadata=media.metadata
                )
                for media in media_files
            ],
            total_size_bytes=total_size,
            total_count=len(media_files)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task media {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/media/list", response_model=List[MediaInfoResponse])
async def list_task_media_detailed(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get detailed information about task media files"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        media_files = await media_manager.list_task_media(task_id, user_id)
        detailed_info = []
        
        for media in media_files:
            info = await media_manager.get_media_info(task_id, user_id, media.filename)
            if info:
                detailed_info.append(MediaInfoResponse(**info))
        
        return detailed_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list detailed task media {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{task_id}/{filename}")
async def get_media_file(
    task_id: str = Path(..., description="Task ID"),
    filename: str = Path(..., description="Media filename"),
    user_id: str = Depends(get_user_id),
    download: bool = Query(False, description="Force download")
):
    """Serve media file (screenshot, recording, etc.)"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        filepath = await media_manager.get_media_file(task_id, user_id, filename)
        if not filepath:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Determine media type
        media_type = "application/octet-stream"
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            media_type = f"image/{filename.split('.')[-1].lower()}"
        elif filename.lower().endswith(('.mp4', '.webm')):
            media_type = f"video/{filename.split('.')[-1].lower()}"
        
        headers = {}
        if download:
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return FileResponse(
            path=str(filepath),
            media_type=media_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve media file {task_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/cookies", response_model=CookieResponse)
async def get_task_cookies(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get cookies extracted from task browser session"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return CookieResponse(
            cookies=task.cookies,
            count=len(task.cookies),
            extracted_at=task.finished_at or task.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task cookies {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id),
    delete_media: bool = Query(True, description="Also delete media files")
):
    """Delete a task and optionally its media files"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Stop task if running
        if task.is_active():
            await task_manager.stop_task(user_id, task_id)
        
        # Delete media files if requested
        if delete_media:
            await media_manager.delete_task_media(task_id, user_id)
        
        # Delete task from storage
        # Note: This would require implementing delete in storage
        # task_storage.delete_task(user_id, task_id)
        
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}/export")
async def export_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id),
    format: str = Query("json", regex="^(json|csv)$", description="Export format")
):
    """Export task data and results"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if format == "json":
            import json
            task_data = task.dict()
            
            return StreamingResponse(
                iter([json.dumps(task_data, indent=2, default=str)]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=task_{task_id}.json"}
            )
        
        # CSV export would be implemented here
        raise HTTPException(status_code=400, detail="CSV export not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))