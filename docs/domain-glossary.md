# Tiny Company Domain Glossary

## Core entities

- Organization: the simulated academy; the top-level business unit.
- Customer: an individual payer or student record connected to an organization.
- Charge: an expected recurring amount due at a certain date.
- BankTransaction: a posted payment event from the bank feed.
- PaymentReceipt: evidence sent by the customer that supports a payment claim.
- CustomerMessage: an inbound message from a customer about billing or account status.
- Case: an operations case created when an issue requires attention.
- AuditEvent: an immutable record of an important system or workflow action.

## Lifecycle notes

- A charge becomes due when its scheduled date is reached.
- A bank transaction may be matched to a charge by reference, amount, or customer evidence.
- A receipt may be attached to a transaction to support a payment claim.
- A customer message or ambiguous payment can open a case requiring human review.
- Approval events are recorded as audit records with a clear outcome and actor.

## Invariants

- A charge belongs to exactly one customer and one organization.
- A bank transaction may reference a customer but must remain traceable to the organization.
- Domain mutations go through services, not ad hoc table writes.
- Ground truth stays in evaluator-only fixtures and simulation state.
