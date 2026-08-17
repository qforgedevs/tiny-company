from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.reliability import redact_model_output


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, str | int | float | bool]
    idempotency_key: str


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    tool_name: str
    result: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 1024


@dataclass(frozen=True)
class ModelResponse:
    provider: str
    text: str
    stop_reason: str
    cost_usd: float = 0.0


class ModelGateway(ABC):
    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        pass


class FakeModelGateway(ModelGateway):
    """Deterministic fake model for testing without paid provider calls."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            provider='fake',
            text=f'[fake-model] Analyzed: {request.prompt[:80]}... suggesting propose_payment_match.',
            stop_reason='end_turn',
            cost_usd=0.0,
        )


class OpenAIModelGateway(ModelGateway):
    """Real OpenAI adapter using server-side environment variables."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OPENAI_API_KEY environment variable not set')

    def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model='gpt-4-turbo',
                messages=[{'role': 'user', 'content': request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            text = response.choices[0].message.content or ''
            return ModelResponse(
                provider='openai',
                text=text,
                stop_reason=response.choices[0].finish_reason or 'end_turn',
                cost_usd=0.01,  # placeholder, real cost calculation would use usage tokens
            )
        except Exception as err:
            raise RuntimeError(f'OpenAI API call failed: {err}') from err


def get_model_gateway() -> ModelGateway:
    """Factory function that selects the model gateway based on environment."""
    provider = os.environ.get('MODEL_PROVIDER', 'fake').lower()

    if provider == 'openai':
        return OpenAIModelGateway()
    elif provider == 'fake':
        return FakeModelGateway()
    else:
        raise ValueError(f'Unknown model provider: {provider}')


@dataclass
class CollectionsAgentTask:
    id: str
    task_type: str
    context: dict[str, Any]
    status: str = 'pending'
    result: dict[str, Any] | None = None
    model_calls: list[dict[str, Any]] = None
    tool_calls: list[ToolCall] = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.model_calls is None:
            object.__setattr__(self, 'model_calls', [])
        if self.tool_calls is None:
            object.__setattr__(self, 'tool_calls', [])


class ToolRegistry:
    """Registry of typed tools available to the Collections Agent."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {
            'search_customers': {
                'description': 'Search for customers by name or email.',
                'params': {'query': 'str'},
                'handler': self._search_customers,
            },
            'get_customer_account': {
                'description': 'Get customer account details.',
                'params': {'customer_id': 'int'},
                'handler': self._get_customer_account,
            },
            'list_unmatched_transactions': {
                'description': 'List unmatched bank transactions.',
                'params': {'limit': 'int'},
                'handler': self._list_unmatched_transactions,
            },
            'propose_payment_match': {
                'description': 'Propose a payment match between transaction and charge.',
                'params': {'transaction_id': 'int', 'charge_id': 'int', 'rationale': 'str', 'confidence': 'float'},
                'handler': self._propose_payment_match,
            },
            'open_case': {
                'description': 'Open an escalation case.',
                'params': {'case_type': 'str', 'summary': 'str', 'priority': 'str'},
                'handler': self._open_case,
            },
        }

    def get_schema(self) -> dict[str, Any]:
        """Return the schema for all available tools."""
        return {name: {'description': tool['description'], 'params': tool['params']} for name, tool in self._tools.items()}

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result."""
        tool = self._tools.get(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.idempotency_key,
                tool_name=tool_call.name,
                result={},
                error=f'Unknown tool: {tool_call.name}',
            )

        try:
            result = tool['handler'](**tool_call.args)
            return ToolResult(
                tool_call_id=tool_call.idempotency_key,
                tool_name=tool_call.name,
                result=result,
            )
        except Exception as err:
            return ToolResult(
                tool_call_id=tool_call.idempotency_key,
                tool_name=tool_call.name,
                result={},
                error=str(err),
            )

    def _search_customers(self, query: str) -> dict[str, Any]:
        return {'customers': [], 'count': 0}

    def _get_customer_account(self, customer_id: int) -> dict[str, Any]:
        return {'customer_id': customer_id, 'status': 'active', 'balance_cents': 0}

    def _list_unmatched_transactions(self, limit: int = 10) -> dict[str, Any]:
        return {'transactions': [], 'count': 0}

    def _propose_payment_match(self, transaction_id: int, charge_id: int, rationale: str, confidence: float) -> dict[str, Any]:
        return {'match_id': str(uuid.uuid4()), 'transaction_id': transaction_id, 'charge_id': charge_id, 'confidence': confidence}

    def _open_case(self, case_type: str, summary: str, priority: str) -> dict[str, Any]:
        return {'case_id': str(uuid.uuid4()), 'case_type': case_type, 'priority': priority}


class CollectionsAgent:
    """Collections Agent orchestrator: inspect unmatched payments, propose matches, escalate ambiguity."""

    def __init__(self, gateway: ModelGateway | None = None, tool_registry: ToolRegistry | None = None) -> None:
        self.gateway = gateway or get_model_gateway()
        self.tool_registry = tool_registry or ToolRegistry()

    async def run_task(self, task: CollectionsAgentTask) -> CollectionsAgentTask:
        """Run a Collections Agent task: analyze context, decide action, make tool calls."""
        task.status = 'running'

        prompt = self._build_prompt(task)
        request = ModelRequest(prompt=prompt, temperature=0.0, max_tokens=1024)

        try:
            response = self.gateway.generate(request)
            task.model_calls.append(
                {
                    'provider': response.provider,
                    'prompt_length': len(prompt),
                    'response': redact_model_output(response.text),
                    'stop_reason': response.stop_reason,
                    'cost_usd': response.cost_usd,
                }
            )

            decision = self._parse_decision(response.text)
            task.result = decision

            if decision.get('action') == 'propose_payment_match':
                tool_call = ToolCall(
                    name='propose_payment_match',
                    args={
                        'transaction_id': task.context.get('transaction_id', 0),
                        'charge_id': task.context.get('charge_id', 0),
                        'rationale': decision.get('rationale', 'Automated match'),
                        'confidence': decision.get('confidence', 0.8),
                    },
                    idempotency_key=f'task:{task.id}:match',
                )
                task.tool_calls.append(tool_call)

                tool_result = await self.tool_registry.execute(tool_call)
                task.result['tool_result'] = {'match_id': tool_result.result.get('match_id')}

            elif decision.get('action') == 'escalate_case':
                tool_call = ToolCall(
                    name='open_case',
                    args={
                        'case_type': 'ambiguous_payment',
                        'summary': decision.get('escalation_reason', 'Requires human review'),
                        'priority': 'normal',
                    },
                    idempotency_key=f'task:{task.id}:escalate',
                )
                task.tool_calls.append(tool_call)

                tool_result = await self.tool_registry.execute(tool_call)
                task.result['tool_result'] = {'case_id': tool_result.result.get('case_id')}

            task.status = 'completed'

        except Exception as err:
            task.status = 'error'
            task.error = str(err)

        return task

    def _build_prompt(self, task: CollectionsAgentTask) -> str:
        """Build a prompt for the Collections Agent based on task context."""
        prompt = 'You are a Collections Agent for a recurring-payments academy.\n\n'
        prompt += f"Task: {task.task_type}\n\n"
        prompt += f"Context:\n{json.dumps(task.context, indent=2)}\n\n"
        prompt += "Available tools:\n"
        for name, details in self.tool_registry.get_schema().items():
            prompt += f"- {name}: {details['description']}\n"
        prompt += "\nDecide on one of: propose_payment_match, escalate_case, or no_action.\n"
        prompt += "Respond with JSON: {\"action\": \"...\", \"rationale\": \"...\", \"confidence\": 0.0-1.0}\n"
        return prompt

    def _parse_decision(self, model_text: str) -> dict[str, Any]:
        """Parse model output to extract decision."""
        try:
            start = model_text.find('{')
            end = model_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = model_text[start:end]
                return json.loads(json_str)
        except Exception:
            pass

        if 'propose_payment_match' in model_text:
            return {'action': 'propose_payment_match', 'rationale': 'Inferred from model output', 'confidence': 0.7}
        elif 'escalate' in model_text or 'ambiguous' in model_text:
            return {'action': 'escalate_case', 'escalation_reason': 'Model flagged ambiguity', 'confidence': 0.5}
        else:
            return {'action': 'no_action', 'rationale': 'No clear action identified'}
