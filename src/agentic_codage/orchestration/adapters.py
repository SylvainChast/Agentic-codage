"""Explicit CLI transports. Provider reports are observations, never authentication."""
import json
from decimal import Decimal, ROUND_HALF_UP

from .profiles import executable
from .protocol import prompt, schema
from ..store import FrameworkError, canonical, validate


def request(profile, role, payload, root, scratch):
    config = profile['roles'][role]
    argv = [executable(config['command'], root), *config['command'][1:]]
    model = config['model']
    writable = role == 'worker'
    text = prompt(role, payload)
    if config['adapter'] == 'codex':
        schema_path = scratch / 'schema.json'
        schema_path.write_text(canonical(schema(role)), encoding='utf-8')
        argv += ['exec', '--model', model, '--sandbox', 'workspace-write' if writable else 'read-only',
                 '--ephemeral', '--ignore-user-config', '--json', '--output-schema', str(schema_path),
                 '--output-last-message', str(scratch / 'result.json'), '-c', 'approval_policy="never"', '-']
    elif config['adapter'] == 'claude':
        argv += ['-p', '--model', model, '--output-format', 'json', '--json-schema', json.dumps(schema(role)),
                 '--no-session-persistence', '--permission-mode', 'acceptEdits' if writable else 'plan',
                 '--tools', 'Read,Glob,Grep,Edit,Write' if writable else 'Read,Glob,Grep',
                 '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}']
    else:
        text = canonical(dict(protocol_version=1, role=role, model=model, payload=payload,
                              prompt=text, response_schema=schema(role)))
    return argv, text


def decode(adapter, role, output, scratch, currency):
    """Normalize a successful transport; validate costs even for a rejected result."""
    models, usage, cost, source = [], {}, None, 'unknown'
    if adapter == 'codex':
        events = [json.loads(line) for line in output.splitlines() if line.strip()]
        for event in events:
            if event.get('type') in ('error', 'turn.failed'):
                raise FrameworkError('Codex reported a failed turn')
            if isinstance(event.get('model'), str):
                models.append(event['model'])
            if event.get('type') in ('turn.completed', 'thread.completed'):
                usage = event.get('usage') or {}
        result = json.loads((scratch / 'result.json').read_text(encoding='utf-8'))
    elif adapter == 'claude':
        data = json.loads(output)
        if data.get('is_error'):
            raise FrameworkError('Claude reported a failed turn')
        result = data.get('structured_output')
        if result is None:
            result = json.loads(data['result'])
        models = list((data.get('modelUsage') or {}).keys())
        usage = data.get('usage') or {}
        amount = data.get('total_cost_usd')
        if currency == 'USD' and isinstance(amount, (int, float)) and not isinstance(amount, bool):
            decimal = Decimal(str(amount))
            if decimal.is_finite() and decimal >= 0:
                cost = int((decimal * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                source = 'actual'
    else:
        data = json.loads(output)
        result = data['result']
        models = data.get('models', [data['model']] if data.get('model') else [])
        usage = data.get('usage') or {}
        if usage.get('currency') == currency:
            cost = usage.get('cost_minor')
            source = usage.get('cost_source', 'unknown')
    if not isinstance(models, list) or any(not isinstance(m, str) or not m for m in models):
        raise FrameworkError('Invalid observed model list')
    if cost is not None and (type(cost) is not int or cost < 0 or source not in ('actual', 'estimate')):
        raise FrameworkError('Invalid cost report')
    if cost is None:
        source = 'unknown'
    tokens = {}
    for key in ('input_tokens', 'output_tokens'):
        value = usage.get(key)
        tokens[key] = value if type(value) is int and value >= 0 else None
    return dict(result=result, observed_models=list(dict.fromkeys(models)), llm_cost_minor=cost,
                cost_source=source, **tokens)


def validate_response(profile, role, decoded):
    models = decoded['observed_models']
    identity = 'reported' if models else 'unverified'
    if set(models) - set(profile['roles'][role]['accepted_models']):
        identity = 'mismatch'
    error = None
    if identity == 'mismatch' or (not models and profile['require_model_report']):
        error = 'Selected model could not be confirmed against explicit accepted_models'
    try:
        validate(decoded['result'], schema(role))
    except FrameworkError as exc:
        error = str(exc)
    return identity, error
