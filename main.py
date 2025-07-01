#!/usr/bin/env python3
"""
Browser-Use Local Bridge API
===========================

A production-ready FastAPI server that provides a local bridge to browser-use functionality.
This serves as a drop-in replacement for Browser Use Cloud API with full n8n integration support.

Features:
- Multiple AI provider support (OpenAI, Azure, Anthropic, Google, Mistral, Ollama, Bedrock)
- Comprehensive task management with real-time monitoring
- WebSocket and SSE live updates
- Media file handling (screenshots, recordings)
- Docker containerization support
- Production-ready logging and error handling
"""

import asyncio
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import structlog
from datetime import datetime

# Fix Windows asyncio policy for Playwright compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import after setting event loop policy
from core.config import settings
from core.media_manager import media_manager
from api.v1.endpoints import tasks, system, media, live

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
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

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Browser-Use Local Bridge API", version="1.0.0")
    
    # Ensure media directory exists
    try:
        media_manager.ensure_media_directory()
        logger.info("📁 Media directory initialized", path=settings.MEDIA_DIR)
    except Exception as e:
        logger.error("❌ Failed to initialize media directory", error=str(e))
    
    # Log configuration
    logger.info("⚙️ Configuration loaded", 
                telemetry_enabled=settings.TELEMETRY_ENABLED,
                max_concurrent_tasks=settings.MAX_CONCURRENT_TASKS,
                default_llm_provider=settings.DEFAULT_LLM_PROVIDER)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Browser-Use Local Bridge API")

# Create FastAPI application
app = FastAPI(
    title="Browser-Use Local Bridge API",
    description="""
    🌐 **Browser-Use Local Bridge API**
    
    A production-ready local bridge for browser automation that serves as a drop-in replacement 
    for Browser Use Cloud API. Perfect for n8n integration and automation workflows.
    
    ## 🚀 Features
    
    - **Multi-AI Provider Support**: OpenAI, Azure OpenAI, Anthropic, Google AI, Mistral, Ollama, Amazon Bedrock
    - **Complete Task Management**: Create, monitor, pause, resume, and stop browser automation tasks
    - **Real-time Monitoring**: WebSocket and Server-Sent Events for live progress updates
    - **Media Handling**: Automatic screenshot capture and file management
    - **Production Ready**: Comprehensive logging, error handling, and monitoring
    - **n8n Integration**: Designed specifically for seamless n8n workflow integration
    
    ## 📚 Quick Start
    
    1. **Create a Task**: `POST /api/v1/run-task`
    2. **Monitor Progress**: `GET /api/v1/task/{id}/status`
    3. **Get Results**: `GET /api/v1/task/{id}`
    4. **Live Updates**: `WebSocket /api/v1/live/{id}`
    
    ## 🔧 Configuration
    
    Configure via environment variables or `.env` file:
    - `OPENAI_API_KEY`: Your OpenAI API key
    - `DEFAULT_LLM_PROVIDER`: AI provider to use (default: openai)
    - `MAX_CONCURRENT_TASKS`: Maximum concurrent tasks (default: 3)
    
    ## 📖 Documentation
    
    - **Examples**: Check the `/examples` folder for practical use cases
    - **API Reference**: Explore the interactive API docs below
    - **GitHub**: [browser-use-local-bridge](https://github.com/deepchokshi/browser-use-local-bridge)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Add security middleware (only in production)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure this properly in production
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = datetime.utcnow()
    
    # Generate request ID
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    # Log request
    logger.info("📥 Request started",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                user_agent=request.headers.get("user-agent"),
                user_id=request.headers.get("x-user-id"))
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log response
    logger.info("📤 Request completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_seconds=round(duration, 3))
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    import traceback
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error("💥 Unhandled exception",
                 request_id=request_id,
                 exception=str(exc),
                 traceback=traceback.format_exc(),
                 url=str(request.url),
                 method=request.method)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please check the logs.",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured response"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    
    Returns the current status of the API service.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    
    Provides basic information about the API and links to documentation.
    """
    return {
        "name": "Browser-Use Local Bridge API",
        "version": "1.0.0",
        "description": "Local bridge for browser automation with n8n integration support",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_base": "/api/v1",
        "github": "https://github.com/deepchokshi/browser-use-local-bridge",
        "examples": "Check the /examples folder for practical use cases"
    }

# Include API routers
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(media.router, prefix="/api/v1", tags=["Media"])
app.include_router(live.router, prefix="/api/v1", tags=["Live Monitoring"])

if __name__ == "__main__":
    # Additional Windows-specific fixes
    if sys.platform == "win32":
        # Set environment variables for better Windows compatibility
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUTF8"] = "1"
    
    # Configure uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
        loop="asyncio"  # Explicitly use asyncio loop
    )