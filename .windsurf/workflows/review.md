---
description: Review the implementation against requirements and quality evidence.
---

# review

Run the Agentic Codage review procedure for the user's request.
Read `.framework/OPERATING.md` and identify the task from the request or current context.
Read only `.framework/method/review.md`, then use `framework method prompt review --task TASK`
for its focused context. In this source checkout use `python3 bin/framework`.
If no task exists, register a bounded task with an explicit budget, owner and criteria first.
Respect the user's model choice and existing permissions; do not infer deployment authority.
