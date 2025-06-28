"""
Media Management API Endpoints
Handles screenshots, recordings, and other media files from browser automation tasks
"""

from fastapi import APIRouter, HTTPException, Header, Query, Path, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from api.v1.schemas import (
    MediaFileResponse, MediaListResponse, MediaInfoResponse,
    CleanupResponse, ErrorResponse
)
from core.media_manager import media_manager
from core.storage import task_storage
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header or use default"""
    return x_user_id or settings.DEFAULT_USER_ID

@router.get("/task/{task_id}/media", response_model=MediaListResponse)
async def get_task_media(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id),
    media_type: Optional[str] = Query(None, description="Filter by media type")
):
    """Get list of media files for a specific task"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get media files
        media_files = await media_manager.list_task_media(task_id, user_id)
        
        # Filter by media type if specified
        if media_type:
            media_files = [m for m in media_files if m.media_type == media_type]
        
        # Calculate totals
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
    """Get detailed information about all media files for a task"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get media files
        media_files = await media_manager.list_task_media(task_id, user_id)
        detailed_info = []
        
        # Get detailed info for each file
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
    download: bool = Query(False, description="Force download instead of inline display"),
    thumbnail: bool = Query(False, description="Return thumbnail for images")
):
    """
    Serve a specific media file
    
    - **task_id**: ID of the task
    - **filename**: Name of the media file
    - **download**: If true, forces download instead of inline display
    - **thumbnail**: If true, returns a thumbnail for image files
    """
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get file path
        filepath = await media_manager.get_media_file(task_id, user_id, filename)
        if not filepath:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Determine media type
        media_type = "application/octet-stream"
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            media_type = f"image/{filename.split('.')[-1].lower().replace('jpg', 'jpeg')}"
        elif filename.lower().endswith(('.mp4', '.webm', '.avi', '.mov')):
            media_type = f"video/{filename.split('.')[-1].lower()}"
        elif filename.lower().endswith('.json'):
            media_type = "application/json"
        elif filename.lower().endswith(('.txt', '.log')):
            media_type = "text/plain"
        
        # Handle thumbnail request for images
        if thumbnail and media_type.startswith('image/'):
            # This would generate a thumbnail
            # For now, just serve the original image
            pass
        
        # Set headers
        headers = {}
        if download:
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        else:
            headers["Content-Disposition"] = f"inline; filename={filename}"
        
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

@router.get("/media/{task_id}/{filename}/info", response_model=MediaInfoResponse)
async def get_media_info(
    task_id: str = Path(..., description="Task ID"),
    filename: str = Path(..., description="Media filename"),
    user_id: str = Depends(get_user_id)
):
    """Get detailed information about a specific media file"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get media info
        info = await media_manager.get_media_info(task_id, user_id, filename)
        if not info:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        return MediaInfoResponse(**info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get media info {task_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/media/{task_id}/{filename}")
async def delete_media_file(
    task_id: str = Path(..., description="Task ID"),
    filename: str = Path(..., description="Media filename"),
    user_id: str = Depends(get_user_id)
):
    """Delete a specific media file"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete the file
        success = await media_manager.delete_media_file(task_id, user_id, filename)
        if not success:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        return {"message": f"Media file {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete media file {task_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/task/{task_id}/media")
async def delete_all_task_media(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Delete all media files for a task"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete all media files
        success = await media_manager.delete_task_media(task_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete media files")
        
        return {"message": f"All media files for task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete all task media {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/stats")
async def get_media_stats(
    user_id: str = Depends(get_user_id)
):
    """Get media storage statistics for a user"""
    try:
        # This would calculate storage stats across all user tasks
        # For now, return placeholder data
        
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "files_by_type": {
                "screenshot": 0,
                "recording": 0,
                "data": 0,
                "log": 0,
                "unknown": 0
            },
            "oldest_file": None,
            "newest_file": None
        }
        
    except Exception as e:
        logger.error(f"Failed to get media stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media/cleanup", response_model=CleanupResponse)
async def cleanup_old_media(
    days_old: int = Query(7, ge=1, le=365, description="Delete media older than this many days"),
    user_id: str = Depends(get_user_id),
    dry_run: bool = Query(False, description="If true, only count files without deleting")
):
    """Clean up old media files"""
    try:
        if dry_run:
            # Count files that would be deleted
            cleaned_count = 0  # This would be implemented
            operation = f"Would delete {cleaned_count} files older than {days_old} days (dry run)"
        else:
            # Actually delete files
            cleaned_count = await media_manager.cleanup_old_media(days_old)
            operation = f"Deleted {cleaned_count} files older than {days_old} days"
        
        return CleanupResponse(
            cleaned_count=cleaned_count,
            operation=operation,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup old media: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/search")
async def search_media(
    user_id: str = Depends(get_user_id),
    query: str = Query(..., description="Search query"),
    media_type: Optional[str] = Query(None, description="Filter by media type"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """Search media files across tasks"""
    try:
        # This would implement media search functionality
        # For now, return empty results
        
        return {
            "results": [],
            "total_count": 0,
            "query": query,
            "filters": {
                "media_type": media_type,
                "task_id": task_id
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to search media: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/media/batch-download")
async def batch_download_media(
    task_id: str,
    user_id: str = Depends(get_user_id),
    media_types: List[str] = Query(None, description="Media types to include"),
    format: str = Query("zip", regex="^(zip|tar)$", description="Archive format")
):
    """Download multiple media files as an archive"""
    try:
        # Verify task exists
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # This would create a zip/tar archive of media files
        # For now, return a placeholder response
        
        raise HTTPException(status_code=501, detail="Batch download not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create batch download {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))