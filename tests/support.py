import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_codage.bootstrap import initialize
from agentic_codage.lifecycle import create_task, record_run, transition
from agentic_codage.leases import acquire
from agentic_codage.store import Store, atomic_write, canonical


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Framework test fixture")
        initialize(self.store, "Fixture", "EUR")
        (self.root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
        self.set_checks(["{python}", "-c", "assert 1 + 1 == 2"])

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "Test fixture")
        return self.store.head()

    def set_checks(self, argv, timeout=10):
        p = self.store.policy()
        p["checks"] = [dict(name="test", argv=argv, timeout_seconds=timeout)]
        atomic_write(self.store.meta / "policy.json", canonical(p))

    def task(self, owner="writer", scope=None, budget=10000, **kw):
        defaults = dict(title="Fixture task", owner=owner, scope=scope or ["src"],
                        criteria=["Value behaves correctly"], deliverables=["Working value"],
                        budget_minor=budget, max_runs=5, resources=[], decisions=[], depends_on=[])
        defaults.update(kw)
        return create_task(self.store, **defaults)

    def active(self, **kw):
        task = self.task(**kw)
        acquire(self.store, task, task["owner"], 3600)
        return transition(self.store, task, "start", task["owner"])

    def run_record(self, task, **kw):
        fields = dict(task=task["id"], actor=task["owner"], model="test-fixture-no-llm",
                      purpose="implementation", outcome="succeeded", currency="EUR",
                      llm_cost_minor=100, infra_cost_minor=0, human_seconds=0,
                      human_rate_minor=0, cost_source="actual", cost_note="Synthetic test amount",
                      summary="Test execution fixture", next_step="Review", input_tokens=None, output_tokens=None)
        fields.update(kw)
        return record_run(self.store, **fields)
