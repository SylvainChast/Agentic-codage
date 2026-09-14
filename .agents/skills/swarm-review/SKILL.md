---
name: swarm-review
description: Independently review a submitted Agentic Codage task against its contract, diff and recorded verification. Use for a requested task review, not implementation.
---

Read `.framework/OPERATING.md`, the task, applicable decisions, diff and evidence. Use the CLI's
subcommand help. Review observable acceptance criteria, error paths, interface compatibility,
security impact and the scope of the actual tests. Do not edit the candidate while reviewing it.

Record every criterion using its exact text and summarize evidence and remaining risks. Check
`framework check` and require current verification for approval. Record `request_changes` when
criteria are not met; missing or failed verification prevents an approval record. A reviewer may
write a finding/handoff explaining a failure before fresh evidence is available.

Use a reviewer identity distinct from every declared implementer. This declaration is not
an authenticated approval: repository protection and real platform reviews enforce authority.
Record the cost of this review with purpose `review`, including an unknown amount if necessary.
Do not resolve a semantic conflict by picking an author's preference; compare both options to
the contract, document the arbitration, and escalate only decisions outside existing authority.

For a task with `method` configured, load `.framework/method/review.md` and run
`framework method prompt review --task TASK` for the selected preparation and its current gate.
Record the execution with `--stage review`. This is the implementation review; a story readiness
review is a separate `method review` record and cannot replace it.
