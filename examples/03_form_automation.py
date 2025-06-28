#!/usr/bin/env python3
"""
Example 3: Form Automation
=========================

This example demonstrates how to:
- Navigate to a form page
- Fill out form fields automatically
- Submit forms and handle responses
- Take screenshots of the process

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured
"""

import requests
import time
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "form_user"

def create_form_task():
    """Create a form automation task"""
    
    print("📝 Creating form automation task...")
    
    task_data = {
        "task": """
        Navigate to https://httpbin.org/forms/post and complete the following form automation:
        
        1. Fill in the form with these details:
           - Customer name: "John Doe"
           - Telephone: "+1-555-123-4567"
           - Email: "john.doe@example.com"
           - Size: Select "Large"
           - Topping: Select "cheese"
           - Delivery time: Select "now"
           - Comments: "Please ring the doorbell twice"
        
        2. Take a screenshot before submitting the form
        3. Submit the form
        4. Take a screenshot of the result page
        5. Extract and return the response data
        
        Be careful to fill all required fields and ensure the form is properly submitted.
        """,
        "browser_config": {
            "headless": False,  # Visual mode to see form filling
            "enable_screenshots": True,
            "viewport_width": 1366,
            "viewport_height": 768,
            "timeout": 45000
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "metadata": {
            "example": "form_automation",
            "form_type": "order_form",
            "target_site": "httpbin.org"
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
        print(f"✅ Form automation task created!")
        print(f"   Task ID: {task_id}")
        print(f"   Target: httpbin.org form")
        return task_id
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def monitor_form_task(task_id):
    """Monitor form task with detailed step tracking"""
    
    print(f"\n🔍 Monitoring form automation progress...")
    
    last_step_count = 0
    
    while True:
        # Get current task status
        response = requests.get(
            f"{API_BASE_URL}/api/v1/task/{task_id}",
            headers={"X-User-ID": USER_ID}
        )
        
        if response.status_code == 200:
            task = response.json()
            current_status = task['status']
            progress = task['progress_percentage']
            steps = task.get('steps', [])
            
            # Show new steps
            if len(steps) > last_step_count:
                new_steps = steps[last_step_count:]
                for step in new_steps:
                    action = step.get('action', 'unknown')
                    description = step.get('description', 'No description')
                    print(f"   🔄 {action}: {description}")
                    
                    if step.get('error'):
                        print(f"      ❌ Error: {step['error']}")
                
                last_step_count = len(steps)
            
            print(f"   📊 Status: {current_status} ({progress}%)")
            
            # Check if completed
            if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                return current_status
            
            time.sleep(3)
        else:
            print(f"❌ Failed to get task details: {response.status_code}")
            break
    
    return None

def analyze_form_results(task_id):
    """Analyze the form submission results"""
    
    print(f"\n📊 Analyzing form submission results...")
    
    # Get complete task results
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        task = response.json()
        
        print(f"✅ Form automation completed!")
        print(f"   Status: {task['status']}")
        print(f"   Duration: {task.get('execution_time_seconds', 'N/A')} seconds")
        
        # Show the result
        if task.get('result'):
            print(f"\n📋 Form Submission Result:")
            result = task['result']
            
            # Try to parse if it's JSON
            try:
                if result.strip().startswith('{'):
                    parsed_result = json.loads(result)
                    print(json.dumps(parsed_result, indent=2))
                else:
                    print(f"   {result}")
            except:
                print(f"   {result}")
        
        # Show execution steps
        print(f"\n📝 Execution Steps:")
        for i, step in enumerate(task.get('steps', []), 1):
            print(f"   {i}. {step.get('action', 'unknown')}: {step.get('description', 'No description')}")
        
        # Media files info
        media_files = task.get('media', [])
        if media_files:
            print(f"\n📸 Screenshots captured: {len(media_files)}")
            for media in media_files:
                print(f"   - {media.get('filename', 'unknown')} ({media.get('media_type', 'unknown')})")
        
        return task
    else:
        print(f"❌ Failed to get results: {response.status_code}")
        return None

def download_form_screenshots(task_id):
    """Download screenshots from the form automation"""
    
    print(f"\n📥 Downloading form screenshots...")
    
    # Get media files
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}/media",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        media = response.json()
        
        if media['total_count'] > 0:
            import os
            os.makedirs("form_screenshots", exist_ok=True)
            
            for media_file in media['media_files']:
                filename = media_file['filename']
                
                download_response = requests.get(
                    f"{API_BASE_URL}/api/v1/media/{task_id}/{filename}",
                    headers={"X-User-ID": USER_ID}
                )
                
                if download_response.status_code == 200:
                    local_path = os.path.join("form_screenshots", f"form_{filename}")
                    with open(local_path, 'wb') as f:
                        f.write(download_response.content)
                    
                    print(f"   ✅ Downloaded: form_{filename}")
                else:
                    print(f"   ❌ Failed to download: {filename}")
        else:
            print("   No screenshots found")
    else:
        print(f"❌ Failed to get media list: {response.status_code}")

def demonstrate_task_control(task_id):
    """Demonstrate task control operations (pause/resume)"""
    
    print(f"\n⏸️ Demonstrating task control...")
    
    # Note: This is just for demonstration - in practice, you'd pause during execution
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}/status",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        status = response.json()
        if status['status'] == 'RUNNING':
            print("   Task is running - control operations available")
        else:
            print(f"   Task is {status['status']} - control operations not applicable")
    else:
        print("   Could not check task status for control demo")

def main():
    """Main form automation example"""
    
    print("=" * 70)
    print("Browser-Use Local Bridge API - Form Automation Example")
    print("=" * 70)
    
    # Step 1: Create form task
    task_id = create_form_task()
    if not task_id:
        return
    
    # Step 2: Monitor with detailed tracking
    final_status = monitor_form_task(task_id)
    if not final_status:
        return
    
    # Step 3: Analyze results
    task_result = analyze_form_results(task_id)
    if not task_result:
        return
    
    # Step 4: Download screenshots
    download_form_screenshots(task_id)
    
    # Step 5: Demonstrate task control
    demonstrate_task_control(task_id)
    
    print("\n" + "=" * 70)
    print("Form automation example completed! 🎉")
    print("Check 'form_screenshots' folder for captured images.")
    print("=" * 70)

if __name__ == "__main__":
    main() 