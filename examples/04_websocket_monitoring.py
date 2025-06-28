#!/usr/bin/env python3
"""
Example 4: Real-time WebSocket Monitoring
========================================

This example demonstrates how to:
- Create a task and monitor it in real-time via WebSocket
- Handle WebSocket connections and messages
- Display live progress updates
- Manage multiple concurrent tasks

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured
- websockets library: pip install websockets
"""

import asyncio
import websockets
import requests
import json
import threading
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "websocket_user"

def create_long_running_task():
    """Create a task that takes some time to complete"""
    
    print("🚀 Creating a long-running task for WebSocket monitoring...")
    
    task_data = {
        "task": """
        Perform a comprehensive web research task:
        
        1. Navigate to https://news.ycombinator.com/
        2. Take a screenshot of the homepage
        3. Find and click on the first story link
        4. Take a screenshot of the story page
        5. Go back to the homepage
        6. Find the "new" link and click it
        7. Take a screenshot of the new stories page
        8. Extract the titles of the first 5 stories and return them as a JSON array
        
        Take your time with each step and ensure screenshots are captured properly.
        """,
        "browser_config": {
            "headless": False,
            "enable_screenshots": True,
            "viewport_width": 1440,
            "viewport_height": 900,
            "timeout": 60000
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "metadata": {
            "example": "websocket_monitoring",
            "expected_duration": "60-120 seconds",
            "steps": 8
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/run-task",
        headers={
            "X-User-ID": USER_ID,
            "Content-Type": "application/json"
        },
        json=task_data
    )
    
    if response.status_code == 201:
        task = response.json()
        task_id = task["id"]
        print(f"✅ Long-running task created!")
        print(f"   Task ID: {task_id}")
        print(f"   Expected duration: 60-120 seconds")
        return task_id
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

async def websocket_monitor(task_id):
    """Monitor task progress via WebSocket"""
    
    print(f"\n🔌 Connecting to WebSocket for real-time monitoring...")
    
    ws_url = f"ws://localhost:8000/api/v1/live/{task_id}?user_id={USER_ID}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ WebSocket connected!")
            print(f"   Monitoring task: {task_id}")
            print(f"   Waiting for updates...\n")
            
            message_count = 0
            start_time = datetime.now()
            
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    message_count += 1
                    
                    # Parse the message
                    try:
                        data = json.loads(message)
                        
                        if 'error' in data:
                            print(f"❌ WebSocket Error: {data['error']}")
                            break
                        
                        # Display update
                        status = data.get('status', 'UNKNOWN')
                        progress = data.get('progress_percentage', 0)
                        current_step = data.get('current_step', 'N/A')
                        timestamp = data.get('timestamp', 'N/A')
                        
                        elapsed = datetime.now() - start_time
                        elapsed_str = f"{elapsed.total_seconds():.1f}s"
                        
                        print(f"📊 Update #{message_count} ({elapsed_str}):")
                        print(f"   Status: {status}")
                        print(f"   Progress: {progress}%")
                        print(f"   Current Step: {current_step}")
                        print(f"   Timestamp: {timestamp}")
                        print()
                        
                        # Check if task is completed
                        if status in ['FINISHED', 'FAILED', 'STOPPED']:
                            print(f"🏁 Task completed with status: {status}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse WebSocket message: {e}")
                        print(f"   Raw message: {message}")
                
                except asyncio.TimeoutError:
                    # Check if task is still running via HTTP
                    response = requests.get(
                        f"{API_BASE_URL}/api/v1/task/{task_id}/status",
                        headers={"X-User-ID": USER_ID}
                    )
                    
                    if response.status_code == 200:
                        status = response.json()
                        if status['status'] in ['FINISHED', 'FAILED', 'STOPPED']:
                            print(f"🏁 Task completed (detected via HTTP): {status['status']}")
                            break
                        else:
                            print(f"⏳ No WebSocket updates (task still {status['status']})")
                    else:
                        print(f"❌ Lost connection to task")
                        break
                
                except websockets.exceptions.ConnectionClosed:
                    print(f"🔌 WebSocket connection closed")
                    break
    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

def poll_monitor(task_id):
    """Alternative monitoring via HTTP polling (runs in parallel)"""
    
    print(f"📡 Starting HTTP polling monitor (backup)...")
    
    last_status = None
    poll_count = 0
    
    while True:
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/task/{task_id}/status",
                headers={"X-User-ID": USER_ID}
            )
            
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data['status']
                
                # Only print if status changed
                if current_status != last_status:
                    poll_count += 1
                    print(f"🔄 HTTP Poll #{poll_count}: Status changed to {current_status}")
                    last_status = current_status
                
                if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                    break
            
            time.sleep(5)  # Poll every 5 seconds
            
        except Exception as e:
            print(f"❌ HTTP polling error: {e}")
            break

async def demonstrate_concurrent_monitoring(task_id):
    """Demonstrate monitoring a task with both WebSocket and HTTP polling"""
    
    print(f"\n🔀 Demonstrating concurrent monitoring methods...")
    
    # Start HTTP polling in a separate thread
    poll_thread = threading.Thread(target=poll_monitor, args=(task_id,), daemon=True)
    poll_thread.start()
    
    # Monitor via WebSocket (main async task)
    await websocket_monitor(task_id)
    
    print(f"\n✅ WebSocket monitoring completed!")

def get_final_results(task_id):
    """Get and display final task results"""
    
    print(f"\n📋 Getting final task results...")
    
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        task = response.json()
        
        print(f"✅ Final Results:")
        print(f"   Status: {task['status']}")
        print(f"   Duration: {task.get('execution_time_seconds', 'N/A')} seconds")
        print(f"   Steps completed: {len(task.get('steps', []))}")
        print(f"   Screenshots taken: {len(task.get('media', []))}")
        
        if task.get('result'):
            print(f"\n📊 Task Result:")
            try:
                # Try to parse as JSON
                result = json.loads(task['result'])
                print(json.dumps(result, indent=2))
            except:
                print(f"   {task['result']}")
        
        if task.get('error'):
            print(f"\n❌ Error: {task['error']}")
        
        return task
    else:
        print(f"❌ Failed to get results: {response.status_code}")
        return None

def demonstrate_system_stats():
    """Demonstrate real-time system statistics"""
    
    print(f"\n📊 Getting real-time system statistics...")
    
    response = requests.get(f"{API_BASE_URL}/api/v1/live/stats")
    
    if response.status_code == 200:
        stats = response.json()
        
        print(f"✅ System Statistics:")
        print(f"   Active tasks: {stats.get('active_tasks', 0)}")
        print(f"   Browser sessions: {stats.get('total_browser_sessions', 0)}")
        print(f"   Memory usage: {stats.get('memory_usage_mb', 0):.1f} MB")
        print(f"   CPU usage: {stats.get('cpu_percent', 0):.1f}%")
        print(f"   WebSocket connections: {stats.get('websocket_connections', 0)}")
        
        providers = stats.get('available_providers', {})
        available_providers = [name for name, available in providers.items() if available]
        print(f"   Available AI providers: {', '.join(available_providers)}")
    else:
        print(f"❌ Failed to get system stats: {response.status_code}")

async def main():
    """Main WebSocket monitoring example"""
    
    print("=" * 80)
    print("Browser-Use Local Bridge API - Real-time WebSocket Monitoring Example")
    print("=" * 80)
    
    # Step 1: Show system stats
    demonstrate_system_stats()
    
    # Step 2: Create long-running task
    task_id = create_long_running_task()
    if not task_id:
        return
    
    # Step 3: Monitor with WebSocket and HTTP polling
    await demonstrate_concurrent_monitoring(task_id)
    
    # Step 4: Get final results
    final_results = get_final_results(task_id)
    
    # Step 5: Show final system stats
    print(f"\n📊 Final system statistics:")
    demonstrate_system_stats()
    
    print("\n" + "=" * 80)
    print("WebSocket monitoring example completed! 🎉")
    print("This example showed real-time task monitoring capabilities.")
    print("=" * 80)

if __name__ == "__main__":
    # Check if websockets is installed
    try:
        import websockets
    except ImportError:
        print("❌ websockets library not found!")
        print("Please install it with: pip install websockets")
        exit(1)
    
    # Run the async main function
    asyncio.run(main()) 