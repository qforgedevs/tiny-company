from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionPolicy:
    fields_to_redact: tuple[str, ...] = ('api_key', 'token', 'secret', 'password', 'ground_truth')

    def redact(self, payload: dict[str, object]) -> dict[str, object]:
        redacted = dict(payload)
        for key in self.fields_to_redact:
            if key in redacted:
                redacted[key] = '[REDACTED]'
        return redacted


class ReliabilityGuard:
    def __init__(self) -> None:
        self.redaction_policy = RedactionPolicy()

    def check_rate_limit(self, total_calls: int, limit: int = 100) -> bool:
        return total_calls <= limit


def redact_model_output(text: str, max_length: int = 500) -> str:
    """Redact sensitive model output and truncate for logging."""
    if not text:
        return '[empty]'
    if len(text) > max_length:
        return text[:max_length] + '...[truncated]'
    return text
