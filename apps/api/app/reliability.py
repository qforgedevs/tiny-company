from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass(frozen=True)
class RedactionPolicy:
    fields_to_redact: tuple[str, ...] = ('api_key', 'token', 'secret', 'password', 'ground_truth', 'OPENAI_API_KEY')

    def redact(self, payload: dict[str, object]) -> dict[str, object]:
        redacted = dict(payload)
        for key in self.fields_to_redact:
            if key in redacted:
                redacted[key] = '[REDACTED]'
        return redacted

    def redact_string(self, text: str) -> str:
        for secret in self.fields_to_redact:
            if secret.upper() in text.upper():
                text = text.replace(secret, '[REDACTED]')
        return text


def redact_model_output(text: str, max_length: int = 500) -> str:
    """Redact sensitive model output and truncate for logging."""
    if not text:
        return '[empty]'
    if len(text) > max_length:
        return text[:max_length] + '...[truncated]'
    return text


@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_delay_seconds: float = 60.0


def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    config: RetryConfig | None = None,
    idempotency_key: str | None = None,
    **kwargs: Any,
) -> T:
    """Execute a function with exponential backoff retry logic."""
    if config is None:
        config = RetryConfig()

    last_error = None
    delay = config.initial_delay_seconds

    for attempt in range(config.max_attempts):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(f'Recovered after {attempt} retries (idempotency_key={idempotency_key})')
            return result
        except Exception as err:
            last_error = err
            if attempt < config.max_attempts - 1:
                logger.warning(f'Attempt {attempt + 1} failed: {str(err)}. Retrying in {delay}s...')
                time.sleep(delay)
                delay = min(delay * config.backoff_factor, config.max_delay_seconds)
            else:
                logger.error(f'All {config.max_attempts} attempts failed. Last error: {str(err)}')

    raise last_error if last_error else RuntimeError('Retry exhausted without error')


class RateLimiter:
    def __init__(self, max_calls: int = 100, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.call_times: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        self.call_times = [t for t in self.call_times if t > cutoff]

        if len(self.call_times) < self.max_calls:
            self.call_times.append(now)
            return True
        return False

    def remaining(self) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        active_calls = [t for t in self.call_times if t > cutoff]
        return max(0, self.max_calls - len(active_calls))


class ReliabilityGuard:
    def __init__(self) -> None:
        self.redaction_policy = RedactionPolicy()
        self.rate_limiter = RateLimiter(max_calls=100, window_seconds=60)
        self.retry_config = RetryConfig()

    def check_rate_limit(self, operation_name: str) -> bool:
        allowed = self.rate_limiter.allow()
        if not allowed:
            logger.warning(f'Rate limit exceeded for {operation_name}')
        return allowed

    def remaining_quota(self) -> int:
        return self.rate_limiter.remaining()

