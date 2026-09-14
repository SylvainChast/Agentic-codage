---
name: swarm-deliver
description: Deliver a bounded task in an Agentic Codage project with reservations, execution costs, evidence and a handoff. Use when .framework/policy.json exists and implementation is requested.
---

Read `.framework/OPERATING.md` from the project root. Inspect `framework task show TASK` and
`framework context PATH` before writing. Use `framework --help` and subcommand help rather
than assuming provider-specific agent tools exist.

Reserve the task's literal paths and shared interface resources, start the task, and implement
its acceptance criteria. Record each execution with costs (including failed attempts), model,
summary and next step. Use `unknown` when billing is unavailable. Recheck the run/budget limit
before another attempt. Never translate a subscription into a fictitious zero cost.

Execute configured verification and submit a handoff for independent review. The implementation
agent does not impersonate the reviewer. Do not accept, merge or deploy beyond existing user
authorization. If delegation tools are unavailable, leave the same files for another session
or a person. This skill is a workflow, not an agent launcher.

## Interface coordination and delivery cost

Define shared signatures, units and schemas in versioned `.framework/interfaces/I-*.json` records.
Import with `framework import interfaces FILE`; pin revisions with `task create --interface ID`.
Never overwrite a revision to unblock a worker. Read the task's interfaces and predecessor handoffs.
In controller-managed work, acknowledge all supplied interface references exactly; report required
changes in `change_requests` and stop rather than implement an incompatible change. Each batch
requires the user-selected orchestrator's checkpoint before dependents proceed. Budget that call.
In accompanied work, the pilot must explicitly transmit handoffs and arrange these checkpoints.

Use one task for one result to accept (dashboard, module, feature); keep every attempt, correction,
coordination and review attached to it. `framework costs --task ID` reports its delivery cost and
breakdowns. Unknown billing remains unknown. Acceptance freezes the included run ids; later runs
are separate from that delivery's total. Never claim that a recorded cost proves complete billing.
