# Browser-Use Local Bridge

A production-ready local bridge for browser automation with comprehensive n8n integration. This project provides a drop-in replacement for Browser Use Cloud API, running entirely on your local infrastructure with support for multiple AI providers and advanced automation capabilities.

## 🎯 Core Purpose

- **Local Browser Automation Bridge**: Complete parity with Browser Use Cloud API endpoints
- **n8n Integration**: Specifically designed for seamless n8n workflow automation
- **Cloud Alternative**: Eliminates dependency on Browser Use cloud service
- **Production Ready**: Comprehensive logging, monitoring, and error handling
- **Advanced Features**: Custom functions, structured output, lifecycle hooks, and more

## ✨ Features

### 🤖 AI/LLM Provider Support
- **OpenAI**: GPT models (gpt-4o, gpt-4o-mini, gpt-4, gpt-3.5-turbo)
- **Azure OpenAI**: Enterprise Azure-hosted OpenAI models with custom endpoints
- **Anthropic**: Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku)
- **MistralAI**: Mistral models (mistral-large, mistral-medium, mistral-small)
- **Google AI**: Gemini models (gemini-pro, gemini-pro-vision)
- **Ollama**: Local LLM hosting with custom models
- **Amazon Bedrock**: AWS-hosted models (Claude, Llama, Titan)
- **Custom OpenAI-compatible APIs**: Via OPENAI_BASE_URL for any compatible service

### 📋 Advanced Task Management
- **Complete Lifecycle**: Create, start, pause, resume, stop, and delete tasks
- **Real-time Monitoring**: WebSocket and Server-Sent Events (SSE) support
- **Progress Tracking**: Step-by-step execution monitoring with detailed logs
- **Status Management**: CREATED, RUNNING, FINISHED, STOPPED, PAUSED, FAILED, STOPPING states
- **Task History**: Comprehensive task execution logs and metadata
- **Multi-user Support**: User-segregated task management with header-based identification
- **Performance Metrics**: Execution time, memory usage, and resource tracking

### 🌐 Comprehensive Browser Configuration
- **Complete BrowserProfile Support**: Full parity with browser-use library
- **Flexible Modes**: Headless and headful browser execution
- **Session Management**: Browser session persistence and cookie handling
- **Advanced Options**: 
  - Stealth mode and security bypass
  - Custom viewport and device simulation
  - Proxy support and geolocation
  - Video recording and HAR capture
  - Custom Chrome flags and arguments
- **Mobile Simulation**: Touch support, mobile viewports, device scaling
- **Security Features**: HTTPS bypass, CSP bypass, certificate handling

### 🎛️ Advanced Agent Configuration
- **Vision Support**: Enable/disable vision capabilities for different models
- **Custom Functions**: Define custom actions with webhook or code implementation
- **Structured Output**: JSON schema validation and structured responses
- **Lifecycle Hooks**: Execute custom code at task lifecycle events
- **Sensitive Data Handling**: Domain-specific data masking and replacement
- **Planner Configuration**: Separate LLM for planning with custom prompts
- **Controller System**: Advanced output formatting and validation

### 📡 Comprehensive API
- **Task Operations**: Full CRUD operations with advanced filtering and pagination
- **Media Management**: Screenshots, recordings, file serving with metadata
- **Live Monitoring**: Real-time task updates via WebSocket and SSE
- **System Management**: Health checks, configuration, metrics, and statistics
- **Cookie Management**: Extract and manage browser cookies
- **Export Capabilities**: JSON and CSV export of task data
- **n8n Compatible**: Drop-in replacement for Browser Use Cloud API

### 🛡️ Security & Production Features
- **Multi-user Support**: Header-based user identification and isolation
- **Comprehensive Logging**: Structured logging with request tracking and correlation IDs
- **Error Handling**: Graceful error management with detailed error reporting
- **Health Monitoring**: Built-in health checks, metrics, and system statistics
- **Resource Management**: Automatic cleanup, resource limits, and memory monitoring
- **CORS Support**: Configurable cross-origin requests
- **Rate Limiting**: Configurable request rate limiting
- **Telemetry**: Optional telemetry and monitoring integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser
- At least one AI provider API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/deepchokshi/browser-use-local-bridge.git
cd browser-use-local-bridge
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Basic deployment**
```bash
docker-compose up -d
```

2. **With monitoring**
```bash
docker-compose --profile monitoring up -d
```

3. **Production with Nginx**
```bash
docker-compose --profile production up -d
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ===== AI Provider Configuration =====
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom endpoint
OPENAI_ORGANIZATION=your_org_id  # Optional

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2023-12-01-preview

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # Optional: custom endpoint

# Google AI
GOOGLE_AI_API_KEY=your_google_key
GOOGLE_AI_PROJECT_ID=your_project_id

# Mistral AI
MISTRAL_API_KEY=your_mistral_key
MISTRAL_BASE_URL=https://api.mistral.ai  # Optional: custom endpoint

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Amazon Bedrock
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Default AI Provider
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini

# ===== Server Configuration =====
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=info
DEBUG=false
ENVIRONMENT=production
API_V1_PREFIX=/api/v1
CORS_ORIGINS=*

# ===== Browser Configuration =====
CHROME_EXECUTABLE_PATH=/path/to/chrome  # Optional
BROWSER_HEADLESS=true
BROWSER_USER_DATA_PERSISTENCE=true
BROWSER_USER_DATA_DIR=./browser_data
BROWSER_TIMEOUT=30000
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080

# ===== Media and Storage =====
MEDIA_DIR=./media
MAX_MEDIA_SIZE_MB=100
SCREENSHOT_QUALITY=90
ENABLE_SCREENSHOTS=true
ENABLE_RECORDINGS=false

# ===== Task Management =====
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT_MINUTES=30
DEFAULT_USER_ID=default_user

# ===== Security =====
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== Monitoring and Telemetry =====
TELEMETRY_ENABLED=false
ENABLE_METRICS=true
SENTRY_DSN=your_sentry_dsn  # Optional

# ===== Redis (Optional) =====
REDIS_URL=redis://localhost:6379
USE_REDIS=false

# ===== Rate Limiting =====
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600
```

### AI Provider Setup Examples

#### OpenAI
```bash
OPENAI_API_KEY=sk-your-key-here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

#### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
DEFAULT_LLM_PROVIDER=azure_openai
```

#### Local Ollama
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
DEFAULT_LLM_PROVIDER=ollama
```

#### Anthropic Claude
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-sonnet-20240229
```

## 📖 API Usage

### Create and Run Task (Basic)
```bash
curl -X POST "http://localhost:8000/api/v1/run-task" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your-user-id" \
  -d '{
    "task": "Navigate to google.com and search for browser automation",
    "browser_config": {
      "headless": true,
      "enable_screenshots": true
    },
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o"
    }
  }'
```

### Advanced Task with Custom Functions
```bash
curl -X POST "http://localhost:8000/api/v1/run-task" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your-user-id" \
  -d '{
    "task": "Extract product information from e-commerce site",
    "browser_profile": {
      "headless": true,
      "stealth": true,
      "viewport": {"width": 1920, "height": 1080},
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.1
    },
    "agent_config": {
      "use_vision": true,
      "max_actions_per_step": 15,
      "controller_config": {
        "output_model_schema": {
          "type": "object",
          "properties": {
            "products": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": {"type": "string"},
                  "price": {"type": "string"},
                  "rating": {"type": "number"}
                }
              }
            }
          }
        },
        "custom_functions": [
          {
            "name": "extract_price",
            "description": "Extract price from product element",
            "implementation_type": "code",
            "python_code": "return element.text.strip()"
          }
        ]
      }
    }
  }'
```

### Monitor Task Progress
```bash
# Get task status
curl "http://localhost:8000/api/v1/task/{task_id}/status" \
  -H "X-User-ID: your-user-id"

# WebSocket monitoring
ws://localhost:8000/api/v1/live/{task_id}

# Server-Sent Events
curl "http://localhost:8000/api/v1/live/{task_id}/sse" \
  -H "X-User-ID: your-user-id"
```

### Task Control Operations
```bash
# Pause task
curl -X PUT "http://localhost:8000/api/v1/pause-task/{task_id}" \
  -H "X-User-ID: your-user-id"

# Resume task
curl -X PUT "http://localhost:8000/api/v1/resume-task/{task_id}" \
  -H "X-User-ID: your-user-id"

# Stop task
curl -X PUT "http://localhost:8000/api/v1/stop-task/{task_id}" \
  -H "X-User-ID: your-user-id"

# Delete task
curl -X DELETE "http://localhost:8000/api/v1/task/{task_id}" \
  -H "X-User-ID: your-user-id"
```

### Get Task Media and Data
```bash
# List media files
curl "http://localhost:8000/api/v1/task/{task_id}/media" \
  -H "X-User-ID: your-user-id"

# Download screenshot
curl "http://localhost:8000/api/v1/media/{task_id}/screenshot_001.png" \
  -H "X-User-ID: your-user-id" \
  -o screenshot.png

# Get task cookies
curl "http://localhost:8000/api/v1/task/{task_id}/cookies" \
  -H "X-User-ID: your-user-id"

# Export task data
curl "http://localhost:8000/api/v1/task/{task_id}/export?format=json" \
  -H "X-User-ID: your-user-id" \
  -o task_export.json
```

## 🔌 n8n Integration

### Setup in n8n

1. **HTTP Request Node Configuration**
   - Method: POST
   - URL: `http://your-server:8000/api/v1/run-task`
   - Headers: `X-User-ID: your-user-id`

2. **Task Creation with Advanced Configuration**
```json
{
  "task": "Your automation task description",
  "browser_profile": {
    "headless": true,
    "stealth": true,
    "enable_screenshots": true
  },
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  "agent_config": {
    "controller_config": {
      "output_model_schema": {
        "type": "object",
        "properties": {
          "result": {"type": "string"},
          "data": {"type": "object"}
        }
      }
    }
  }
}
```

3. **Monitor Progress with WebSocket**
   - Use n8n WebSocket nodes for real-time updates
   - URL: `ws://your-server:8000/api/v1/live/{task_id}`

### Example n8n Workflow

```json
{
  "nodes": [
    {
      "name": "Create Browser Task",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/v1/run-task",
        "method": "POST",
        "headers": {
          "X-User-ID": "n8n-user"
        },
        "body": {
          "task": "Navigate to example.com and extract data",
          "browser_profile": {
            "headless": true,
            "enable_screenshots": true
          },
          "agent_config": {
            "controller_config": {
              "output_model_schema": {
                "type": "object",
                "properties": {
                  "title": {"type": "string"},
                  "content": {"type": "string"}
                }
              }
            }
          }
        }
      }
    },
    {
      "name": "Monitor Task",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/v1/task/{{$json.id}}/status",
        "headers": {
          "X-User-ID": "n8n-user"
        }
      }
    }
  ]
}
```

## 📊 Monitoring & Observability

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Comprehensive health check
curl http://localhost:8000/api/v1/health

# System statistics
curl http://localhost:8000/api/v1/system-stats

# Available AI providers
curl http://localhost:8000/api/v1/llm-providers
```

### Metrics and Monitoring
```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Live system stats
curl http://localhost:8000/api/v1/live/stats

# Task list with filtering
curl "http://localhost:8000/api/v1/list-tasks?status=RUNNING&page=1&page_size=10" \
  -H "X-User-ID: your-user-id"
```

### Logging

The application uses structured logging with request tracking:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "message": "Request completed",
  "request_id": "abc12345",
  "method": "POST",
  "status_code": 200,
  "duration_seconds": 1.23,
  "user_id": "user123"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      n8n        │────│  Local Bridge   │────│   Browser-Use   │
│   Workflows     │    │      API        │    │     Library     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Providers  │
                       │ OpenAI/Claude/  │
                       │ Ollama/Gemini/  │
                       │ Mistral/Bedrock │
                       └─────────────────┘
```

### Components

- **FastAPI Application**: Main API server with comprehensive endpoints
- **Task Manager**: Handles task lifecycle and browser automation
- **LLM Factory**: Dynamic AI provider instantiation and management
- **Media Manager**: Screenshot, recording, and file management
- **Live Monitoring**: WebSocket and SSE for real-time updates
- **Agent System**: Advanced browser automation with custom functions
- **Controller System**: Structured output and validation

## 📚 Examples and Tutorials

### Comprehensive Example Suite

The project includes 5 production-ready examples demonstrating different use cases:

1. **`01_basic_web_search.py`** - Basic web search and data extraction
2. **`02_ecommerce_automation.py`** - E-commerce automation and price monitoring
3. **`03_form_automation.py`** - Advanced form handling and job applications
4. **`04_n8n_integration.py`** - n8n workflow integration patterns
5. **`05_advanced_monitoring.py`** - Real-time monitoring and system management

### Running Examples

```bash
# Run individual example
python examples/01_basic_web_search.py

# Run all examples with comprehensive reporting
python examples/run_all_examples.py

# Quick mode with shorter timeouts
python examples/run_all_examples.py --quick
```

### Example Features Demonstrated

- ✅ **Basic Operations**: Task creation, monitoring, result retrieval
- ✅ **Advanced Configuration**: Custom functions, structured output, lifecycle hooks
- ✅ **Real-time Monitoring**: WebSocket live updates and system statistics
- ✅ **Error Handling**: Comprehensive error management and recovery
- ✅ **Production Patterns**: Best practices for production deployment

## 🛠️ Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt

# Run in development mode
DEBUG=true python main.py
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.

# Test specific functionality
python -m pytest tests/test_tasks.py

# Run example suite
python examples/run_all_examples.py
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Linting
flake8 .
```

## 🔧 Troubleshooting

### Common Issues

1. **Chrome not found**
   ```bash
   # Set Chrome path explicitly
   export CHROME_EXECUTABLE_PATH=/path/to/chrome
   ```

2. **Permission denied errors**
   ```bash
   # Fix permissions for media directory
   chmod 755 ./media
   chmod 755 ./browser_data
   ```

3. **AI Provider errors**
   ```bash
   # Check provider configuration
   curl http://localhost:8000/api/v1/llm-providers
   ```

4. **Task timeout**
   ```bash
   # Increase timeout
   export TASK_TIMEOUT_MINUTES=60
   ```

5. **Windows compatibility issues**
   ```bash
   # Use Docker or WSL for better compatibility
   docker-compose up -d
   ```

### Debug Mode

Enable debug mode for detailed logging:
```bash
DEBUG=true LOG_LEVEL=debug python main.py
```

### Performance Issues

1. **High memory usage**
   ```bash
   # Reduce concurrent tasks
   export MAX_CONCURRENT_TASKS=3
   
   # Enable automatic cleanup
   export ENABLE_AUTO_CLEANUP=true
   ```

2. **Slow task execution**
   ```bash
   # Use headless mode
   export BROWSER_HEADLESS=true
   
   # Optimize browser settings
   export BROWSER_TIMEOUT=15000
   ```

## 📈 Performance Tuning

### Production Settings
```bash
# Optimize for production
ENVIRONMENT=production
MAX_CONCURRENT_TASKS=10
BROWSER_HEADLESS=true
ENABLE_SCREENSHOTS=true
SCREENSHOT_QUALITY=80
ENABLE_METRICS=true
TELEMETRY_ENABLED=false
```

### Resource Limits
```bash
# Container resource limits
docker run --memory=2g --cpus=2 browser-use-bridge

# System resource monitoring
curl http://localhost:8000/api/v1/system-stats
```

### Scaling Considerations

- **Horizontal Scaling**: Run multiple instances behind a load balancer
- **Redis Integration**: Enable Redis for task queuing and session management
- **Database Persistence**: Configure database for task history and analytics
- **Monitoring**: Set up comprehensive monitoring with Prometheus/Grafana

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for API changes
- Include example usage in the examples folder
- Ensure backward compatibility when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Browser-Use](https://github.com/browser-use/browser-use) - The underlying browser automation library
- [FastAPI](https://fastapi.tiangolo.com/) - The web framework
- [n8n](https://n8n.io/) - The workflow automation platform this integrates with
- [Playwright](https://playwright.dev/) - Browser automation engine
- [Pydantic](https://pydantic.dev/) - Data validation and settings management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/deepchokshi/browser-use-local-bridge/issues)
- **Documentation**: [Wiki](https://github.com/deepchokshi/browser-use-local-bridge/wiki)
- **Examples**: Check the `/examples` folder for comprehensive usage examples
- **API Docs**: Interactive documentation at `http://localhost:8000/docs`

## 🚀 What's New

### Latest Features (v1.0.0)

- ✅ **Complete BrowserProfile Support**: Full parity with browser-use library
- ✅ **Advanced Agent Configuration**: Custom functions, structured output, lifecycle hooks
- ✅ **Comprehensive Examples**: 5 production-ready examples with different use cases
- ✅ **Real-time Monitoring**: WebSocket and SSE support for live updates
- ✅ **Multi-AI Provider Support**: 8+ AI providers with custom endpoints
- ✅ **Production Features**: Comprehensive logging, monitoring, and error handling
- ✅ **n8n Integration**: Seamless workflow automation integration
- ✅ **Security Features**: Multi-user support, rate limiting, and data protection

---

**Made with ❤️ for the automation community** 