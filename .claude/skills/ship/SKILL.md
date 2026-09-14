---
name: ship
description: Prepare a verified change for a pull request within existing authorization.
---

Run the Agentic Codage ship procedure for the user's request.
Read `.framework/OPERATING.md` and identify the task from the request or current context.
Read only `.framework/method/ship.md`, then use `framework method prompt ship --task TASK`
for its focused context. In this source checkout use `python3 bin/framework`.
If no task exists, register a bounded task with an explicit budget, owner and criteria first.
Respect the user's model choice and existing permissions; do not infer deployment authority.
