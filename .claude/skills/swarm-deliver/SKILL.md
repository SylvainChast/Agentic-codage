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
