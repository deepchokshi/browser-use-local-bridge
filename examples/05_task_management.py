#!/usr/bin/env python3
"""
Example 5: Advanced Task Management and Control
==============================================

This example demonstrates how to:
- Create multiple tasks
- List and filter tasks
- Control task execution (pause, resume, stop)
- Manage task lifecycle
- Export task data

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "task_manager"

class TaskManager:
    """Helper class for managing multiple tasks"""
    
    def __init__(self, api_base_url: str, user_id: str):
        self.api_base_url = api_base_url
        self.user_id = user_id
        self.headers = {
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        }
    
    def create_task(self, task_description: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new task and return its ID"""
        
        task_data = {
            "task": task_description,
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
            "metadata": metadata or {}
        }
        
        response = requests.post(
            f"{self.api_base_url}/api/v1/run-task",
            headers=self.headers,
            json=task_data
        )
        
        if response.status_code == 201:
            task = response.json()
            return task["id"]
        else:
            raise Exception(f"Failed to create task: {response.status_code} - {response.text}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current task status"""
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/task/{task_id}/status",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get task status: {response.status_code}")
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get complete task details"""
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/task/{task_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get task details: {response.status_code}")
    
    def list_tasks(self, page: int = 1, page_size: int = 10, status_filter: str = None) -> Dict[str, Any]:
        """List tasks with optional filtering"""
        
        params = {
            "page": page,
            "page_size": page_size
        }
        
        if status_filter:
            params["status"] = status_filter
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/list-tasks",
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list tasks: {response.status_code}")
    
    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """Stop a running task"""
        
        response = requests.put(
            f"{self.api_base_url}/api/v1/stop-task/{task_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to stop task: {response.status_code}")
    
    def pause_task(self, task_id: str) -> Dict[str, Any]:
        """Pause a running task"""
        
        response = requests.put(
            f"{self.api_base_url}/api/v1/pause-task/{task_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to pause task: {response.status_code}")
    
    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resume a paused task"""
        
        response = requests.put(
            f"{self.api_base_url}/api/v1/resume-task/{task_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to resume task: {response.status_code}")

def create_sample_tasks(manager: TaskManager) -> List[str]:
    """Create several sample tasks for demonstration"""
    
    print("🚀 Creating sample tasks for management demonstration...")
    
    tasks = [
        {
            "description": "Navigate to https://httpbin.org/get and extract the IP address",
            "metadata": {"category": "api_test", "priority": "high"}
        },
        {
            "description": "Go to https://quotes.toscrape.com and get the first quote",
            "metadata": {"category": "scraping", "priority": "medium"}
        },
        {
            "description": "Visit https://news.ycombinator.com and count the number of stories on the front page",
            "metadata": {"category": "analysis", "priority": "low"}
        }
    ]
    
    task_ids = []
    
    for i, task_config in enumerate(tasks, 1):
        try:
            task_id = manager.create_task(
                task_config["description"],
                task_config["metadata"]
            )
            task_ids.append(task_id)
            print(f"   ✅ Task {i} created: {task_id[:8]}... ({task_config['metadata']['category']})")
            
            # Small delay between task creation
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed to create task {i}: {e}")
    
    return task_ids

def demonstrate_task_listing(manager: TaskManager):
    """Demonstrate task listing and filtering"""
    
    print(f"\n📋 Demonstrating task listing and filtering...")
    
    try:
        # List all tasks
        all_tasks = manager.list_tasks(page=1, page_size=20)
        print(f"   📊 Total tasks: {all_tasks['total_count']}")
        print(f"   📄 Current page: {all_tasks['page']} (showing {len(all_tasks['tasks'])} tasks)")
        
        # Show task summary
        for task in all_tasks['tasks']:
            status = task['status']
            created_at = task['created_at'][:19]  # Remove microseconds
            metadata = task.get('metadata', {})
            category = metadata.get('category', 'unknown')
            priority = metadata.get('priority', 'unknown')
            
            print(f"   • {task['id'][:8]}... | {status} | {category} | {priority} | {created_at}")
        
        # Filter by status (if any running tasks exist)
        running_tasks = manager.list_tasks(status_filter="RUNNING")
        if running_tasks['total_count'] > 0:
            print(f"\n   🏃 Running tasks: {running_tasks['total_count']}")
            for task in running_tasks['tasks']:
                print(f"     • {task['id'][:8]}... | {task['status']}")
        else:
            print(f"\n   ⏸️ No currently running tasks")
        
    except Exception as e:
        print(f"   ❌ Failed to list tasks: {e}")

def demonstrate_task_control(manager: TaskManager, task_ids: List[str]):
    """Demonstrate task control operations"""
    
    print(f"\n🎮 Demonstrating task control operations...")
    
    if not task_ids:
        print("   ❌ No tasks available for control demonstration")
        return
    
    # Pick the first task for control demo
    task_id = task_ids[0]
    print(f"   🎯 Using task {task_id[:8]}... for control demonstration")
    
    try:
        # Check initial status
        status = manager.get_task_status(task_id)
        print(f"   📊 Initial status: {status['status']} ({status['progress_percentage']}%)")
        
        # If task is running, demonstrate pause/resume
        if status['status'] == 'RUNNING':
            print(f"   ⏸️ Attempting to pause task...")
            try:
                pause_result = manager.pause_task(task_id)
                print(f"      ✅ Task paused: {pause_result['status']}")
                
                # Wait a moment
                time.sleep(2)
                
                print(f"   ▶️ Attempting to resume task...")
                resume_result = manager.resume_task(task_id)
                print(f"      ✅ Task resumed: {resume_result['status']}")
                
            except Exception as e:
                print(f"      ❌ Pause/resume failed: {e}")
        
        # Demonstrate stop operation
        current_status = manager.get_task_status(task_id)
        if current_status['status'] in ['RUNNING', 'PAUSED']:
            print(f"   🛑 Stopping task...")
            try:
                stop_result = manager.stop_task(task_id)
                print(f"      ✅ Task stopped: {stop_result['status']}")
            except Exception as e:
                print(f"      ❌ Stop failed: {e}")
        else:
            print(f"   ℹ️ Task is {current_status['status']} - control operations not applicable")
        
    except Exception as e:
        print(f"   ❌ Control demonstration failed: {e}")

def monitor_task_progress(manager: TaskManager, task_ids: List[str], timeout: int = 60):
    """Monitor progress of multiple tasks"""
    
    print(f"\n📊 Monitoring task progress (timeout: {timeout}s)...")
    
    if not task_ids:
        print("   ❌ No tasks to monitor")
        return
    
    start_time = time.time()
    completed_tasks = set()
    
    while time.time() - start_time < timeout:
        try:
            active_tasks = []
            
            for task_id in task_ids:
                if task_id in completed_tasks:
                    continue
                
                status = manager.get_task_status(task_id)
                current_status = status['status']
                progress = status['progress_percentage']
                
                if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                    completed_tasks.add(task_id)
                    print(f"   🏁 Task {task_id[:8]}... completed: {current_status}")
                else:
                    active_tasks.append((task_id, current_status, progress))
            
            # Show active tasks
            if active_tasks:
                print(f"   📈 Active tasks:")
                for task_id, status, progress in active_tasks:
                    print(f"     • {task_id[:8]}... | {status} | {progress}%")
            
            # Check if all tasks completed
            if len(completed_tasks) == len(task_ids):
                print(f"   ✅ All tasks completed!")
                break
            
            time.sleep(5)
            
        except Exception as e:
            print(f"   ❌ Monitoring error: {e}")
            break
    
    if len(completed_tasks) < len(task_ids):
        print(f"   ⏰ Monitoring timeout - {len(completed_tasks)}/{len(task_ids)} tasks completed")

def generate_task_report(manager: TaskManager, task_ids: List[str]):
    """Generate a comprehensive task report"""
    
    print(f"\n📊 Generating task execution report...")
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_tasks": len(task_ids),
        "tasks": []
    }
    
    total_duration = 0
    status_counts = {}
    
    for task_id in task_ids:
        try:
            task_details = manager.get_task_details(task_id)
            
            task_info = {
                "id": task_id,
                "status": task_details['status'],
                "duration": task_details.get('execution_time_seconds', 0),
                "steps": len(task_details.get('steps', [])),
                "media_files": len(task_details.get('media', [])),
                "created_at": task_details['created_at'],
                "metadata": task_details.get('metadata', {})
            }
            
            report["tasks"].append(task_info)
            
            # Update statistics
            if task_info['duration']:
                total_duration += task_info['duration']
            
            status = task_info['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
        except Exception as e:
            print(f"   ❌ Failed to get details for task {task_id[:8]}...: {e}")
    
    # Add summary statistics
    report["summary"] = {
        "total_duration_seconds": total_duration,
        "average_duration_seconds": total_duration / len(task_ids) if task_ids else 0,
        "status_distribution": status_counts
    }
    
    # Display report
    print(f"   📋 Task Execution Report:")
    print(f"      Total tasks: {report['total_tasks']}")
    print(f"      Total duration: {total_duration:.1f} seconds")
    print(f"      Average duration: {report['summary']['average_duration_seconds']:.1f} seconds")
    print(f"      Status distribution:")
    for status, count in status_counts.items():
        print(f"        • {status}: {count}")
    
    # Save report to file
    with open("task_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"   💾 Report saved to: task_report.json")
    
    return report

def main():
    """Main task management demonstration"""
    
    print("=" * 80)
    print("Browser-Use Local Bridge API - Advanced Task Management Example")
    print("=" * 80)
    
    # Initialize task manager
    manager = TaskManager(API_BASE_URL, USER_ID)
    
    try:
        # Step 1: Create sample tasks
        task_ids = create_sample_tasks(manager)
        
        if not task_ids:
            print("❌ No tasks created - cannot continue demonstration")
            return
        
        # Step 2: Demonstrate task listing
        demonstrate_task_listing(manager)
        
        # Step 3: Monitor task progress
        monitor_task_progress(manager, task_ids, timeout=90)
        
        # Step 4: Demonstrate task control
        demonstrate_task_control(manager, task_ids)
        
        # Step 5: Final task listing
        print(f"\n📋 Final task listing:")
        demonstrate_task_listing(manager)
        
        # Step 6: Generate comprehensive report
        report = generate_task_report(manager, task_ids)
        
        print("\n" + "=" * 80)
        print("Task management example completed! 🎉")
        print("Check 'task_report.json' for detailed execution report.")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Example failed: {e}")

if __name__ == "__main__":
    main() 