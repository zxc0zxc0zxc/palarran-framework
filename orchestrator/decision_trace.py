"""Review/render public decision summaries, never a private reasoning transcript."""
import argparse
import html
import json
from pathlib import Path
import re

OUTCOMES = {'proposed', 'succeeded', 'failed', 'unknown'}


def validate(value):
    def require(ok):
        if not ok:
            raise ValueError('Invalid public decision trace')
    def text(item, limit):
        require(isinstance(item, str) and 0 < len(item.strip()) <= limit and '\x00' not in item)
    require(isinstance(value, dict) and set(value) == {'version', 'review_status', 'task', 'steps'})
    require(type(value['version']) is int and value['version'] == 1)
    require(value['review_status'] in ('draft', 'reviewed', 'rejected'))
    text(value['task'], 500)
    require(isinstance(value['steps'], list) and 1 <= len(value['steps']) <= 32)
    seen = set()
    for step in value['steps']:
        require(isinstance(step, dict) and set(step) == {'id', 'action', 'summary', 'evidence', 'decision_ref', 'outcome'})
        identifier = step['id']
        require(isinstance(identifier, str) and bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', identifier)) and identifier not in seen)
        seen.add(identifier)
        text(step['action'], 120)
        text(step['summary'], 600)
        require(isinstance(step['outcome'], str) and step['outcome'] in OUTCOMES)
        require(isinstance(step['decision_ref'], str) and len(step['decision_ref']) <= 300)
        require(isinstance(step['evidence'], list) and len(step['evidence']) <= 10)
        for reference in step['evidence']:
            text(reference, 500)
    return value


def render(value):
    value = validate(value)
    escape = lambda item: html.escape(item, quote=True)
    cards = []
    for step in value['steps']:
        refs = ''.join('<li>' + escape(ref) + '</li>' for ref in step['evidence'])
        cards.append('<article id="' + step['id'] + '" class="' + step['outcome'] + '"><header><b>' +
                     escape(step['action']) + '</b><span>' + step['outcome'] + '</span></header><p>' +
                     escape(step['summary']) + '</p><small>Step ' + step['id'] + ' · ADR ' +
                     escape(step['decision_ref']) + '</small><ul>' + refs + '</ul></article>')
    return '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decision trace</title><style>body{font:16px/1.5 system-ui;margin:24px auto;padding:0 16px;max-width:900px;color:#17212b;background:#f6f8fa}article{padding:18px;margin:16px 0;background:white;border-left:5px solid #73808c;border-radius:8px;overflow-wrap:anywhere}header{display:flex;gap:12px;justify-content:space-between;flex-wrap:wrap}span,small{font-size:13px}li{font-size:14px}article:target{outline:3px solid #b6bdea}.succeeded{border-color:#237b4b}.failed{border-color:#bd3434}.unknown{border-color:#bd8c20}.proposed{border-color:#3e68b4}</style><h1>''' + escape(value['task']) + '</h1><p>Review: ' + value['review_status'] + '''. Публичные объяснения решений. Outcomes сообщены автором; renderer не подтверждает выполнение проверок. Перед few-shot нужны очистка, evidence review и актуальность.</p>''' + ''.join(cards) + '</html>'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        source = Path(args.trace)
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 131072:
            raise ValueError('Invalid trace file')
        content = render(json.loads(source.read_text(encoding='utf-8')))
        # No overwrite, no network, no executable trace content.
        with open(args.output, 'x', encoding='utf-8') as output:
            output.write(content)
    except (OSError, ValueError, TypeError):
        parser.exit(2, 'Unable to render public decision trace\n')


if __name__ == '__main__':
    main()
