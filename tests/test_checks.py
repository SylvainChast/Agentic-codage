from support import ProjectCase
from agentic_codage.checks import check
from agentic_codage.lifecycle import transition
from agentic_codage.store import now


class CheckTests(ProjectCase):
    def test_trusted_scope_detects_untracked_outside_changes(self):
        task = self.task()
        base = self.commit()
        (self.root / "src/app.py").write_text("value = 2\n")
        self.assertTrue(check(self.store, base, task["id"])["ok"])
        (self.root / "outside.txt").write_text("unexpected")
        result = check(self.store, base, task["id"])
        self.assertFalse(result["ok"])
        self.assertTrue(any("outside.txt" in e for e in result["errors"]))

    def test_scope_changes_cannot_authorize_themselves(self):
        task = self.task()
        base = self.commit()
        task["scope"].append("outside.txt")
        self.store.put("tasks", task)
        (self.root / "outside.txt").write_text("unexpected")
        self.assertFalse(check(self.store, base, task["id"])["ok"])

    def test_new_task_requires_planning_on_base(self):
        base = self.commit()
        task = self.task()
        result = check(self.store, base, task["id"])
        self.assertFalse(result["ok"])
        self.assertTrue(any("registered" in e for e in result["errors"]))

    def test_cycles_fail(self):
        a = self.task()
        b = self.task(depends_on=[a["id"]])
        a["depends_on"] = [b["id"]]
        self.store.put("tasks", a)
        self.assertFalse(check(self.store)["ok"])

    def test_expired_exception_and_resolved_finding_fail(self):
        finding = dict(id="F-test", created_at=now(), title="Risk", severity="high", status="open",
                       owner="owner", paths=["src"], evidence="Reproduction", resolution=None)
        self.store.put("findings", finding, new=True)
        exception = dict(id="X-test", created_at=now(), finding="F-test", owner="owner",
                         reason="Temporary fixture", expires_at="2000-01-01T00:00:00+00:00", paths=["src"])
        self.store.put("exceptions", exception, new=True)
        self.assertFalse(check(self.store)["ok"])
        exception["expires_at"] = "2099-01-01T00:00:00+00:00"
        self.store.put("exceptions", exception)
        self.assertTrue(check(self.store)["ok"])
        finding.update(status="resolved", resolution="Verified fix")
        self.store.put("findings", finding)
        self.assertFalse(check(self.store)["ok"])
