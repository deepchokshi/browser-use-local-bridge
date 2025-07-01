# Browser-Use Local Bridge - Examples

This folder contains practical examples demonstrating the capabilities of the Browser-Use Local Bridge API. Each example showcases different aspects of browser automation and integration patterns.

## 📁 Example Files

### 1. `01_basic_web_search.py` - Basic Web Search
**Difficulty**: Beginner  
**Runtime**: ~2-3 minutes

Demonstrates fundamental browser automation features:
- Creating and running basic browser tasks
- Monitoring task progress and status
- Retrieving results and screenshots
- Structured output configuration

**Use Cases**:
- Simple web scraping
- Search result extraction
- Basic data collection

**Key Features Shown**:
- Task creation with `run-task` endpoint
- Progress monitoring
- Screenshot generation
- Structured JSON output

### 2. `02_ecommerce_automation.py` - E-Commerce Automation
**Difficulty**: Intermediate  
**Runtime**: ~5-8 minutes

Advanced e-commerce automation scenarios:
- Product search and price comparison
- Shopping cart management
- Session persistence and cookie handling
- Multi-step workflows

**Use Cases**:
- Competitive price monitoring
- Product research automation
- Shopping workflow automation
- Market analysis

**Key Features Shown**:
- Browser session persistence
- Complex form interactions
- Structured data extraction
- Multi-page navigation

### 3. `03_form_automation.py` - Form Automation
**Difficulty**: Intermediate  
**Runtime**: ~4-6 minutes

Sophisticated form handling capabilities:
- Multi-step form workflows
- Custom functions for smart form filling
- Form validation and error handling
- File upload automation

**Use Cases**:
- Job application automation
- Contact form submissions
- Survey completion
- Data entry automation

**Key Features Shown**:
- Custom function integration
- Smart form field detection
- Validation handling
- Safe demo mode (prevents actual submissions)

### 4. `04_n8n_integration.py` - n8n Workflow Integration
**Difficulty**: Advanced  
**Runtime**: ~3-5 minutes

Integration with n8n workflow automation:
- Webhook-triggered browser tasks
- Custom functions for workflow callbacks
- Structured data for workflow continuation
- Automation pipeline patterns

**Use Cases**:
- Workflow automation
- Scheduled data extraction
- Business process automation
- Integration with existing tools

**Key Features Shown**:
- Webhook integration
- Workflow data handling
- Custom callback functions
- Pipeline automation

### 5. `05_advanced_monitoring.py` - Advanced Monitoring
**Difficulty**: Advanced  
**Runtime**: ~6-10 minutes

Real-time monitoring and system management:
- WebSocket live task monitoring
- System performance tracking
- Task lifecycle management (pause/resume/stop)
- Performance metrics collection

**Use Cases**:
- Real-time monitoring dashboards
- System administration
- Performance optimization
- Production monitoring

**Key Features Shown**:
- WebSocket live updates
- System statistics
- Task control operations
- Performance monitoring

## 🚀 Quick Start

### Prerequisites

1. **Browser-Use Local Bridge API running**:
   ```bash
   python main.py
   ```
   API should be available at `http://localhost:8000`

2. **Required Python packages**:
   ```bash
   pip install httpx websockets
   ```

3. **AI Provider configured** (at least one):
   - OpenAI API key in environment
   - Or other supported provider configured

### Running Examples

Each example can be run independently:

```bash
# Basic web search
python examples/01_basic_web_search.py

# E-commerce automation
python examples/02_ecommerce_automation.py

# Form automation
python examples/03_form_automation.py

# n8n integration
python examples/04_n8n_integration.py

# Advanced monitoring
python examples/05_advanced_monitoring.py
```

### Configuration

Examples use these default settings:
- **API URL**: `http://localhost:8000`
- **User ID**: Varies per example
- **AI Provider**: OpenAI (gpt-4o)
- **Browser**: Headless mode (mostly)

Modify the configuration constants at the top of each file to customize:

```python
API_BASE_URL = "http://localhost:8000"
USER_ID = "your_user_id"
```

## 🔧 Configuration Options

### Browser Configuration
```python
"browser_config": {
    "headless": True,          # Run without GUI
    "viewport_width": 1920,    # Browser width
    "viewport_height": 1080,   # Browser height
    "enable_screenshots": True, # Capture screenshots
    "enable_recordings": False, # Record videos
    "timeout": 30000           # Page timeout (ms)
}
```

### AI/LLM Configuration
```python
"llm_config": {
    "provider": "openai",      # AI provider
    "model": "gpt-4o",         # Model name
    "temperature": 0.1         # Response creativity
}
```

### Agent Configuration
```python
"agent_config": {
    "max_actions_per_step": 10,    # Actions per step
    "max_failures": 3,             # Retry limit
    "retry_delay": 2.0,            # Delay between retries
    "use_vision": True             # Enable vision capabilities
}
```

## 📊 Understanding Output

### Task Status Values
- `CREATED`: Task created but not started
- `RUNNING`: Task is currently executing
- `FINISHED`: Task completed successfully
- `FAILED`: Task failed with error
- `STOPPED`: Task was manually stopped
- `PAUSED`: Task is temporarily paused

### Response Structure
```json
{
  "id": "task-uuid",
  "status": "FINISHED",
  "result": { /* Task results */ },
  "execution_time_seconds": 45.2,
  "progress_percentage": 100.0,
  "media": [
    {
      "filename": "screenshot_001.png",
      "media_type": "screenshot",
      "size_bytes": 125432
    }
  ],
  "steps": [ /* Execution steps */ ]
}
```

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```
   ❌ Cannot connect to API
   ```
   - Ensure the main API server is running: `python main.py`
   - Check the API URL in the example file

2. **AI Provider Not Configured**
   ```
   ❌ Task failed: LLM provider not configured
   ```
   - Set your AI provider API key in environment variables
   - Check `.env` file configuration

3. **Browser Issues on Windows**
   ```
   ❌ Browser automation failed due to Windows compatibility issues
   ```
   - Try running in Docker or WSL
   - Ensure Playwright browsers are installed
   - See `WINDOWS_TROUBLESHOOTING.md`

4. **Task Timeout**
   ```
   ❌ Task timed out after X seconds
   ```
   - Increase timeout in example configuration
   - Check if target websites are accessible
   - Verify task complexity is reasonable

### Debug Mode

Enable debug output by modifying examples:
```python
# Add at top of file
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Documentation

For complete API reference:
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI spec: `http://localhost:8000/api/v1/openapi.json`

## 🛡️ Safety and Ethics

### Demo Safety Features
- Examples include safety measures to prevent accidental actions
- Form automation stops before actual submissions
- E-commerce examples avoid real purchases
- Rate limiting and timeouts prevent abuse

### Best Practices
1. **Respect robots.txt** and website terms of service
2. **Add delays** between requests to avoid overloading servers
3. **Use headless mode** in production for better performance
4. **Monitor resource usage** with system stats
5. **Implement proper error handling** for production use

### Legal Considerations
- Always comply with website terms of service
- Respect rate limits and access restrictions
- Consider data privacy regulations (GDPR, CCPA, etc.)
- Obtain permission for commercial data extraction

## 📈 Performance Tips

### Optimization Strategies
1. **Use headless mode** for better performance
2. **Enable screenshots only when needed**
3. **Set appropriate timeouts** for different tasks
4. **Monitor system resources** with advanced monitoring
5. **Use structured output** for better data processing

### Scaling Considerations
- Monitor concurrent task limits
- Use Redis for task queuing in production
- Implement proper logging and monitoring
- Consider horizontal scaling with multiple instances

## 🤝 Contributing

To add new examples:

1. Follow the existing naming pattern: `XX_example_name.py`
2. Include comprehensive docstrings and comments
3. Add error handling and safety measures
4. Update this README with example description
5. Test with different AI providers
6. Include example output in comments

### Example Template
```python
#!/usr/bin/env python3
"""
Example X: Your Example Name
============================

Description of what this example demonstrates.

Use case: Specific scenario this example addresses
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"
USER_ID = "your_example_user"

async def your_example_function():
    """Example function with descriptive docstring"""
    # Implementation here
    pass

if __name__ == "__main__":
    asyncio.run(your_example_function())
```

## 📞 Support

For help with examples:
- Check the main project README
- Review API documentation at `/docs`
- Open an issue on GitHub
- Check existing issues for common problems

---

**Happy Automating! 🤖✨** 