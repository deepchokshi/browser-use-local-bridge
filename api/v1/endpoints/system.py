"""
System Management and Health Check API Endpoints
Provides system status, configuration, and monitoring capabilities
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any
import logging
import psutil
import time
from datetime import datetime

from api.v1.schemas import (
    PingResponse, BrowserConfigResponse, SystemStatsResponse,
    HealthCheckResponse, LLMProviderResponse, ConfigResponse,
    ScreenshotTestResponse, CleanupResponse
)
from core.config import settings
from core.llm_factory import LLMFactory
from core.tasks import task_manager
from core.media_manager import media_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Track server start time for uptime calculation
SERVER_START_TIME = time.time()

@router.get("/ping", response_model=PingResponse)
async def ping():
    """Simple health check endpoint"""
    return PingResponse(
        message="pong",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check with system status"""
    try:
        checks = {}
        
        # Check memory usage
        memory_info = psutil.virtual_memory()
        checks["memory_ok"] = memory_info.percent < 90
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        checks["cpu_ok"] = cpu_percent < 90
        
        # Check disk space
        disk_info = psutil.disk_usage('/')
        checks["disk_ok"] = (disk_info.free / disk_info.total) > 0.1
        
        # Check if at least one AI provider is available
        providers = LLMFactory.get_available_providers()
        checks["llm_provider_ok"] = any(providers.values())
        
        # Check media directory
        try:
            media_manager.ensure_media_directory()
            checks["media_dir_ok"] = True
        except Exception:
            checks["media_dir_ok"] = False
        
        # Overall status
        status = "healthy" if all(checks.values()) else "degraded"
        
        return HealthCheckResponse(
            status=status,
            timestamp=datetime.utcnow(),
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            checks={"error": False}
        )

@router.get("/browser-config", response_model=BrowserConfigResponse)
async def get_browser_config():
    """Get current browser configuration"""
    return BrowserConfigResponse(
        headless=settings.BROWSER_HEADLESS,
        user_data_persistence=settings.BROWSER_USER_DATA_PERSISTENCE,
        user_data_dir=settings.BROWSER_USER_DATA_DIR,
        viewport_width=settings.BROWSER_VIEWPORT_WIDTH,
        viewport_height=settings.BROWSER_VIEWPORT_HEIGHT,
        timeout=settings.BROWSER_TIMEOUT,
        chrome_executable_path=settings.CHROME_EXECUTABLE_PATH,
        enable_screenshots=settings.ENABLE_SCREENSHOTS,
        enable_recordings=settings.ENABLE_RECORDINGS
    )

@router.get("/system-stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        # Get task manager stats
        task_stats = task_manager.get_system_stats()
        
        # Calculate uptime
        uptime_seconds = time.time() - SERVER_START_TIME
        
        return SystemStatsResponse(
            active_tasks=task_stats.get("active_tasks", 0),
            max_concurrent_tasks=task_stats.get("max_concurrent_tasks", 5),
            total_browser_sessions=task_stats.get("total_browser_sessions", 0),
            available_providers=task_stats.get("available_providers", {}),
            memory_usage_mb=task_stats.get("memory_usage_mb", 0),
            cpu_percent=task_stats.get("cpu_percent", 0),
            uptime_seconds=uptime_seconds
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/llm-providers", response_model=List[LLMProviderResponse])
async def get_llm_providers():
    """Get information about available LLM providers"""
    try:
        providers = LLMFactory.get_available_providers()
        
        provider_info = [
            LLMProviderResponse(
                provider="openai",
                available=providers.get("openai", False),
                models=["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
                description="OpenAI GPT models"
            ),
            LLMProviderResponse(
                provider="azure_openai",
                available=providers.get("azure_openai", False),
                models=["gpt-4", "gpt-35-turbo"],
                description="Azure-hosted OpenAI models"
            ),
            LLMProviderResponse(
                provider="anthropic",
                available=providers.get("anthropic", False),
                models=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                description="Anthropic Claude models"
            ),
            LLMProviderResponse(
                provider="google",
                available=providers.get("google", False),
                models=["gemini-pro", "gemini-pro-vision"],
                description="Google Gemini models"
            ),
            LLMProviderResponse(
                provider="mistral",
                available=providers.get("mistral", False),
                models=["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"],
                description="Mistral AI models"
            ),
            LLMProviderResponse(
                provider="ollama",
                available=providers.get("ollama", False),
                models=["llama2", "codellama", "mistral", "phi"],
                description="Local Ollama models"
            ),
            LLMProviderResponse(
                provider="bedrock",
                available=providers.get("bedrock", False),
                models=["anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-3-haiku-20240307-v1:0"],
                description="Amazon Bedrock models"
            )
        ]
        
        return provider_info
        
    except Exception as e:
        logger.error(f"Failed to get LLM providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=ConfigResponse)
async def get_configuration():
    """Get current system configuration"""
    try:
        from models.task import BrowserConfig
        
        browser_config = BrowserConfig(
            headless=settings.BROWSER_HEADLESS,
            user_data_dir=settings.BROWSER_USER_DATA_DIR,
            chrome_executable_path=settings.CHROME_EXECUTABLE_PATH,
            viewport_width=settings.BROWSER_VIEWPORT_WIDTH,
            viewport_height=settings.BROWSER_VIEWPORT_HEIGHT,
            timeout=settings.BROWSER_TIMEOUT,
            enable_screenshots=settings.ENABLE_SCREENSHOTS,
            enable_recordings=settings.ENABLE_RECORDINGS
        )
        
        return ConfigResponse(
            browser_config=browser_config,
            default_llm_provider=settings.DEFAULT_LLM_PROVIDER,
            default_model=settings.DEFAULT_MODEL,
            max_concurrent_tasks=settings.MAX_CONCURRENT_TASKS,
            available_providers=LLMFactory.get_available_providers()
        )
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-screenshot", response_model=ScreenshotTestResponse)
async def test_screenshot():
    """Test screenshot functionality"""
    try:
        # This would create a test browser session and take a screenshot
        # For now, we'll just return a placeholder response
        
        # In a real implementation:
        # 1. Create a temporary browser session
        # 2. Navigate to a test page
        # 3. Take a screenshot
        # 4. Save it temporarily
        # 5. Return the result
        
        return ScreenshotTestResponse(
            success=True,
            message="Screenshot test not fully implemented yet",
            screenshot_path=None,
            size_bytes=None,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Screenshot test failed: {e}")
        return ScreenshotTestResponse(
            success=False,
            message=f"Screenshot test failed: {str(e)}",
            screenshot_path=None,
            size_bytes=None,
            timestamp=datetime.utcnow()
        )

@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_old_data(
    days_old: int = Query(7, ge=1, le=365, description="Days old for cleanup")
):
    """Clean up old task data and media files"""
    try:
        cleaned_count = await task_manager.cleanup_completed_tasks(days_old)
        
        return CleanupResponse(
            cleaned_count=cleaned_count,
            operation=f"Cleaned up data older than {days_old} days",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    """Get detailed system metrics (Prometheus format)"""
    try:
        stats = task_manager.get_system_stats()
        
        # Basic metrics in Prometheus format
        metrics = []
        metrics.append(f"# HELP browser_use_active_tasks Number of active tasks")
        metrics.append(f"# TYPE browser_use_active_tasks gauge")
        metrics.append(f"browser_use_active_tasks {stats.get('active_tasks', 0)}")
        
        metrics.append(f"# HELP browser_use_memory_usage_mb Memory usage in MB")
        metrics.append(f"# TYPE browser_use_memory_usage_mb gauge")
        metrics.append(f"browser_use_memory_usage_mb {stats.get('memory_usage_mb', 0)}")
        
        metrics.append(f"# HELP browser_use_cpu_percent CPU usage percentage")
        metrics.append(f"# TYPE browser_use_cpu_percent gauge")
        metrics.append(f"browser_use_cpu_percent {stats.get('cpu_percent', 0)}")
        
        metrics.append(f"# HELP browser_use_uptime_seconds Server uptime in seconds")
        metrics.append(f"# TYPE browser_use_uptime_seconds counter")
        metrics.append(f"browser_use_uptime_seconds {time.time() - SERVER_START_TIME}")
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/version")
async def get_version():
    """Get API version and build information"""
    return {
        "version": "1.0.0",
        "build_date": "2024-01-01",
        "git_commit": "unknown",
        "python_version": "3.8+",
        "dependencies": {
            "fastapi": "0.104+",
            "browser-use": "0.1+",
            "pydantic": "2.5+"
        }
    }

@router.get("/environment")
async def get_environment_info():
    """Get environment information (non-sensitive)"""
    try:
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "port": settings.PORT,
            "host": settings.HOST,
            "log_level": settings.LOG_LEVEL,
            "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
            "task_timeout_minutes": settings.TASK_TIMEOUT_MINUTES,
            "browser_headless": settings.BROWSER_HEADLESS,
            "telemetry_enabled": settings.TELEMETRY_ENABLED,
            "media_dir": settings.MEDIA_DIR,
            "enable_screenshots": settings.ENABLE_SCREENSHOTS,
            "enable_recordings": settings.ENABLE_RECORDINGS
        }
        
    except Exception as e:
        logger.error(f"Failed to get environment info: {e}")
        raise HTTPException(status_code=500, detail=str(e))