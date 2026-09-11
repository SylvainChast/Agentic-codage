import sys
from pathlib import Path
from support import ProjectCase
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ci_scope import assess
from agentic_codage.store import FrameworkError


class CIScopeTests(ProjectCase):
    def event(self, base, body):
        return {"pull_request": {"base": {"sha": base}, "body": body}}

    def test_code_pr_uses_registered_task_and_platform_base(self):
        task = self.task()
        base = self.commit()
        (self.root / "src/app.py").write_text("value = 2\n")
        self.assertTrue(assess(self.store, self.event(base, f"Task: {task['id']}"))["ok"])

    def test_planning_cannot_change_source_code(self):
        base = self.commit()
        (self.root / "src/app.py").write_text("value = 2\n")
        self.assertFalse(assess(self.store, self.event(base, "Type: planning"))["ok"])

    def test_planning_can_register_new_task(self):
        base = self.commit()
        self.task()
        # CI works against committed PR changes; add the new planning files to index.
        self.git("add", ".")
        self.assertTrue(assess(self.store, self.event(base, "Type: planning"))["ok"])

    def test_missing_pr_contract_is_rejected(self):
        base = self.commit()
        with self.assertRaises(FrameworkError):
            assess(self.store, self.event(base, "Some vague PR description"))
