import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def query_groq_llm(prompt: str, max_retries: int = 3, timeout: int = 30) -> str:
    """
    Query Groq LLM with enhanced error handling and fallback options.
    
    Args:
        prompt: The text prompt to send to the LLM
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        str: LLM response or fallback message
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return get_fallback_summary(prompt)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 1000
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting Groq API call (attempt {attempt + 1}/{max_retries})")
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()["choices"][0]["message"]["content"]
            logger.info("Groq API call successful")
            return result
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return get_fallback_summary(prompt)
            continue
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return get_fallback_summary(prompt)
            continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return get_fallback_summary(prompt)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return get_fallback_summary(prompt)
    
    # Fallback if all retries failed
    return get_fallback_summary(prompt)

def get_fallback_summary(text: str) -> str:
    """
    Generate a fallback summary when Groq API is unavailable.
    
    Args:
        text: The text to summarize
    
    Returns:
        str: A basic summary or informative message
    """
    # Remove the fallback message if it's already in the text
    if "❌ GROQ_API_KEY not set" in text or "❌ Groq API error" in text:
        return "⚠️ **Offline Mode**: Groq API is currently unavailable. Here's a basic summary:\n\n" + create_basic_summary(text)
    
    return create_basic_summary(text)

def create_basic_summary(text: str) -> str:
    """
    Create a basic summary without using external APIs.
    
    Args:
        text: The text to summarize
    
    Returns:
        str: A basic summary
    """
    if not text or len(text.strip()) < 50:
        return "📄 **Document Summary**: Text is too short to summarize meaningfully."
    
    # Basic text analysis
    lines = text.strip().split('\n')
    words = text.split()
    
    # Count key metrics
    word_count = len(words)
    line_count = len([line for line in lines if line.strip()])
    
    # Extract first few meaningful lines as preview
    meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 20][:3]
    preview = '\n'.join(meaningful_lines) if meaningful_lines else text[:200] + "..."
    
    # Create summary
    summary = f"""📊 **Document Analysis**:
• **Word Count**: {word_count:,} words
• **Line Count**: {line_count} lines
• **Document Type**: {'PDF' if 'pdf' in text.lower() else 'Image'} document

📝 **Content Preview**:
{preview}

💡 **Note**: This is a basic analysis. For AI-powered summarization, please check your internet connection and Groq API configuration."""

    return summary

def test_groq_connection() -> dict:
    """
    Test Groq API connectivity and return status.
    
    Returns:
        dict: Connection status and details
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY not set in environment",
            "available": False
        }
    
    try:
        # Simple test request
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "Groq API is accessible",
                "available": True
            }
        else:
            return {
                "status": "error",
                "message": f"API returned status {response.status_code}",
                "available": False
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Network connection failed - check internet connectivity",
            "available": False
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Request timed out",
            "available": False
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "available": False
        }
