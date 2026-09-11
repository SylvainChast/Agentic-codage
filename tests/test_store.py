from support import ProjectCase
from agentic_codage.store import FrameworkError, atomic_write, read_json, safe_relative, validate_record
from agentic_codage.bootstrap import initialize, sync_adapters


class StoreTests(ProjectCase):
    def test_task_id_cannot_escape(self):
        for ident in ("../../outside", "T-../secret", "/tmp/evil", "T-a/b"):
            with self.subTest(ident=ident), self.assertRaises(FrameworkError):
                self.store.get("tasks", ident)

    def test_literal_scope_rejects_traversal_and_globs(self):
        for path in ("../src", "/src", "src/../outside", "src/**", "src\\x", ".git/config", "src//x", "./src"):
            with self.subTest(path=path), self.assertRaises(FrameworkError):
                safe_relative(path)
        self.assertEqual(safe_relative("src/finance.py"), "src/finance.py")

    def test_strict_types_duplicate_keys_and_extra_fields(self):
        task = self.task()
        task["budget_minor"] = True
        with self.assertRaises(FrameworkError):
            validate_record("tasks", task)
        task["budget_minor"] = 100
        task["invented"] = "no"
        with self.assertRaises(FrameworkError):
            validate_record("tasks", task)
        path = self.root / "duplicate.json"
        path.write_text('{"a":1,"a":2}')
        with self.assertRaises(FrameworkError):
            read_json(path)

    def test_append_does_not_replace_existing_record(self):
        task = self.task()
        with self.assertRaises(FrameworkError):
            self.store.put("tasks", task, new=True)

    def test_fingerprint_tracks_code_not_lifecycle(self):
        before = self.store.fingerprint()
        task = self.active()
        self.run_record(task)
        self.assertEqual(before, self.store.fingerprint())
        (self.root / "src/app.py").write_text("value = 2\n")
        self.assertNotEqual(before, self.store.fingerprint())

    def test_fingerprint_tracks_deletions(self):
        self.commit()
        before = self.store.fingerprint()
        (self.root / "src/app.py").unlink()
        self.assertNotEqual(before, self.store.fingerprint())

    def test_adapters_refuse_to_overwrite_user_instructions(self):
        path = self.root / "CLAUDE.md"
        path.write_text("My important instructions")
        with self.assertRaises(FrameworkError):
            sync_adapters(self.store)
        self.assertEqual(path.read_text(), "My important instructions")

    def test_initialization_is_not_destructive(self):
        before = (self.store.meta / "policy.json").read_text()
        with self.assertRaises(FrameworkError):
            initialize(self.store, "Other", "USD")
        self.assertEqual(before, (self.store.meta / "policy.json").read_text())

    def test_symlink_escape_rejected(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            try:
                (self.store.meta / "tasks").rmdir()
                (self.store.meta / "tasks").symlink_to(Path(temp), target_is_directory=True)
            except OSError:
                self.skipTest("OS does not allow symlinks")
            with self.assertRaises(FrameworkError):
                self.task()
