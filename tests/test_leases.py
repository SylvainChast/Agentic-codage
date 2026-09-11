import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from support import ProjectCase
from agentic_codage.leases import acquire, list_leases, release
from agentic_codage.store import FrameworkError, Store


class LeaseTests(ProjectCase):
    def test_overlapping_parent_path_conflicts(self):
        a = self.task(scope=["src"])
        b = self.task(owner="other", scope=["src/app.py"])
        acquire(self.store, a, a["owner"], 100)
        with self.assertRaises(FrameworkError):
            acquire(self.store, b, b["owner"], 100)

    def test_resource_conflicts_even_when_paths_differ(self):
        a = self.task(scope=["src/a"], resources=["api:billing"])
        b = self.task(owner="other", scope=["src/b"], resources=["api:billing"])
        acquire(self.store, a, a["owner"], 100)
        with self.assertRaises(FrameworkError):
            acquire(self.store, b, b["owner"], 100)

    def test_prefix_boundary_and_expiry(self):
        a = self.task(scope=["src/a"])
        b = self.task(owner="other", scope=["src/ab"])
        with patch("agentic_codage.leases.time.time", return_value=100):
            acquire(self.store, a, a["owner"], 5)
            acquire(self.store, b, b["owner"], 5)
            self.assertEqual(len(list_leases(self.store)), 2)
        with patch("agentic_codage.leases.time.time", return_value=106):
            self.assertEqual(list_leases(self.store), [])

    def test_wrong_owner_cannot_release(self):
        task = self.task()
        acquire(self.store, task, task["owner"], 100)
        with self.assertRaises(FrameworkError):
            release(self.store, task["id"], "impostor")
        self.assertEqual(len(list_leases(self.store)), 1)

    def test_two_processes_cannot_both_reserve_same_scope(self):
        tasks = [self.task(owner=name) for name in ("one", "two")]
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
        def run(task):
            return subprocess.run([sys.executable, "-m", "agentic_codage", "--root", str(self.root),
                                   "lease", "acquire", task["id"], "--owner", task["owner"]],
                                  env=env, capture_output=True)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(run, tasks))
        self.assertEqual(sorted(r.returncode for r in results), [0, 2])
        self.assertEqual(len(list_leases(self.store)), 1)

    def test_worktrees_share_database(self):
        a = self.task()
        b = self.task(owner="other")
        self.commit()
        path = self.root / "other-worktree"
        self.git("worktree", "add", "--detach", str(path), "HEAD")
        self.addCleanup(lambda: self.git("worktree", "remove", "--force", str(path)))
        acquire(self.store, a, a["owner"], 100)
        with self.assertRaises(FrameworkError):
            acquire(Store(path), b, b["owner"], 100)
