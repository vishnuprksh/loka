#!/usr/bin/env python3
"""
Standalone script to test the google/gemma-4-26b-a4b-it:free model on OpenRouter.
"""

import os
import sys
import json
import requests
from datetime import datetime


def test_gemma_model(api_key: str, model: str = "qwen/qwen3.6-plus") -> None:
    """
    Test the specified model on OpenRouter.
    
    Args:
        api_key: OpenRouter API key
        model: Model identifier (default: google/gemma-4-26b-a4b-it:free)
    """
    
    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Test message
    test_message = "Write a brief greeting as if you're an NPC in a virtual world called 'Loka'. Keep it under 50 words."
    
    # Request payload
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": test_message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 150,
    }
    
    print("=" * 70)
    print(f"Testing OpenRouter Model: {model}")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test prompt: {test_message}\n")
    
    try:
        print("🔄 Sending request to OpenRouter...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check response status
        if response.status_code == 200:
            print("✅ Request successful (HTTP 200)\n")
            
            result = response.json()
            
            # Extract the response content
            if "choices" in result and len(result["choices"]) > 0:
                assistant_message = result["choices"][0]["message"]["content"]
                print("Model Response:")
                print("-" * 70)
                print(assistant_message)
                print("-" * 70)
                
                # Display usage stats if available
                if "usage" in result:
                    usage = result["usage"]
                    print(f"\nUsage Statistics:")
                    print(f"  Input tokens: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"  Output tokens: {usage.get('completion_tokens', 'N/A')}")
                    print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
                
                print("\n✅ Model is working correctly!")
                return True
            else:
                print("❌ Unexpected response format (no choices)")
                print("Full response:", json.dumps(result, indent=2))
                return False
                
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (30 seconds exceeded)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - cannot reach OpenRouter API")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return False
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response")
        print(f"Response text: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    
    # Get API key from argument or environment variable
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ Error: API key not provided")
        print("\nUsage:")
        print("  python test_gemma_model.py <API_KEY>")
        print("  OR set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    # Run the test
    success = test_gemma_model(api_key)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Model test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Model test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
