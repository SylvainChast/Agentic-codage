---
name: swarm-orchestrate
description: Configure user-selected model roles and run or inspect a bounded Agentic Codage orchestration. Use when the user asks to delegate a registered task through the orchestration controller.
---

Read `.framework/OPERATING.md`, the task contract and `.framework/orchestration.json`.
Use `framework orchestration --help`. The user selects each role's exact model and adapter.
Never replace their choice with a preferred model, rank whitelist or silent fallback. A capable
planning model is useful, but a name or price tier does not establish delegation ability.

If configuration is absent, obtain the missing model/adapter choice before launching a paid
invocation. `orchestration init --model ID --adapter codex|claude|command` assigns that explicit
choice to all four roles initially. Use `set-role` for a different worker, reviewer or arbiter.
Use an explicit JSON argv for a custom command bridge. Inspect `doctor`, which checks executable
presence only. Read `docs/orchestration.md` in this framework repository, or `docs/framework.md`
in an initialized project, for limits and transport details.

Commit source, policy, configuration and the task contract before `orchestration run TASK`.
Confirm the existing user authorization covers actual model use and the task budget. This does
not require another confirmation when already authorized. The run is foreground; the controller
owns leases, isolated worktrees, dependency scheduling, all invocation costs, verification,
separate reviewer sessions and bounded arbitration/replanning. Do not duplicate these records
or recursively launch this skill from a controller-managed worker.

Inspect `orchestration show SESSION` and `framework costs`. `feedback` supplies a message at the
next planning round; `cancel` requests subprocess termination. A blocked run preserves evidence
and costs. A fresh `run` starts a fresh plan against the current committed source; it does not
silently resume a partial candidate. Never delete retained candidates to disguise failed work.

Only `orchestration integrate SESSION --actor ACTOR` applies the approved candidate and records
acceptance. Use it within the user's existing authority after reviewing the result. It checks
source freshness; it does not commit, push or deploy. Generate `framework map` afterward.
Report limitations, unknown billing and missing model observations; never fabricate independence,
provider identity or a live provider test from an offline fixture.

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
