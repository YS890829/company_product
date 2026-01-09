"""
Gemini API Helper Functions

Provides convenience functions for common Gemini API operations
with auto-fallback support.

Phase 2 Implementation: 2025-10-21
"""

import logging
from typing import Optional, Any, Dict, List
import google.generativeai as genai

from .gemini_client import GeminiClient, create_gemini_client

# Configure logger
logger = logging.getLogger(__name__)

# Global client instance (lazy initialization)
_global_client: Optional[GeminiClient] = None


def get_global_client() -> GeminiClient:
    """
    Get or create global GeminiClient instance.

    Returns:
        Shared GeminiClient instance

    Example:
        client = get_global_client()
        response = client.generate_content("Hello!")
    """
    global _global_client

    if _global_client is None:
        _global_client = create_gemini_client()

    return _global_client


def generate_with_fallback(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.1,
    response_mime_type: Optional[str] = None,
    enable_fallback: bool = True
) -> str:
    """
    Generate text content with automatic fallback.

    Args:
        prompt: Prompt text
        model_name: Model name (default: gemini-2.5-flash)
        temperature: Temperature for generation (default: 0.1)
        response_mime_type: Response MIME type (e.g., "application/json")
        enable_fallback: Whether to enable auto-fallback

    Returns:
        Generated text

    Example:
        # Basic usage
        text = generate_with_fallback("What is AI?")

        # JSON output
        json_text = generate_with_fallback(
            prompt="Generate JSON...",
            response_mime_type="application/json"
        )
    """
    client = get_global_client()

    generation_config = {"temperature": temperature}
    if response_mime_type:
        generation_config["response_mime_type"] = response_mime_type

    response = client.generate_content(
        prompt=prompt,
        model_name=model_name,
        generation_config=generation_config,
        enable_fallback=enable_fallback
    )

    return response.text


def generate_with_audio(
    audio_data: bytes,
    mime_type: str,
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.1,
    response_mime_type: Optional[str] = None,
    enable_fallback: bool = True
) -> str:
    """
    Generate content from audio with automatic fallback.

    Args:
        audio_data: Audio file bytes
        mime_type: Audio MIME type (e.g., "audio/m4a")
        prompt: Prompt text
        model_name: Model name (default: gemini-2.5-flash)
        temperature: Temperature for generation (default: 0.1)
        response_mime_type: Response MIME type (e.g., "application/json")
        enable_fallback: Whether to enable auto-fallback

    Returns:
        Generated text

    Example:
        with open("audio.m4a", "rb") as f:
            audio_bytes = f.read()

        transcription = generate_with_audio(
            audio_data=audio_bytes,
            mime_type="audio/m4a",
            prompt="Transcribe this audio...",
            response_mime_type="application/json"
        )
    """
    client = get_global_client()

    generation_config = {"temperature": temperature}
    if response_mime_type:
        generation_config["response_mime_type"] = response_mime_type

    # Note: For audio/multimodal content, we need to use genai directly
    # The GeminiClient handles API key configuration and fallback
    from .config import GEMINI_API_KEY_FREE, GEMINI_API_KEY_PAID, USE_PAID_TIER

    # Determine which key to use
    use_paid = USE_PAID_TIER
    api_key = GEMINI_API_KEY_PAID if use_paid else GEMINI_API_KEY_FREE

    if not api_key:
        # Try alternate key
        api_key = GEMINI_API_KEY_FREE if use_paid else GEMINI_API_KEY_PAID
        if not api_key:
            raise ValueError("No Gemini API key available")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    try:
        response = model.generate_content(
            [prompt, {"mime_type": mime_type, "data": audio_data}],
            generation_config=generation_config
        )

        # Log usage through client
        client._log_usage(
            model_name=model_name,
            tier_used="paid" if use_paid else "free",
            was_fallback=False
        )

        if use_paid:
            client.usage_stats["paid_tier_calls"] += 1
        else:
            client.usage_stats["free_tier_calls"] += 1
        client.usage_stats["total_calls"] += 1

        return response.text

    except Exception as e:
        # Log error
        client._log_usage(
            model_name=model_name,
            tier_used="paid" if use_paid else "free",
            was_fallback=False,
            error=str(e)
        )

        # If fallback enabled and quota error, try alternate tier
        if enable_fallback and "quota" in str(e).lower():
            logger.warning(f"Quota exhausted on {'paid' if use_paid else 'free'} tier, attempting fallback...")

            alternate_key = GEMINI_API_KEY_FREE if use_paid else GEMINI_API_KEY_PAID
            if not alternate_key:
                raise

            genai.configure(api_key=alternate_key)
            model = genai.GenerativeModel(model_name)

            response = model.generate_content(
                [prompt, {"mime_type": mime_type, "data": audio_data}],
                generation_config=generation_config
            )

            # Log fallback usage
            client._log_usage(
                model_name=model_name,
                tier_used="free" if use_paid else "paid",
                was_fallback=True
            )

            client.usage_stats["fallback_count"] += 1
            if use_paid:
                client.usage_stats["free_tier_calls"] += 1
            else:
                client.usage_stats["paid_tier_calls"] += 1
            client.usage_stats["total_calls"] += 1

            logger.info("✅ Fallback successful!")
            return response.text

        raise


def print_usage_summary():
    """
    Print usage summary for the global client.

    Example:
        # After some API calls
        print_usage_summary()
    """
    client = get_global_client()
    client.print_usage_summary()


# ==================== Backward Compatibility ====================

def get_api_key() -> str:
    """
    Get Gemini API key (backward compatibility).

    This function maintains backward compatibility with existing code
    that directly accesses API keys.

    Returns:
        API key string
    """
    from .config import get_gemini_api_key
    return get_gemini_api_key()


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example 1: Simple text generation
    text = generate_with_fallback("What is the capital of France?")
    print(f"Response: {text}")

    # Example 2: JSON generation
    json_response = generate_with_fallback(
        prompt='Generate a JSON object: {"name": "John", "age": 30}',
        response_mime_type="application/json"
    )
    print(f"JSON: {json_response}")

    # Example 3: Print usage
    print_usage_summary()
