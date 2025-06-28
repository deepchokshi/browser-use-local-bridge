# Browser-Use Local Bridge API Examples

This folder contains practical examples demonstrating how to use the Browser-Use Local Bridge API for various automation tasks. Each example is self-contained and includes detailed comments explaining the concepts.

## 🚀 Quick Start

1. **Start the API server:**
   ```bash
   python main.py
   ```

2. **Configure your environment:**
   - Set your OpenAI API key in `.env` file
   - Ensure the API is running on `http://localhost:8000`

3. **Run any example:**
   ```bash
   python examples/01_basic_task_creation.py
   ```

## 📁 Examples Overview

### 1. Basic Task Creation (`01_basic_task_creation.py`)
**What it demonstrates:**
- Creating a simple browser automation task
- Monitoring task progress
- Retrieving task results
- Basic error handling

**Use case:** Perfect for beginners to understand the basic API workflow.

**Key concepts:**
- Task creation with `/api/v1/run-task`
- Status monitoring with `/api/v1/task/{id}/status`
- Result retrieval with `/api/v1/task/{id}`

### 2. Web Scraping (`02_web_scraping.py`)
**What it demonstrates:**
- Scraping structured data from websites
- Taking screenshots during automation
- Downloading media files
- Parsing JSON results

**Use case:** Data extraction from websites with visual verification.

**Key concepts:**
- Screenshot capture configuration
- Media file handling
- JSON data extraction
- File download from `/api/v1/media/{task_id}/{filename}`

### 3. Form Automation (`03_form_automation.py`)
**What it demonstrates:**
- Filling out web forms automatically
- Form submission and response handling
- Step-by-step progress tracking
- Screenshot capture for verification

**Use case:** Automating form submissions, data entry, and form testing.

**Key concepts:**
- Complex task instructions
- Form field interaction
- Submission verification
- Detailed step monitoring

### 4. WebSocket Monitoring (`04_websocket_monitoring.py`)
**What it demonstrates:**
- Real-time task monitoring via WebSocket
- Concurrent monitoring (WebSocket + HTTP polling)
- Live progress updates
- Connection management

**Use case:** Applications requiring real-time updates and monitoring.

**Key concepts:**
- WebSocket connection to `/api/v1/live/{task_id}`
- Real-time message handling
- Concurrent monitoring strategies
- System statistics via `/api/v1/live/stats`

**Requirements:**
```bash
pip install websockets
```

### 5. Task Management (`05_task_management.py`)
**What it demonstrates:**
- Creating and managing multiple tasks
- Task listing and filtering
- Task control operations (pause, resume, stop)
- Comprehensive reporting

**Use case:** Managing multiple automation tasks in production environments.

**Key concepts:**
- Bulk task creation
- Task lifecycle management
- Status filtering and pagination
- Performance reporting

### 6. n8n Integration (`06_n8n_integration.py`)
**What it demonstrates:**
- n8n workflow integration patterns
- HTTP Request node configurations
- Webhook processing
- Workflow JSON generation

**Use case:** Integrating browser automation into n8n workflows.

**Key concepts:**
- n8n-compatible API calls
- Workflow structure design
- Error handling in workflows
- Generated workflow import

## 🛠️ Configuration

All examples use these default configurations that you can modify:

```python
# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "example_user"  # Change for different examples

# Browser Configuration
browser_config = {
    "headless": True,  # Set to False to see browser
    "enable_screenshots": True,
    "viewport_width": 1280,
    "viewport_height": 720,
    "timeout": 30000  # 30 seconds
}

# LLM Configuration
llm_config = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.1
}
```

## 📊 Example Output

When you run an example, you'll see output like this:

```
============================================================
Browser-Use Local Bridge API - Basic Task Example
============================================================
🚀 Creating a basic browser automation task...
✅ Task created successfully!
   Task ID: abc123de-f456-7890-ghij-klmnopqrstuv
   Status: CREATED
   Provider: openai

📊 Monitoring task progress...
   Status: RUNNING (10.0%)
   Status: RUNNING (50.0%)
   Status: FINISHED (100.0%)

📋 Getting task results...
✅ Task completed with status: FINISHED
   Execution time: 15.3 seconds
   Result: The origin IP address is 203.0.113.42

📝 Execution Steps:
   1. created: Task created and initialized
   2. started: Task execution started
   3. llm_init: Initializing openai LLM
   4. browser_init: Initializing browser session
   5. execution_start: Starting task execution
   6. completed: Task completed successfully

============================================================
Example completed! 🎉
============================================================
```

## 🔧 Customization

### Modifying Task Instructions

Each example includes detailed task instructions. You can modify these to suit your needs:

```python
task_data = {
    "task": """
    Your custom task description here.
    Be specific about what you want the browser to do:
    1. Navigate to a specific URL
    2. Interact with elements
    3. Extract specific data
    4. Take screenshots at key points
    """,
    "browser_config": {
        # Your browser settings
    },
    "llm_config": {
        # Your LLM settings
    }
}
```

### Different AI Providers

You can use different AI providers by changing the LLM configuration:

```python
# OpenAI
llm_config = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.1
}

# Anthropic Claude
llm_config = {
    "provider": "anthropic",
    "model": "claude-3-opus-20240229",
    "temperature": 0.1
}

# Local Ollama
llm_config = {
    "provider": "ollama",
    "model": "llama2",
    "temperature": 0.1
}
```

### Browser Settings

Customize browser behavior:

```python
browser_config = {
    "headless": False,  # Show browser window
    "enable_screenshots": True,
    "enable_recordings": True,  # Enable video recording
    "viewport_width": 1920,
    "viewport_height": 1080,
    "timeout": 60000,  # 60 seconds
    "custom_flags": ["--disable-web-security"]  # Custom Chrome flags
}
```

## 🚨 Error Handling

All examples include comprehensive error handling. Common issues and solutions:

### API Connection Issues
```python
try:
    response = requests.post(f"{API_BASE_URL}/api/v1/run-task", ...)
    response.raise_for_status()
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to API. Is the server running?")
except requests.exceptions.HTTPError as e:
    print(f"❌ API error: {e}")
```

### Task Execution Failures
- **Invalid API Key**: Ensure your OpenAI API key is set correctly
- **Timeout Issues**: Increase timeout values for complex tasks
- **Browser Issues**: Check if Chrome/Chromium is installed properly

### WebSocket Connection Issues
- **Connection Refused**: Verify the API server is running
- **Authentication**: Ensure user_id parameter is included in WebSocket URL

## 📈 Performance Tips

1. **Use Headless Mode**: Set `headless: true` for better performance
2. **Optimize Screenshots**: Only enable when needed
3. **Reasonable Timeouts**: Set appropriate timeout values
4. **Concurrent Tasks**: Limit concurrent tasks based on system resources
5. **Monitor Memory**: Use system stats endpoint to monitor resource usage

## 🔗 Integration Patterns

### Python Applications
```python
from examples.task_manager import TaskManager

manager = TaskManager("http://localhost:8000", "my_app")
task_id = manager.create_task("Navigate to example.com")
result = manager.wait_for_completion(task_id)
```

### n8n Workflows
Import the generated `n8n_browser_automation_workflow.json` into n8n for ready-to-use workflows.

### REST API Integration
Use the examples as templates for integrating with other REST API clients.

## 📚 Additional Resources

- **API Documentation**: See `README.md` in the root directory
- **OpenAPI Spec**: Available at `http://localhost:8000/docs`
- **Test Suite**: Run `python test_api.py` for comprehensive testing
- **Docker Deployment**: Use `docker-compose up` for containerized deployment

## 🤝 Contributing

Feel free to contribute additional examples! Follow the existing pattern:

1. Create a new file: `XX_example_name.py`
2. Include comprehensive comments and error handling
3. Add a section to this README
4. Test thoroughly before submitting

## 📄 License

These examples are part of the Browser-Use Local Bridge project and follow the same license terms. 