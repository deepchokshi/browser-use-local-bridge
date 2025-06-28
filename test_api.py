#!/usr/bin/env python3
"""
Browser-Use Local Bridge API Test Script
Tests all major API endpoints and functionality
"""

import asyncio
import json
import time
import requests
import websockets
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserUseBridgeTest:
    """Test suite for Browser-Use Local Bridge API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", user_id: str = "test_user"):
        self.base_url = base_url
        self.user_id = user_id
        self.headers = {"X-User-ID": user_id, "Content-Type": "application/json"}
        self.task_id = None
        
    def test_health_check(self) -> bool:
        """Test basic health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Health check passed: {data['status']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def test_system_info(self) -> bool:
        """Test system information endpoints"""
        try:
            # Test ping
            response = requests.get(f"{self.base_url}/api/v1/ping")
            response.raise_for_status()
            logger.info("✅ Ping endpoint working")
            
            # Test system stats
            response = requests.get(f"{self.base_url}/api/v1/system-stats")
            response.raise_for_status()
            stats = response.json()
            logger.info(f"✅ System stats: {stats['active_tasks']} active tasks")
            
            # Test LLM providers
            response = requests.get(f"{self.base_url}/api/v1/llm-providers")
            response.raise_for_status()
            providers = response.json()
            available = [p for p in providers if p['available']]
            logger.info(f"✅ Available LLM providers: {len(available)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System info test failed: {e}")
            return False
    
    def test_create_task(self) -> bool:
        """Test task creation"""
        try:
            task_data = {
                "task": "Navigate to https://httpbin.org/get and verify the page loads",
                "browser_config": {
                    "headless": True,
                    "enable_screenshots": True,
                    "viewport_width": 1280,
                    "viewport_height": 720
                },
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "temperature": 0.1
                },
                "metadata": {
                    "test_run": True,
                    "created_by": "test_script"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/run-task",
                headers=self.headers,
                json=task_data
            )
            response.raise_for_status()
            
            task = response.json()
            self.task_id = task['id']
            logger.info(f"✅ Task created: {self.task_id}")
            logger.info(f"   Status: {task['status']}")
            logger.info(f"   Provider: {task['llm_config']['provider']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task creation failed: {e}")
            return False
    
    def test_task_monitoring(self) -> bool:
        """Test task monitoring endpoints"""
        if not self.task_id:
            logger.error("❌ No task ID available for monitoring test")
            return False
        
        try:
            # Test task status
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}/status",
                headers=self.headers
            )
            response.raise_for_status()
            status = response.json()
            logger.info(f"✅ Task status: {status['status']} ({status['progress_percentage']}%)")
            
            # Test task details
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            task = response.json()
            logger.info(f"✅ Task details retrieved: {len(task['steps'])} steps")
            
            # Test task steps
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}/steps",
                headers=self.headers
            )
            response.raise_for_status()
            steps = response.json()
            logger.info(f"✅ Task steps: {len(steps['steps'])} steps")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task monitoring test failed: {e}")
            return False
    
    def test_wait_for_completion(self, timeout: int = 120) -> bool:
        """Wait for task completion with timeout"""
        if not self.task_id:
            logger.error("❌ No task ID available")
            return False
        
        logger.info(f"⏳ Waiting for task completion (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/task/{self.task_id}/status",
                    headers=self.headers
                )
                response.raise_for_status()
                status = response.json()
                
                current_status = status['status']
                progress = status['progress_percentage']
                
                logger.info(f"   Status: {current_status} ({progress}%)")
                
                if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                    if current_status == 'FINISHED':
                        logger.info("✅ Task completed successfully")
                        return True
                    else:
                        logger.error(f"❌ Task ended with status: {current_status}")
                        return False
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Error checking task status: {e}")
                return False
        
        logger.error(f"❌ Task timed out after {timeout}s")
        return False
    
    def test_media_endpoints(self) -> bool:
        """Test media file endpoints"""
        if not self.task_id:
            logger.error("❌ No task ID available for media test")
            return False
        
        try:
            # Test media list
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}/media",
                headers=self.headers
            )
            response.raise_for_status()
            media = response.json()
            logger.info(f"✅ Media files: {media['total_count']} files, {media['total_size_bytes']} bytes")
            
            # Test detailed media list
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}/media/list",
                headers=self.headers
            )
            response.raise_for_status()
            detailed_media = response.json()
            logger.info(f"✅ Detailed media info: {len(detailed_media)} files")
            
            # Test downloading a media file if available
            if media['total_count'] > 0:
                first_file = media['media_files'][0]['filename']
                response = requests.get(
                    f"{self.base_url}/api/v1/media/{self.task_id}/{first_file}",
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"✅ Downloaded media file: {first_file} ({len(response.content)} bytes)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Media endpoints test failed: {e}")
            return False
    
    def test_task_control(self) -> bool:
        """Test task control operations (pause/resume/stop)"""
        if not self.task_id:
            logger.error("❌ No task ID available for control test")
            return False
        
        try:
            # Note: These operations might not work if task is already completed
            # This is mainly to test the API endpoints
            
            # Test stop (if task is still running)
            response = requests.get(
                f"{self.base_url}/api/v1/task/{self.task_id}/status",
                headers=self.headers
            )
            current_status = response.json()['status']
            
            if current_status == 'RUNNING':
                response = requests.put(
                    f"{self.base_url}/api/v1/stop-task/{self.task_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    logger.info("✅ Task stop endpoint working")
                else:
                    logger.info("ℹ️ Task stop endpoint tested (task may not be running)")
            else:
                logger.info("ℹ️ Task control test skipped (task not running)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task control test failed: {e}")
            return False
    
    async def test_websocket_monitoring(self) -> bool:
        """Test WebSocket live monitoring"""
        if not self.task_id:
            logger.error("❌ No task ID available for WebSocket test")
            return False
        
        try:
            ws_url = f"ws://localhost:8000/api/v1/live/{self.task_id}?user_id={self.user_id}"
            
            async with websockets.connect(ws_url) as websocket:
                logger.info("✅ WebSocket connected")
                
                # Receive a few messages
                for i in range(3):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10)
                        data = json.loads(message)
                        logger.info(f"✅ WebSocket message {i+1}: {data['status']} ({data['progress_percentage']}%)")
                    except asyncio.TimeoutError:
                        logger.info("ℹ️ WebSocket timeout (normal for completed tasks)")
                        break
                
                return True
                
        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            return False
    
    def test_list_tasks(self) -> bool:
        """Test task listing endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/list-tasks",
                headers=self.headers,
                params={"page": 1, "page_size": 10}
            )
            response.raise_for_status()
            
            tasks = response.json()
            logger.info(f"✅ Task list: {len(tasks['tasks'])} tasks, page {tasks['page']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task list test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("🚀 Starting Browser-Use Local Bridge API Tests")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   User ID: {self.user_id}")
        
        results = {}
        
        # Basic connectivity tests
        results['health_check'] = self.test_health_check()
        results['system_info'] = self.test_system_info()
        
        # Task management tests
        results['create_task'] = self.test_create_task()
        results['task_monitoring'] = self.test_task_monitoring()
        results['wait_for_completion'] = self.test_wait_for_completion()
        results['media_endpoints'] = self.test_media_endpoints()
        results['task_control'] = self.test_task_control()
        results['list_tasks'] = self.test_list_tasks()
        
        # WebSocket test (async)
        try:
            results['websocket_monitoring'] = asyncio.run(self.test_websocket_monitoring())
        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            results['websocket_monitoring'] = False
        
        # Summary
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")
        
        if passed == total:
            logger.info("🎉 All tests passed! API is working correctly.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check the logs above.")
        
        return results

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Browser-Use Local Bridge API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--user-id", default="test_user", help="User ID for testing")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (skip task execution)")
    
    args = parser.parse_args()
    
    tester = BrowserUseBridgeTest(args.url, args.user_id)
    
    if args.quick:
        # Quick tests only
        results = {}
        results['health_check'] = tester.test_health_check()
        results['system_info'] = tester.test_system_info()
        results['list_tasks'] = tester.test_list_tasks()
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        logger.info(f"\n📊 Quick Test Results: {passed}/{total} tests passed")
    else:
        # Full test suite
        results = tester.run_all_tests()
    
    return results

if __name__ == "__main__":
    main() 