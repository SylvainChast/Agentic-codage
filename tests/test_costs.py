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

    def test_delivery_total_freezes_attempts_and_separates_other_tasks(self):
        from agentic_codage.costs import task_report
        from agentic_codage.evidence import verify, review, accept
        from agentic_codage.lifecycle import transition
        task = self.active(max_runs=10)
        self.run_record(task, outcome='failed', llm_cost_minor=200)
        self.run_record(task, llm_cost_minor=300, human_seconds=60, human_rate_minor=6000)
        self.run_record(task, actor='planner', purpose='coordination', llm_cost_minor=50)
        self.run_record(task, actor='reviewer', purpose='review', llm_cost_minor=25)
        before = task_report(self.store, task['id'])
        self.assertIsNone(before['delivery']['total_cost_minor'])
        proof = verify(self.store, task['id'])
        task = transition(self.store, task, 'submit', task['owner'])
        verdict = review(self.store, task, 'reviewer', 'approve', 'Fixture', task['criteria'], proof['id'])
        task = accept(self.store, task, verdict['id'], 'human')
        self.run_record(task, llm_cost_minor=10, purpose='coordination')
        other = self.active(scope=['other'])
        self.run_record(other, llm_cost_minor=900)
        result = task_report(self.store, task['id'])
        self.assertEqual(result['delivery']['total_cost_minor'], 675)
        self.assertEqual(result['delivery']['later_known_cost_minor'], 10)
        self.assertEqual(result['components']['human_minor'], 100)
        self.assertEqual(result['delivery']['runs'], 4)
        self.assertEqual(len(result['by_purpose']), 3)

    def test_accepted_unknown_and_estimated_totals_remain_honest(self):
        from agentic_codage.costs import delivery_cost
        task = self.active()
        run = self.run_record(task, cost_source='unknown', llm_cost_minor=None)
        task.update(status='accepted', acceptance=dict(accepted_at='fixture', run_ids=[run['id']]))
        result = delivery_cost(task, [run])
        self.assertIsNone(result['total_cost_minor'])
        self.assertEqual(result['state'], 'incomplete')
        run.update(cost_source='estimate', llm_cost_minor=42)
        result = delivery_cost(task, [run])
        self.assertEqual(result['total_cost_minor'], 42)
        self.assertEqual(result['state'], 'estimated')
        with self.assertRaises(FrameworkError): delivery_cost(task, [])
