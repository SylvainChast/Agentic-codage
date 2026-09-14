"""Preparation freshness, risk tracks, focused context and shipping refusal paths."""
import json
import tomllib
from pathlib import Path

from support import ProjectCase
from agentic_codage.store import FrameworkError, atomic_write, canonical
from agentic_codage.method import artifacts, workflow, shipping, catalog
from agentic_codage.evidence import verify, review, accept
from agentic_codage.lifecycle import transition
from agentic_codage.costs import task_report
from agentic_codage.bootstrap import adapter_files, sync_adapters


class MethodTests(ProjectCase):
    def prepare(self, track='feature', ui=False):
        task = self.active(scope=['src', 'docs'], max_runs=20)
        artifacts.initialize(self.store, task, track, ui)
        if track != 'express':
            artifacts.set_story(self.store, task, 'S-value', 2, ['value is an integer'])
        return task

    def doc(self, task, kind, inputs=(), filename=None, body=None):
        name = filename or f'docs/{kind}.md'
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = body or f'# {kind}\n\nFixture requirement: value must equal 2.\n'
        if kind in ('prd', 'stories'):
            from agentic_codage.method import templates
            values = {key: text for key in templates.schema(kind)['properties'] if key not in ('kind', 'schema_version')}
            if kind == 'prd':
                values.update(requirements='REQ-001: value is 2', acceptance='AC-001: assert value == 2')
            else:
                chosen = task['method'].get('story', dict(id='S-value', complexity=2, agent_notes=['value is an integer']))
                values.update(story=chosen['id'] + ': user receives value', criteria='AC-001: value == 2',
                              agent_notes='\n'.join(chosen['agent_notes']), complexity=f"Complexité: {chosen['complexity']}/5 — fixture")
            text = templates.render(kind, values)
        path.write_text(text, encoding='utf-8')
        return artifacts.register(self.store, task, kind, name, 'author', list(inputs))

    def approve(self, task, record):
        return artifacts.review(self.store, task, record['id'], 'independent', 'approve', 'Fixture review', [])

    def feature(self):
        task = self.prepare()
        stories = self.doc(task, 'stories')
        self.approve(task, stories)
        design = self.doc(task, 'design', [stories['id']])
        plan = self.doc(task, 'plan', [design['id'], stories['id']])
        return task, stories, design, plan

    def test_express_needs_only_plan_and_existing_tasks_stay_compatible(self):
        task = self.active()
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])
        # Keep this unrelated lease out of the preparation task's paths.
        from agentic_codage.leases import release
        release(self.store, task['id'], task['owner'])
        task = self.prepare('express')
        with self.assertRaisesRegex(FrameworkError, 'plan'):
            workflow.require_ready(self.store, task)
        self.doc(task, 'plan')
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])
        self.run_record(task)
        self.assertTrue(verify(self.store, task['id'])['passed'])

    def test_feature_missing_review_or_design_blocks_execution(self):
        task = self.prepare()
        stories = self.doc(task, 'stories')
        self.doc(task, 'plan')
        with self.assertRaisesRegex(FrameworkError, 'Method not ready'):
            verify(self.store, task['id'])
        with self.assertRaisesRegex(FrameworkError, 'reviewer'):
            artifacts.review(self.store, task, stories['id'], 'author', 'approve', 'bad', [])
        self.approve(task, stories)
        design = self.doc(task, 'design', [stories['id']])
        self.doc(task, 'plan', [design['id'], stories['id']])
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])

    def test_upstream_edit_and_selection_change_invalidate_descendants(self):
        task, stories, _, _ = self.feature()
        original = (self.root / stories['path']).read_text()
        (self.root / stories['path']).write_text('changed requirements')
        with self.assertRaisesRegex(FrameworkError, 'Stale'):
            workflow.require_ready(self.store, task)
        # Even two current files cannot silently mix old and selected revisions.
        (self.root / stories['path']).write_text(original)
        new = self.doc(task, 'stories', filename='docs/stories-v2.md')
        self.approve(task, new)
        with self.assertRaisesRegex(FrameworkError, 'unselected revision'):
            workflow.require_ready(self.store, task)

    def test_changed_task_criteria_invalidate_readiness_review(self):
        task, _, _, _ = self.feature()
        task['criteria'] = ['Different required behavior']
        self.store.put('tasks', task)
        with self.assertRaises(FrameworkError):
            workflow.require_ready(self.store, task)

    def test_product_ui_requires_shared_foundations_and_explicit_links(self):
        task = self.prepare('product', True)
        prd = self.doc(task, 'prd')
        arch = self.doc(task, 'architecture', [prd['id']])
        system = self.doc(task, 'design-system', [prd['id']])
        stories = self.doc(task, 'stories', [prd['id'], arch['id']])
        self.approve(task, stories)
        design = self.doc(task, 'design', [stories['id'], system['id']])
        self.doc(task, 'plan', [design['id']])
        self.assertTrue(workflow.require_ready(self.store, task)['ready'])

    def test_context_budget_exposes_truncation_and_omits_unneeded_research(self):
        task, _, _, _ = self.feature()
        self.doc(task, 'research', body='irrelevant history' * 10000)
        result = workflow.packet(self.store, task, 'execute', max_chars=20)
        self.assertEqual(sum(len(d['excerpt']) for d in result['documents']), 20)
        self.assertTrue(result['documents'][0]['truncated'])
        self.assertNotIn('research', [d['kind'] for d in result['documents']])
        self.assertTrue(all(d['path'] and d['sha256'] for d in result['documents']))

    def test_stage_costs_include_framing_and_failed_research(self):
        task = self.prepare('express')
        self.run_record(task, stage='research', purpose='coordination', outcome='failed', llm_cost_minor=50)
        self.run_record(task, stage='prd', purpose='coordination', llm_cost_minor=150)
        self.run_record(task, stage='execute', llm_cost_minor=100)
        result = task_report(self.store, task['id'])
        self.assertEqual(result['known_cost_minor'], 300)
        self.assertEqual({r['name'] for r in result['by_stage']}, {'research', 'prd', 'execute'})

    def test_shipping_prepares_body_and_refuses_stale_or_untrusted_proof(self):
        task = self.prepare('express')
        self.doc(task, 'plan')
        base = self.commit()
        (self.root / 'src/app.py').write_text('value = 2\n')
        self.run_record(task)
        proof = verify(self.store, task['id'])
        task = transition(self.store, task, 'submit', task['owner'])
        verdict = review(self.store, task, 'reviewer', 'approve', 'Fixture', task['criteria'], proof['id'])
        result = shipping.prepare(self.store, task, base, verdict['id'])
        self.assertEqual(result['publication'], 'not_started')
        self.assertIn(task['id'], Path(result['body_file']).read_text())
        self.assertEqual(self.store.fingerprint(), proof['fingerprint'])
        (self.root / 'src/app.py').write_text('value = 3\n')
        with self.assertRaisesRegex(FrameworkError, 'stale'):
            shipping.prepare(self.store, task, base, verdict['id'])

    def test_adapter_generation_and_no_overwrite_preflight(self):
        generated = adapter_files()
        for step in catalog.STEPS:
            data = tomllib.loads(generated[f'.gemini/commands/{step}.toml'])
            self.assertIn('prompt', data)
            self.assertIn(f'.framework/method/{step}.md', data['prompt'])
        path = self.root / '.claude/skills/prd/SKILL.md'
        path.write_text('custom user skill')
        with self.assertRaisesRegex(FrameworkError, 'reconcile'):
            sync_adapters(self.store)
        self.assertEqual(path.read_text(), 'custom user skill')

    def test_rejected_story_revision_cannot_be_approved_without_new_registration(self):
        task = self.prepare()
        stories = self.doc(task, 'stories')
        artifacts.review(self.store, task, stories['id'], 'independent', 'request_changes', 'Missing case', ['No failure behavior'])
        self.approve(task, stories)
        self.assertFalse(artifacts.approval(self.store, task, stories))
        new = self.doc(task, 'stories', body='# Corrected story with failure behavior')
        self.approve(task, new)
        self.assertTrue(artifacts.approval(self.store, task, new))

    def test_controller_requires_preparation_and_receives_focused_context(self):
        import test_orchestration
        from agentic_codage.orchestration import engine
        from agentic_codage.leases import acquire
        task = test_orchestration.OrchestrationTests.setup_profile(self, scope=['src', 'docs'])
        artifacts.initialize(self.store, task, 'express', False)
        with self.assertRaisesRegex(FrameworkError, 'Method not ready'):
            engine.run(self.store, task['id'])
        self.assertFalse(self.store.all('runs'))
        acquire(self.store, task, task['owner'], 3600)
        task = transition(self.store, task, 'start', task['owner'])
        self.doc(task, 'plan')
        bridge = self.root / 'bridge.py'
        bridge.write_text(bridge.read_text().replace("elif role == 'worker':", "elif role == 'worker':\n    assert payload['coordination']['method_context']['documents'][0]['kind']=='plan'"))
        self.commit()
        result = engine.run(self.store, task['id'])
        self.assertTrue(result['ok'], result['message'])
        engine.integrate(self.store, result['id'], 'human')
        self.assertEqual(self.store.get('tasks', task['id'])['status'], 'accepted')

    def test_oversized_story_blocks_planning_and_later_score_change_needs_review(self):
        task, _, _, _ = self.feature()
        artifacts.set_story(self.store, task, 'S-value', 5, ['Needs decomposition'])
        with self.assertRaisesRegex(FrameworkError, 'complexity 5'):
            workflow.prompt(self.store, task, 'plan', 100)
        with self.assertRaises(FrameworkError):
            workflow.require_ready(self.store, task)
        artifacts.set_story(self.store, task, 'S-value', 3, ['Smaller scope'])
        with self.assertRaises(FrameworkError):
            workflow.require_ready(self.store, task)

    def test_document_templates_reject_unfilled_missing_and_duplicate_sections(self):
        from agentic_codage.method import templates
        task = self.prepare()
        target = 'docs/story-template.md'
        templates.scaffold(self.store, task, 'stories', target)
        with self.assertRaisesRegex(FrameworkError, 'completing'):
            artifacts.register(self.store, task, 'stories', target, 'author', [])
        with self.assertRaises(FrameworkError):
            templates.scaffold(self.store, task, 'stories', target)
        record = self.doc(task, 'stories')
        text = (self.root / record['path']).read_text()
        templates.parse('stories', text)
        for bad in (text.replace('## Dépendances et prérequis', '### Dépendances et prérequis'),
                    text + '\n## Complexité et découpage\nDuplicate',
                    text.replace('AC-001', 'missing-id')):
            with self.assertRaises(FrameworkError): templates.parse('stories', bad)

    def test_invocation_rechecks_preparation_contract_documents_and_reviews(self):
        from unittest.mock import patch
        from copy import deepcopy
        from agentic_codage.store import task_contract
        from agentic_codage.orchestration import coordination
        from agentic_codage.orchestration.calls import Calls
        task, stories, _, plan = self.feature()
        session = dict(id='O-preparation-test', task=task['id'], contract=task_contract(task),
                       profile={'roles': {'worker': {}}})
        coordination.initialize(self.store, task, session)
        coordination.assert_current(self.store, session)
        original_task = deepcopy(task)
        task['criteria'] = ['Different behavior']
        self.store.put('tasks', task)
        with self.assertRaisesRegex(FrameworkError, 'Task contract changed'):
            coordination.assert_current(self.store, session)
        self.store.put('tasks', original_task)
        plan_file = self.root / plan['path']
        original_body = plan_file.read_text()
        plan_file.write_text('Changed after launch')
        with self.assertRaisesRegex(FrameworkError, 'Stale'):
            coordination.assert_current(self.store, session)
        plan_file.write_text(original_body)
        artifacts.review(self.store, original_task, stories['id'], 'second-reviewer',
                         'request_changes', 'Missing case discovered', ['A failure case is unspecified'])
        with patch('agentic_codage.orchestration.transport.execute') as transport:
            with self.assertRaisesRegex(FrameworkError, 'Method not ready'):
                Calls(self.store, session).invoke('worker', {}, self.store)
            transport.assert_not_called()
        self.assertFalse(self.store.all('runs'))

    def test_worker_cannot_rewrite_registered_framing_even_with_doc_scope(self):
        from agentic_codage.orchestration.workspaces import commit_worker
        task = self.prepare('express')
        plan = self.doc(task, 'plan')
        base = self.commit()
        (self.root / plan['path']).write_text('Unauthorized changed plan')
        with self.assertRaisesRegex(FrameworkError, 'registered framing document'):
            commit_worker(self.store, base, ['docs'])
        self.assertEqual(self.store.head(), base)

    def test_later_story_rejection_blocks_integration_of_ready_candidate(self):
        import test_orchestration
        from agentic_codage.orchestration import engine
        from agentic_codage.leases import acquire
        task = test_orchestration.OrchestrationTests.setup_profile(self, scope=['src', 'docs'])
        acquire(self.store, task, task['owner'], 3600)
        task = transition(self.store, task, 'start', task['owner'])
        artifacts.initialize(self.store, task, 'feature', False)
        artifacts.set_story(self.store, task, 'S-value', 2, ['value is an integer'])
        stories = self.doc(task, 'stories')
        self.approve(task, stories)
        design = self.doc(task, 'design', [stories['id']])
        self.doc(task, 'plan', [design['id']])
        self.commit()
        session = engine.run(self.store, task['id'])
        self.assertTrue(session['ok'], session['message'])
        artifacts.review(self.store, task, stories['id'], 'later-reviewer', 'request_changes',
                         'New blocking omission', ['Permission case missing'])
        with self.assertRaisesRegex(FrameworkError, 'Method not ready'):
            engine.integrate(self.store, session['id'], 'human')
        self.assertEqual((self.root / 'src/app.py').read_text(), 'value = 1\n')
        self.assertIsNone(self.store.get('tasks', task['id'])['acceptance'])
