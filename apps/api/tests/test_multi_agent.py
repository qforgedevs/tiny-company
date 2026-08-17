from __future__ import annotations

import pytest

from app.agent import CustomerServiceAgent, CustomerServiceAgentTask, FakeModelGateway, ToolRegistry
from app.multi_agent import AgentContext, AgentHandoffProtocol, AgentRole, HandoffRequest


class TestAgentHandoffProtocol:
    def test_allowed_handoffs(self) -> None:
        protocol = AgentHandoffProtocol()
        assert protocol.can_handoff(AgentRole.COLLECTIONS_AGENT, AgentRole.CUSTOMER_SERVICE_AGENT)
        assert protocol.can_handoff(AgentRole.CUSTOMER_SERVICE_AGENT, AgentRole.COLLECTIONS_AGENT)
        assert protocol.can_handoff(AgentRole.COLLECTIONS_AGENT, AgentRole.MANAGER_AGENT)

    def test_disallowed_handoff_to_same_role(self) -> None:
        protocol = AgentHandoffProtocol()
        assert not protocol.can_handoff(AgentRole.COLLECTIONS_AGENT, AgentRole.COLLECTIONS_AGENT)

    def test_role_tool_isolation(self) -> None:
        protocol = AgentHandoffProtocol()
        assert protocol.can_use_tool(AgentRole.COLLECTIONS_AGENT, 'propose_payment_match')
        assert not protocol.can_use_tool(AgentRole.COLLECTIONS_AGENT, 'send_customer_message')

        assert protocol.can_use_tool(AgentRole.CUSTOMER_SERVICE_AGENT, 'send_customer_message')
        assert not protocol.can_use_tool(AgentRole.CUSTOMER_SERVICE_AGENT, 'propose_payment_match')

        assert protocol.can_use_tool(AgentRole.MANAGER_AGENT, 'approve_payment_match')
        assert not protocol.can_use_tool(AgentRole.MANAGER_AGENT, 'send_customer_message')

    def test_validate_handoff_request_valid(self) -> None:
        protocol = AgentHandoffProtocol()
        context = AgentContext(
            organization_id=1,
            run_id='run1',
            actor_agent=AgentRole.COLLECTIONS_AGENT,
            task_id='task1',
            reasoning_summary='Ambiguous case needs human attention',
            confidence=0.6,
        )
        request = HandoffRequest(
            from_agent=AgentRole.COLLECTIONS_AGENT,
            to_agent=AgentRole.CUSTOMER_SERVICE_AGENT,
            reason='Customer inquiry detected',
            task_id='task1',
            context=context,
        )

        valid, msg = protocol.validate_handoff_request(request)
        assert valid is True
        assert msg == 'Handoff request valid'

    def test_validate_handoff_request_invalid_agents(self) -> None:
        protocol = AgentHandoffProtocol()
        context = AgentContext(
            organization_id=1,
            run_id='run1',
            actor_agent=AgentRole.COLLECTIONS_AGENT,
            task_id='task1',
            reasoning_summary='Test',
            confidence=0.5,
        )
        request = HandoffRequest(
            from_agent=AgentRole.COLLECTIONS_AGENT,
            to_agent=AgentRole.COLLECTIONS_AGENT,  # same role
            reason='Test',
            task_id='task1',
            context=context,
        )

        valid, msg = protocol.validate_handoff_request(request)
        assert valid is False

    def test_validate_handoff_request_invalid_confidence(self) -> None:
        protocol = AgentHandoffProtocol()
        context = AgentContext(
            organization_id=1,
            run_id='run1',
            actor_agent=AgentRole.COLLECTIONS_AGENT,
            task_id='task1',
            reasoning_summary='Test',
            confidence=1.5,  # invalid
        )
        request = HandoffRequest(
            from_agent=AgentRole.COLLECTIONS_AGENT,
            to_agent=AgentRole.CUSTOMER_SERVICE_AGENT,
            reason='Test',
            task_id='task1',
            context=context,
        )

        valid, msg = protocol.validate_handoff_request(request)
        assert valid is False
        assert 'Confidence' in msg

    def test_create_handoff(self) -> None:
        protocol = AgentHandoffProtocol()
        context = AgentContext(
            organization_id=1,
            run_id='run1',
            actor_agent=AgentRole.COLLECTIONS_AGENT,
            task_id='task1',
            reasoning_summary='Handoff needed',
            confidence=0.7,
        )

        handoff = protocol.create_handoff(
            from_agent=AgentRole.COLLECTIONS_AGENT,
            to_agent=AgentRole.CUSTOMER_SERVICE_AGENT,
            reason='Customer service inquiry',
            task_id='task1',
            context=context,
        )

        assert handoff is not None
        assert handoff.from_agent == AgentRole.COLLECTIONS_AGENT
        assert handoff.to_agent == AgentRole.CUSTOMER_SERVICE_AGENT

    def test_create_handoff_invalid(self) -> None:
        protocol = AgentHandoffProtocol()
        context = AgentContext(
            organization_id=1,
            run_id='run1',
            actor_agent=AgentRole.COLLECTIONS_AGENT,
            task_id='task1',
            reasoning_summary='Test',
            confidence=2.0,  # invalid
        )

        handoff = protocol.create_handoff(
            from_agent=AgentRole.COLLECTIONS_AGENT,
            to_agent=AgentRole.CUSTOMER_SERVICE_AGENT,
            reason='Test',
            task_id='task1',
            context=context,
        )

        assert handoff is None


class TestCustomerServiceAgent:
    def test_customer_service_agent_initialize(self) -> None:
        gateway = FakeModelGateway()
        registry = ToolRegistry()
        agent = CustomerServiceAgent(gateway=gateway, tool_registry=registry)

        assert agent.gateway == gateway
        assert agent.tool_registry == registry

    def test_customer_service_agent_build_prompt(self) -> None:
        agent = CustomerServiceAgent()
        task = CustomerServiceAgentTask(
            id='task1',
            organization_id=1,
            run_id='run1',
            task_type='answer_inquiry',
            context={'customer_id': 42, 'inquiry': 'How do I update my billing info?'},
        )

        prompt = agent._build_prompt(task)
        assert 'Customer Service Agent' in prompt
        assert 'answer_inquiry' in prompt
        assert 'customer_id' in prompt

    def test_customer_service_agent_parse_decision_send_message(self) -> None:
        agent = CustomerServiceAgent()
        model_text = '{"action": "send_message", "response": "You can update billing info in settings.", "confidence": 0.9}'
        decision = agent._parse_decision(model_text)

        assert decision['action'] == 'send_message'
        assert 'response' in decision
        assert decision['confidence'] == 0.9

    def test_customer_service_agent_parse_decision_fallback(self) -> None:
        agent = CustomerServiceAgent()
        model_text = 'The customer is asking about billing. We should send them a message with instructions.'
        decision = agent._parse_decision(model_text)

        assert decision['action'] == 'send_message'
        assert decision['confidence'] == 0.6


class TestAgentComparison:
    def test_role_tools_coverage(self) -> None:
        """Verify that each agent has exclusive and non-overlapping tool sets."""
        protocol = AgentHandoffProtocol()

        # Collections Agent should not have customer service tools
        cs_tools = protocol.ROLE_TOOLS[AgentRole.CUSTOMER_SERVICE_AGENT]
        collections_tools = protocol.ROLE_TOOLS[AgentRole.COLLECTIONS_AGENT]

        # send_customer_message should be CS-only
        assert 'send_customer_message' in cs_tools
        assert 'send_customer_message' not in collections_tools

        # propose_payment_match should be Collections-only
        assert 'propose_payment_match' in collections_tools
        assert 'propose_payment_match' not in cs_tools

        # Manager should have oversight tools
        manager_tools = protocol.ROLE_TOOLS[AgentRole.MANAGER_AGENT]
        assert 'approve_payment_match' in manager_tools
        assert 'reject_payment_match' in manager_tools
