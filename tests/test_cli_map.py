import json
import os
import re
import subprocess
import sys
from pathlib import Path

from support import ProjectCase
from agentic_codage.map import render
from agentic_codage.store import FrameworkError


class MapAndCliTests(ProjectCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "bin/framework"),
                               "--root", str(self.root), *args], capture_output=True, text=True)

    def test_cli_output_is_json_and_bad_records_fail(self):
        result = self.cli("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        result = self.cli("task", "show", "../../bad")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stderr)["ok"])

    def test_map_escapes_untrusted_html_and_detects_staleness(self):
        task = self.task(title='</script><script>alert("bad")</script>')
        result = render(self.store)
        text = Path(result["path"]).read_text(encoding="utf-8")
        self.assertNotIn(task["title"], text)
        self.assertIn('\\u003c/script>', text)
        self.assertTrue(render(self.store, check_only=True)["ok"])
        task["title"] = "Changed"
        self.store.put("tasks", task)
        with self.assertRaises(FrameworkError):
            render(self.store, check_only=True)

    def test_map_content_is_reproducible_and_survives_commit(self):
        render(self.store)
        self.commit()
        self.assertTrue(render(self.store, check_only=True)["ok"])

    def test_verify_exit_one_for_failed_checks(self):
        task = self.active()
        self.set_checks(["{python}", "-c", "raise SystemExit(3)"])
        result = self.cli("verify", task["id"])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["passed"])
