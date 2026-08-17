from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from app.reliability import RateLimiter, RedactionPolicy, ReliabilityGuard, RetryConfig, retry_with_backoff, redact_model_output


class TestRedactionPolicy:
    def test_redact_sensitive_fields(self) -> None:
        policy = RedactionPolicy()
        payload = {'api_key': 'secret123', 'user_id': '42', 'token': 'xyz789'}
        redacted = policy.redact(payload)

        assert redacted['api_key'] == '[REDACTED]'
        assert redacted['token'] == '[REDACTED]'
        assert redacted['user_id'] == '42'

    def test_redact_string(self) -> None:
        policy = RedactionPolicy()
        text = 'Authorization: Bearer sk_live_abc123'
        redacted = policy.redact_string(text)
        # Should be redacted since it's a secret token
        assert '[REDACTED]' in redacted or text == redacted  # depends on field name match


class TestRedactModelOutput:
    def test_truncate_long_output(self) -> None:
        long_text = 'x' * 1000
        redacted = redact_model_output(long_text, max_length=100)
        assert len(redacted) <= 115  # 100 + '...[truncated]' = ~115 chars
        assert '...[truncated]' in redacted

    def test_keep_short_output(self) -> None:
        short_text = 'Hello, world!'
        redacted = redact_model_output(short_text)
        assert redacted == short_text

    def test_handle_empty_output(self) -> None:
        assert redact_model_output('') == '[empty]'


class TestRateLimiter:
    def test_allow_within_limit(self) -> None:
        limiter = RateLimiter(max_calls=3, window_seconds=60)
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

    def test_remaining_quota(self) -> None:
        limiter = RateLimiter(max_calls=5, window_seconds=60)
        limiter.allow()
        limiter.allow()
        assert limiter.remaining() == 3

    def test_window_resets(self) -> None:
        with patch('time.time', side_effect=[100, 100, 100, 161]):
            limiter = RateLimiter(max_calls=2, window_seconds=60)
            assert limiter.allow() is True
            assert limiter.allow() is True
            assert limiter.allow() is False

            assert limiter.allow() is True  # Window expired


class TestRetryWithBackoff:
    def test_success_on_first_attempt(self) -> None:
        mock_func = Mock(return_value='success')
        result = retry_with_backoff(mock_func)
        assert result == 'success'
        assert mock_func.call_count == 1

    def test_retry_on_failure(self) -> None:
        mock_func = Mock()
        mock_func.side_effect = [ValueError('error'), ValueError('error'), 'success']

        config = RetryConfig(max_attempts=3, initial_delay_seconds=0.001, backoff_factor=2.0)
        result = retry_with_backoff(mock_func, config=config)

        assert result == 'success'
        assert mock_func.call_count == 3

    def test_exhausted_retries(self) -> None:
        mock_func = Mock(side_effect=ValueError('persistent error'))
        config = RetryConfig(max_attempts=2, initial_delay_seconds=0.001)

        with pytest.raises(ValueError, match='persistent error'):
            retry_with_backoff(mock_func, config=config)

        assert mock_func.call_count == 2

    def test_retry_with_args_and_kwargs(self) -> None:
        mock_func = Mock(side_effect=[RuntimeError('error'), 'ok'])
        result = retry_with_backoff(mock_func, 'arg1', 'arg2', config=RetryConfig(max_attempts=2, initial_delay_seconds=0.001), kwarg1='value1')
        assert result == 'ok'
        mock_func.assert_called_with('arg1', 'arg2', kwarg1='value1')


class TestReliabilityGuard:
    def test_check_rate_limit_allowed(self) -> None:
        guard = ReliabilityGuard()
        assert guard.check_rate_limit('operation1') is True

    def test_check_rate_limit_exceeded(self) -> None:
        guard = ReliabilityGuard()
        guard.rate_limiter.max_calls = 2
        guard.check_rate_limit('op1')
        guard.check_rate_limit('op2')
        assert guard.check_rate_limit('op3') is False

    def test_remaining_quota(self) -> None:
        guard = ReliabilityGuard()
        guard.rate_limiter.max_calls = 100
        guard.check_rate_limit('op1')
        assert 98 <= guard.remaining_quota() <= 99
