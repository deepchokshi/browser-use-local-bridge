# Browser-Use Local Bridge

A production-ready local bridge for browser automation with comprehensive n8n integration. This project provides a drop-in replacement for Browser Use Cloud API, running entirely on your local infrastructure with support for multiple AI providers.

## 🎯 Core Purpose

- **Local Browser Automation Bridge**: Mimics Browser Use Cloud API endpoints but runs locally
- **n8n Integration**: Specifically designed to work with n8n workflow automation platform  
- **Cloud Alternative**: Eliminates dependency on Browser Use cloud service
- **Production Ready**: Comprehensive logging, error handling, and monitoring

## ✨ Features

### 🤖 AI/LLM Provider Support
- **OpenAI**: GPT models (gpt-4o, gpt-4o-mini, etc.)
- **Azure OpenAI**: Enterprise Azure-hosted OpenAI models
- **Anthropic**: Claude models (claude-3-opus, etc.)
- **MistralAI**: Mistral models
- **Google AI**: Gemini models
- **Ollama**: Local LLM hosting
- **Amazon Bedrock**: AWS-hosted models
- **Custom OpenAI-compatible APIs**: Via OPENAI_BASE_URL

### 📋 Task Management
- **Complete Lifecycle**: Create, start, pause, resume, stop tasks
- **Real-time Monitoring**: WebSocket and Server-Sent Events support
- **Progress Tracking**: Step-by-step execution monitoring
- **Status Management**: CREATED, RUNNING, FINISHED, STOPPED, PAUSED, FAILED states
- **Task History**: Comprehensive task execution logs
- **Multi-user Support**: User-segregated task management

### 🌐 Browser Configuration
- **Flexible Modes**: Headless and headful browser execution
- **User Data Persistence**: Maintain browser sessions/cookies
- **Custom Chrome**: Use specific Chrome executable path
- **Viewport Control**: Configurable browser dimensions
- **Cookie Extraction**: Save browser cookies after task completion

### 📡 Comprehensive API
- **Task Operations**: Full CRUD operations for tasks
- **Media Management**: Screenshots, recordings, file serving
- **Live Monitoring**: Real-time task updates
- **System Management**: Health checks, configuration, metrics
- **n8n Compatible**: Drop-in replacement for Browser Use Cloud API

### 🛡️ Security & Production Features
- **Multi-user Support**: Header-based user identification
- **Comprehensive Logging**: Structured logging with request tracking
- **Error Handling**: Graceful error management and recovery
- **Health Monitoring**: Built-in health checks and metrics
- **Resource Management**: Automatic cleanup and resource limits
- **CORS Support**: Configurable cross-origin requests

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser
- At least one AI provider API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/browser-use-local-bridge.git
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
# AI Provider (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# Server Configuration
PORT=8000
LOG_LEVEL=info
ENVIRONMENT=production

# Browser Settings
BROWSER_HEADLESS=true
ENABLE_SCREENSHOTS=true

# Task Management
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT_MINUTES=30
```

### AI Provider Setup

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

## 📖 API Usage

### Create and Run Task
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

### Get Task Media
```bash
# List media files
curl "http://localhost:8000/api/v1/task/{task_id}/media" \
  -H "X-User-ID: your-user-id"

# Download screenshot
curl "http://localhost:8000/api/v1/media/{task_id}/screenshot_001.png" \
  -H "X-User-ID: your-user-id" \
  -o screenshot.png
```

## 🔌 n8n Integration

### Setup in n8n

1. **HTTP Request Node Configuration**
   - Method: POST
   - URL: `http://your-server:8000/api/v1/run-task`
   - Headers: `X-User-ID: your-user-id`

2. **Task Creation**
```json
{
  "task": "Your automation task description",
  "browser_config": {
    "headless": true,
    "enable_screenshots": true
  }
}
```

3. **Monitor Progress**
   - Use HTTP Request nodes to poll task status
   - Implement WebSocket nodes for real-time updates

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
          "task": "Navigate to example.com and take a screenshot"
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
```

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Live system stats
curl http://localhost:8000/api/v1/live/stats
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
  "duration_seconds": 1.23
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
                       │ Ollama/Gemini   │
                       └─────────────────┘
```

### Components

- **FastAPI Application**: Main API server with comprehensive endpoints
- **Task Manager**: Handles task lifecycle and browser automation
- **LLM Factory**: Dynamic AI provider instantiation
- **Media Manager**: Screenshot and file management
- **Live Monitoring**: WebSocket and SSE for real-time updates

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

### Debug Mode

Enable debug mode for detailed logging:
```bash
DEBUG=true LOG_LEVEL=debug python main.py
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
```

### Resource Limits
```bash
# Container resource limits
docker run --memory=2g --cpus=2 browser-use-bridge
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Browser-Use](https://github.com/browser-use/browser-use) - The underlying browser automation library
- [FastAPI](https://fastapi.tiangolo.com/) - The web framework
- [n8n](https://n8n.io/) - The workflow automation platform this integrates with

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/deepchokshi/browser-use-local-bridge/issues)
- **Documentation**: [Wiki](https://github.com/deepchokshi/browser-use-local-bridge/wiki)

---

**Made with ❤️ for the automation community** 