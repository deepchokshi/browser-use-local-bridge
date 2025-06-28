"""
Media Manager for handling screenshots, recordings, and file operations
"""

import os
import asyncio
import aiofiles
from typing import List, Optional, Dict, Any
from pathlib import Path
from PIL import Image
import logging
from datetime import datetime

from core.config import settings
from models.task import TaskMedia

logger = logging.getLogger(__name__)

class MediaManager:
    """Manages media files for tasks including screenshots and recordings"""
    
    def __init__(self):
        self.media_dir = Path(settings.MEDIA_DIR)
        self.ensure_media_directory()
    
    def ensure_media_directory(self):
        """Ensure media directory exists"""
        try:
            self.media_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Media directory ensured: {self.media_dir}")
        except Exception as e:
            logger.error(f"Failed to create media directory: {e}")
            raise
    
    def get_task_media_dir(self, task_id: str, user_id: str) -> Path:
        """Get media directory for a specific task"""
        task_dir = self.media_dir / user_id / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir
    
    async def save_screenshot(
        self, 
        task_id: str, 
        user_id: str, 
        screenshot_data: bytes,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskMedia:
        """Save screenshot data to file"""
        try:
            task_dir = self.get_task_media_dir(task_id, user_id)
            
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = task_dir / filename
            
            # Save screenshot
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(screenshot_data)
            
            # Optimize screenshot if needed
            if settings.SCREENSHOT_QUALITY < 100:
                await self._optimize_image(filepath, settings.SCREENSHOT_QUALITY)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Create media record
            media = TaskMedia(
                filename=filename,
                filepath=str(filepath),
                media_type="screenshot",
                size_bytes=file_size,
                metadata=metadata or {}
            )
            
            logger.info(f"Screenshot saved: {filepath} ({file_size} bytes)")
            return media
            
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            raise
    
    async def save_recording(
        self,
        task_id: str,
        user_id: str,
        recording_data: bytes,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskMedia:
        """Save recording data to file"""
        try:
            task_dir = self.get_task_media_dir(task_id, user_id)
            
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"recording_{timestamp}.webm"
            
            filepath = task_dir / filename
            
            # Save recording
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(recording_data)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Check file size limit
            max_size_bytes = settings.MAX_MEDIA_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                logger.warning(f"Recording file size ({file_size} bytes) exceeds limit ({max_size_bytes} bytes)")
            
            # Create media record
            media = TaskMedia(
                filename=filename,
                filepath=str(filepath),
                media_type="recording",
                size_bytes=file_size,
                metadata=metadata or {}
            )
            
            logger.info(f"Recording saved: {filepath} ({file_size} bytes)")
            return media
            
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            raise
    
    async def get_media_file(self, task_id: str, user_id: str, filename: str) -> Optional[Path]:
        """Get path to media file"""
        try:
            task_dir = self.get_task_media_dir(task_id, user_id)
            filepath = task_dir / filename
            
            if filepath.exists() and filepath.is_file():
                return filepath
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get media file: {e}")
            return None
    
    async def list_task_media(self, task_id: str, user_id: str) -> List[TaskMedia]:
        """List all media files for a task"""
        try:
            task_dir = self.get_task_media_dir(task_id, user_id)
            media_files = []
            
            if not task_dir.exists():
                return media_files
            
            for filepath in task_dir.iterdir():
                if filepath.is_file():
                    file_size = os.path.getsize(filepath)
                    file_stat = os.stat(filepath)
                    created_at = datetime.fromtimestamp(file_stat.st_ctime)
                    
                    # Determine media type from extension
                    media_type = self._get_media_type_from_extension(filepath.suffix)
                    
                    media = TaskMedia(
                        filename=filepath.name,
                        filepath=str(filepath),
                        media_type=media_type,
                        size_bytes=file_size,
                        created_at=created_at
                    )
                    media_files.append(media)
            
            # Sort by creation time
            media_files.sort(key=lambda x: x.created_at)
            return media_files
            
        except Exception as e:
            logger.error(f"Failed to list task media: {e}")
            return []
    
    async def delete_task_media(self, task_id: str, user_id: str) -> bool:
        """Delete all media files for a task"""
        try:
            task_dir = self.get_task_media_dir(task_id, user_id)
            
            if not task_dir.exists():
                return True
            
            # Delete all files in task directory
            for filepath in task_dir.iterdir():
                if filepath.is_file():
                    filepath.unlink()
            
            # Remove directory if empty
            try:
                task_dir.rmdir()
            except OSError:
                pass  # Directory not empty or other error
            
            logger.info(f"Deleted media for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task media: {e}")
            return False
    
    async def delete_media_file(self, task_id: str, user_id: str, filename: str) -> bool:
        """Delete a specific media file"""
        try:
            filepath = await self.get_media_file(task_id, user_id, filename)
            
            if filepath and filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted media file: {filepath}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete media file: {e}")
            return False
    
    async def get_media_info(self, task_id: str, user_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a media file"""
        try:
            filepath = await self.get_media_file(task_id, user_id, filename)
            
            if not filepath or not filepath.exists():
                return None
            
            file_stat = os.stat(filepath)
            info = {
                "filename": filepath.name,
                "size_bytes": file_stat.st_size,
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "media_type": self._get_media_type_from_extension(filepath.suffix)
            }
            
            # Add image-specific info for screenshots
            if filepath.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                try:
                    with Image.open(filepath) as img:
                        info["width"] = img.width
                        info["height"] = img.height
                        info["format"] = img.format
                except Exception as e:
                    logger.warning(f"Failed to get image info: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get media info: {e}")
            return None
    
    async def _optimize_image(self, filepath: Path, quality: int):
        """Optimize image file size"""
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save with optimization
                img.save(filepath, format='JPEG', quality=quality, optimize=True)
                
        except Exception as e:
            logger.warning(f"Failed to optimize image {filepath}: {e}")
    
    def _get_media_type_from_extension(self, extension: str) -> str:
        """Get media type from file extension"""
        extension = extension.lower()
        
        if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return "screenshot"
        elif extension in ['.mp4', '.webm', '.avi', '.mov']:
            return "recording"
        elif extension in ['.json']:
            return "data"
        elif extension in ['.txt', '.log']:
            return "log"
        else:
            return "unknown"
    
    async def cleanup_old_media(self, days_old: int = 7) -> int:
        """Clean up media files older than specified days"""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days_old * 24 * 3600)
            deleted_count = 0
            
            for user_dir in self.media_dir.iterdir():
                if not user_dir.is_dir():
                    continue
                
                for task_dir in user_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    
                    for filepath in task_dir.iterdir():
                        if filepath.is_file():
                            file_stat = os.stat(filepath)
                            if file_stat.st_mtime < cutoff_time:
                                filepath.unlink()
                                deleted_count += 1
                    
                    # Remove empty task directories
                    try:
                        if not any(task_dir.iterdir()):
                            task_dir.rmdir()
                    except OSError:
                        pass
                
                # Remove empty user directories
                try:
                    if not any(user_dir.iterdir()):
                        user_dir.rmdir()
                except OSError:
                    pass
            
            logger.info(f"Cleaned up {deleted_count} old media files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old media: {e}")
            return 0

# Global media manager instance
media_manager = MediaManager() 