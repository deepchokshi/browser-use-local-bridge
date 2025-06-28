"""
Browser-Use Local Bridge API
A production-ready local bridge for browser automation with n8n integration
"""

import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import structlog
from datetime import datetime
import os

from core.config import settings
from api.v1.endpoints import system, tasks, media, live

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Setup logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.LOG_LEVEL.upper())
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Browser-Use Local Bridge API", 
                version="1.0.0", 
                environment=settings.ENVIRONMENT,
                port=settings.PORT)
    
    # Ensure directories exist
    try:
        os.makedirs(settings.MEDIA_DIR, exist_ok=True)
        os.makedirs(settings.BROWSER_USER_DATA_DIR, exist_ok=True)
        logger.info("Directories initialized", 
                   media_dir=settings.MEDIA_DIR,
                   browser_data_dir=settings.BROWSER_USER_DATA_DIR)
    except Exception as e:
        logger.error("Failed to create directories", error=str(e))
        raise
    
    # Validate AI providers
    from core.llm_factory import LLMFactory
    providers = LLMFactory.get_available_providers()
    available_count = sum(1 for available in providers.values() if available)
    
    if available_count == 0:
        logger.warning("No AI providers configured - tasks will fail without proper configuration")
    else:
        logger.info("AI providers available", 
                   count=available_count, 
                   providers={k: v for k, v in providers.items() if v})
    
    # Initialize task manager
    from core.tasks import task_manager
    logger.info("Task manager initialized", 
               max_concurrent_tasks=settings.MAX_CONCURRENT_TASKS)
    
    # Initialize media manager
    from core.media_manager import media_manager
    logger.info("Media manager initialized", 
               media_dir=settings.MEDIA_DIR)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Browser-Use Local Bridge API")
    
    # Cleanup active tasks
    try:
        # Stop all active tasks gracefully
        for task_id in list(task_manager.active_tasks.keys()):
            try:
                await task_manager.stop_task(settings.DEFAULT_USER_ID, task_id)
            except Exception as e:
                logger.warning("Failed to stop task during shutdown", 
                              task_id=task_id, error=str(e))
        
        # Close browser sessions
        for session in list(task_manager.browser_sessions.values()):
            try:
                await session.close()
            except Exception as e:
                logger.warning("Failed to close browser session", error=str(e))
                
        logger.info("Cleanup completed")
        
    except Exception as e:
        logger.error("Error during shutdown cleanup", error=str(e))

# Create FastAPI app with comprehensive configuration
app = FastAPI(
    title="Browser-Use Local Bridge API",
    description="""
    A production-ready local bridge for browser automation with comprehensive n8n integration.
    
    ## Features
    - **Multi-AI Provider Support**: OpenAI, Azure OpenAI, Anthropic, Google AI, Mistral, Ollama, Amazon Bedrock
    - **Task Management**: Complete task lifecycle with pause/resume/stop capabilities
    - **Media Handling**: Automatic screenshots, recordings, and file management
    - **Real-time Monitoring**: WebSocket and SSE support for live task updates
    - **Production Ready**: Comprehensive logging, error handling, and monitoring
    - **n8n Integration**: Drop-in replacement for Browser Use Cloud API
    
    ## Getting Started
    1. Configure your AI provider API keys in environment variables
    2. Create a task using POST /api/v1/run-task
    3. Monitor progress via WebSocket at /live/{task_id}
    4. Access media files at /api/v1/media/{task_id}/{filename}
    """,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure this properly in production
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware for request logging and user tracking
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and add request ID"""
    start_time = datetime.utcnow()
    
    # Generate request ID
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    # Log request
    logger.info("Request started",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                user_agent=request.headers.get("user-agent"),
                user_id=request.headers.get("x-user-id"))
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log response
        logger.info("Request completed",
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_seconds=duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error("Request failed",
                     request_id=request_id,
                     error=str(e),
                     duration_seconds=duration)
        raise

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error("Unhandled exception",
                 request_id=request_id,
                 exception_type=type(exc).__name__,
                 exception_message=str(exc),
                 path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning("HTTP exception",
                   request_id=request_id,
                   status_code=exc.status_code,
                   detail=exc.detail,
                   path=request.url.path)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Include API routers
app.include_router(
    system.router, 
    prefix=settings.API_V1_PREFIX, 
    tags=["system"]
)

app.include_router(
    tasks.router, 
    prefix=settings.API_V1_PREFIX, 
    tags=["tasks"]
)

app.include_router(
    media.router, 
    prefix=settings.API_V1_PREFIX, 
    tags=["media"]
)

app.include_router(
    live.router, 
    prefix=settings.API_V1_PREFIX, 
    tags=["live-monitoring"]
)

# Serve static files for web interface (if exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/")
async def read_root():
    """API root endpoint with basic information"""
    return {
        "message": "Welcome to Browser-Use Local Bridge API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.DEBUG else "disabled",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Multi-AI Provider Support",
            "Complete Task Management", 
            "Real-time Monitoring",
            "Media File Handling",
            "n8n Integration",
            "Production Ready"
        ]
    }

# Health check endpoint (duplicate for convenience)
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
        access_log=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )