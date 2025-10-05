"""
Retry utilities for resilient Telegram API calls.

Implements exponential backoff with proper handling of Telegram-specific errors:
- TelegramRetryAfter: Wait for specified duration
- TelegramBadRequest: Don't retry (permanent error)
- Network errors: Retry with exponential backoff
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Optional, Tuple
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramAPIError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_bad_request: bool = False
    ):
        """
        Args:
            max_attempts: Maximum number of retry attempts (including initial call)
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff calculation
            retry_on_bad_request: Whether to retry on TelegramBadRequest errors
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_bad_request = retry_on_bad_request


# Default configurations for different use cases
CRITICAL_RETRY_CONFIG = RetryConfig(max_attempts=5, initial_delay=2.0, max_delay=120.0)
STANDARD_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=60.0)
FAST_RETRY_CONFIG = RetryConfig(max_attempts=2, initial_delay=0.5, max_delay=10.0)


def async_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions that need retry logic with exponential backoff.

    Usage:
        @async_retry(STANDARD_RETRY_CONFIG)
        async def send_message_to_user(bot, user_id, text):
            await bot.send_message(user_id, text)

    Args:
        config: RetryConfig instance, defaults to STANDARD_RETRY_CONFIG
    """
    if config is None:
        config = STANDARD_RETRY_CONFIG

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            attempt = 0

            while attempt < config.max_attempts:
                try:
                    return await func(*args, **kwargs)

                except TelegramRetryAfter as e:
                    # Telegram explicitly tells us when to retry
                    retry_after = e.retry_after
                    logger.warning(
                        f"{func.__name__} hit rate limit, retrying after {retry_after}s "
                        f"(attempt {attempt + 1}/{config.max_attempts})"
                    )

                    if attempt + 1 < config.max_attempts:
                        await asyncio.sleep(retry_after)
                        attempt += 1
                        last_exception = e
                    else:
                        raise

                except TelegramBadRequest as e:
                    # Bad request errors are usually permanent (wrong chat_id, invalid message, etc)
                    if not config.retry_on_bad_request:
                        logger.error(f"{func.__name__} failed with bad request: {e}")
                        raise
                    else:
                        last_exception = e
                        attempt += 1

                except TelegramAPIError as e:
                    # Generic Telegram API errors - retry with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )

                    logger.warning(
                        f"{func.__name__} failed with API error: {e}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{config.max_attempts})"
                    )

                    if attempt + 1 < config.max_attempts:
                        await asyncio.sleep(delay)
                        attempt += 1
                        last_exception = e
                    else:
                        raise

                except (asyncio.TimeoutError, ConnectionError, OSError) as e:
                    # Network-related errors - retry with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )

                    logger.warning(
                        f"{func.__name__} failed with network error: {e}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{config.max_attempts})"
                    )

                    if attempt + 1 < config.max_attempts:
                        await asyncio.sleep(delay)
                        attempt += 1
                        last_exception = e
                    else:
                        raise

            # All retries exhausted
            logger.error(
                f"{func.__name__} failed after {config.max_attempts} attempts, "
                f"last error: {last_exception}"
            )
            raise last_exception

        return wrapper
    return decorator


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: RetryConfig instance

    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    return min(delay, config.max_delay)


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Execute an async function with retry logic (functional approach).

    Usage:
        result = await retry_with_backoff(
            bot.send_message,
            user_id,
            "Hello!",
            config=CRITICAL_RETRY_CONFIG
        )

    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: RetryConfig instance
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        Exception from func after all retries exhausted
    """
    if config is None:
        config = STANDARD_RETRY_CONFIG

    last_exception = None
    attempt = 0

    while attempt < config.max_attempts:
        try:
            return await func(*args, **kwargs)

        except TelegramRetryAfter as e:
            retry_after = e.retry_after
            logger.warning(
                f"{func.__name__} hit rate limit, retrying after {retry_after}s "
                f"(attempt {attempt + 1}/{config.max_attempts})"
            )

            if attempt + 1 < config.max_attempts:
                await asyncio.sleep(retry_after)
                attempt += 1
                last_exception = e
            else:
                raise

        except TelegramBadRequest as e:
            if not config.retry_on_bad_request:
                logger.error(f"{func.__name__} failed with bad request: {e}")
                raise
            else:
                last_exception = e
                attempt += 1

        except TelegramAPIError as e:
            delay = calculate_backoff_delay(attempt, config)

            logger.warning(
                f"{func.__name__} failed with API error: {e}, "
                f"retrying in {delay:.1f}s (attempt {attempt + 1}/{config.max_attempts})"
            )

            if attempt + 1 < config.max_attempts:
                await asyncio.sleep(delay)
                attempt += 1
                last_exception = e
            else:
                raise

        except (asyncio.TimeoutError, ConnectionError, OSError) as e:
            delay = calculate_backoff_delay(attempt, config)

            logger.warning(
                f"{func.__name__} failed with network error: {e}, "
                f"retrying in {delay:.1f}s (attempt {attempt + 1}/{config.max_attempts})"
            )

            if attempt + 1 < config.max_attempts:
                await asyncio.sleep(delay)
                attempt += 1
                last_exception = e
            else:
                raise

    logger.error(
        f"{func.__name__} failed after {config.max_attempts} attempts, "
        f"last error: {last_exception}"
    )
    raise last_exception


class RetryableOperation:
    """
    Context manager for retryable operations with detailed metrics.

    Usage:
        async with RetryableOperation("send_welcome_message", CRITICAL_RETRY_CONFIG) as retry:
            await bot.send_message(user_id, "Welcome!")
            retry.mark_success()

        # Check metrics
        if retry.succeeded:
            print(f"Succeeded after {retry.attempts} attempts")
    """

    def __init__(self, operation_name: str, config: Optional[RetryConfig] = None):
        self.operation_name = operation_name
        self.config = config or STANDARD_RETRY_CONFIG
        self.attempts = 0
        self.succeeded = False
        self.total_delay = 0.0
        self.errors = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.errors.append((exc_type.__name__, str(exc_val)))

            if self.attempts < self.config.max_attempts:
                # Calculate delay
                if isinstance(exc_val, TelegramRetryAfter):
                    delay = exc_val.retry_after
                else:
                    delay = calculate_backoff_delay(self.attempts, self.config)

                self.total_delay += delay
                self.attempts += 1

                logger.info(
                    f"{self.operation_name} attempt {self.attempts}/{self.config.max_attempts} "
                    f"failed: {exc_type.__name__}, retrying in {delay:.1f}s"
                )

                await asyncio.sleep(delay)
                return True  # Suppress exception, retry

            else:
                logger.error(
                    f"{self.operation_name} failed after {self.attempts} attempts, "
                    f"total delay: {self.total_delay:.1f}s, errors: {self.errors}"
                )
                return False  # Let exception propagate

        return False

    def mark_success(self):
        """Mark the operation as successful"""
        self.succeeded = True
