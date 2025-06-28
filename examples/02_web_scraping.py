#!/usr/bin/env python3
"""
Example 2: Web Scraping with Screenshots
=======================================

This example demonstrates how to:
- Scrape product information from a website
- Take screenshots during the process
- Extract structured data
- Download media files

Prerequisites:
- Browser-Use Local Bridge API running on http://localhost:8000
- Valid OpenAI API key configured
"""

import requests
import time
import json
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "scraper_user"

def create_scraping_task():
    """Create a web scraping task"""
    
    print("🕷️ Creating web scraping task...")
    
    task_data = {
        "task": """
        Navigate to https://quotes.toscrape.com/ and scrape the first 3 quotes.
        For each quote, extract:
        1. The quote text
        2. The author name
        3. The tags
        
        Format the results as a JSON array with this structure:
        [
            {
                "text": "quote text here",
                "author": "author name",
                "tags": ["tag1", "tag2"]
            }
        ]
        
        Take a screenshot after loading the page.
        """,
        "browser_config": {
            "headless": False,  # Set to False to see the browser in action
            "enable_screenshots": True,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "timeout": 30000
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "metadata": {
            "example": "web_scraping",
            "target_site": "quotes.toscrape.com",
            "data_points": ["quotes", "authors", "tags"]
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
        print(f"✅ Scraping task created!")
        print(f"   Task ID: {task_id}")
        print(f"   Target: quotes.toscrape.com")
        return task_id
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def monitor_with_live_updates(task_id):
    """Monitor task with real-time updates"""
    
    print(f"\n📡 Monitoring task with live updates...")
    
    # First, monitor via polling
    while True:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/task/{task_id}/status",
            headers={"X-User-ID": USER_ID}
        )
        
        if response.status_code == 200:
            status = response.json()
            current_status = status['status']
            progress = status['progress_percentage']
            
            print(f"   📊 Status: {current_status} ({progress}%)")
            
            if current_status in ['FINISHED', 'FAILED', 'STOPPED']:
                return current_status
            
            time.sleep(3)
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            break
    
    return None

def download_screenshots(task_id):
    """Download all screenshots from the task"""
    
    print(f"\n📸 Downloading screenshots...")
    
    # Get media files list
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}/media",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        media = response.json()
        
        if media['total_count'] > 0:
            # Create downloads directory
            os.makedirs("downloads", exist_ok=True)
            
            print(f"   Found {media['total_count']} media files")
            
            for media_file in media['media_files']:
                filename = media_file['filename']
                
                # Download the file
                download_response = requests.get(
                    f"{API_BASE_URL}/api/v1/media/{task_id}/{filename}",
                    headers={"X-User-ID": USER_ID}
                )
                
                if download_response.status_code == 200:
                    local_path = os.path.join("downloads", filename)
                    with open(local_path, 'wb') as f:
                        f.write(download_response.content)
                    
                    print(f"   ✅ Downloaded: {filename} ({media_file['size_bytes']} bytes)")
                else:
                    print(f"   ❌ Failed to download: {filename}")
        else:
            print("   No media files found")
    else:
        print(f"❌ Failed to get media list: {response.status_code}")

def parse_scraped_data(task_result):
    """Parse and display the scraped data"""
    
    print(f"\n📊 Parsing scraped data...")
    
    if not task_result.get('result'):
        print("   No result data found")
        return
    
    result_text = task_result['result']
    
    try:
        # Try to extract JSON from the result
        import re
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            quotes_data = json.loads(json_str)
            
            print(f"   ✅ Successfully parsed {len(quotes_data)} quotes:")
            
            for i, quote in enumerate(quotes_data, 1):
                print(f"\n   Quote {i}:")
                print(f"     Text: \"{quote.get('text', 'N/A')}\"")
                print(f"     Author: {quote.get('author', 'N/A')}")
                print(f"     Tags: {', '.join(quote.get('tags', []))}")
        else:
            print("   Raw result (no JSON found):")
            print(f"   {result_text}")
            
    except Exception as e:
        print(f"   ❌ Failed to parse JSON: {e}")
        print(f"   Raw result: {result_text}")

def main():
    """Main scraping example"""
    
    print("=" * 70)
    print("Browser-Use Local Bridge API - Web Scraping Example")
    print("=" * 70)
    
    # Step 1: Create scraping task
    task_id = create_scraping_task()
    if not task_id:
        return
    
    # Step 2: Monitor progress
    final_status = monitor_with_live_updates(task_id)
    if not final_status:
        return
    
    # Step 3: Get results
    response = requests.get(
        f"{API_BASE_URL}/api/v1/task/{task_id}",
        headers={"X-User-ID": USER_ID}
    )
    
    if response.status_code == 200:
        task_result = response.json()
        
        print(f"\n✅ Task completed with status: {task_result['status']}")
        
        # Parse scraped data
        parse_scraped_data(task_result)
        
        # Download screenshots
        download_screenshots(task_id)
        
        print(f"\n📋 Task Summary:")
        print(f"   Duration: {task_result.get('execution_time_seconds', 'N/A')} seconds")
        print(f"   Steps: {len(task_result.get('steps', []))}")
        print(f"   Media files: {len(task_result.get('media', []))}")
        
    else:
        print(f"❌ Failed to get results: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("Web scraping example completed! 🎉")
    print("Check the 'downloads' folder for screenshots.")
    print("=" * 70)

if __name__ == "__main__":
    main() 