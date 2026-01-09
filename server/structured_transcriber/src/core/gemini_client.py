"""
Gemini API Client with Auto-Fallback Support

This module provides a unified interface for Gemini API calls with:
- Automatic fallback from free tier to paid tier on quota exhaustion
- Request tracking and cost monitoring
- Comprehensive error handling

Phase 2 Implementation: 2025-10-21
"""

import logging
import time
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import json
from pathlib import Path

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .config import (
    GEMINI_API_KEY_FREE,
    GEMINI_API_KEY_PAID,
    USE_PAID_TIER,
    LOG_DIR,
)
from .error_handlers import retry_gemini_api_call, APIErrorHandler

# Configure logger
logger = logging.getLogger(__name__)

# Usage tracking file
USAGE_TRACKING_FILE = Path(LOG_DIR) / "gemini_usage_tracking.jsonl"


class GeminiClient:
    """
    Unified Gemini API client with auto-fallback support.

    Features:
    - Automatically tries free tier first (unless USE_PAID_TIER=true)
    - Falls back to paid tier on quota exhaustion
    - Tracks API usage and costs
    - Provides detailed logging

    Example:
        client = GeminiClient()
        response = client.generate_content(
            prompt="Hello, world!",
            model_name="gemini-2.5-flash"
        )
    """

    def __init__(self):
        """Initialize Gemini client with both free and paid API keys."""
        self.free_key = GEMINI_API_KEY_FREE
        self.paid_key = GEMINI_API_KEY_PAID
        self.use_paid_tier = USE_PAID_TIER

        # Validate API keys
        if not self.free_key and not self.paid_key:
            raise ValueError("At least one Gemini API key (free or paid) must be configured")

        # Initialize tracking
        self.usage_stats = {
            "free_tier_calls": 0,
            "paid_tier_calls": 0,
            "fallback_count": 0,
            "total_calls": 0,
        }

        logger.info(f"GeminiClient initialized - USE_PAID_TIER: {self.use_paid_tier}")
        logger.info(f"Free key available: {bool(self.free_key)}, Paid key available: {bool(self.paid_key)}")

    def _configure_api_key(self, use_paid: bool) -> bool:
        """
        Configure genai with appropriate API key.

        Args:
            use_paid: Whether to use paid tier key

        Returns:
            True if key was successfully configured, False otherwise
        """
        key = self.paid_key if use_paid else self.free_key

        if not key:
            logger.warning(f"{'Paid' if use_paid else 'Free'} tier key not available")
            return False

        genai.configure(api_key=key)
        return True

    def _log_usage(
        self,
        model_name: str,
        tier_used: str,
        was_fallback: bool,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log API usage to tracking file.

        Args:
            model_name: Name of the model used
            tier_used: "free" or "paid"
            was_fallback: Whether this was a fallback call
            tokens_used: Number of tokens used (if available)
            error: Error message if call failed
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "tier": tier_used,
            "was_fallback": was_fallback,
            "tokens": tokens_used,
            "error": error,
        }

        # Ensure log directory exists
        USAGE_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Append to tracking file
        with open(USAGE_TRACKING_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    @retry_gemini_api_call(max_attempts=3, min_wait=2, max_wait=60)
    def _call_api(
        self,
        model_name: str,
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None,
        use_paid: bool = False
    ) -> Any:
        """
        Internal API call with retry logic.

        Args:
            model_name: Model to use
            prompt: Prompt text
            generation_config: Generation configuration
            use_paid: Whether to use paid tier

        Returns:
            API response

        Raises:
            google_exceptions.ResourceExhausted: If quota is exhausted
            Other exceptions from Gemini API
        """
        if not self._configure_api_key(use_paid):
            raise ValueError(f"{'Paid' if use_paid else 'Free'} tier API key not configured")

        model = genai.GenerativeModel(model_name)

        tier_name = "paid" if use_paid else "free"
        logger.info(f"Calling Gemini API - Model: {model_name}, Tier: {tier_name}")

        start_time = time.time()

        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config or {}
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"API call successful - Duration: {duration_ms:.2f}ms, Tier: {tier_name}")

            # Log usage
            tokens_used = getattr(response, 'usage_metadata', None)
            token_count = None
            if tokens_used:
                token_count = getattr(tokens_used, 'total_token_count', None)

            self._log_usage(
                model_name=model_name,
                tier_used=tier_name,
                was_fallback=False,
                tokens_used=token_count
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"API call failed - Duration: {duration_ms:.2f}ms, Error: {str(e)}")

            self._log_usage(
                model_name=model_name,
                tier_used=tier_name,
                was_fallback=False,
                error=str(e)
            )

            raise

    def generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.5-flash",
        generation_config: Optional[Dict[str, Any]] = None,
        enable_fallback: bool = True
    ) -> Any:
        """
        Generate content with automatic fallback support.

        This method will:
        1. Try free tier first (unless USE_PAID_TIER=true)
        2. If quota exhausted and fallback enabled, try paid tier
        3. Track usage statistics

        Args:
            prompt: Prompt text
            model_name: Model to use (default: gemini-2.5-flash)
            generation_config: Generation configuration
            enable_fallback: Whether to enable auto-fallback (default: True)

        Returns:
            API response

        Raises:
            Exception: If both tiers fail or fallback is disabled

        Example:
            client = GeminiClient()

            # Basic usage
            response = client.generate_content("Hello!")

            # With configuration
            response = client.generate_content(
                prompt="Analyze this text...",
                generation_config={"temperature": 0.1}
            )

            # Disable fallback
            response = client.generate_content(
                prompt="Quick task",
                enable_fallback=False
            )
        """
        self.usage_stats["total_calls"] += 1

        # Determine which tier to try first
        try_paid_first = self.use_paid_tier

        # First attempt
        try:
            response = self._call_api(
                model_name=model_name,
                prompt=prompt,
                generation_config=generation_config,
                use_paid=try_paid_first
            )

            # Update stats
            if try_paid_first:
                self.usage_stats["paid_tier_calls"] += 1
            else:
                self.usage_stats["free_tier_calls"] += 1

            return response

        except google_exceptions.ResourceExhausted as e:
            logger.warning(
                f"{'Paid' if try_paid_first else 'Free'} tier quota exhausted: {str(e)}"
            )

            # Check if fallback is enabled and alternate key is available
            if not enable_fallback:
                logger.error("Fallback disabled - raising exception")
                raise

            alternate_key = self.free_key if try_paid_first else self.paid_key
            if not alternate_key:
                logger.error(
                    f"No {'free' if try_paid_first else 'paid'} tier key available for fallback"
                )
                raise

            # Attempt fallback
            logger.info(
                f"Attempting fallback to {'free' if try_paid_first else 'paid'} tier..."
            )

            try:
                response = self._call_api(
                    model_name=model_name,
                    prompt=prompt,
                    generation_config=generation_config,
                    use_paid=not try_paid_first
                )

                # Update stats
                self.usage_stats["fallback_count"] += 1
                if try_paid_first:
                    self.usage_stats["free_tier_calls"] += 1
                else:
                    self.usage_stats["paid_tier_calls"] += 1

                logger.info("✅ Fallback successful!")

                # Log fallback event
                self._log_usage(
                    model_name=model_name,
                    tier_used="free" if not try_paid_first else "paid",
                    was_fallback=True
                )

                return response

            except Exception as fallback_error:
                logger.error(f"❌ Fallback failed: {str(fallback_error)}")
                raise

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get current usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return self.usage_stats.copy()

    def print_usage_summary(self):
        """Print a summary of API usage."""
        print("\n" + "=" * 70)
        print("Gemini API Usage Summary")
        print("=" * 70)
        print(f"Total API calls:        {self.usage_stats['total_calls']}")
        print(f"Free tier calls:        {self.usage_stats['free_tier_calls']}")
        print(f"Paid tier calls:        {self.usage_stats['paid_tier_calls']}")
        print(f"Fallback occurrences:   {self.usage_stats['fallback_count']}")
        print("=" * 70 + "\n")


# ==================== Utility Functions ====================

def create_gemini_client() -> GeminiClient:
    """
    Factory function to create a GeminiClient instance.

    Returns:
        Configured GeminiClient

    Example:
        client = create_gemini_client()
        response = client.generate_content("Hello!")
    """
    return GeminiClient()


def get_usage_history(days: int = 7) -> list:
    """
    Get usage history from tracking file.

    Args:
        days: Number of days to retrieve (default: 7)

    Returns:
        List of usage log entries
    """
    if not USAGE_TRACKING_FILE.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    history = []

    with open(USAGE_TRACKING_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entry_date = datetime.fromisoformat(entry["timestamp"])

                if entry_date >= cutoff_date:
                    history.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse log entry: {e}")
                continue

    return history


def print_usage_report(days: int = 7):
    """
    Print a detailed usage report.

    Args:
        days: Number of days to report (default: 7)
    """
    history = get_usage_history(days)

    if not history:
        print(f"\nNo usage data found for the last {days} days.\n")
        return

    # Calculate statistics
    total_calls = len(history)
    free_calls = sum(1 for h in history if h["tier"] == "free")
    paid_calls = sum(1 for h in history if h["tier"] == "paid")
    fallback_calls = sum(1 for h in history if h.get("was_fallback", False))
    errors = sum(1 for h in history if h.get("error"))

    print("\n" + "=" * 70)
    print(f"Gemini API Usage Report (Last {days} Days)")
    print("=" * 70)
    print(f"Period: {history[0]['timestamp'][:10]} to {history[-1]['timestamp'][:10]}")
    print(f"\nTotal API calls:        {total_calls}")
    print(f"  Free tier:            {free_calls} ({free_calls/total_calls*100:.1f}%)")
    print(f"  Paid tier:            {paid_calls} ({paid_calls/total_calls*100:.1f}%)")
    print(f"Fallback events:        {fallback_calls}")
    print(f"Errors:                 {errors}")
    print("=" * 70 + "\n")


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example: Basic usage
    client = create_gemini_client()

    try:
        response = client.generate_content(
            prompt="What is the capital of Japan?",
            model_name="gemini-2.5-flash"
        )
        print(f"Response: {response.text}")

        # Print usage stats
        client.print_usage_summary()

    except Exception as e:
        print(f"Error: {e}")

    # Print usage report
    print_usage_report(days=7)
