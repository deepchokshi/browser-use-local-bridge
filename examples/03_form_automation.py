#!/usr/bin/env python3
"""
Example 3: Advanced Form Automation with Browser-Use Local Bridge
=================================================================

This example demonstrates sophisticated form handling capabilities:
- Multi-step form workflows
- Dynamic form validation and error handling
- File uploads and form submissions
- Custom functions for specific form interactions

Use case: Job application automation with resume upload and custom responses
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "form_automation_user"


class FormAutomationClient:
    """Client specialized for form automation tasks"""
    
    def __init__(self, base_url: str = API_BASE_URL, user_id: str = USER_ID):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    async def create_form_task(self, task: str, **config) -> Dict[str, Any]:
        """Create task with form automation optimizations"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/run-task",
                json={"task": task, **config},
                headers=self.headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def monitor_task(self, task_id: str, timeout: int = 900) -> Dict[str, Any]:
        """Monitor task with detailed progress tracking"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/task/{task_id}/status",
                    headers=self.headers
                )
                status = response.json()
            
            print(f"📊 {status['status']}: {status['progress_percentage']:.1f}%")
            
            if status['status'] in ['FINISHED', 'FAILED', 'STOPPED']:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/task/{task_id}",
                        headers=self.headers
                    )
                return response.json()
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Task {task_id} timeout after {timeout}s")


async def job_application_automation():
    """
    Example: Automated job application with resume upload and form completion
    """
    client = FormAutomationClient()
    
    print("💼 Example 3a: Job Application Form Automation")
    print("=" * 55)
    
    # Create a realistic job application scenario
    application_task = """
    Automate a job application process:
    
    1. Visit Indeed.com or a similar job board
    2. Search for "Software Engineer Python remote" jobs
    3. Find a suitable job posting (entry to mid-level)
    4. Click "Apply Now" or similar application button
    5. Fill out the application form with the following information:
       - Name: John Smith
       - Email: john.smith.demo@email.com
       - Phone: (555) 123-4567
       - Location: San Francisco, CA
       - Years of Experience: 3 years
       - Current Job Title: Software Developer
       - Why interested: "Passionate about Python development and remote work opportunities"
    6. Handle any additional form fields intelligently
    7. Take screenshots of each form step
    8. Stop before final submission (for safety)
    
    Document the entire process and any challenges encountered.
    """
    
    # Configure for form automation with custom functions
    task_config = {
        "browser_config": {
            "headless": False,  # Show browser for demo
            "viewport_width": 1366,
            "viewport_height": 768,
            "enable_screenshots": True,
            "timeout": 60000
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1  # Lower temperature for consistent form filling
        },
        "agent_config": {
            "max_actions_per_step": 12,
            "max_failures": 3,
            "retry_delay": 2.0,
            "use_vision": True,
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "application_progress": {
                            "type": "object",
                            "properties": {
                                "job_title": {"type": "string"},
                                "company_name": {"type": "string"},
                                "job_url": {"type": "string"},
                                "application_status": {"type": "string"},
                                "form_fields_completed": {"type": "array", "items": {"type": "string"}},
                                "challenges_encountered": {"type": "array", "items": {"type": "string"}},
                                "next_steps": {"type": "string"}
                            }
                        },
                        "form_data_entered": {
                            "type": "object",
                            "properties": {
                                "personal_info": {"type": "object"},
                                "experience_details": {"type": "object"},
                                "additional_questions": {"type": "array", "items": {"type": "object"}}
                            }
                        }
                    }
                },
                "validate_output": True,
                "custom_functions": [
                    {
                        "name": "smart_form_fill",
                        "description": "Intelligently fill form fields based on context and field type",
                        "parameters": [
                            {
                                "name": "field_label",
                                "type": "str",
                                "description": "The label or placeholder text of the form field"
                            },
                            {
                                "name": "field_type",
                                "type": "str", 
                                "description": "Type of form field (text, email, tel, textarea, select, etc.)"
                            },
                            {
                                "name": "context",
                                "type": "str",
                                "description": "Additional context about what information is expected"
                            }
                        ],
                        "implementation_type": "code",
                        "python_code": """
def smart_form_fill(field_label, field_type, context):
    # Smart form filling logic based on field context
    user_data = {
        'name': 'John Smith',
        'first_name': 'John',
        'last_name': 'Smith',
        'email': 'john.smith.demo@email.com',
        'phone': '(555) 123-4567',
        'location': 'San Francisco, CA',
        'city': 'San Francisco',
        'state': 'CA',
        'experience': '3',
        'current_title': 'Software Developer',
        'skills': 'Python, JavaScript, React, Django, SQL'
    }
    
    field_lower = field_label.lower()
    
    if 'name' in field_lower and 'first' in field_lower:
        return user_data['first_name']
    elif 'name' in field_lower and 'last' in field_lower:
        return user_data['last_name']
    elif 'name' in field_lower:
        return user_data['name']
    elif 'email' in field_lower:
        return user_data['email']
    elif 'phone' in field_lower:
        return user_data['phone']
    elif any(loc in field_lower for loc in ['location', 'city', 'address']):
        return user_data['location']
    elif 'experience' in field_lower or 'years' in field_lower:
        return user_data['experience']
    elif 'title' in field_lower or 'position' in field_lower:
        return user_data['current_title']
    elif 'skill' in field_lower:
        return user_data['skills']
    elif 'why' in field_lower or 'interest' in field_lower or 'motivation' in field_lower:
        return "Passionate about Python development and excited about remote work opportunities in innovative tech companies."
    else:
        return "Please provide appropriate information"
                        """
                    }
                ]
            }
        },
        "metadata": {
            "example": "job_application_automation",
            "safety_mode": "demo_only"  # Prevent actual submissions
        }
    }
    
    try:
        print("🚀 Starting job application automation...")
        task = await client.create_form_task(application_task, **task_config)
        task_id = task["id"]
        
        print(f"✅ Task created: {task_id}")
        result = await client.monitor_task(task_id)
        
        if result['status'] == 'FINISHED':
            print("✅ Job application automation completed!")
            
            # Parse and display structured results
            if result.get('result') and isinstance(result['result'], dict):
                data = result['result']
                
                # Display application progress
                progress = data.get('application_progress', {})
                if progress:
                    print(f"\n📋 Application Progress:")
                    print(f"   Job Title: {progress.get('job_title', 'N/A')}")
                    print(f"   Company: {progress.get('company_name', 'N/A')}")
                    print(f"   Status: {progress.get('application_status', 'N/A')}")
                    
                    completed_fields = progress.get('form_fields_completed', [])
                    if completed_fields:
                        print(f"   ✅ Completed Fields ({len(completed_fields)}):")
                        for field in completed_fields:
                            print(f"      • {field}")
                    
                    challenges = progress.get('challenges_encountered', [])
                    if challenges:
                        print(f"   ⚠️  Challenges:")
                        for challenge in challenges:
                            print(f"      • {challenge}")
                
                # Display form data
                form_data = data.get('form_data_entered', {})
                if form_data:
                    print(f"\n📝 Form Data Entered:")
                    personal_info = form_data.get('personal_info', {})
                    if personal_info:
                        print(f"   Personal Information: {len(personal_info)} fields")
                    
                    experience = form_data.get('experience_details', {})
                    if experience:
                        print(f"   Experience Details: {len(experience)} fields")
            
            # Show screenshots
            media_files = result.get('media', [])
            if media_files:
                print(f"\n📸 Generated {len(media_files)} screenshots:")
                for media in media_files:
                    print(f"   • {media['filename']}")
        
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in job application: {e}")
        return None


async def contact_form_automation():
    """
    Example: Automated contact form submissions with validation
    """
    client = FormAutomationClient()
    
    print("\n📝 Example 3b: Contact Form Automation")
    print("=" * 45)
    
    contact_task = """
    Automate contact form submissions on business websites:
    
    1. Visit a business website with a contact form (e.g., a software company)
    2. Navigate to their contact/demo request page
    3. Fill out the contact form with business inquiry information:
       - Name: Sarah Johnson
       - Email: sarah.johnson.business@email.com
       - Company: TechStart Solutions
       - Phone: (555) 987-6543
       - Subject: Partnership Inquiry
       - Message: "Interested in exploring partnership opportunities for our automation solutions"
    4. Handle any required fields, dropdowns, or checkboxes
    5. Validate form completion before submission
    6. Take screenshot of completed form
    7. Stop before final submission
    
    Return summary of form fields and validation status.
    """
    
    task_config = {
        "browser_config": {
            "headless": True,
            "enable_screenshots": True
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.0
        },
        "agent_config": {
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "website_info": {
                            "type": "object",
                            "properties": {
                                "company_name": {"type": "string"},
                                "website_url": {"type": "string"},
                                "form_location": {"type": "string"}
                            }
                        },
                        "form_completion": {
                            "type": "object",
                            "properties": {
                                "total_fields": {"type": "integer"},
                                "completed_fields": {"type": "integer"},
                                "required_fields_met": {"type": "boolean"},
                                "validation_errors": {"type": "array", "items": {"type": "string"}},
                                "form_ready_for_submission": {"type": "boolean"}
                            }
                        },
                        "field_details": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field_name": {"type": "string"},
                                    "field_type": {"type": "string"},
                                    "value_entered": {"type": "string"},
                                    "is_required": {"type": "boolean"},
                                    "validation_status": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        print("🚀 Starting contact form automation...")
        task = await client.create_form_task(contact_task, **task_config)
        task_id = task["id"]
        
        result = await client.monitor_task(task_id)
        
        if result['status'] == 'FINISHED' and result.get('result'):
            data = result['result']
            
            # Display website info
            website_info = data.get('website_info', {})
            if website_info:
                print(f"\n🌐 Website: {website_info.get('company_name', 'Unknown')}")
                print(f"   URL: {website_info.get('website_url', 'N/A')}")
            
            # Display form completion status
            completion = data.get('form_completion', {})
            if completion:
                print(f"\n📋 Form Completion Status:")
                print(f"   Total Fields: {completion.get('total_fields', 0)}")
                print(f"   Completed: {completion.get('completed_fields', 0)}")
                print(f"   Required Fields Met: {'✅' if completion.get('required_fields_met') else '❌'}")
                print(f"   Ready for Submission: {'✅' if completion.get('form_ready_for_submission') else '❌'}")
                
                errors = completion.get('validation_errors', [])
                if errors:
                    print(f"   ⚠️  Validation Errors:")
                    for error in errors:
                        print(f"      • {error}")
            
            # Display field details
            fields = data.get('field_details', [])
            if fields:
                print(f"\n📝 Field Details:")
                for field in fields:
                    status_icon = "✅" if field.get('validation_status') == 'valid' else "❌"
                    required_icon = "🔴" if field.get('is_required') else "⚪"
                    print(f"   {status_icon} {required_icon} {field.get('field_name', 'Unknown')}: {field.get('value_entered', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in contact form automation: {e}")
        return None


async def main():
    """Run all form automation examples"""
    print("📝 Browser-Use Local Bridge - Form Automation Examples")
    print("=" * 60)
    
    # Check API availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print(f"❌ API not available")
                return
            print("✅ API is ready")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run examples
    await job_application_automation()
    await contact_form_automation()
    
    print("\n✨ Form automation examples completed!")
    print("\n💡 These examples demonstrate:")
    print("   • Complex multi-step form workflows")
    print("   • Custom function integration for smart form filling")
    print("   • Form validation and error handling")
    print("   • Structured output for form completion tracking")
    print("   • Safe demo mode (stops before actual submissions)")


if __name__ == "__main__":
    asyncio.run(main()) 