"""CLI registration kept separate from provider-independent lifecycle commands."""
import json

from ..store import FrameworkError
from . import engine, profiles


def register(commands):
    p = commands.add_parser('orchestration', help='Configure user-selected models and run bounded delegation')
    actions = p.add_subparsers(dest='action', required=True)
    for name in ('init', 'set-role'):
        sub = actions.add_parser(name)
        if name == 'set-role':
            sub.add_argument('role', choices=profiles.ROLES)
            sub.add_argument('--allow-observed', action='append', default=[])
        sub.add_argument('--model', required=True, help='Exact user-selected model; no implicit fallback')
        sub.add_argument('--adapter', choices=('codex', 'claude', 'command'), required=True)
        sub.add_argument('--command-json', help='Explicit executable argv as a JSON array')
    actions.add_parser('doctor')
    actions.add_parser('config')
    actions.add_parser('list')
    sub = actions.add_parser('run')
    sub.add_argument('task')
    for action in ('show', 'cancel', 'feedback', 'integrate'):
        sub = actions.add_parser(action)
        sub.add_argument('session')
        if action == 'feedback':
            sub.add_argument('--message', required=True)
        if action == 'integrate':
            sub.add_argument('--actor', required=True)


def dispatch(store, args):
    action = args.action
    if action in ('init', 'set-role'):
        try:
            command = json.loads(args.command_json) if args.command_json else None
        except ValueError as exc:
            raise FrameworkError('--command-json must be a JSON argv array') from exc
        if command is not None and (not isinstance(command, list) or not command or any(not isinstance(v, str) or not v for v in command)):
            raise FrameworkError('--command-json must be a nonempty string array')
        if action == 'init':
            return profiles.initialize(store, args.model, args.adapter, command)
        return profiles.set_role(store, args.role, args.model, args.adapter, command, args.allow_observed)
    if action == 'config':
        return profiles.load(store)
    if action == 'doctor':
        return profiles.doctor(store)
    if action == 'list':
        return store.all('orchestrations')
    if action == 'show':
        return store.get('orchestrations', args.session)
    if action == 'run':
        return engine.run(store, args.task)
    if action in ('cancel', 'feedback'):
        return engine.feedback(store, args.session, getattr(args, 'message', None), action == 'cancel')
    return engine.integrate(store, args.session, args.actor)
