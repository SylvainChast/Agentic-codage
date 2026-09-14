"""Public starter choice, provenance and downstream preparation invalidation."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

from support import ProjectCase
import test_method
from agentic_codage.method import artifacts, starters, workflow, catalog
from agentic_codage.store import FrameworkError, task_contract
from agentic_codage.orchestration import coordination

BIN = Path(__file__).resolve().parents[1] / 'bin/framework'


class ArchitectureTests(ProjectCase):
    prepare = test_method.MethodTests.prepare
    doc = test_method.MethodTests.doc
    approve = test_method.MethodTests.approve

    def test_public_catalog_is_explicit_and_returns_isolated_values(self):
        result = starters.catalog()
        self.assertEqual({p['id'] for p in result['starters']}, {'nextjs-saas', 'open-saas', 'fastapi-react'})
        self.assertTrue(all(p['license'] == 'MIT' and p['license_url'] for p in result['starters']))
        result['starters'][0]['stack'].clear()
        self.assertTrue(starters.catalog()['starters'][0]['stack'])
        self.assertIn('not a code audit', result['verification'])

    def test_cli_supports_custom_existing_and_exclusive_modes(self):
        task = self.prepare('express')
        def command(*args):
            return subprocess.run([sys.executable, str(BIN), '--root', str(self.root),
                'method', 'architecture', task['id'], *args], capture_output=True, text=True)
        result = command('--custom', '--stack', 'Django', '--stack', 'PostgreSQL', '--constraint', 'Self-hosted')
        self.assertEqual(result.returncode, 0, result.stderr)
        choice = json.loads(result.stdout)['task']['method']['architecture']
        self.assertEqual(choice['stack'], ['Django', 'PostgreSQL'])
        self.assertEqual(workflow.packet(self.store, self.store.get('tasks', task['id']), 'architecture')['architecture'], choice)
        self.assertNotEqual(command('--custom', '--existing').returncode, 0)
        self.assertNotEqual(command('--custom').returncode, 0)
        self.assertNotEqual(command('--boilerplate', 'shipsaas').returncode, 0)
        result = command('--existing')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['task']['method']['architecture']['mode'], 'existing')
        self.assertEqual(json.loads(result.stdout)['installed'], False)

    def test_boilerplate_needs_full_revision_before_architecture_registration(self):
        task = self.prepare('express')
        result = starters.select(self.store, task, boilerplate='nextjs-saas')
        self.assertFalse(result['downloaded'])
        self.assertIn('Pin the inspected', ' '.join(workflow.status(self.store, task)['problems']))
        with self.assertRaisesRegex(FrameworkError, 'Pin the inspected'):
            self.doc(task, 'architecture')
        self.assertFalse(self.store.all('artifacts'))
        for bad in ('main', 'abc123', 'z' * 40):
            with self.assertRaises(FrameworkError):
                starters.select(self.store, task, boilerplate='nextjs-saas', revision=bad)
        starters.select(self.store, task, boilerplate='nextjs-saas', revision='a' * 40)
        architecture = self.doc(task, 'architecture')
        self.assertIn('architecture_basis', architecture)
        self.doc(task, 'plan', [architecture['id']])
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])
        self.assertEqual(catalog.parents('plan', task['method']), ['architecture'])

    def test_change_invalidates_architecture_story_review_and_running_context(self):
        task = self.prepare()
        starters.select(self.store, task, custom=True, stack=['Django'], constraints=['Single region'])
        architecture = self.doc(task, 'architecture')
        stories = self.doc(task, 'stories', [architecture['id']])
        self.approve(task, stories)
        design = self.doc(task, 'design', [stories['id']])
        self.doc(task, 'plan', [design['id']])
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])
        session = dict(task=task['id'], contract=task_contract(task))
        coordination.initialize(self.store, task, session)
        starters.select(self.store, task, custom=True, stack=['Django'], constraints=['Two regions'])
        problems = workflow.status(self.store, task)['problems']
        self.assertTrue(any('different choice' in p for p in problems))
        self.assertFalse(artifacts.approval(self.store, task, stories))
        with self.assertRaisesRegex(FrameworkError, 'contract changed'):
            coordination.assert_current(self.store, session)
        # Re-registration of architecture alone cannot silently approve old downstream inputs.
        self.doc(task, 'architecture')
        with self.assertRaisesRegex(FrameworkError, 'unselected revision'):
            workflow.require_ready(self.store, task)

    def test_choices_reject_inconsistent_catalog_data_and_terminal_tasks(self):
        task = self.prepare('express')
        starters.select(self.store, task, boilerplate='open-saas', revision='b' * 40)
        choice = deepcopy(task['method']['architecture'])
        choice['repository'] = 'https://example.invalid/private-kit'
        with self.assertRaises(FrameworkError): starters.validate_choice(choice)
        with self.assertRaises(FrameworkError):
            starters.select(self.store, task, boilerplate='open-saas', stack=['Other'])
        with self.assertRaises(FrameworkError):
            starters.select(self.store, task, existing=True, revision='b' * 40)
        for state in ('accepted', 'cancelled'):
            terminal = deepcopy(task); terminal['status'] = state
            with self.assertRaises(FrameworkError): starters.select(self.store, terminal, existing=True)

    def test_unconfigured_legacy_architecture_keeps_its_existing_behavior(self):
        task = self.prepare('express')
        self.doc(task, 'plan')
        original = artifacts.baseline(task)
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])
        self.assertEqual(artifacts.baseline(task), original)
        self.assertNotIn('architecture', catalog.required(task['method']))
        self.assertNotIn('architecture', workflow.packet(self.store, task, 'execute'))
        session = dict(task=task['id'], contract=task_contract(task))
        coordination.initialize(self.store, task, session)
        # Same packet shape as a session created before architecture choice support.
        session['method_context'].pop('architecture', None)
        coordination.assert_current(self.store, session)
