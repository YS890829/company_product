"""
Error Handling and Retry Logic Module

This module provides decorators and utilities for handling errors
with exponential backoff and jitter based on 2025 best practices.

Based on research from:
- Tenacity library (https://tenacity.readthedocs.io/)
- AWS Architecture Blog on exponential backoff
- Google Cloud API retry best practices
"""

import logging
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Configure logger
logger = logging.getLogger(__name__)


# ==================== Retry Decorators ====================

def retry_with_exponential_backoff(
    max_attempts: int = 5,
    min_wait: int = 1,
    max_wait: int = 60,
    multiplier: int = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_name: Optional[str] = None
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Multiplier for exponential backoff
        exceptions: Tuple of exception types to retry on
        logger_name: Logger name for logging retry attempts

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_attempts=3)
        def call_api():
            return requests.get('https://api.example.com')
    """
    log = logging.getLogger(logger_name) if logger_name else logger

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=multiplier,
            min=min_wait,
            max=max_wait
        ),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(log, logging.WARNING),
        after=after_log(log, logging.INFO),
        reraise=True
    )


def retry_gemini_api_call(
    max_attempts: int = 5,
    min_wait: int = 2,
    max_wait: int = 120
) -> Callable:
    """
    Specialized retry decorator for Gemini API calls.

    Handles:
    - Rate limit errors (429)
    - Temporary server errors (500, 502, 503, 504)
    - Network errors
    - Resource exhausted errors

    Args:
        max_attempts: Maximum number of retry attempts (default: 5)
        min_wait: Minimum wait time in seconds (default: 2)
        max_wait: Maximum wait time in seconds (default: 120)

    Returns:
        Decorated function with Gemini-specific retry logic

    Example:
        @retry_gemini_api_call()
        def generate_content(prompt: str):
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt)
    """
    # Gemini-specific exceptions to retry
    retryable_exceptions = (
        google_exceptions.ResourceExhausted,  # 429 Rate limit
        google_exceptions.ServiceUnavailable,  # 503
        google_exceptions.DeadlineExceeded,    # Timeout
        google_exceptions.InternalServerError, # 500
        google_exceptions.TooManyRequests,     # 429
        ConnectionError,
        TimeoutError,
    )

    return retry_with_exponential_backoff(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        multiplier=2,
        exceptions=retryable_exceptions,
        logger_name='gemini_api'
    )


def retry_with_jitter(
    max_attempts: int = 3,
    base_wait: int = 1,
    max_wait: int = 30
) -> Callable:
    """
    Retry decorator with jitter to prevent thundering herd problem.

    Jitter helps distribute retry attempts over time when multiple
    clients are retrying simultaneously.

    Args:
        max_attempts: Maximum number of retry attempts
        base_wait: Base wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorator function

    Example:
        @retry_with_jitter(max_attempts=3)
        def fetch_data():
            return database.query()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts",
                            exc_info=True
                        )
                        raise

                    # Calculate exponential backoff with jitter
                    wait_time = min(
                        base_wait * (2 ** (attempt - 1)) + random.uniform(0, 1),
                        max_wait
                    )

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                        f"Retrying in {wait_time:.2f}s... Error: {str(e)}"
                    )

                    import time
                    time.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator


# ==================== Error Handler Classes ====================

class APIErrorHandler:
    """
    Centralized error handling for API calls.

    Provides:
    - Error categorization (retryable vs non-retryable)
    - Error logging
    - Error response formatting
    """

    @staticmethod
    def is_retryable_error(exception: Exception) -> bool:
        """
        Determine if an error is retryable.

        Args:
            exception: The exception to check

        Returns:
            True if the error is retryable, False otherwise
        """
        retryable_types = (
            google_exceptions.ResourceExhausted,
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InternalServerError,
            google_exceptions.TooManyRequests,
            ConnectionError,
            TimeoutError,
        )

        return isinstance(exception, retryable_types)

    @staticmethod
    def format_error_response(exception: Exception, context: str = "") -> dict:
        """
        Format an exception into a standardized error response.

        Args:
            exception: The exception to format
            context: Additional context about where the error occurred

        Returns:
            Dictionary with error details
        """
        error_type = type(exception).__name__
        error_message = str(exception)

        # Check if it's a Gemini API error
        if isinstance(exception, google_exceptions.GoogleAPIError):
            status_code = getattr(exception, 'code', 500)
        else:
            status_code = 500

        logger.error(
            f"Error in {context}: {error_type} - {error_message}",
            exc_info=True
        )

        return {
            "error": error_type,
            "message": error_message,
            "context": context,
            "retryable": APIErrorHandler.is_retryable_error(exception),
            "status_code": status_code
        }

    @staticmethod
    def log_api_call(
        function_name: str,
        success: bool,
        duration_ms: float,
        error: Optional[Exception] = None
    ):
        """
        Log API call metrics.

        Args:
            function_name: Name of the API function
            success: Whether the call succeeded
            duration_ms: Duration of the call in milliseconds
            error: Exception if call failed
        """
        log_data = {
            "function": function_name,
            "success": success,
            "duration_ms": duration_ms,
        }

        if error:
            log_data["error"] = str(error)
            log_data["error_type"] = type(error).__name__

        if success:
            logger.info(f"API call successful: {log_data}")
        else:
            logger.error(f"API call failed: {log_data}")


# ==================== Utility Functions ====================

def safe_api_call(func: Callable, *args, **kwargs) -> Tuple[Optional[any], Optional[Exception]]:
    """
    Safely execute an API call and return result or error.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Tuple of (result, error) where one is None

    Example:
        result, error = safe_api_call(gemini_model.generate_content, "Hello")
        if error:
            handle_error(error)
        else:
            process_result(result)
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Error in safe_api_call: {str(e)}", exc_info=True)
        return None, e


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example 1: Simple retry with exponential backoff
    @retry_with_exponential_backoff(max_attempts=3)
    def example_function():
        print("Attempting API call...")
        raise ConnectionError("Network unreachable")

    # Example 2: Gemini API retry
    @retry_gemini_api_call()
    def example_gemini_call(prompt: str):
        model = genai.GenerativeModel('gemini-pro')
        return model.generate_content(prompt)

    # Example 3: Retry with jitter
    @retry_with_jitter(max_attempts=3)
    def example_jitter():
        print("Attempting with jitter...")
        raise ValueError("Temporary error")

    # Example 4: Safe API call
    result, error = safe_api_call(example_gemini_call, "What is AI?")
    if error:
        print(f"Error occurred: {error}")
    else:
        print(f"Success: {result}")
