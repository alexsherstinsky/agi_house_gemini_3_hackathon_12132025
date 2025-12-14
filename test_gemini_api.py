#!/usr/bin/env python
"""Simple test script to verify Gemini API access."""
import os
from langchain_google_genai import ChatGoogleGenerativeAI

def test_gemini_api():
    """Test Gemini API access with a simple prompt."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("✗ GOOGLE_API_KEY environment variable is not set")
        return False
    
    print(f"✓ GOOGLE_API_KEY is set (length: {len(api_key)} characters)")
    
    try:
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Use flash model for quick test
            temperature=0.1,
            google_api_key=api_key,
        )
        
        # Test with a simple prompt
        response = llm.invoke("Say 'API test successful' if you can read this.")
        print(f"✓ Gemini API response received: {response.content[:100]}")
        return True
        
    except Exception as e:
        print(f"✗ Gemini API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    exit(0 if success else 1)

