from support import ProjectCase
from agentic_codage import leases
from agentic_codage.checks import check
from agentic_codage.costs import report
from agentic_codage.evidence import accept, review, verify
from agentic_codage.lifecycle import transition
from agentic_codage.store import FrameworkError


class LifecycleTests(ProjectCase):
    def submitted(self):
        task = self.active()
        self.run_record(task)
        return transition(self.store, task, "submit", task["owner"])

    def approve(self, task):
        proof = verify(self.store, task["id"])
        return review(self.store, task, "reviewer", "approve", "Criteria verified in fixture", task["criteria"], proof["id"])

    def test_full_acceptance_requires_current_proof_and_review(self):
        task = self.submitted()
        rev = self.approve(task)
        accepted = accept(self.store, task, rev["id"], "maintainer")
        self.assertEqual(accepted["status"], "accepted")
        self.assertTrue(check(self.store)["ok"])
        self.assertEqual(report(self.store)["accepted_deliverables"], 1)

    def test_cannot_start_without_lease(self):
        task = self.task()
        with self.assertRaises(FrameworkError):
            transition(self.store, task, "start", task["owner"])

    def test_dependency_must_be_accepted(self):
        dependency = self.task(scope=["docs"])
        task = self.task(depends_on=[dependency["id"]])
        leases.acquire(self.store, task, task["owner"], 100)
        with self.assertRaises(FrameworkError):
            transition(self.store, task, "start", task["owner"])

    def test_no_self_review(self):
        task = self.submitted()
        proof = verify(self.store, task["id"])
        with self.assertRaises(FrameworkError):
            review(self.store, task, task["owner"], "approve", "No", task["criteria"], proof["id"])

    def test_secondary_implementer_cannot_review(self):
        task = self.submitted()
        self.run_record(task, actor="another-writer")
        proof = verify(self.store, task["id"])
        with self.assertRaises(FrameworkError):
            review(self.store, task, "another-writer", "approve", "No", task["criteria"], proof["id"])

    def test_stale_code_or_contract_rejects_acceptance(self):
        task = self.submitted()
        rev = self.approve(task)
        (self.root / "src/app.py").write_text("value = 2\n")
        with self.assertRaises(FrameworkError):
            accept(self.store, task, rev["id"], "maintainer")
        (self.root / "src/app.py").write_text("value = 1\n")
        task["criteria"] = ["Changed criterion"]
        self.store.put("tasks", task)
        with self.assertRaises(FrameworkError):
            accept(self.store, task, rev["id"], "maintainer")

    def test_failed_checks_are_retained_and_block_approval(self):
        task = self.submitted()
        self.set_checks(["{python}", "-c", "raise SystemExit(1)"])
        proof = verify(self.store, task["id"])
        self.assertFalse(proof["passed"])
        self.assertEqual(len(self.store.all("evidence")), 1)
        with self.assertRaises(FrameworkError):
            review(self.store, task, "reviewer", "approve", "No", task["criteria"], proof["id"])

    def test_timeout_is_failure(self):
        task = self.active()
        self.set_checks(["{python}", "-c", "import time; time.sleep(20)"], timeout=1)
        proof = verify(self.store, task["id"])
        self.assertFalse(proof["passed"])
        self.assertEqual(proof["checks"][0]["exit_code"], 124)

    def test_check_cannot_change_code_and_claim_success(self):
        task = self.active()
        self.set_checks(["{python}", "-c", "from pathlib import Path; Path('src/app.py').write_text('changed')"])
        self.assertFalse(verify(self.store, task["id"])["passed"])

    def test_tampered_logs_detected(self):
        task = self.submitted()
        rev = self.approve(task)
        proof = self.store.get("evidence", rev["evidence"])
        (self.root / proof["checks"][0]["log"]).write_text("fake")
        self.assertFalse(check(self.store)["ok"])
        with self.assertRaises(FrameworkError):
            accept(self.store, task, rev["id"], "maintainer")

    def test_exhausted_budget_blocks_next_start_but_records_overrun(self):
        task = self.active(budget=100)
        self.run_record(task, llm_cost_minor=200)
        self.assertTrue(report(self.store)["tasks"][0]["over_budget"])
        with self.assertRaises(FrameworkError):
            transition(self.store, task, "start", task["owner"])

    def test_missing_handoff_blocks_submission(self):
        task = self.active()
        with self.assertRaises(FrameworkError):
            transition(self.store, task, "submit", task["owner"])

    def test_portfolio_accepted_unit_cost_includes_other_failed_tasks(self):
        task = self.submitted()
        rev = self.approve(task)
        accept(self.store, task, rev["id"], "maintainer")
        leases.release(self.store, task["id"], task["owner"])
        failed = self.active(owner="other")
        self.run_record(failed, outcome="failed", llm_cost_minor=300)
        transition(self.store, failed, "cancel", failed["owner"])
        costs = report(self.store)
        self.assertEqual(costs["cost_per_accepted_deliverable_minor"], 400)
        self.assertEqual(costs["cost_per_executed_task_minor"], 200)
