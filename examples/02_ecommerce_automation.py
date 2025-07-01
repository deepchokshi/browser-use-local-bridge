#!/usr/bin/env python3
"""
Example 2: E-Commerce Automation with Browser-Use Local Bridge
==============================================================

This example demonstrates advanced browser automation for e-commerce scenarios:
- Product search and comparison
- Form interactions and data extraction
- Cookie handling and session management
- Multiple page navigation

Use case: Amazon product search, price comparison, and wishlist management
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "ecommerce_user"


class ECommerceAutomationClient:
    """Client specialized for e-commerce automation tasks"""
    
    def __init__(self, base_url: str = API_BASE_URL, user_id: str = USER_ID):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    async def create_task_with_session_persistence(self, task: str, **config) -> Dict[str, Any]:
        """Create task with browser session persistence for multi-step workflows"""
        # Configure browser to maintain session data
        browser_config = config.get('browser_config', {})
        browser_config.update({
            "user_data_dir": f"./browser_data/{self.user_id}_ecommerce",
            "enable_screenshots": True,
            "viewport_width": 1400,
            "viewport_height": 900
        })
        config['browser_config'] = browser_config
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/run-task",
                json={"task": task, **config},
                headers=self.headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def wait_for_task(self, task_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for task completion with extended timeout for complex operations"""
        start_time = time.time()
        last_step = ""
        
        while time.time() - start_time < timeout:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/task/{task_id}/status",
                    headers=self.headers
                )
                status = response.json()
            
            current_step = status.get('current_step', '')
            if current_step != last_step:
                print(f"🔄 Progress: {status['progress_percentage']:.1f}% - {current_step}")
                last_step = current_step
            
            if status['status'] in ['FINISHED', 'FAILED', 'STOPPED']:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/task/{task_id}",
                        headers=self.headers
                    )
                return response.json()
            
            await asyncio.sleep(3)
        
        raise TimeoutError(f"Task {task_id} timeout")
    
    async def get_task_cookies(self, task_id: str) -> List[Dict[str, Any]]:
        """Extract cookies from completed task for session analysis"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/task/{task_id}/cookies",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get('cookies', [])
            return []


async def product_search_and_comparison():
    """
    Example: Search for products across different categories and compare prices
    """
    client = ECommerceAutomationClient()
    
    print("🛍️  Example 2a: Product Search and Price Comparison")
    print("=" * 60)
    
    search_task = """
    Navigate to Amazon.com and perform the following product research:
    
    1. Search for 'wireless bluetooth headphones under $100'
    2. Filter results by customer rating (4+ stars) and price range ($30-$100)
    3. Extract details for the top 5 products including:
       - Product name and brand
       - Price and any discounts
       - Customer rating and number of reviews
       - Key features from the product title
       - Availability status
    4. Take screenshots of the search results
    
    Present the results in a structured format for easy comparison.
    """
    
    task_config = {
        "browser_config": {
            "headless": False,  # Show browser for demo purposes
            "user_data_dir": "./browser_data/amazon_session",
            "enable_screenshots": True,
            "timeout": 45000
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.2
        },
        "agent_config": {
            "max_actions_per_step": 15,
            "max_failures": 5,
            "retry_delay": 3.0
        }
    }
    
    try:
        print("🚀 Starting product search and comparison...")
        task = await client.create_task_with_session_persistence(search_task, **task_config)
        task_id = task["id"]
        
        print(f"✅ Task created: {task_id}")
        result = await client.wait_for_task(task_id)
        
        if result['status'] == 'FINISHED':
            print("✅ Product research completed successfully!")
            
            # Display basic results
            if result.get('result'):
                print(f"\n📋 Task Result:")
                if isinstance(result['result'], str):
                    print(result['result'])
                else:
                    print(json.dumps(result['result'], indent=2))
            
            # Show media files
            media_files = result.get('media', [])
            if media_files:
                print(f"\n📸 Generated {len(media_files)} screenshots:")
                for media in media_files:
                    print(f"   • {media['filename']} ({media['size_bytes']} bytes)")
        
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in product search: {e}")
        return None


async def shopping_cart_automation():
    """
    Example: Automated shopping cart management and checkout preparation
    """
    client = ECommerceAutomationClient()
    
    print("\n🛒 Example 2b: Shopping Cart Automation")
    print("=" * 50)
    
    cart_task = """
    Perform automated shopping cart management on Amazon:
    
    1. Search for 'desk organizer' and 'wireless mouse pad'
    2. Add the top-rated product from each search to the cart
    3. Navigate to the shopping cart
    4. Review cart contents and calculate total price
    5. Update quantities if needed (set desk organizer to 2 units)
    6. Apply any available coupons or promotional codes
    7. Proceed to checkout preparation (stop before actual purchase)
    8. Extract shipping options and estimated delivery dates
    
    Document each step with screenshots and provide a summary of the cart state.
    """
    
    task_config = {
        "browser_config": {
            "headless": False,
            "enable_screenshots": True,
            "user_data_dir": "./browser_data/amazon_cart_session"
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1
        },
        "agent_config": {
            "max_actions_per_step": 20,
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "cart_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_name": {"type": "string"},
                                    "quantity": {"type": "integer"},
                                    "unit_price": {"type": "string"},
                                    "total_price": {"type": "string"},
                                    "availability": {"type": "string"}
                                }
                            }
                        },
                        "cart_summary": {
                            "type": "object",
                            "properties": {
                                "subtotal": {"type": "string"},
                                "shipping": {"type": "string"},
                                "tax": {"type": "string"},
                                "total": {"type": "string"},
                                "savings": {"type": "string"}
                            }
                        },
                        "shipping_options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "method": {"type": "string"},
                                    "cost": {"type": "string"},
                                    "estimated_delivery": {"type": "string"}
                                }
                            }
                        },
                        "coupons_applied": {"type": "array", "items": {"type": "string"}},
                        "checkout_ready": {"type": "boolean"}
                    }
                }
            }
        }
    }
    
    try:
        print("🚀 Starting shopping cart automation...")
        task = await client.create_task_with_session_persistence(cart_task, **task_config)
        task_id = task["id"]
        
        result = await client.wait_for_task(task_id, timeout=800)
        
        if result['status'] == 'FINISHED':
            print("✅ Shopping cart automation completed!")
            
            if result.get('result'):
                data = result['result']
                
                # Display cart items
                cart_items = data.get('cart_items', [])
                print(f"\n🛒 Cart Contents ({len(cart_items)} items):")
                for item in cart_items:
                    print(f"   📦 {item.get('product_name', 'Unknown')}")
                    print(f"      Quantity: {item.get('quantity', 1)} × {item.get('unit_price', 'N/A')}")
                    print(f"      Total: {item.get('total_price', 'N/A')}")
                    print(f"      Status: {item.get('availability', 'Unknown')}")
                
                # Display cart summary
                summary = data.get('cart_summary', {})
                if summary:
                    print(f"\n💰 Cart Summary:")
                    print(f"   Subtotal: {summary.get('subtotal', 'N/A')}")
                    print(f"   Shipping: {summary.get('shipping', 'N/A')}")
                    print(f"   Tax: {summary.get('tax', 'N/A')}")
                    print(f"   Total: {summary.get('total', 'N/A')}")
                    if summary.get('savings'):
                        print(f"   💸 Savings: {summary['savings']}")
                
                # Display shipping options
                shipping = data.get('shipping_options', [])
                if shipping:
                    print(f"\n🚚 Shipping Options:")
                    for option in shipping:
                        print(f"   • {option.get('method', 'Standard')}: {option.get('cost', 'Free')}")
                        print(f"     Delivery: {option.get('estimated_delivery', 'Unknown')}")
                
                # Display applied coupons
                coupons = data.get('coupons_applied', [])
                if coupons:
                    print(f"\n🎟️  Applied Coupons: {', '.join(coupons)}")
                
                print(f"\n✅ Checkout Ready: {data.get('checkout_ready', False)}")
        
        # Extract and display session cookies
        cookies = await client.get_task_cookies(task_id)
        if cookies:
            print(f"\n🍪 Session cookies captured: {len(cookies)} cookies")
            session_cookies = [c for c in cookies if 'session' in c.get('name', '').lower()]
            if session_cookies:
                print(f"   🔐 Session cookies: {len(session_cookies)}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in cart automation: {e}")
        return None


async def price_monitoring_setup():
    """
    Example: Set up price monitoring for multiple products
    """
    client = ECommerceAutomationClient()
    
    print("\n📈 Example 2c: Price Monitoring Setup")
    print("=" * 45)
    
    monitoring_task = """
    Set up price monitoring for multiple products:
    
    1. Visit Amazon and search for these products:
       - "MacBook Air M2"
       - "Sony WH-1000XM5 headphones"
       - "iPad Pro 12.9 inch"
    
    2. For each product, find the current best deal and extract:
       - Current price and any active discounts
       - Historical price information if visible
       - Stock availability
       - Seller information (sold by Amazon vs third party)
       - Prime shipping eligibility
    
    3. Create a monitoring report with price alerts recommendations
    4. Take screenshots of each product page for reference
    
    Return structured data suitable for automated price tracking.
    """
    
    task_config = {
        "browser_config": {
            "headless": True,
            "enable_screenshots": True
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "agent_config": {
            "controller_config": {
                "output_model_schema": {
                    "type": "object",
                    "properties": {
                        "monitored_products": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_name": {"type": "string"},
                                    "current_price": {"type": "string"},
                                    "original_price": {"type": "string"},
                                    "discount_percentage": {"type": "string"},
                                    "stock_status": {"type": "string"},
                                    "seller": {"type": "string"},
                                    "prime_eligible": {"type": "boolean"},
                                    "product_url": {"type": "string"},
                                    "asin": {"type": "string"},
                                    "last_checked": {"type": "string"}
                                }
                            }
                        },
                        "price_alerts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product": {"type": "string"},
                                    "suggested_alert_price": {"type": "string"},
                                    "current_discount": {"type": "string"},
                                    "recommendation": {"type": "string"}
                                }
                            }
                        },
                        "monitoring_summary": {
                            "type": "object",
                            "properties": {
                                "total_products": {"type": "integer"},
                                "products_on_sale": {"type": "integer"},
                                "average_discount": {"type": "string"},
                                "best_deal": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        print("🚀 Setting up price monitoring...")
        task = await client.create_task_with_session_persistence(monitoring_task, **task_config)
        task_id = task["id"]
        
        result = await client.wait_for_task(task_id)
        
        if result['status'] == 'FINISHED' and result.get('result'):
            data = result['result']
            
            products = data.get('monitored_products', [])
            print(f"\n📊 Price Monitoring Report ({len(products)} products):")
            
            for product in products:
                print(f"\n📱 {product.get('product_name', 'Unknown Product')}")
                print(f"   💰 Price: {product.get('current_price', 'N/A')}")
                if product.get('original_price'):
                    print(f"   🏷️  Original: {product['original_price']} ({product.get('discount_percentage', '0')}% off)")
                print(f"   📦 Stock: {product.get('stock_status', 'Unknown')}")
                print(f"   🏪 Seller: {product.get('seller', 'Unknown')}")
                print(f"   🚚 Prime: {'✅' if product.get('prime_eligible') else '❌'}")
            
            # Display price alerts
            alerts = data.get('price_alerts', [])
            if alerts:
                print(f"\n🔔 Price Alert Recommendations:")
                for alert in alerts:
                    print(f"   • {alert.get('product', 'Unknown')}")
                    print(f"     Alert at: {alert.get('suggested_alert_price', 'N/A')}")
                    print(f"     Reason: {alert.get('recommendation', 'N/A')}")
            
            # Display summary
            summary = data.get('monitoring_summary', {})
            if summary:
                print(f"\n📈 Summary:")
                print(f"   Total products monitored: {summary.get('total_products', 0)}")
                print(f"   Products currently on sale: {summary.get('products_on_sale', 0)}")
                print(f"   Average discount: {summary.get('average_discount', '0%')}")
                if summary.get('best_deal'):
                    print(f"   🏆 Best deal: {summary['best_deal']}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error in price monitoring setup: {e}")
        return None


async def main():
    """Run all e-commerce automation examples"""
    print("🛍️  Browser-Use Local Bridge - E-Commerce Automation Examples")
    print("=" * 70)
    
    # Check API availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print(f"❌ API not available: {response.status_code}")
                return
            print("✅ API is ready")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run examples
    print("\n" + "="*70)
    await product_search_and_comparison()
    
    print("\n" + "="*70)
    await shopping_cart_automation()
    
    print("\n" + "="*70)
    await price_monitoring_setup()
    
    print("\n✨ All e-commerce automation examples completed!")
    print("\n💡 These examples demonstrate:")
    print("   • Advanced product research and comparison")
    print("   • Shopping cart and checkout flow automation")
    print("   • Price monitoring and alert configuration")
    print("   • Session persistence and cookie management")
    print("   • Structured data extraction from e-commerce sites")


if __name__ == "__main__":
    asyncio.run(main()) 