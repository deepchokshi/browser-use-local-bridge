"""
Live Monitoring API Endpoints
Provides real-time task monitoring via WebSocket and Server-Sent Events
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header, Path
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import asyncio
import json
import logging
from datetime import datetime

from api.v1.schemas import LiveTaskUpdate
from core.storage import task_storage
from core.config import settings
from models.task import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header or use default"""
    return x_user_id or settings.DEFAULT_USER_ID

class ConnectionManager:
    """Manages WebSocket connections for live monitoring"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept a WebSocket connection and add to task monitoring"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove WebSocket connection"""
        if task_id in self.active_connections:
            try:
                self.active_connections[task_id].remove(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
                logger.info(f"WebSocket disconnected for task {task_id}")
            except ValueError:
                pass
    
    async def send_task_update(self, task_id: str, update: Dict[str, Any]):
        """Send update to all connections monitoring a specific task"""
        if task_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_text(json.dumps(update))
                except Exception as e:
                    logger.warning(f"Failed to send update to WebSocket: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected connections
            for ws in disconnected:
                self.disconnect(ws, task_id)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a user"""
        # This would require tracking user connections
        # For now, just log the message
        logger.info(f"Broadcasting to user {user_id}: {message}")

manager = ConnectionManager()

@router.websocket("/live/{task_id}")
async def websocket_task_monitor(
    websocket: WebSocket,
    task_id: str = Path(..., description="Task ID to monitor")
):
    """
    WebSocket endpoint for real-time task monitoring
    
    Provides live updates on task progress, status changes, and new media files
    """
    try:
        await manager.connect(websocket, task_id)
        
        # Send initial task status
        # Try to get user_id from query parameters
        query_params = dict(websocket.query_params)
        user_id = query_params.get("user_id", settings.DEFAULT_USER_ID)
        
        # Try to find task under the specified user, then try default user
        task = task_storage.get_task(user_id, task_id)
        if not task and user_id != settings.DEFAULT_USER_ID:
            task = task_storage.get_task(settings.DEFAULT_USER_ID, task_id)
            if task:
                user_id = settings.DEFAULT_USER_ID
        
        if task:
            initial_update = LiveTaskUpdate(
                task_id=task_id,
                status=task.status,
                progress_percentage=task.progress_percentage,
                current_step=task.current_step,
                latest_screenshot=None,  # Would get latest screenshot path
                timestamp=datetime.utcnow()
            )
            await websocket.send_text(initial_update.model_dump_json())
        else:
            await websocket.send_text(json.dumps({
                "error": "Task not found",
                "task_id": task_id
            }))
            return
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for a short period
                await asyncio.sleep(2)
                
                # Get updated task status
                task = task_storage.get_task(user_id, task_id)
                if task:
                    update = LiveTaskUpdate(
                        task_id=task_id,
                        status=task.status,
                        progress_percentage=task.progress_percentage,
                        current_step=task.current_step,
                        latest_screenshot=None,  # Would get latest screenshot
                        timestamp=datetime.utcnow()
                    )
                    await websocket.send_text(update.model_dump_json())
                    
                    # If task is completed, send final update and close
                    if task.is_completed():
                        await asyncio.sleep(1)  # Give time for final update
                        break
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket monitoring: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket, task_id)

@router.get("/live/{task_id}/sse")
async def sse_task_monitor(
    task_id: str = Path(..., description="Task ID to monitor"),
    user_id: str = Depends(get_user_id)
):
    """
    Server-Sent Events endpoint for real-time task monitoring
    
    Alternative to WebSocket for browsers that prefer SSE
    """
    
    async def event_stream():
        """Generate Server-Sent Events for task updates"""
        try:
            # Send initial task status
            task = task_storage.get_task(user_id, task_id)
            if not task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                return
            
            # Send initial update
            initial_update = LiveTaskUpdate(
                task_id=task_id,
                status=task.status,
                progress_percentage=task.progress_percentage,
                current_step=task.current_step,
                latest_screenshot=None,
                timestamp=datetime.utcnow()
            )
            yield f"data: {initial_update.model_dump_json()}\n\n"
            
            # Send periodic updates
            last_update_time = datetime.utcnow()
            while True:
                await asyncio.sleep(2)
                
                # Get current task status
                current_task = task_storage.get_task(user_id, task_id)
                if not current_task:
                    yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                    break
                
                # Check if task has been updated
                if current_task.updated_at > last_update_time:
                    update = LiveTaskUpdate(
                        task_id=task_id,
                        status=current_task.status,
                        progress_percentage=current_task.progress_percentage,
                        current_step=current_task.current_step,
                        latest_screenshot=None,
                        timestamp=datetime.utcnow()
                    )
                    yield f"data: {update.model_dump_json()}\n\n"
                    last_update_time = current_task.updated_at
                
                # Stop streaming if task is completed
                if current_task.is_completed():
                    # Send final update
                    final_update = LiveTaskUpdate(
                        task_id=task_id,
                        status=current_task.status,
                        progress_percentage=100.0 if current_task.status == TaskStatus.FINISHED else current_task.progress_percentage,
                        current_step=current_task.current_step,
                        latest_screenshot=None,
                        timestamp=datetime.utcnow()
                    )
                    yield f"data: {final_update.model_dump_json()}\n\n"
                    yield f"event: close\ndata: Task completed\n\n"
                    break
                    
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/live/{task_id}/status")
async def get_live_task_status(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Depends(get_user_id)
):
    """Get current task status for live monitoring (polling endpoint)"""
    try:
        task = task_storage.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get latest screenshot if available
        latest_screenshot = None
        if task.media:
            screenshots = [m for m in task.media if m.media_type == "screenshot"]
            if screenshots:
                latest_screenshot = screenshots[-1].filename
        
        return LiveTaskUpdate(
            task_id=task_id,
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            latest_screenshot=latest_screenshot,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live/user/{user_id}/tasks")
async def get_user_active_tasks(
    user_id: str = Path(..., description="User ID"),
    requesting_user_id: str = Depends(get_user_id)
):
    """Get all active tasks for a user (for dashboard monitoring)"""
    try:
        # Simple authorization check
        if user_id != requesting_user_id and requesting_user_id != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all tasks for user
        all_tasks = task_storage.list_tasks(user_id, 1, 1000)
        
        # Filter active tasks
        active_tasks = [task for task in all_tasks if task.is_active()]
        
        # Create live updates for each active task
        updates = []
        for task in active_tasks:
            latest_screenshot = None
            if task.media:
                screenshots = [m for m in task.media if m.media_type == "screenshot"]
                if screenshots:
                    latest_screenshot = screenshots[-1].filename
            
            update = LiveTaskUpdate(
                task_id=task.id,
                status=task.status,
                progress_percentage=task.progress_percentage,
                current_step=task.current_step,
                latest_screenshot=latest_screenshot,
                timestamp=datetime.utcnow()
            )
            updates.append(update)
        
        return {
            "user_id": user_id,
            "active_tasks_count": len(updates),
            "tasks": updates,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user active tasks {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live/stats")
async def get_live_system_stats():
    """Get real-time system statistics"""
    try:
        from core.tasks import task_manager
        
        stats = task_manager.get_system_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_tasks": stats.get("active_tasks", 0),
            "total_browser_sessions": stats.get("total_browser_sessions", 0),
            "memory_usage_mb": stats.get("memory_usage_mb", 0),
            "cpu_percent": stats.get("cpu_percent", 0),
            "available_providers": stats.get("available_providers", {}),
            "websocket_connections": sum(len(connections) for connections in manager.active_connections.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to get live system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 