import asyncio
import uuid

from app.agent import (
    CollectionsAgent,
    CollectionsAgentTask,
    FakeModelGateway,
    ModelRequest,
    ToolRegistry,
)


def test_fake_model_gateway_generates_deterministic_responses() -> None:
    gateway = FakeModelGateway()
    request = ModelRequest(prompt='Test prompt')
    response = gateway.generate(request)

    assert response.provider == 'fake'
    assert response.cost_usd == 0.0
    assert 'propose_payment_match' in response.text


def test_collections_agent_proposes_payment_match_on_unmatched_transaction() -> None:
    async def run_test() -> None:
        agent = CollectionsAgent(
            gateway=FakeModelGateway(),
            tool_registry=ToolRegistry(),
        )

        task = CollectionsAgentTask(
            id=str(uuid.uuid4()),
            task_type='unmatched_payment',
            context={
                'transaction_id': 7,
                'charge_id': 9,
                'amount_cents': 5000,
                'customer_name': 'Alicia Stone',
            },
        )

        result = await agent.run_task(task)

        assert result.status == 'completed'
        assert result.result is not None
        assert 'action' in result.result
        assert len(result.model_calls) > 0

    asyncio.run(run_test())


def test_collections_agent_persists_tool_calls_when_proposing_match() -> None:
    async def run_test() -> None:
        agent = CollectionsAgent(
            gateway=FakeModelGateway(),
            tool_registry=ToolRegistry(),
        )

        task = CollectionsAgentTask(
            id=str(uuid.uuid4()),
            task_type='unmatched_payment',
            context={
                'transaction_id': 7,
                'charge_id': 9,
                'amount_cents': 5000,
            },
        )

        result = await agent.run_task(task)

        assert result.status == 'completed'
        if result.result and result.result.get('action') == 'propose_payment_match':
            assert len(result.tool_calls) >= 1
            tool_call = result.tool_calls[0]
            assert tool_call.name == 'propose_payment_match'
            assert 'transaction_id' in tool_call.args

    asyncio.run(run_test())


def test_tool_registry_rejects_unknown_tools() -> None:
    async def run_test() -> None:
        registry = ToolRegistry()
        from app.agent import ToolCall

        unknown_tool = ToolCall(
            name='unknown_tool',
            args={},
            idempotency_key='test:unknown',
        )

        result = await registry.execute(unknown_tool)
        assert result.error is not None
        assert 'Unknown tool' in result.error

    asyncio.run(run_test())
