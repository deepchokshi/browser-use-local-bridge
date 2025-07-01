#!/usr/bin/env python3
"""
Example 5: Advanced Monitoring with Browser-Use Local Bridge
============================================================

This example demonstrates advanced monitoring and real-time features:
- WebSocket live task monitoring
- Server-Sent Events (SSE) for progress updates  
- Task lifecycle management
- Performance metrics and system monitoring

Use case: Real-time monitoring dashboard for browser automation tasks
"""

import asyncio
import httpx
import json
import websockets
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"
USER_ID = "monitoring_user"


class AdvancedMonitoringClient:
    """Client with advanced monitoring capabilities"""
    
    def __init__(self):
        self.base_url = API_BASE_URL.rstrip('/')
        self.ws_base_url = WS_BASE_URL.rstrip('/')
        self.user_id = USER_ID
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    async def create_monitored_task(self, task: str, **config) -> Dict[str, Any]:
        """Create task with monitoring optimizations"""
        config.setdefault('browser_config', {}).update({
            'enable_screenshots': True,
            'headless': True
        })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/run-task",
                json={"task": task, **config},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def monitor_with_websocket(self, task_id: str):
        """Monitor task progress via WebSocket"""
        ws_url = f"{self.ws_base_url}/api/v1/live/{task_id}"
        
        try:
            print(f"🔗 Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket connected - receiving live updates...")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if data.get('type') == 'task_update':
                            task_data = data.get('data', {})
                            status = task_data.get('status', 'UNKNOWN')
                            progress = task_data.get('progress_percentage', 0)
                            step = task_data.get('current_step', 'N/A')
                            
                            print(f"📊 Live Update: {status} ({progress:.1f}%) - {step}")
                            
                            if status in ['FINISHED', 'FAILED', 'STOPPED']:
                                print("🏁 Task completed - closing WebSocket")
                                break
                        
                        elif data.get('type') == 'screenshot':
                            screenshot_path = data.get('path', 'N/A')
                            print(f"📸 New screenshot: {screenshot_path}")
                        
                        elif data.get('type') == 'error':
                            error_msg = data.get('message', 'Unknown error')
                            print(f"❌ Live Error: {error_msg}")
                    
                    except json.JSONDecodeError:
                        print(f"⚠️  Received non-JSON message: {message}")
                
        except Exception as e:
            print(f"💥 WebSocket error: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/system-stats",
                headers=self.headers
            )
            return response.json()


async def websocket_monitoring_example():
    """
    Example: Real-time task monitoring with WebSocket
    """
    client = AdvancedMonitoringClient()
    
    print("📡 Example 5a: WebSocket Live Monitoring")
    print("=" * 50)
    
    # Create a longer-running task for monitoring
    monitoring_task = """
    Perform comprehensive website analysis:
    
    1. Visit 3 different tech news websites (TechCrunch, Ars Technica, The Verge)
    2. For each site:
       - Navigate to the homepage
       - Find the latest 5 article headlines
       - Take a screenshot
       - Extract article publication dates
       - Look for trending topics or categories
    3. Compare and analyze the content focus across sites
    4. Generate a summary report of current tech news trends
    
    Take your time and be thorough - this task is designed for monitoring.
    """
    
    task_config = {
        "browser_config": {
            "headless": True,
            "enable_screenshots": True,
            "viewport_width": 1920,
            "viewport_height": 1080
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.2
        },
        "agent_config": {
            "max_actions_per_step": 8,
            "retry_delay": 2.0,
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "website_analysis": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "website_name": {"type": "string"},
                                    "url": {"type": "string"},
                                    "headlines": {"type": "array"},
                                    "trending_topics": {"type": "array"},
                                    "content_focus": {"type": "string"}
                                }
                            }
                        },
                        "trend_analysis": {
                            "type": "object",
                            "properties": {
                                "common_themes": {"type": "array"},
                                "unique_perspectives": {"type": "array"},
                                "summary": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        print("🚀 Creating monitored task...")
        task = await client.create_monitored_task(monitoring_task, **task_config)
        task_id = task["id"]
        
        print(f"✅ Task created: {task_id}")
        print("🔄 Starting real-time monitoring...\n")
        
        # Start WebSocket monitoring
        await client.monitor_with_websocket(task_id)
        
        # Get final results
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(
                f"{client.base_url}/api/v1/task/{task_id}",
                headers=client.headers
            )
            result = response.json()
        
        if result['status'] == 'FINISHED':
            print("\n✅ Monitoring completed successfully!")
            
            if result.get('result'):
                data = result['result']
                
                # Display website analysis
                websites = data.get('website_analysis', [])
                print(f"\n📊 Analyzed {len(websites)} websites:")
                
                for site in websites:
                    print(f"\n🌐 {site.get('website_name', 'Unknown')}")
                    headlines = site.get('headlines', [])
                    if headlines:
                        print(f"   📰 Headlines ({len(headlines)}):")
                        for headline in headlines[:3]:
                            print(f"      • {headline}")
                    
                    topics = site.get('trending_topics', [])
                    if topics:
                        print(f"   🔥 Trending: {', '.join(topics[:3])}")
                
                # Display trend analysis
                trends = data.get('trend_analysis', {})
                if trends:
                    print(f"\n📈 Trend Analysis:")
                    common = trends.get('common_themes', [])
                    if common:
                        print(f"   🔗 Common Themes: {', '.join(common)}")
                    
                    if trends.get('summary'):
                        print(f"   📝 Summary: {trends['summary']}")
            
            # Show execution metrics
            if result.get('execution_time_seconds'):
                print(f"\n⏱️  Total Execution Time: {result['execution_time_seconds']:.1f}s")
            
            media_count = len(result.get('media', []))
            if media_count > 0:
                print(f"📸 Screenshots Generated: {media_count}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in WebSocket monitoring: {e}")
        return None


async def system_monitoring_dashboard():
    """
    Example: System monitoring and performance tracking
    """
    client = AdvancedMonitoringClient()
    
    print("\n📊 Example 5b: System Monitoring Dashboard")
    print("=" * 50)
    
    try:
        # Get current system stats
        stats = await client.get_system_stats()
        
        print("🖥️  System Status:")
        print(f"   Active Tasks: {stats.get('active_tasks', 0)}")
        print(f"   Max Concurrent: {stats.get('max_concurrent_tasks', 0)}")
        print(f"   Memory Usage: {stats.get('memory_usage_mb', 0):.1f} MB")
        print(f"   CPU Usage: {stats.get('cpu_percent', 0):.1f}%")
        
        # Show available providers
        providers = stats.get('available_providers', {})
        print(f"\n🤖 AI Providers:")
        for provider, available in providers.items():
            status = "✅" if available else "❌"
            print(f"   {status} {provider}")
        
        # Monitor system over time
        print(f"\n📈 Monitoring system performance (30 seconds)...")
        
        for i in range(6):  # Monitor for 30 seconds
            await asyncio.sleep(5)
            
            stats = await client.get_system_stats()
            timestamp = time.strftime("%H:%M:%S")
            
            print(f"   {timestamp} - Tasks: {stats.get('active_tasks', 0)}, "
                  f"Memory: {stats.get('memory_usage_mb', 0):.1f}MB, "
                  f"CPU: {stats.get('cpu_percent', 0):.1f}%")
        
        print("✅ System monitoring completed")
        
    except Exception as e:
        print(f"💥 Error in system monitoring: {e}")


async def task_lifecycle_management():
    """
    Example: Advanced task lifecycle management
    """
    client = AdvancedMonitoringClient()
    
    print("\n🔄 Example 5c: Task Lifecycle Management")
    print("=" * 50)
    
    # Create a long-running task for lifecycle testing
    lifecycle_task = """
    Perform a slow, methodical website survey:
    
    1. Visit Wikipedia.org
    2. Search for "artificial intelligence"
    3. Read the introduction section carefully
    4. Navigate to related articles (machine learning, neural networks)
    5. For each article, extract key points
    6. Take screenshots at each step
    7. Compile a comprehensive research summary
    
    Work slowly and deliberately - this is for testing task control.
    """
    
    try:
        print("🚀 Creating lifecycle test task...")
        task = await client.create_monitored_task(lifecycle_task)
        task_id = task["id"]
        
        print(f"✅ Task created: {task_id}")
        
        # Let task run for a bit
        await asyncio.sleep(10)
        
        # Demonstrate pause/resume
        print("⏸️  Pausing task...")
        async with httpx.AsyncClient() as client_http:
            response = await client_http.put(
                f"{client.base_url}/api/v1/pause-task/{task_id}",
                headers=client.headers
            )
            pause_result = response.json()
            print(f"   Status: {pause_result.get('status', 'Unknown')}")
        
        # Wait a moment
        await asyncio.sleep(5)
        
        # Resume task
        print("▶️  Resuming task...")
        async with httpx.AsyncClient() as client_http:
            response = await client_http.put(
                f"{client.base_url}/api/v1/resume-task/{task_id}",
                headers=client.headers
            )
            resume_result = response.json()
            print(f"   Status: {resume_result.get('status', 'Unknown')}")
        
        # Let it run a bit more
        await asyncio.sleep(10)
        
        # Stop task
        print("🛑 Stopping task...")
        async with httpx.AsyncClient() as client_http:
            response = await client_http.put(
                f"{client.base_url}/api/v1/stop-task/{task_id}",
                headers=client.headers
            )
            stop_result = response.json()
            print(f"   Final Status: {stop_result.get('status', 'Unknown')}")
        
        print("✅ Task lifecycle management demo completed")
        
    except Exception as e:
        print(f"💥 Error in lifecycle management: {e}")


async def main():
    """Run all advanced monitoring examples"""
    print("📡 Browser-Use Local Bridge - Advanced Monitoring Examples")
    print("=" * 70)
    
    # Check API health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print("❌ API not available")
                return
            print("✅ API is ready for monitoring")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run monitoring examples
    await websocket_monitoring_example()
    await system_monitoring_dashboard()
    await task_lifecycle_management()
    
    print("\n✨ Advanced monitoring examples completed!")
    print("\n💡 These examples demonstrate:")
    print("   • Real-time WebSocket task monitoring")
    print("   • System performance tracking")
    print("   • Task lifecycle management (pause/resume/stop)")
    print("   • Live progress updates and notifications")


if __name__ == "__main__":
    asyncio.run(main()) 