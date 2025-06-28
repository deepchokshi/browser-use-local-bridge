#!/usr/bin/env python3
"""
Example 6: n8n Integration Workflow
==================================

This example demonstrates how to:
- Use the Browser-Use Local Bridge API in n8n workflows
- Create reusable workflow components
- Handle different response scenarios
- Integrate with webhook triggers
- Process results for downstream nodes

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured
- This example can be adapted for n8n HTTP Request nodes
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "n8n_workflow"

class N8nBrowserAutomation:
    """
    n8n-compatible browser automation wrapper
    This class provides methods that can be easily adapted for n8n HTTP Request nodes
    """
    
    def __init__(self, api_base_url: str, user_id: str):
        self.api_base_url = api_base_url
        self.user_id = user_id
        self.headers = {
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        }
    
    def create_browser_task(
        self, 
        task_description: str, 
        headless: bool = True,
        enable_screenshots: bool = True,
        timeout_seconds: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a browser automation task
        
        This method structure is designed to be easily replicated in n8n HTTP Request nodes
        """
        
        payload = {
            "task": task_description,
            "browser_config": {
                "headless": headless,
                "enable_screenshots": enable_screenshots,
                "viewport_width": 1280,
                "viewport_height": 720,
                "timeout": timeout_seconds * 1000  # Convert to milliseconds
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
            json=payload
        )
        
        if response.status_code == 201:
            task_data = response.json()
            return {
                "success": True,
                "task_id": task_data["id"],
                "status": task_data["status"],
                "message": "Task created successfully",
                "data": task_data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": response.text,
                "data": None
            }
    
    def wait_for_completion(
        self, 
        task_id: str, 
        timeout_seconds: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for task completion with polling
        
        Returns structured data suitable for n8n workflow processing
        """
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            # Check task status
            response = requests.get(
                f"{self.api_base_url}/api/v1/task/{task_id}/status",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": "Failed to check task status",
                    "data": None
                }
            
            status_data = response.json()
            current_status = status_data["status"]
            
            # Check if completed
            if current_status in ["FINISHED", "FAILED", "STOPPED"]:
                # Get full task details
                details_response = requests.get(
                    f"{self.api_base_url}/api/v1/task/{task_id}",
                    headers=self.headers
                )
                
                if details_response.status_code == 200:
                    task_details = details_response.json()
                    
                    return {
                        "success": current_status == "FINISHED",
                        "status": current_status,
                        "task_id": task_id,
                        "result": task_details.get("result"),
                        "error": task_details.get("error"),
                        "execution_time": task_details.get("execution_time_seconds"),
                        "steps_count": len(task_details.get("steps", [])),
                        "media_count": len(task_details.get("media", [])),
                        "data": task_details
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to get task details",
                        "message": details_response.text,
                        "data": None
                    }
            
            # Still running, wait before next check
            time.sleep(poll_interval)
        
        # Timeout reached
        return {
            "success": False,
            "error": "TIMEOUT",
            "message": f"Task did not complete within {timeout_seconds} seconds",
            "data": None
        }
    
    def get_task_media_urls(self, task_id: str) -> Dict[str, Any]:
        """
        Get downloadable URLs for task media files
        
        Useful for n8n workflows that need to process screenshots or recordings
        """
        
        response = requests.get(
            f"{self.api_base_url}/api/v1/task/{task_id}/media",
            headers=self.headers
        )
        
        if response.status_code == 200:
            media_data = response.json()
            
            # Build downloadable URLs
            media_urls = []
            for media_file in media_data.get("media_files", []):
                filename = media_file["filename"]
                download_url = f"{self.api_base_url}/api/v1/media/{task_id}/{filename}"
                
                media_urls.append({
                    "filename": filename,
                    "download_url": download_url,
                    "media_type": media_file["media_type"],
                    "size_bytes": media_file["size_bytes"],
                    "created_at": media_file["created_at"]
                })
            
            return {
                "success": True,
                "media_count": len(media_urls),
                "total_size_bytes": media_data.get("total_size_bytes", 0),
                "media_files": media_urls,
                "data": media_data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": response.text,
                "data": None
            }

def demonstrate_n8n_workflow_patterns():
    """Demonstrate common n8n workflow patterns"""
    
    print("🔄 Demonstrating n8n Workflow Patterns")
    print("=" * 60)
    
    automation = N8nBrowserAutomation(API_BASE_URL, USER_ID)
    
    # Pattern 1: Simple Data Extraction
    print("\n📊 Pattern 1: Simple Data Extraction Workflow")
    print("-" * 50)
    
    # Step 1: Create task (HTTP Request node in n8n)
    task_result = automation.create_browser_task(
        task_description="Navigate to https://httpbin.org/json and extract all the data as JSON",
        metadata={"workflow": "data_extraction", "pattern": "simple"}
    )
    
    print(f"✅ Task Creation Result:")
    print(f"   Success: {task_result['success']}")
    if task_result['success']:
        print(f"   Task ID: {task_result['task_id']}")
        
        # Step 2: Wait for completion (HTTP Request node with polling)
        completion_result = automation.wait_for_completion(
            task_result['task_id'], 
            timeout_seconds=120
        )
        
        print(f"\n✅ Task Completion Result:")
        print(f"   Success: {completion_result['success']}")
        print(f"   Status: {completion_result.get('status', 'N/A')}")
        print(f"   Execution Time: {completion_result.get('execution_time', 'N/A')}s")
        
        if completion_result['success'] and completion_result.get('result'):
            print(f"   Result Preview: {completion_result['result'][:200]}...")
        
        # Step 3: Get media files (Optional HTTP Request node)
        media_result = automation.get_task_media_urls(task_result['task_id'])
        print(f"\n📸 Media Files: {media_result['media_count']} files")
        
        return task_result['task_id'], completion_result
    else:
        print(f"   Error: {task_result['message']}")
        return None, None

def generate_n8n_workflow_json():
    """Generate example n8n workflow JSON"""
    
    print("\n📋 Generating n8n Workflow JSON Example")
    print("-" * 50)
    
    # This is an example n8n workflow that uses the Browser-Use Local Bridge API
    n8n_workflow = {
        "name": "Browser Automation with Local Bridge",
        "nodes": [
            {
                "parameters": {},
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [240, 300]
            },
            {
                "parameters": {
                    "url": "http://localhost:8000/api/v1/run-task",
                    "options": {
                        "headers": {
                            "X-User-ID": "n8n_user",
                            "Content-Type": "application/json"
                        }
                    },
                    "bodyParametersUi": {
                        "parameter": [
                            {
                                "name": "task",
                                "value": "Navigate to https://httpbin.org/get and extract the origin IP"
                            },
                            {
                                "name": "browser_config",
                                "value": {
                                    "headless": True,
                                    "enable_screenshots": True,
                                    "viewport_width": 1280,
                                    "viewport_height": 720
                                }
                            },
                            {
                                "name": "llm_config",
                                "value": {
                                    "provider": "openai",
                                    "model": "gpt-4o",
                                    "temperature": 0.1
                                }
                            }
                        ]
                    }
                },
                "name": "Create Browser Task",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "url": "=http://localhost:8000/api/v1/task/{{$json[\"id\"]}}/status",
                    "options": {
                        "headers": {
                            "X-User-ID": "n8n_user"
                        }
                    }
                },
                "name": "Check Task Status",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "conditions": {
                        "string": [
                            {
                                "value1": "={{$json[\"status\"]}}",
                                "operation": "equal",
                                "value2": "FINISHED"
                            }
                        ]
                    }
                },
                "name": "Task Completed?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 1,
                "position": [900, 300]
            },
            {
                "parameters": {
                    "url": "=http://localhost:8000/api/v1/task/{{$json[\"task_id\"]}}}",
                    "options": {
                        "headers": {
                            "X-User-ID": "n8n_user"
                        }
                    }
                },
                "name": "Get Task Results",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [1120, 200]
            },
            {
                "parameters": {
                    "amount": 5,
                    "unit": "seconds"
                },
                "name": "Wait 5 Seconds",
                "type": "n8n-nodes-base.wait",
                "typeVersion": 1,
                "position": [1120, 400]
            }
        ],
        "connections": {
            "Start": {
                "main": [
                    [
                        {
                            "node": "Create Browser Task",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Create Browser Task": {
                "main": [
                    [
                        {
                            "node": "Check Task Status",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Check Task Status": {
                "main": [
                    [
                        {
                            "node": "Task Completed?",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Task Completed?": {
                "main": [
                    [
                        {
                            "node": "Get Task Results",
                            "type": "main",
                            "index": 0
                        }
                    ],
                    [
                        {
                            "node": "Wait 5 Seconds",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Wait 5 Seconds": {
                "main": [
                    [
                        {
                            "node": "Check Task Status",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
    }
    
    # Save workflow to file
    with open("n8n_browser_automation_workflow.json", "w") as f:
        json.dump(n8n_workflow, f, indent=2)
    
    print(f"✅ n8n Workflow JSON generated!")
    print(f"   File: n8n_browser_automation_workflow.json")
    print(f"   Nodes: {len(n8n_workflow['nodes'])}")
    print(f"   Import this file into n8n to use the workflow")
    
    return n8n_workflow

def main():
    """Main n8n integration demonstration"""
    
    print("=" * 80)
    print("Browser-Use Local Bridge API - n8n Integration Examples")
    print("=" * 80)
    
    try:
        # Pattern 1: Simple workflow
        task_id, result = demonstrate_n8n_workflow_patterns()
        
        # Pattern 2: Generate n8n workflow
        workflow_json = generate_n8n_workflow_json()
        
        print("\n" + "=" * 80)
        print("n8n Integration Examples Completed! 🎉")
        print()
        print("📋 Key Takeaways for n8n Integration:")
        print("   1. Use HTTP Request nodes to call the API endpoints")
        print("   2. Set X-User-ID header for user identification")
        print("   3. Use polling with Wait nodes for task completion")
        print("   4. Process JSON responses with Set/Code nodes")
        print("   5. Handle errors with IF nodes and error workflows")
        print()
        print("📁 Files Generated:")
        print("   • n8n_browser_automation_workflow.json - Import into n8n")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Integration demo failed: {e}")

if __name__ == "__main__":
    main() 