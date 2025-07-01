#!/usr/bin/env python3
"""
Example 4: n8n Integration with Browser-Use Local Bridge
========================================================

This example demonstrates how to integrate browser automation with n8n workflows:
- Webhook-triggered browser tasks
- Custom functions for n8n callbacks
- Workflow automation patterns
- Data passing between n8n and browser automation

Use case: n8n workflow triggers browser automation for data extraction
"""

import asyncio
import httpx
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"
USER_ID = "n8n_integration_user"


async def n8n_data_extraction_workflow():
    """
    Example: Browser automation triggered by n8n webhook with data extraction
    """
    print("🔄 Example 4: n8n Integration - Data Extraction Workflow")
    print("=" * 60)
    
    # Simulate n8n webhook payload
    webhook_payload = {
        "trigger": "schedule",
        "workflow_id": "competitor_monitoring",
        "data": {
            "target_websites": [
                "https://example-competitor.com",
                "https://another-competitor.com"
            ],
            "extraction_config": {
                "extract_prices": True,
                "extract_features": True,
                "take_screenshots": True
            }
        }
    }
    
    # Task configured for n8n integration
    extraction_task = f"""
    Execute competitive analysis based on n8n workflow data:
    
    Targets: {webhook_payload['data']['target_websites']}
    
    For each website:
    1. Navigate to the homepage
    2. Look for pricing information
    3. Extract key product features
    4. Take screenshots for documentation
    5. Compile results into structured format
    
    Return data suitable for n8n workflow continuation.
    """
    
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
                        "workflow_id": {"type": "string"},
                        "extraction_results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "website": {"type": "string"},
                                    "pricing_info": {"type": "object"},
                                    "features": {"type": "array"},
                                    "screenshot_path": {"type": "string"},
                                    "extraction_timestamp": {"type": "string"}
                                }
                            }
                        },
                        "n8n_callback_data": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "next_action": {"type": "string"},
                                "summary": {"type": "string"}
                            }
                        }
                    }
                },
                "custom_functions": [
                    {
                        "name": "n8n_callback",
                        "description": "Send results back to n8n workflow via webhook",
                        "implementation_type": "webhook",
                        "webhook_url": "http://localhost:5678/webhook/browser-automation-complete",
                        "async_execution": True
                    }
                ]
            }
        },
        "metadata": {
            "workflow_id": webhook_payload["workflow_id"],
            "n8n_integration": True
        }
    }
    
    headers = {"Content-Type": "application/json", "X-User-ID": USER_ID}
    
    try:
        print("🚀 Creating n8n-triggered browser task...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/run-task",
                json={"task": extraction_task, **task_config},
                headers=headers,
                timeout=60.0
            )
            task = response.json()
            task_id = task["id"]
            
            print(f"✅ Task created: {task_id}")
            print(f"🔄 Monitoring task for n8n workflow: {webhook_payload['workflow_id']}")
            
            # Monitor task completion
            while True:
                status_response = await client.get(
                    f"{API_BASE_URL}/api/v1/task/{task_id}/status",
                    headers=headers
                )
                status = status_response.json()
                
                print(f"📊 Status: {status['status']} ({status['progress_percentage']:.1f}%)")
                
                if status['status'] in ['FINISHED', 'FAILED', 'STOPPED']:
                    break
                
                await asyncio.sleep(3)
            
            # Get final results
            result_response = await client.get(
                f"{API_BASE_URL}/api/v1/task/{task_id}",
                headers=headers
            )
            result = result_response.json()
            
            if result['status'] == 'FINISHED':
                print("✅ n8n workflow automation completed!")
                
                if result.get('result'):
                    data = result['result']
                    
                    # Display extraction results
                    extractions = data.get('extraction_results', [])
                    print(f"\n📊 Extracted data from {len(extractions)} websites:")
                    
                    for extraction in extractions:
                        print(f"\n🌐 {extraction.get('website', 'Unknown')}")
                        
                        pricing = extraction.get('pricing_info', {})
                        if pricing:
                            print(f"   💰 Pricing: {json.dumps(pricing, indent=6)}")
                        
                        features = extraction.get('features', [])
                        if features:
                            print(f"   🔧 Features: {', '.join(features[:3])}...")
                    
                    # Show n8n callback data
                    callback = data.get('n8n_callback_data', {})
                    if callback:
                        print(f"\n🔄 n8n Callback:")
                        print(f"   Status: {callback.get('status', 'N/A')}")
                        print(f"   Next Action: {callback.get('next_action', 'N/A')}")
                        print(f"   Summary: {callback.get('summary', 'N/A')}")
            
            else:
                print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            
            return result
            
    except Exception as e:
        print(f"💥 Error in n8n integration: {e}")
        return None


async def main():
    """Run n8n integration example"""
    print("🔄 Browser-Use Local Bridge - n8n Integration Example")
    print("=" * 60)
    
    # Check API health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print("❌ API not available")
                return
            print("✅ API is ready")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    await n8n_data_extraction_workflow()
    
    print("\n✨ n8n integration example completed!")
    print("\n💡 This example shows:")
    print("   • Webhook-triggered browser automation")
    print("   • Structured data extraction for workflows")
    print("   • Custom functions for n8n callbacks")
    print("   • Workflow integration patterns")


if __name__ == "__main__":
    asyncio.run(main()) 