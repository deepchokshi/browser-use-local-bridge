# Windows Troubleshooting Guide

This guide helps resolve common Windows-specific issues with the Browser-Use Local Bridge API.

## 🔧 Common Issues and Solutions

### 1. Playwright Browser Connection Errors

**Error**: `NotImplementedError` in subprocess creation
```
Task exception was never retrieved
NotImplementedError
```

**Solution**:
```bash
# Install Playwright browsers
playwright install chromium

# If that fails, try with system flag
playwright install --with-deps chromium

# Verify installation
playwright --version
```

### 2. Memory Overload Warnings

**Warning**: `System overload detected: Memory: 86.9%`

**Solutions**:
- Reduce `MAX_CONCURRENT_TASKS` in your environment:
  ```bash
  set MAX_CONCURRENT_TASKS=1
  ```
- Close unnecessary applications
- Restart the API service
- Use headless mode for tasks:
  ```json
  {
    "instruction": "Your task",
    "headless": true
  }
  ```

### 3. AsyncIO Event Loop Issues

**Error**: Event loop policy conflicts

**Solution**: The API now automatically sets the Windows event loop policy. If issues persist:

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

### 4. Browser Process Creation Failed

**Error**: Subprocess creation fails

**Solutions**:

1. **Run as Administrator**: Right-click PowerShell and "Run as Administrator"

2. **Check Windows Defender**: Add exclusions for:
   - Project directory
   - Python installation
   - Playwright cache directory

3. **Set Environment Variables**:
   ```bash
   set PYTHONIOENCODING=utf-8
   set PYTHONUTF8=1
   ```

4. **Install Visual C++ Redistributables**:
   Download and install Microsoft Visual C++ Redistributable

### 5. Port Binding Issues

**Error**: `[Errno 10048] Only one usage of each socket address`

**Solution**:
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
set PORT=8001
```

## 🚀 Performance Optimization for Windows

### 1. Browser Arguments Optimization

The API now includes Windows-specific browser arguments:
- `--no-sandbox`: Disables sandboxing for compatibility
- `--disable-dev-shm-usage`: Prevents shared memory issues
- `--disable-gpu`: Avoids GPU-related crashes
- `--force-device-scale-factor=1`: Consistent scaling

### 2. System Configuration

**PowerShell Execution Policy**:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows Features** (if needed):
- Enable "Windows Subsystem for Linux" (optional)
- Install "Windows Terminal" for better command line experience

### 3. Environment Variables

Create a `.env` file in your project root:
```bash
# AI Provider
OPENAI_API_KEY=your_key_here
DEFAULT_LLM_PROVIDER=openai

# Performance
MAX_CONCURRENT_TASKS=2
TASK_TIMEOUT=300

# Windows-specific
BROWSER_HEADLESS=true
TELEMETRY_ENABLED=false

# Paths (use forward slashes)
MEDIA_STORAGE_PATH=./media
BROWSER_USER_DATA_DIR=./browser_data
```

## 🔍 Debugging Steps

### 1. Check System Requirements

```bash
# Python version (3.8+)
python --version

# Available memory
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory

# Disk space
dir C:\ /-c
```

### 2. Test Playwright Installation

```bash
# Test Playwright
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Test browser launch
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    browser.close()
    print('Browser launch OK')
"
```

### 3. Verify API Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Test imports
python -c "
import fastapi
import browser_use
import structlog
print('All imports OK')
"
```

### 4. Test API Endpoints

```bash
# Start the API
python main.py

# Test health endpoint (in another terminal)
curl http://localhost:8000/health

# Test task creation
curl -X POST http://localhost:8000/api/v1/run-task \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Go to google.com", "headless": true}'
```

## 🛠️ Advanced Solutions

### 1. Custom Browser Configuration

If default settings don't work, try custom browser args:

```python
import requests

response = requests.post("http://localhost:8000/api/v1/run-task", json={
    "instruction": "Navigate to example.com",
    "headless": True,
    "browser_config": {
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",  # Use single process mode
            "--no-zygote"        # Disable zygote process
        ]
    }
})
```

### 2. Windows Firewall Configuration

If you encounter network issues:

1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Add Python and your application
4. Allow both Private and Public networks

### 3. Registry Fixes (Advanced)

For persistent subprocess issues, you may need to check Windows registry:

```bash
# Run in Administrator Command Prompt
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\SubSystems"
```

## 📞 Getting Help

If issues persist:

1. **Check Logs**: Look for detailed error messages in the API logs
2. **GitHub Issues**: Report issues at [browser-use-local-bridge](https://github.com/deepchokshi/browser-use-local-bridge)
3. **System Info**: Include your Windows version, Python version, and error logs

### Log Collection

Enable debug logging:
```bash
set LOG_LEVEL=DEBUG
python main.py
```

The logs will show detailed information about what's failing.

## ✅ Success Indicators

You'll know everything is working when:
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Task creation returns a task ID
- ✅ Browser launches without `NotImplementedError`
- ✅ Tasks complete successfully with results
- ✅ No memory overload warnings in logs

---

**Note**: This API has been tested on Windows 10/11 with Python 3.8-3.11. Most issues are related to browser setup or system permissions. 