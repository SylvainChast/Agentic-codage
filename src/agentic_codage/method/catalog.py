"""One procedure catalog for CLI, skills and editor commands."""
from ..store import ASSETS

STEPS = {
    'research': 'Resolve a specific product or technical uncertainty using evidence.',
    'prd': 'Create or revise requirements, success criteria and exclusions for a product.',
    'architecture': 'Define or revise components, data, interfaces and technical decisions.',
    'design-system': 'Define reusable UI components, visual tokens and accessible behaviors.',
    'stories': 'Slice requirements into deliverable stories with testable acceptance criteria.',
    'story-review': 'Review stories and their framing for ambiguity, coverage and feasibility.',
    'design': 'Design the local technical and UX solution for a feature.',
    'plan': 'Produce a bounded implementation plan with dependencies and verification.',
    'execute': 'Implement a prepared task using its scope, tests and coordination gates.',
    'review': 'Review the implementation against requirements and quality evidence.',
    'ship': 'Prepare a verified change for a pull request within existing authorization.',
}
DOCUMENTS = ('research', 'prd', 'architecture', 'design-system', 'stories', 'design', 'plan')
TRACKS = ('express', 'feature', 'product')


def required(method):
    result = ['plan'] if method['track'] == 'express' else ['stories', 'design', 'plan']
    if method['track'] == 'product':
        result = ['prd', 'architecture'] + result
    if method['ui']:
        result = ['design-system'] + result
    if 'architecture' in method:
        result = ['architecture'] + result
    return list(dict.fromkeys(result))


def parents(kind, method):
    if kind == 'architecture':
        return ['prd'] if method['track'] == 'product' else []
    if kind == 'stories':
        return ['prd', 'architecture'] if method['track'] == 'product' else (
            ['architecture'] if 'architecture' in method else [])
    if kind == 'design':
        return ['stories'] + (['design-system'] if method['ui'] else [])
    if kind == 'plan':
        return (['design', 'stories'] if method['track'] != 'express' else (
            ['design-system'] if method['ui'] else [])) + (['architecture'] if 'architecture' in method else [])
    return []


def procedure(step):
    return (ASSETS / 'method' / f'{step}.md').read_text(encoding='utf-8')


def adapter_files():
    files = {}
    for step, description in STEPS.items():
        body = (f"Run the Agentic Codage {step} procedure for the user's request.\n"
                "Read `.framework/OPERATING.md` and identify the task from the request or current context.\n"
                f"Read only `.framework/method/{step}.md`, then use `framework method prompt {step} --task TASK`\n"
                "for its focused context. In this source checkout use `python3 bin/framework`.\n"
                "If no task exists, register a bounded task with an explicit budget, owner and criteria first.\n"
                "Respect the user's model choice and existing permissions; do not infer deployment authority.\n")
        # Small entry points: only the selected procedure is loaded.
        front = f'---\nname: swarm-{step}\ndescription: {description}\n---\n\n'
        if step != 'review':  # Preserve the existing canonical swarm-review entry point.
            files[f'.agents/skills/swarm-{step}/SKILL.md'] = front + body
        for host in ('claude', 'cursor'):
            files[f'.{host}/skills/{step}/SKILL.md'] = front.replace(f'swarm-{step}', step) + body
        files[f'.github/prompts/{step}.prompt.md'] = f'---\ndescription: {description}\nagent: agent\n---\n\n' + body
        files[f'.gemini/commands/{step}.toml'] = (
            f'description = "{description}"\nprompt = """\n' + body + '\nUser request: {{args}}\n"""\n')
        files[f'.windsurf/workflows/{step}.md'] = f'---\ndescription: {description}\n---\n\n# {step}\n\n' + body
        files[f'.framework/method/{step}.md'] = procedure(step)
    from .templates import KINDS, render
    for kind in KINDS:
        files[f'.framework/method/templates/{kind}.md'] = render(kind)
    return files
