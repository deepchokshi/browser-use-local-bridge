#!/usr/bin/env python3
"""
Example 1: Basic Web Search with Browser-Use Local Bridge
==========================================================

This example demonstrates the fundamental features of the browser-use local bridge:
- Creating and running a basic browser automation task
- Monitoring task progress and status
- Retrieving task results and screenshots

Use case: Automated Google search with result extraction
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "example_user_01"


class BrowserUseClient:
    """Simple client for Browser-Use Local Bridge API"""
    
    def __init__(self, base_url: str = API_BASE_URL, user_id: str = USER_ID):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    async def create_and_run_task(self, task: str, **config) -> Dict[str, Any]:
        """Create and immediately start a browser automation task"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/run-task",
                json={"task": task, **config},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current task status and progress"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/task/{task_id}/status",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get complete task details including results"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/task/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for task to complete with progress monitoring"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = await self.get_task_status(task_id)
            
            print(f"⏳ Task {task_id}: {status['status']} ({status['progress_percentage']:.1f}%)")
            
            if status['status'] in ['FINISHED', 'FAILED', 'STOPPED']:
                return await self.get_task_details(task_id)
            
            if status.get('current_step'):
                print(f"   Current step: {status['current_step']}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")


async def basic_web_search_example():
    """
    Example: Perform a Google search and extract the first few results
    """
    client = BrowserUseClient()
    
    print("🔍 Example 1: Basic Web Search")
    print("=" * 50)
    
    # Define the browser automation task
    search_task = """
    Navigate to Google.com and search for 'browser automation with AI'.
    Extract the first 3 search result titles and URLs.
    Take a screenshot of the search results page.
    """
    
    # Configure browser and AI settings
    task_config = {
        "browser_config": {
            "headless": True,  # Run in headless mode
            "viewport_width": 1920,
            "viewport_height": 1080,
            "enable_screenshots": True,
            "enable_recordings": False
        },
        "llm_config": {
            "provider": "openai",  # Using OpenAI as the AI provider
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "metadata": {
            "example": "basic_web_search",
            "purpose": "Demonstrate core browser automation functionality"
        }
    }
    
    try:
        # Step 1: Create and start the task
        print("🚀 Creating and starting browser automation task...")
        task = await client.create_and_run_task(search_task, **task_config)
        task_id = task["id"]
        
        print(f"✅ Task created with ID: {task_id}")
        print(f"📝 Task description: {task['task']}")
        print(f"🤖 Using {task['llm_config']['provider']} ({task['llm_config']['model']})")
        
        # Step 2: Monitor task progress
        print("\n📊 Monitoring task progress...")
        result = await client.wait_for_completion(task_id)
        
        # Step 3: Display results
        print(f"\n🎯 Task completed with status: {result['status']}")
        
        if result['status'] == 'FINISHED':
            print("✅ SUCCESS! Task completed successfully")
            
            # Display task result
            if result.get('result'):
                print(f"\n📋 Task Result:")
                if isinstance(result['result'], str):
                    print(result['result'])
                else:
                    print(json.dumps(result['result'], indent=2))
            
            # Display execution metrics
            if result.get('execution_time_seconds'):
                print(f"\n⏱️  Execution Time: {result['execution_time_seconds']:.2f} seconds")
            
            if result.get('steps'):
                print(f"\n📝 Task executed {len(result['steps'])} steps:")
                for i, step in enumerate(result['steps'][-5:], 1):  # Show last 5 steps
                    print(f"   {i}. {step['action']}: {step['description']}")
            
            # Show media files if available
            if result.get('media'):
                print(f"\n📸 Generated {len(result['media'])} media files:")
                for media in result['media']:
                    print(f"   - {media['filename']} ({media['media_type']}, {media['size_bytes']} bytes)")
                    print(f"     Download: {API_BASE_URL}/api/v1/media/{task_id}/{media['filename']}")
        
        else:
            print(f"❌ Task failed with error: {result.get('error', 'Unknown error')}")
            
            # Show error details
            error_steps = [step for step in result.get('steps', []) if step.get('error')]
            if error_steps:
                print("\n🔍 Error details:")
                for step in error_steps:
                    print(f"   - {step['action']}: {step['error']}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return None


async def structured_search_example():
    """
    Example: Search with structured output using controller configuration
    """
    client = BrowserUseClient()
    
    print("\n🎯 Example 1b: Structured Web Search")
    print("=" * 50)
    
    # Task with structured output requirements
    search_task = """
    Search for 'Python web frameworks 2024' on Google.
    Extract and return a structured list of the top 5 search results.
    """
    
    # Configure for structured output
    task_config = {
        "browser_config": {
            "headless": True,
            "enable_screenshots": True
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "agent_config": {
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "search_results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "snippet": {"type": "string"}
                                },
                                "required": ["title", "url"]
                            }
                        },
                        "search_query": {"type": "string"},
                        "total_results_found": {"type": "integer"}
                    },
                    "required": ["search_results", "search_query"]
                },
                "validate_output": True,
                "output_instructions": "Return the search results as a structured JSON object"
            }
        }
    }
    
    try:
        print("🚀 Creating structured search task...")
        task = await client.create_and_run_task(search_task, **task_config)
        task_id = task["id"]
        
        print(f"✅ Task created: {task_id}")
        result = await client.wait_for_completion(task_id)
        
        if result['status'] == 'FINISHED' and result.get('result'):
            print("\n📊 Structured Results:")
            if isinstance(result['result'], dict):
                search_results = result['result'].get('search_results', [])
                print(f"Query: {result['result'].get('search_query', 'N/A')}")
                print(f"Found {len(search_results)} results:")
                
                for i, item in enumerate(search_results, 1):
                    print(f"\n{i}. {item.get('title', 'No title')}")
                    print(f"   URL: {item.get('url', 'No URL')}")
                    if item.get('snippet'):
                        print(f"   Snippet: {item['snippet'][:100]}...")
            else:
                print(result['result'])
        
        return result
        
    except Exception as e:
        print(f"💥 Error in structured search: {e}")
        return None


async def main():
    """Run both basic and structured search examples"""
    print("🌐 Browser-Use Local Bridge - Basic Web Search Examples")
    print("=" * 60)
    
    # Check API health first
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                print("✅ API is healthy and ready")
            else:
                print(f"⚠️  API health check failed: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure the server is running at {API_BASE_URL}")
        return
    
    # Run examples
    await basic_web_search_example()
    await structured_search_example()
    
    print("\n✨ Examples completed!")
    print(f"\n💡 Tip: You can view the API documentation at {API_BASE_URL}/docs")


if __name__ == "__main__":
    asyncio.run(main()) 