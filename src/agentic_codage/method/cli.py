"""Portable procedure, artifact and readiness commands."""
from . import artifacts, catalog, workflow


def register(commands):
    parser = commands.add_parser('method', help='Adaptive framing, artifacts, readiness and PR preparation')
    subs = parser.add_subparsers(dest='method_action', required=True)
    subs.add_parser('catalog')
    subs.add_parser('starters')
    architecture = subs.add_parser('architecture')
    architecture.add_argument('task')
    mode = architecture.add_mutually_exclusive_group(required=True)
    from .starters import CATALOG
    mode.add_argument('--boilerplate', choices=CATALOG)
    mode.add_argument('--custom', action='store_true')
    mode.add_argument('--existing', action='store_true')
    architecture.add_argument('--revision')
    architecture.add_argument('--stack', action='append', default=[])
    architecture.add_argument('--constraint', action='append', default=[])

    template = subs.add_parser('template')
    template.add_argument('kind', choices=('prd', 'stories'))
    scaffold = subs.add_parser('scaffold')
    scaffold.add_argument('task')
    scaffold.add_argument('--kind', choices=('prd', 'stories'), required=True)
    scaffold.add_argument('--file', required=True)
    init = subs.add_parser('init')
    init.add_argument('task')
    init.add_argument('--track', choices=catalog.TRACKS, required=True)
    init.add_argument('--ui', action='store_true')
    for action in ('status', 'gate'):
        sub = subs.add_parser(action)
        sub.add_argument('task')
    prompt = subs.add_parser('prompt')
    prompt.add_argument('step', choices=catalog.STEPS)
    prompt.add_argument('--task', required=True)
    prompt.add_argument('--max-chars', type=int, default=12000)
    story = subs.add_parser('story')
    story.add_argument('task')
    story.add_argument('--id', required=True)
    story.add_argument('--complexity', type=int, choices=range(1, 6), required=True)
    story.add_argument('--note', action='append', required=True)
    record = subs.add_parser('record')
    record.add_argument('task')
    record.add_argument('--kind', choices=catalog.DOCUMENTS, required=True)
    record.add_argument('--file', required=True)
    record.add_argument('--author', required=True)
    record.add_argument('--input', action='append', default=[])
    use = subs.add_parser('use')
    use.add_argument('task')
    use.add_argument('artifact')
    review = subs.add_parser('review')
    review.add_argument('task')
    for field in ('artifact', 'reviewer', 'summary'):
        review.add_argument(f'--{field}', required=True)
    review.add_argument('--verdict', choices=('approve', 'request_changes'), required=True)
    review.add_argument('--finding', action='append', default=[])
    ship = subs.add_parser('ship')
    ship.add_argument('task')
    ship.add_argument('--base', required=True)
    ship.add_argument('--review', required=True)


def dispatch(store, args):
    action = args.method_action
    if action == 'catalog':
        return dict(tracks=catalog.TRACKS, steps=catalog.STEPS)
    if action == 'starters':
        from .starters import catalog as starter_catalog
        return starter_catalog()
    if action == 'template':
        from .templates import render, schema
        return dict(markdown=render(args.kind), schema=schema(args.kind))
    task = store.get('tasks', args.task)
    if action == 'architecture':
        from .starters import select
        return select(store, task, boilerplate=args.boilerplate, custom=args.custom,
                      existing=args.existing, revision=args.revision, stack=args.stack, constraints=args.constraint)
    if action == 'scaffold':
        from .templates import scaffold
        return scaffold(store, task, args.kind, args.file)
    if action == 'init':
        return artifacts.initialize(store, task, args.track, args.ui)
    if action == 'status':
        return workflow.status(store, task)
    if action == 'gate':
        return dict(ok=True, **workflow.require_ready(store, task))
    if action == 'prompt':
        return workflow.prompt(store, task, args.step, args.max_chars)
    if action == 'story':
        return artifacts.set_story(store, task, args.id, args.complexity, args.note)
    if action == 'record':
        return artifacts.register(store, task, args.kind, args.file, args.author, args.input)
    if action == 'use':
        return artifacts.use(store, task, store.get('artifacts', args.artifact))
    if action == 'review':
        return artifacts.review(store, task, args.artifact, args.reviewer, args.verdict, args.summary, args.finding)
    if action == 'ship':
        from .shipping import prepare
        return prepare(store, task, args.base, args.review)
