from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    idempotency_key: str


class ModelGateway:
    def __init__(self, provider_name: str = 'fake') -> None:
        self.provider_name = provider_name

    def generate(self, prompt: str, *, temperature: float = 0.0) -> str:
        return f'[{self.provider_name}] {prompt[:80]}'


class FakeModelGateway(ModelGateway):
    def __init__(self) -> None:
        super().__init__('fake')


@dataclass
class CollectionsAgent:
    gateway: ModelGateway = field(default_factory=FakeModelGateway)
    tool_registry: dict[str, Any] = field(default_factory=dict)

    def choose_next_action(self, context: dict[str, Any]) -> str:
        if context.get('unmatched_transaction'):
            return 'propose_payment_match'
        if context.get('ambiguous'):
            return 'escalate_case'
        return 'no_action'

    def run_task(self, context: dict[str, Any]) -> dict[str, Any]:
        action = self.choose_next_action(context)
        prompt = context.get('prompt', 'Assess the overdue account.')
        model_text = self.gateway.generate(prompt)
        return {
            'action': action,
            'summary': f'{action} based on policy-safe review.',
            'model_response': model_text,
            'tool_calls': [],
        }
