---
description: Implement a prepared task using its scope, tests and coordination gates.
agent: agent
---

Run the Agentic Codage execute procedure for the user's request.
Read `.framework/OPERATING.md` and identify the task from the request or current context.
Read only `.framework/method/execute.md`, then use `framework method prompt execute --task TASK`
for its focused context. In this source checkout use `python3 bin/framework`.
If no task exists, register a bounded task with an explicit budget, owner and criteria first.
Respect the user's model choice and existing permissions; do not infer deployment authority.
