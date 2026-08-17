from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.models import Organization


class AgentRole(str, Enum):
    COLLECTIONS_AGENT = 'collections'
    CUSTOMER_SERVICE_AGENT = 'customer_service'
    MANAGER_AGENT = 'manager'


@dataclass
class AgentContext:
    """Shared context for agent handoff and collaboration."""

    organization_id: int
    run_id: str
    actor_agent: AgentRole
    task_id: str
    reasoning_summary: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffRequest:
    """Request to hand off work to another agent."""

    from_agent: AgentRole
    to_agent: AgentRole
    reason: str
    task_id: str
    context: AgentContext


@dataclass
class HandoffResponse:
    """Response from handoff target agent."""

    accepted: bool
    handoff_id: str
    from_agent: AgentRole
    to_agent: AgentRole
    action_taken: str
    outcome: str


class AgentHandoffProtocol:
    """Manages agent-to-agent handoff and ensures role isolation."""

    ALLOWED_HANDOFFS = {
        AgentRole.COLLECTIONS_AGENT: {AgentRole.CUSTOMER_SERVICE_AGENT, AgentRole.MANAGER_AGENT},
        AgentRole.CUSTOMER_SERVICE_AGENT: {AgentRole.COLLECTIONS_AGENT, AgentRole.MANAGER_AGENT},
        AgentRole.MANAGER_AGENT: {AgentRole.COLLECTIONS_AGENT, AgentRole.CUSTOMER_SERVICE_AGENT},
    }

    ROLE_TOOLS = {
        AgentRole.COLLECTIONS_AGENT: {
            'search_customers',
            'get_customer_account',
            'list_unmatched_transactions',
            'propose_payment_match',
            'open_case',
        },
        AgentRole.CUSTOMER_SERVICE_AGENT: {
            'search_customers',
            'get_customer_account',
            'list_customer_messages',
            'send_customer_message',
            'create_service_case',
            'get_case_details',
        },
        AgentRole.MANAGER_AGENT: {
            'search_customers',
            'get_customer_account',
            'list_unmatched_transactions',
            'get_case_details',
            'list_all_cases',
            'list_approval_requests',
            'approve_payment_match',
            'reject_payment_match',
        },
    }

    def can_handoff(self, from_agent: AgentRole, to_agent: AgentRole) -> bool:
        """Check if handoff between roles is allowed."""
        return to_agent in self.ALLOWED_HANDOFFS.get(from_agent, set())

    def can_use_tool(self, agent_role: AgentRole, tool_name: str) -> bool:
        """Check if agent can use a specific tool."""
        allowed_tools = self.ROLE_TOOLS.get(agent_role, set())
        return tool_name in allowed_tools

    def validate_handoff_request(self, request: HandoffRequest) -> tuple[bool, str]:
        """Validate a handoff request for role isolation and policy."""
        if not self.can_handoff(request.from_agent, request.to_agent):
            return False, f'Handoff from {request.from_agent} to {request.to_agent} not allowed'

        if not request.reason:
            return False, 'Handoff must include reason'

        if request.context.confidence < 0.0 or request.context.confidence > 1.0:
            return False, 'Confidence must be between 0 and 1'

        return True, 'Handoff request valid'

    def create_handoff(
        self,
        from_agent: AgentRole,
        to_agent: AgentRole,
        reason: str,
        task_id: str,
        context: AgentContext,
    ) -> HandoffRequest | None:
        """Create a handoff request if valid."""
        request = HandoffRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            task_id=task_id,
            context=context,
        )

        valid, msg = self.validate_handoff_request(request)
        if not valid:
            return None

        return request
