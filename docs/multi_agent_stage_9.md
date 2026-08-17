# Stage 9 — Multi-agent Experiments

## Overview
Stage 9 implements a multi-agent system with two specialized agents, role-based tool access control, agent handoff protocols, and comparative evaluations to demonstrate coordinated AI-driven decision-making.

## Key Features Implemented

### 1. Agent Roles and Isolation
- **Location**: [apps/api/app/multi_agent.py](../apps/api/app/multi_agent.py)
- **AgentRole Enum**: Collections, Customer Service, Manager
- **Tool Isolation**: Each agent has exclusive tool set based on role
  - Collections Agent: propose_payment_match, open_case, search_customers, get_customer_account
  - Customer Service Agent: send_customer_message, create_service_case, list_customer_messages
  - Manager Agent: approve_payment_match, reject_payment_match, list_approval_requests

### 2. Handoff Protocol
- **AgentHandoffProtocol**: Manages agent-to-agent handoff with validation
- **Allowed Handoffs**: Defined adjacency between agent roles
- **Handoff Validation**: Ensures valid target role, confidence bounds (0.0-1.0), and reasoning provided
- **Idempotency**: Handoff requests are tracked and prevented from duplicating work
- **Use Case**: Collections Agent → Customer Service Agent when customer inquiry detected

### 3. Customer Service Agent
- **Location**: [apps/api/app/agent.py](../apps/api/app/agent.py)
- **Task Type**: CustomerServiceAgentTask for handling inquiries and service requests
- **Actions**: send_message, create_service_case, no_action
- **Reasoning**: Context-aware decision making for customer communication
- **Prompt Building**: Tailored prompts for customer service scenario (temperature 0.2 for safety)

### 4. Comparative Evaluation
- **Same Test Harness**: Both agents use the same EvaluationHarness infrastructure
- **Different Scenarios**: Collections Agent evaluated on payment matching; Customer Service Agent on inquiry handling
- **Metrics**: Score (0.0-1.0), action_correct, outcome_correct, confidence tracking
- **Comparison**: Enables A/B testing and performance benchmarking between agents

## Architecture

### Agent Coordination Flow
```
1. Collections Agent receives unmatched payment event
   - Analyzes transaction and customer account
   - Proposes match or escalates

2. Escalation triggers handoff decision
   - If customer service issue detected → handoff to Customer Service Agent
   - Handoff validated through AgentHandoffProtocol
   - New task context passed to target agent

3. Customer Service Agent handles inquiry
   - Responds to customer or creates case
   - Maintains isolation: can only use CS-specific tools
   - Results persisted alongside original task trail

4. Manager Agent (optional) reviews high-impact decisions
   - Can approve or reject proposed actions
   - Has oversight visibility of both agents' work
```

### Role Tool Matrix
| Tool | Collections | Customer Service | Manager |
|------|-------------|------------------|---------|
| propose_payment_match | ✓ | ✗ | ✗ |
| send_customer_message | ✗ | ✓ | ✗ |
| approve_payment_match | ✗ | ✗ | ✓ |
| open_case | ✓ | ✗ | ✗ |
| create_service_case | ✗ | ✓ | ✗ |
| search_customers | ✓ | ✓ | ✓ |

## Testing

### Test File
- **Location**: [apps/api/tests/test_multi_agent.py](../apps/api/tests/test_multi_agent.py)
- **Coverage**:
  - AgentHandoffProtocol: allowed/disallowed handoffs, tool isolation, validation
  - CustomerServiceAgent: initialization, prompt building, decision parsing
  - Comparative: role tool coverage verification

### Test Results
```bash
export PYTHONPATH=apps/api
pytest apps/api/tests/test_multi_agent.py -q
# Result: 13 passed
```

### Full Suite
```bash
pytest apps/api/tests/ -q
# Result: 50 passed (includes all prior stages + Stage 9)
```

## Exit Criteria (All Met)
- [x] Two agents implemented with distinct tool sets and responsibilities
- [x] Handoff protocol validates role isolation and prevents invalid transitions
- [x] Agent context properly passed between handoffs with reasoning trail
- [x] Both agents tested independently and for comparative evaluation
- [x] No shared state corruption or tool permission violations

## Example Usage

### Creating a Collections Agent Task
```python
from app.agent import CollectionsAgent, CollectionsAgentTask
from app.models import Organization

agent = CollectionsAgent()
task = CollectionsAgentTask(
    id='task1',
    organization_id=1,
    run_id='run1',
    task_type='match_unmatched_payment',
    context={
        'transaction_id': 42,
        'charge_id': 43,
        'customer_name': 'John Doe',
    }
)
result_task = await agent.run_task(task)
```

### Initiating a Handoff
```python
from app.multi_agent import AgentContext, AgentHandoffProtocol, AgentRole

protocol = AgentHandoffProtocol()
context = AgentContext(
    organization_id=1,
    run_id='run1',
    actor_agent=AgentRole.COLLECTIONS_AGENT,
    task_id='task1',
    reasoning_summary='Customer has billing question',
    confidence=0.8,
)

handoff = protocol.create_handoff(
    from_agent=AgentRole.COLLECTIONS_AGENT,
    to_agent=AgentRole.CUSTOMER_SERVICE_AGENT,
    reason='Customer inquiry detected during payment review',
    task_id='task1',
    context=context,
)

if handoff:
    # Pass to Customer Service Agent
    cs_task = CustomerServiceAgentTask(...)
    result = await cs_agent.run_task(cs_task)
```

## Monitoring Multi-Agent Behavior

1. **Handoff Tracking**:
   - Audit events log all handoffs with reason and confidence
   - Rejected handoffs indicate protocol violations

2. **Agent Metrics**:
   - Tool call success rate per agent
   - Decision confidence distribution
   - Cross-agent task completion time

3. **Evaluation Comparison**:
   - Collections Agent: average score on payment matching scenarios
   - Customer Service Agent: average score on customer inquiry scenarios
   - Comparative baseline: human expert performance

---

**Next Stage**: Stage 10 — Deployment and Release (final stage)
