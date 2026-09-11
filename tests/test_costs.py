from support import ProjectCase
from agentic_codage.costs import report, run_cost
from agentic_codage.store import FrameworkError


class CostTests(ProjectCase):
    def test_failed_runs_and_human_time_are_counted(self):
        task = self.active()
        first = self.run_record(task, outcome="failed", llm_cost_minor=200,
                                human_seconds=600, human_rate_minor=6000, infra_cost_minor=50)
        self.assertEqual(run_cost(first), 1250)
        self.run_record(task, llm_cost_minor=100)
        costs = report(self.store)
        self.assertEqual(costs["total_known_cost_minor"], 1350)
        self.assertEqual(costs["cost_per_executed_task_minor"], 1350)
        self.assertIsNone(costs["cost_per_accepted_deliverable_minor"])
        self.assertEqual(costs["tasks"][0]["failed_runs"], 1)

    def test_unknown_is_not_zero(self):
        task = self.active()
        self.run_record(task, cost_source="unknown", llm_cost_minor=None, human_seconds=60, human_rate_minor=6000)
        costs = report(self.store)
        self.assertEqual(costs["total_known_cost_minor"], 100)
        self.assertFalse(costs["complete"])
        self.assertIsNone(costs["cost_per_executed_task_minor"])

    def test_estimates_and_explicit_zero_are_visible(self):
        task = self.active()
        self.run_record(task, llm_cost_minor=0, cost_source="estimate")
        costs = report(self.store)
        self.assertTrue(costs["complete"])
        self.assertEqual(costs["estimated_cost_runs"], 1)
        self.assertEqual(costs["total_known_cost_minor"], 0)

    def test_rejects_negative_mixed_or_inconsistent_costs(self):
        task = self.active()
        for fields in ({"llm_cost_minor":-1}, {"currency":"USD"},
                       {"cost_source":"unknown","llm_cost_minor":0},
                       {"cost_source":"actual","llm_cost_minor":None}):
            with self.subTest(fields=fields), self.assertRaises(FrameworkError):
                self.run_record(task, **fields)

    def test_human_rounding_is_half_up(self):
        task = self.active()
        run = self.run_record(task, llm_cost_minor=0, human_seconds=1800, human_rate_minor=1)
        self.assertEqual(run_cost(run), 1)

    def test_unproven_accepted_status_cannot_inflate_delivery_metrics(self):
        task = self.active()
        self.run_record(task)
        task["status"] = "accepted"
        self.store.put("tasks", task)
        with self.assertRaises(FrameworkError):
            report(self.store)
