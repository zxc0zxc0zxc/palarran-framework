"""Render approved JSON into a new local, self-contained review page (stdlib only)."""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

MAX_BYTES = 128 * 1024
STATUSES = ("PASS", "FAIL", "NOT_RUN", "INCONCLUSIVE", "NA")
LOCALES = ("en", "ru", "sr-Latn")
CONTENT_FIELDS = ("feature", "title", "revision", "readiness", "what", "why", "how", "results",
                  "environment_names", "risks", "evidence", "tests", "metrics", "flow")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")


class ArtifactError(ValueError):
    """Invalid input or unsafe local destination."""


def obj(value, required, optional=()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ArtifactError("Invalid object fields")


def text(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ArtifactError("Expected bounded nonempty text")
    if any((ord(c) < 32 and c not in '\n\t') or 0xD800 <= ord(c) <= 0xDFFF or ord(c) == 127 for c in value):
        raise ArtifactError("Invalid text characters")
    return value


def items(value, limit):
    if type(value) is not list or len(value) > limit:
        raise ArtifactError("Invalid collection size")
    return value


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ArtifactError("Invalid identifier")
    return value


def public_url(value):
    text(value)
    if any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value:
        raise ArtifactError("Unsafe URL")
    try:
        u = urlsplit(value)
        host = u.hostname or ''
        if u.scheme != 'https' or u.username is not None or u.password is not None or u.query or u.port not in (None, 443):
            raise ArtifactError("Only public HTTPS links without credentials/query are allowed")
        if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', host) or not re.search(r'\.[A-Za-z]{2,63}\Z', host):
            raise ArtifactError("Public DNS host required")
        if any(not part or len(part) > 63 or part.startswith('-') or part.endswith('-') for part in host.split('.')):
            raise ArtifactError("Invalid DNS host")
        if host.lower().endswith(('.local', '.localhost', '.internal', '.private', '.lan', '.home', '.test', '.invalid')):
            raise ArtifactError("Private host suffix")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ArtifactError("IP links are not allowed")
    except (ValueError, UnicodeError) as exc:
        raise ArtifactError("Unsafe URL") from exc
    return value


def validate(data):
    obj(data, ('version', 'approved_for_render', 'privacy_reviewed') + CONTENT_FIELDS, ('language',))
    if 'language' in data and data['language'] not in LOCALES:
        raise ArtifactError('Invalid language tag')
    if type(data['version']) is not int or data['version'] != 1:
        raise ArtifactError("Unsupported version")
    if data['approved_for_render'] is not True or data['privacy_reviewed'] is not True:
        raise ArtifactError("Explicit input approval and privacy review required")
    if not isinstance(data['feature'], str) or not SLUG.fullmatch(data['feature']):
        raise ArtifactError("Invalid feature slug")
    for key in ('title', 'revision', 'readiness'):
        text(data[key])
    for key in ('what', 'why', 'how', 'results'):
        text(data[key], 8000)
    for name in items(data['environment_names'], 40):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', name):
            raise ArtifactError("Invalid environment variable name")
    for risk in items(data['risks'], 40):
        text(risk)
    evidence_ids = set()
    for evidence in items(data['evidence'], 60):
        obj(evidence, ('id', 'description'), ('url',))
        eid = identifier(evidence['id'])
        if eid in evidence_ids:
            raise ArtifactError("Duplicate evidence ID")
        evidence_ids.add(eid)
        text(evidence['description'])
        if 'url' in evidence:
            public_url(evidence['url'])
    for test in items(data['tests'], 80):
        obj(test, ('name', 'status', 'environment', 'steps', 'prerequisites', 'evidence_ids'), ('note',))
        for field in ('name', 'environment'):
            text(test[field])
        if not isinstance(test['status'], str) or test['status'] not in STATUSES:
            raise ArtifactError("Unknown test status")
        if not items(test['steps'], 20):
            raise ArtifactError("Test steps required")
        for field in ('steps', 'prerequisites'):
            for entry in items(test[field], 20):
                text(entry)
        for eid in items(test['evidence_ids'], 60):
            identifier(eid)
            if eid not in evidence_ids:
                raise ArtifactError("Unknown test evidence reference")
        if test['status'] == 'NA' and 'note' not in test:
            raise ArtifactError('NA requires an explicit rationale')
        if 'note' in test:
            text(test['note'])
    for metric in items(data['metrics'], 40):
        obj(metric, ('name', 'value', 'unit', 'source', 'kind', 'denominator', 'uncertainty'))
        for field in ('name', 'unit', 'source', 'denominator', 'uncertainty'):
            text(metric[field])
        if not isinstance(metric['kind'], str) or metric['kind'] not in ('observed', 'target', 'estimate'):
            raise ArtifactError("Invalid metric kind")
        value = metric['value']
        if value is not None and (type(value) not in (int, float) or abs(value) > 1e100 or not math.isfinite(value)):
            raise ArtifactError("Metric must be a bounded finite number or null")
    obj(data['flow'], ('nodes', 'edges'))
    node_ids = set()
    for node in items(data['flow']['nodes'], 12):
        obj(node, ('id', 'label'))
        nid = identifier(node['id'])
        if nid in node_ids:
            raise ArtifactError("Duplicate flow node")
        node_ids.add(nid)
        text(node['label'], 120)
    for edge in items(data['flow']['edges'], 24):
        obj(edge, ('from', 'to', 'label'))
        identifier(edge['from']); identifier(edge['to']); text(edge['label'], 120)
        if edge['from'] not in node_ids or edge['to'] not in node_ids:
            raise ArtifactError("Unknown flow node reference")
    # Apply the same byte bound to direct Python callers as to JSON files.
    if len(json.dumps(data, ensure_ascii=False).encode('utf-8')) > MAX_BYTES:
        raise ArtifactError("Input exceeds byte limit")
    return data


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactError("Duplicate JSON key")
        result[key] = value
    return result


def _path(path):
    """Check components without resolving away symlinks; trusted local filesystem only."""
    path = Path(os.path.abspath(os.fspath(path)))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ArtifactError("Symlink components are forbidden")
        if current != path and not stat.S_ISDIR(metadata.st_mode):
            raise ArtifactError("Parent component must be a directory")
    return path


def load_input(path):
    path = _path(path)
    # Bound reads even if a file grows after the metadata check.
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ArtifactError("Input must be a regular file")
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ArtifactError("Input exceeds byte limit")
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ArtifactError('Nonfinite JSON number')))
        return validate(data)
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError) as exc:
        raise ArtifactError("Invalid UTF-8 JSON input") from exc


def esc(value):
    return html.escape(str(value), quote=True)



CSS = '''
:root{color-scheme:dark;--bg:#101010;--panel:#1b1b1b;--ink:#f5f2eb;--muted:#b8b5ae;--line:#404040;--accent:#b9dbc5}*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:48px 24px 80px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.15;letter-spacing:-.04em}h2{margin-top:0}h3{font-size:1.1rem}p,li,td,dd{overflow-wrap:anywhere;white-space:pre-wrap}a{color:var(--accent)}.muted,dt{color:var(--muted)}.eyebrow{letter-spacing:.12em;text-transform:uppercase;font-size:.8rem}nav,.filters{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}button,nav a{font:inherit;background:var(--panel);color:var(--ink);border:1px solid var(--line);padding:9px 15px;border-radius:24px;cursor:pointer;text-decoration:none}button[aria-pressed=true],nav a[aria-current=true]{border-color:var(--accent);color:var(--accent)}:focus-visible{outline:3px solid var(--accent);outline-offset:4px}section{border-top:1px solid var(--line);padding:30px 0;scroll-margin-top:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px}.card,details{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;min-width:0}.value{font-size:2rem;line-height:1.2;margin:12px 0}dl{margin-bottom:0}dd{margin:0 0 10px}summary{cursor:pointer;overflow-wrap:anywhere}details+details{margin-top:12px}table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}.table-wrap{overflow:auto}svg{width:100%;height:auto;display:block;max-width:700px;margin:16px auto}svg text{fill:var(--ink);font:15px system-ui,sans-serif}.check{display:flex;gap:12px;align-items:start;margin:12px 0}.check input{margin-top:7px;accent-color:var(--accent)}[hidden]{display:none!important}.skip{position:absolute;top:-100px}.skip:focus{top:10px;background:var(--bg);padding:12px}.badge{font-size:.8rem;border:1px solid var(--line);border-radius:5px;padding:2px 7px;margin-right:8px}footer{margin-top:30px;color:var(--muted)}@media(max-width:600px){main{padding:24px 16px 48px}.card,details{padding:16px}th,td{padding:8px;font-size:.9rem}}@media(prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}@media print{button,.filters,.check{display:none}body{background:white;color:black}section[hidden]{display:block!important}}
'''
UI = {
    'en': {
        'skip': 'Skip to content', 'review': 'Feature review', 'revision': 'Source revision',
        'navigation': 'Review sections', 'all': 'All', 'what': 'What changed', 'why': 'Why it matters',
        'how': 'How it works', 'results': 'Results and review', 'env': 'Environment variable names',
        'none': 'None recorded.', 'flow': 'Provided flow', 'flow_aria': 'Provided directed relationships; complete labels in the table below',
        'relationships': 'Flow relationships (full text)', 'from': 'From', 'relationship': 'Relationship', 'to': 'To',
        'nodes': 'All flow nodes', 'no_flow': 'No flow supplied.', 'metrics': 'Metrics', 'unknown': 'Unknown',
        'classification': 'Classification', 'source': 'Source', 'denominator': 'Denominator', 'uncertainty': 'Uncertainty',
        'observed': 'Observed', 'target': 'Target', 'estimate': 'Estimate', 'no_metrics': 'No measurements supplied.',
        'tests': 'Test scenarios', 'distribution': 'Distribution counts {n} listed scenarios; it does not measure coverage or execution count.',
        'chart_aria': 'Counts of listed scenarios by status; exact counts follow', 'scenarios': 'scenarios',
        'filter': 'Filter test status', 'all_statuses': 'All statuses', 'shown': '{n} listed scenarios shown',
        'environment': 'Environment', 'prerequisites': 'Prerequisites', 'steps': 'Steps', 'evidence': 'Evidence',
        'no_evidence': 'None supplied', 'risks': 'Remaining risks and blockers', 'references': 'Evidence references',
        'open_source': 'Open source', 'no_references': 'No evidence references supplied.',
        'reminders': 'Review reminders', 'checklist': 'Reviewer checklist',
        'local_only': 'Page-local reminders only; checking a box does not verify a test or persist acceptance.',
        'checks': ('Confirm the source revision and scope.', 'Review prerequisites, evidence and checks that were not run.',
                   'Check mobile layout, keyboard controls and remaining risks.'),
        'checked': '{n} of {total} review reminders checked (not verification evidence).',
        'footer': 'Portable snapshot · no test, deployment or task execution. Privacy review is declarative, not automatic secret detection.',
        'PASS': 'Passed', 'FAIL': 'Failed', 'NOT_RUN': 'Not run', 'INCONCLUSIVE': 'Inconclusive', 'NA': 'Not applicable',
    },
    'ru': {
        'skip': 'Перейти к содержимому', 'review': 'Обзор изменения', 'revision': 'Ревизия исходников',
        'navigation': 'Разделы обзора', 'all': 'Все разделы', 'what': 'Что изменилось', 'why': 'Зачем это нужно',
        'how': 'Как это работает', 'results': 'Результаты и проверка', 'env': 'Имена переменных окружения',
        'none': 'Ничего не записано.', 'flow': 'Схема взаимодействия', 'flow_aria': 'Указанные направленные связи; полные подписи в таблице ниже',
        'relationships': 'Связи на схеме: полные подписи', 'from': 'Откуда', 'relationship': 'Взаимодействие', 'to': 'Куда',
        'nodes': 'Все узлы схемы', 'no_flow': 'Схема не предоставлена.', 'metrics': 'Метрики', 'unknown': 'Неизвестно',
        'classification': 'Тип значения', 'source': 'Источник', 'denominator': 'Объём выборки или база расчёта', 'uncertainty': 'Неопределённость',
        'observed': 'Измерено', 'target': 'Цель', 'estimate': 'Оценка', 'no_metrics': 'Измерения не предоставлены.',
        'tests': 'Сценарии проверки', 'distribution': 'Показано распределение {n} перечисленных сценариев. Это не покрытие и не число запусков.',
        'chart_aria': 'Число перечисленных сценариев по статусам; точные значения ниже', 'scenarios': 'сценариев',
        'filter': 'Фильтр статусов проверки', 'all_statuses': 'Все статусы', 'shown': 'Показано сценариев: {n}',
        'environment': 'Окружение', 'prerequisites': 'Что нужно перед проверкой', 'steps': 'Шаги', 'evidence': 'Подтверждения',
        'no_evidence': 'Не предоставлены', 'risks': 'Оставшиеся риски и препятствия', 'references': 'Источники и подтверждения',
        'open_source': 'Открыть источник', 'no_references': 'Ссылки на подтверждения не предоставлены.',
        'reminders': 'Напоминания проверяющему', 'checklist': 'Что проверить',
        'local_only': 'Отметки действуют только на этой странице. Галочка не подтверждает тест и не сохраняет приёмку.',
        'checks': ('Сверить ревизию исходников и границы изменения.', 'Просмотреть условия, подтверждения и незапущенные проверки.',
                   'Проверить мобильную версию, управление с клавиатуры и оставшиеся риски.'),
        'checked': 'Отмечено напоминаний: {n} из {total}. Это не подтверждение проверки.',
        'footer': 'Переносимый снимок · не запускает тесты, развёртывание или задачи. Проверка приватности заявлена автором; автоматического поиска секретов нет.',
        'PASS': 'Пройдено', 'FAIL': 'Не пройдено', 'NOT_RUN': 'Не запускалось', 'INCONCLUSIVE': 'Нет однозначного вывода', 'NA': 'Не применимо',
    },
    'sr-Latn': {
        'skip': 'Pređi na sadržaj', 'review': 'Pregled izmene', 'revision': 'Revizija izvornog koda',
        'navigation': 'Odeljci pregleda', 'all': 'Svi odeljci', 'what': 'Šta se promenilo', 'why': 'Zašto je važno',
        'how': 'Kako radi', 'results': 'Rezultati i provera', 'env': 'Nazivi promenljivih okruženja',
        'none': 'Ništa nije zabeleženo.', 'flow': 'Dostavljeni tok', 'flow_aria': 'Dostavljene usmerene veze; potpuni nazivi u tabeli ispod',
        'relationships': 'Veze u toku (potpuni nazivi)', 'from': 'Od', 'relationship': 'Veza', 'to': 'Do',
        'nodes': 'Svi čvorovi toka', 'no_flow': 'Tok nije dostavljen.', 'metrics': 'Metrike', 'unknown': 'Nepoznato',
        'classification': 'Vrsta vrednosti', 'source': 'Izvor', 'denominator': 'Veličina uzorka ili osnova obračuna', 'uncertainty': 'Neizvesnost',
        'observed': 'Izmereno', 'target': 'Cilj', 'estimate': 'Procena', 'no_metrics': 'Merenja nisu dostavljena.',
        'tests': 'Scenariji provere', 'distribution': 'Raspodela obuhvata {n} navedenih scenarija; ne meri pokrivenost niti broj izvršavanja.',
        'chart_aria': 'Broj navedenih scenarija po statusu; tačni brojevi slede', 'scenarios': 'scenarija',
        'filter': 'Filtriraj status provere', 'all_statuses': 'Svi statusi', 'shown': 'Prikazano scenarija: {n}',
        'environment': 'Okruženje', 'prerequisites': 'Preduslovi', 'steps': 'Koraci', 'evidence': 'Dokazi',
        'no_evidence': 'Nisu dostavljeni', 'risks': 'Preostali rizici i prepreke', 'references': 'Izvori i dokazi',
        'open_source': 'Otvori izvor', 'no_references': 'Reference na dokaze nisu dostavljene.',
        'reminders': 'Podsetnici za pregled', 'checklist': 'Šta proveriti',
        'local_only': 'Oznake važe samo na ovoj stranici. Obeležavanje ne potvrđuje test i ne čuva prihvatanje.',
        'checks': ('Potvrdi reviziju izvornog koda i obim izmene.', 'Pregledaj preduslove, dokaze i neizvršene provere.',
                   'Proveri mobilni prikaz, upravljanje tastaturom i preostale rizike.'),
        'checked': 'Obeleženo podsetnika: {n} od {total}. Ovo nije dokaz provere.',
        'footer': 'Prenosivi snimak · ne izvršava testove, objavljivanje niti zadatke. Pregled privatnosti je izjava autora, a ne automatsko otkrivanje tajni.',
        'PASS': 'Prošlo', 'FAIL': 'Nije prošlo', 'NOT_RUN': 'Nije pokrenuto', 'INCONCLUSIVE': 'Bez konačnog zaključka', 'NA': 'Nije primenljivo',
    },
}
JS = '''
'use strict';
const pages=[...document.querySelectorAll('.locale-page')];
pages.forEach(page=>{
 const sections=[...page.querySelectorAll('main > section[data-section]')];
 const links=[...page.querySelectorAll('nav a[data-section]')];
 links.forEach(link=>link.addEventListener('click',event=>{event.preventDefault();const id=link.dataset.section;sections.forEach(s=>s.hidden=id!=='all'&&s.dataset.section!==id);links.forEach(a=>a.setAttribute('aria-current',a===link?'true':'false'));const shown=sections.find(s=>!s.hidden);if(shown){shown.querySelector('h2').focus();}}));
 page.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{const status=button.dataset.filter;let count=0;page.querySelectorAll('details[data-status]').forEach(row=>{row.hidden=status!=='all'&&row.dataset.status!==status;if(!row.hidden)count++;});page.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',b===button?'true':'false'));const state=page.querySelector('[data-filter-state]');state.textContent=state.dataset.template.replace('{n}',count);}));
 page.querySelectorAll('.check input').forEach(box=>box.addEventListener('change',()=>{const boxes=[...page.querySelectorAll('.check input')];const state=page.querySelector('[data-review-state]');state.textContent=state.dataset.template.replace('{n}',boxes.filter(b=>b.checked).length).replace('{total}',boxes.length);}));

});
'''


def _render_page(data, locale):
    e = esc
    ui = UI[locale]
    def t(key):
        return e(ui[key])
    def listing(values):
        return '<ul>' + ''.join('<li>' + e(v) + '</li>' for v in values) + '</ul>' if values else '<p class="muted">'+t('none')+'</p>'
    def pid(key):
        return locale+'-'+key
    parts = ['<div class="locale-page" lang="'+locale+'">',
             '<a class="skip" href="#'+pid('main')+'">'+t('skip')+'</a><main id="'+pid('main')+'">']
    parts.extend(['<header><p class="eyebrow">'+t('review')+' · '+e(data['feature'])+'</p><h1 tabindex="-1">'+e(data['title'])+'</h1><p>'+e(data['readiness'])+'</p><p class="muted">'+t('revision')+': '+e(data['revision'])+'</p></header><nav aria-label="'+t('navigation')+'">'])
    for key in ('all', 'what', 'why', 'how', 'results'):
        parts.append('<a data-section="'+key+'" href="#'+pid('what' if key=='all' else key)+'" aria-current="'+('true' if key=='all' else 'false')+'">'+t(key)+'</a>')
    parts.append('</nav>')
    for key in ('what', 'why', 'how', 'results'):
        parts.append('<section data-section="'+key+'" id="'+pid(key)+'"><h2 tabindex="-1">'+t(key)+'</h2><p>'+e(data[key])+'</p>')
        if key == 'how':
            parts.append('<h3>'+t('env')+'</h3>'+listing(data['environment_names']))
            nodes, edges = data['flow']['nodes'], data['flow']['edges']
            if nodes:
                labels = {n['id']: n['label'] for n in nodes}
                parts.append('<h3>'+t('flow')+'</h3>')
                if edges:
                    arrow=pid('arrow')
                    parts.append('<svg viewBox="0 0 700 '+str(len(edges)*110)+'" role="img" aria-label="'+t('flow_aria')+'"><defs><marker id="'+arrow+'" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#b9dbc5"/></marker></defs>')
                    for i, edge in enumerate(edges):
                        y=i*110+20
                        parts.append(f'<rect x="5" y="{y}" width="235" height="45" rx="8" fill="#252525"/><rect x="460" y="{y}" width="235" height="45" rx="8" fill="#252525"/><path d="M245,{y+22} H450" stroke="#b9dbc5" marker-end="url(#{arrow})"/><text x="15" y="{y+28}">{e(labels[edge["from"]][:23])}</text><text x="470" y="{y+28}">{e(labels[edge["to"]][:23])}</text><text x="15" y="{y+78}">{i+1}. {e(edge["label"][:70])}</text>')
                    parts.append('</svg><div class="table-wrap"><table><caption>'+t('relationships')+'</caption><thead><tr><th scope="col">'+t('from')+'</th><th scope="col">'+t('relationship')+'</th><th scope="col">'+t('to')+'</th></tr></thead><tbody>')
                    for edge in edges:
                        parts.append('<tr><td>'+e(labels[edge['from']])+'</td><td>'+e(edge['label'])+'</td><td>'+e(labels[edge['to']])+'</td></tr>')
                    parts.append('</tbody></table></div>')
                parts.append('<h3>'+t('nodes')+'</h3>'+listing([n['id']+': '+n['label'] for n in nodes]))
            else:
                parts.append('<p class="muted">'+t('no_flow')+'</p>')
        if key == 'results':
            parts.append('<h3>'+t('metrics')+'</h3><div class="grid">')
            for metric in data['metrics']:
                value=ui['unknown'] if metric['value'] is None else str(metric['value'])
                parts.append('<article class="card"><h3>'+e(metric['name'])+'</h3><p class="value">'+e(value)+' <small>'+e(metric['unit'])+'</small></p><dl>'+''.join('<dt>'+t(field if field!='kind' else 'classification')+'</dt><dd>'+e(ui[metric[field]] if field=='kind' else metric[field])+'</dd>' for field in ('kind','source','denominator','uncertainty'))+'</dl></article>')
            parts.append('</div>' if data['metrics'] else '</div><p class="muted">'+t('no_metrics')+'</p>')
            tests=data['tests']; total=len(tests)
            parts.append('<h3>'+t('tests')+'</h3><p>'+e(ui['distribution'].replace('{n}',str(total)))+'</p>')
            if tests:
                parts.append('<svg viewBox="0 0 700 210" role="img" aria-label="'+t('chart_aria')+'">')
                for i,status in enumerate(STATUSES):
                    count=sum(test['status']==status for test in tests); y=20+i*40
                    # Full localized labels remain in the textual list. Keep the approved chart geometry.
                    chart_status = {'ru': {'INCONCLUSIVE': 'Неясно'}, 'sr-Latn': {'INCONCLUSIVE': 'Nejasno'}}.get(locale, {}).get(status, ui[status])
                    parts.append(f'<text x="0" y="{y+17}">{e(chart_status)}</text><rect x="160" y="{y}" width="{count/total*460:.3f}" height="24" fill="#b9dbc5"/><text x="640" y="{y+17}">{count}</text>')
                parts.append('</svg>')
            parts.append('<ul>'+''.join('<li>'+t(status)+': '+str(sum(test['status']==status for test in tests))+' '+t('scenarios')+'</li>' for status in STATUSES)+'</ul><div class="filters" aria-label="'+t('filter')+'">')
            for status in ('all',)+STATUSES:
                parts.append('<button type="button" data-filter="'+status+'" aria-pressed="'+('true' if status=='all' else 'false')+'">'+t('all_statuses' if status=='all' else status)+'</button>')
            parts.append('</div><p data-filter-state data-template="'+t('shown')+'" role="status">'+e(ui['shown'].replace('{n}',str(total)))+'</p>')
            for test in tests:
                parts.append('<details data-status="'+test['status']+'"><summary><span class="badge">'+t(test['status'])+'</span>'+e(test['name'])+'</summary><p>'+t('environment')+': '+e(test['environment'])+'</p><h3>'+t('prerequisites')+'</h3>'+listing(test['prerequisites'])+'<h3>'+t('steps')+'</h3><ol>'+''.join('<li>'+e(step)+'</li>' for step in test['steps'])+'</ol><p>'+t('evidence')+': '+e(', '.join(test['evidence_ids']) or ui['no_evidence'])+'</p>')
                if 'note' in test:
                    parts.append('<p>'+e(test['note'])+'</p>')
                parts.append('</details>')
            parts.append('<h3>'+t('risks')+'</h3>'+listing(data['risks'])+'<h3>'+t('references')+'</h3><ul>')
            for evidence in data['evidence']:
                parts.append('<li>'+e(evidence['id'])+': '+e(evidence['description'])+(' · <a rel="noopener noreferrer" href="'+e(evidence['url'])+'">'+t('open_source')+'</a>' if 'url' in evidence else '')+'</li>')
            parts.append('</ul>' if data['evidence'] else '</ul><p class="muted">'+t('no_references')+'</p>')
        parts.append('</section>')
    parts.append('<aside aria-label="'+t('reminders')+'"><h2>'+t('checklist')+'</h2><p>'+t('local_only')+'</p>')
    for reminder in ui['checks']:
        parts.append('<label class="check"><input type="checkbox"><span>'+e(reminder)+'</span></label>')
    parts.append('<p data-review-state data-template="'+t('checked')+'" role="status">'+e(ui['checked'].replace('{n}','0').replace('{total}','3'))+'</p></aside><footer>'+t('footer')+'</footer></main></div>')
    return ''.join(parts)


def render_html(data):
    validate(data)
    locale=data.get('language','en')
    return ('<!doctype html><html lang="'+locale+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; script-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;; connect-src &#39;none&#39;">'
            '<title>'+esc(data['title'])+'</title><style>'+CSS+'</style></head><body>'
            +_render_page(data,locale)
            +'<script>'+JS+'</script></body></html>')


def render_to_target(data, target):
    page = render_html(data)
    target = _path(target)
    if not target.is_dir():
        raise ArtifactError("Target must be an existing directory")
    output = target / 'artifacts' / data['feature'] / 'index.html'
    _path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    _path(output)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(output, flags, 0o600), 'w', encoding='utf-8') as stream:
        stream.write(page)
    return output


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--input')
    parser.add_argument('--target')
    args=parser.parse_args(argv)
    if args.plan:
        print('PLAN ONLY: select the visible feature, prepare scoped evidence, review privacy, then explicitly render a new artifact. No input or target read.')
        return 0
    if not args.approved or not args.input or not args.target:
        parser.error('rendering requires --approved, --input and --target')
    try:
        output=render_to_target(load_input(args.input), args.target)
    except (ArtifactError, OSError, ValueError, RecursionError, OverflowError):
        # Never echo source contents, private URLs or credential-bearing exception strings.
        print('Artifact not rendered: invalid input, unsafe path, or existing/unwritable output.')
        return 2
    print('Rendered: '+str(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
