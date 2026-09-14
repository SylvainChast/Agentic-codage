"""Public starter catalog and explicit architecture choices; never installs external code."""
from copy import deepcopy
import re

from ..store import FrameworkError

CATALOG = {
    'nextjs-saas': dict(
        name='Next.js SaaS Starter', repository='https://github.com/nextjs/saas-starter',
        license='MIT', license_url='https://github.com/nextjs/saas-starter/blob/main/LICENSE',
        stack=['Next.js', 'TypeScript', 'PostgreSQL', 'Drizzle', 'shadcn/ui'],
        includes=['Authentication', 'Basic team roles', 'Stripe subscriptions', 'Dashboard'],
        limits=['Intentionally minimal learning starter; assess production controls and tenant isolation.']),
    'open-saas': dict(
        name='Open SaaS', repository='https://github.com/wasp-lang/open-saas',
        license='MIT', license_url='https://github.com/wasp-lang/open-saas/blob/main/LICENSE',
        stack=['Wasp', 'React', 'Node.js', 'Prisma'],
        includes=['Authentication', 'Payments', 'Email', 'Background jobs', 'Playwright examples'],
        limits=['Requires Wasp conventions/compiler; confirm fit before selecting.',
                'External services may have usage costs despite the free code license.']),
    'fastapi-react': dict(
        name='Full Stack FastAPI Template', repository='https://github.com/fastapi/full-stack-fastapi-template',
        license='MIT', license_url='https://github.com/fastapi/full-stack-fastapi-template/blob/master/LICENSE',
        stack=['FastAPI', 'Python', 'React', 'TypeScript', 'SQLModel', 'PostgreSQL'],
        includes=['Authentication', 'Generated API client', 'Docker Compose', 'Pytest', 'Playwright', 'CI'],
        limits=['General application starter; billing and SaaS tenant rules need product-specific work.']),
}


def catalog():
    return dict(starters=[dict(id=ident, **deepcopy(data)) for ident, data in CATALOG.items()],
                verified_on='2026-09-14', verification='Public documentation and license only; not a code audit',
                note='No default stack, downloads, dependency installation or paid provider calls. Preserve upstream license notices.')


def validate_choice(choice, ready=False):
    """Check relationships that the small JSON Schema validator cannot express."""
    mode = choice['mode']
    if mode == 'boilerplate':
        profile = CATALOG.get(choice['boilerplate'])
        if not profile or choice['repository'] != profile['repository'] or choice['stack'] != profile['stack']:
            raise FrameworkError('Architecture must reference an unchanged public catalog profile; use custom for another stack')
        if choice['revision'] is not None and not re.fullmatch(r'[a-f0-9]{40}', choice['revision']):
            raise FrameworkError('Boilerplate revision must be a full lowercase Git commit SHA')
        if ready and choice['revision'] is None:
            raise FrameworkError('Pin the inspected boilerplate commit with --revision before registering architecture')
    else:
        if mode not in ('custom', 'existing'):
            raise FrameworkError('Unknown architecture mode')
        if any(choice[k] is not None for k in ('boilerplate', 'repository', 'revision')):
            raise FrameworkError('Only boilerplate mode accepts a repository and revision')
        if mode == 'custom' and not choice['stack']:
            raise FrameworkError('Custom architecture needs at least one --stack choice')
    for value in choice['stack'] + choice['constraints']:
        if not value.strip():
            raise FrameworkError('Architecture stack and constraints must not be blank')


def select(store, task, *, boilerplate=None, custom=False, existing=False, revision=None, stack=(), constraints=()):
    from .artifacts import editable
    editable(task)
    if 'method' not in task:
        raise FrameworkError('Configure method init first')
    if sum((boilerplate is not None, bool(custom), bool(existing))) != 1:
        raise FrameworkError('Select exactly one architecture mode')
    profile = CATALOG.get(boilerplate) if boilerplate else None
    if boilerplate and (not profile or stack):
        raise FrameworkError('Choose a public boilerplate without --stack, or use --custom with your own stack')
    mode = 'boilerplate' if boilerplate else 'custom' if custom else 'existing'
    choice = dict(mode=mode, boilerplate=boilerplate, repository=profile['repository'] if profile else None,
                  revision=revision, stack=list(profile['stack'] if profile else stack),
                  constraints=list(constraints))
    validate_choice(choice)
    task['method']['architecture'] = choice
    store.put('tasks', task)
    return dict(task=task, downloaded=False, installed=False,
                next='Inspect the chosen source, pin its commit for a boilerplate, then write and register architecture. Re-review affected stories after changes.')
