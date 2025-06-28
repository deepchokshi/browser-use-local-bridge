#!/usr/bin/env python3
"""
Example 1: Basic Task Creation and Monitoring
============================================

This example demonstrates how to:
- Create a simple browser automation task
- Monitor its progress
- Get the final results

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured (or other LLM provider)
"""

import requests
import time
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "example_user"

def create_basic_task():
    """Create a simple task to navigate to a website and extract information"""
    
    print("🚀 Creating a basic browser automation task...")
    
    # Task configuration
    task_data = {
        "task": "Navigate to https://httpbin.org/get and extract the 'origin' IP address from the JSON response",
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
            "example": "basic_task",
            "description": "Simple information extraction task"
        }
    }
    
    # Create and start the task
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
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {task['status']}")
        print(f"   Provider: {task['llm_config']['provider']}")
        return task_id
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def monitor_task(task_id):
    """Monitor task progress until completion"""
    
    print(f"\n📊 Monitoring task progress...")
    
    while True:
        # Get task status
        response = requests.get(
            f"{API_BASE_URL}/api/v1/task/{task_id}/status",
            headers={"X-User-ID": USER_ID}
        )
        
        if response.status_code == 200:
            status = response.json()
            current_status = status['status']
            progress = status['progress_percentage']
            
            print(f"   Status: {current_status} ({progress}%)")
            
            # Check if task is completed
            if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                return current_status
            
            # Wait before next check
            time.sleep(2)
        else:
            print(f"❌ Failed to get task status: {response.status_code}")
            break
    
    return None

def get_task_results(task_id):
    """Get detailed task results and output"""
    
    print(f"\n📋 Getting task results...")
    
    # Get complete task details
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        task = response.json()
        
        print(f"✅ Task completed with status: {task['status']}")
        print(f"   Execution time: {task.get('execution_time_seconds', 'N/A')} seconds")
        
        if task.get('result'):
            print(f"   Result: {task['result']}")
        
        if task.get('error'):
            print(f"   Error: {task['error']}")
        
        # Show execution steps
        print(f"\n📝 Execution Steps:")
        for i, step in enumerate(task['steps'], 1):
            print(f"   {i}. {step['action']}: {step['description']}")
            if step.get('error'):
                print(f"      ❌ Error: {step['error']}")
        
        # Check for media files
        if task.get('media'):
            print(f"\n📸 Media Files: {len(task['media'])} files")
            for media in task['media']:
                print(f"   - {media['filename']} ({media['media_type']})")
        
        return task
    else:
        print(f"❌ Failed to get task results: {response.status_code}")
        return None

def main():
    """Main example function"""
    
    print("=" * 60)
    print("Browser-Use Local Bridge API - Basic Task Example")
    print("=" * 60)
    
    # Step 1: Create task
    task_id = create_basic_task()
    if not task_id:
        return
    
    # Step 2: Monitor progress
    final_status = monitor_task(task_id)
    if not final_status:
        return
    
    # Step 3: Get results
    task_results = get_task_results(task_id)
    
    print("\n" + "=" * 60)
    print("Example completed! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    main() 