"""Offline renderer acceptance: real files, hostile text, boundaries and honest gaps."""
import copy
import importlib.util
import io
import json
from contextlib import redirect_stdout, redirect_stderr
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

RENDER = Path(__file__).resolve().parents[1] / 'packages/docs/documentation/render.py'
spec = importlib.util.spec_from_file_location('docs_artifact_render', RENDER)
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


def fixture():
    return {
        'version': 1, 'approved_for_render': True, 'privacy_reviewed': True,
        'feature': 'safe-export', 'title': 'Export · Привет 世界', 'revision': 'abc123',
        'readiness': 'Partial: browser NOT_RUN', 'what': 'Portable feature review',
        'why': 'Give reviewers context', 'how': 'Approved local rendering',
        'results': 'One fixture scenario passed; production NOT_RUN',
        'environment_names': ['APP_MODE'], 'risks': ['Live verification NOT_RUN'],
        'evidence': [{'id': 'E1', 'description': 'Fixture source', 'url': 'https://example.com/guide#section'}],
        'tests': [{'name': 'Render fixture', 'status': 'PASS', 'environment': 'offline disposable directory',
                   'steps': ['Render approved input', 'Inspect generated source'],
                   'prerequisites': ['Python standard library'], 'evidence_ids': ['E1']}],
        'metrics': [{'name': 'Latency', 'value': None, 'unit': 'ms', 'source': 'No observation',
                     'kind': 'observed', 'denominator': 'unknown', 'uncertainty': 'not measured'}],
        'flow': {'nodes': [{'id': 'input', 'label': 'Approved input'}, {'id': 'output', 'label': 'HTML output'}],
                 'edges': [{'from': 'input', 'to': 'output', 'label': 'Offline render'}]}}


def localized_fixtures():
    """Three standalone authored narratives for an explicit synthetic renderer-review subject."""
    en=fixture()
    en.update(
        title='A review page you can hand to someone — synthetic example',
        revision='synthetic-fixture-locales',
        readiness='Example only. Local rendering is exercised; browser and production checks remain open.',
        what='A reviewer should not have to reconstruct a change from a long chat. This synthetic example packages the scope, the reasons and the remaining checks into one page that opens locally. It demonstrates the handoff format; it does not describe a released application.',
        why='The page puts the explanation next to its evidence so a reviewer can decide what to inspect next. We chose an offline file to keep the review independent of a running server. We have not measured a reduction in review time or any business impact.',
        how='The author prepares the narrative and evidence, reviews the text, and then renders approved JSON into a new HTML file. The flow below shows that proposed handoff. The page is written in the chosen document language and never contacts a translation service.',
        results='This fixture contains three scenarios. Rendering can be checked locally, while browser review and operational conclusions need their own evidence. Open the checks below, inspect the source revision and follow the review steps. Latency stays unknown because no timing measurement was supplied.',
        environment_names=[],
        risks=['This is synthetic input, not evidence of a released feature.', 'No application runtime or production SLA was evaluated.'],
        evidence=[{'id':'E1','description':'Synthetic input authored for an offline renderer review; not an external verified source.'}],
        tests=[
            {'name':'Render this approved fixture', 'status':'PASS', 'environment':'Disposable local directory',
             'steps':['Render the complete approved fixture.', 'Open the resulting file and compare its content with the input.'],
             'prerequisites':['Python standard library'], 'evidence_ids':['E1'],
             'note':'This scenario is a local renderer fixture; it establishes no application acceptance.'},
            {'name':'Review this page in a browser', 'status':'NOT_RUN', 'environment':'Desktop and mobile browser',
             'steps':['Read the narrative and inspect the diagrams.', 'Check keyboard navigation, status filtering and the checklist.'],
             'prerequisites':['Generated HTML file'], 'evidence_ids':['E1'],
             'note':'The renderer does not mark a browser review complete.'},
            {'name':'Assess production behavior', 'status':'INCONCLUSIVE', 'environment':'No application runtime supplied',
             'steps':['Obtain separately authorized runtime evidence.', 'Evaluate the actual operational window.'],
             'prerequisites':['An identified application and independent evidence'], 'evidence_ids':['E1'],
             'note':'This synthetic example cannot establish an operational SLA.'}],
        metrics=[
            {'name':'Page load time', 'value':None, 'unit':'ms', 'source':'No timing observation supplied', 'kind':'observed', 'denominator':'unknown', 'uncertainty':'not measured'},
            {'name':'Scenarios in this example', 'value':3, 'unit':'scenarios', 'source':'The three scenario entries in this synthetic input', 'kind':'observed', 'denominator':'n=3 listed scenarios, not production executions', 'uncertainty':'exact input count'}],
        flow={'nodes':[{'id':'input','label':'Reviewed input'},{'id':'output','label':'Portable review page'}], 'edges':[{'from':'input','to':'output','label':'Proposed local handoff: approve, render, then review'}]})
    ru=copy.deepcopy(en)
    ru.update(
        title='Страница, которую можно передать проверяющему — учебный пример',
        readiness='Только пример. Локальное формирование проверяется; браузер и рабочая среда ещё требуют проверки.',
        what='Проверяющему не должно требоваться восстанавливать изменение по длинной переписке. В этом учебном примере описание, причины решений и оставшиеся проверки собраны на одной странице, которая открывается локально. Это демонстрация формата передачи, а не выпущенного приложения.',
        why='Объяснение расположено рядом с подтверждениями: так проверяющий может выбрать следующий шаг. Мы выбрали автономный файл, чтобы просмотр не зависел от работающего сервера. Сокращение времени проверки и влияние на бизнес не измерялись.',
        how='Автор готовит описание и подтверждения, проверяет текст, затем формирует новый HTML-файл из одобренного JSON. Ниже показана предлагаемая передача результата. Страница подготовлена на языке документации проекта и не обращается в сервис перевода.',
        results='В примере три сценария. Формирование файла можно проверить локально; для браузерной проверки и выводов о работе приложения нужны отдельные подтверждения. Откройте сценарии ниже, сверьте ревизию и выполните шаги проверки. Время загрузки неизвестно: измерений не предоставлено.',
        risks=['Это учебные данные, а не подтверждение выпуска функции.', 'Работа приложения и соглашение об уровне сервиса в рабочей среде не оценивались.'])
    ru['evidence'][0]['description']='Учебные данные для автономной проверки генератора; это не проверенный внешний источник.'
    test_texts=[
        ('Сформировать страницу из одобренного примера','Временный локальный каталог',['Сформировать страницу из полного одобренного набора данных.','Открыть файл и сопоставить его содержимое с исходными данными.'],['Стандартная библиотека Python'],'Это локальный тест генератора; он не подтверждает приёмку приложения.'),
        ('Проверить страницу в браузере','Браузер на компьютере и мобильном устройстве',['Прочитать описание и просмотреть схемы.','Проверить клавиатуру, фильтр статусов и список напоминаний.'],['Сформированный HTML-файл'],'Генератор не отмечает браузерную проверку выполненной.'),
        ('Оценить работу в рабочей среде','Работающее приложение не предоставлено',['Получить отдельно разрешённые подтверждения работы приложения.','Оценить фактический период наблюдения.'],['Определённое приложение и независимые подтверждения'],'Учебный пример не подтверждает соглашение об уровне сервиса.')]
    for test, values in zip(ru['tests'], test_texts):
        test.update(zip(('name','environment','steps','prerequisites','note'),values))
    ru['metrics'][0].update(name='Время загрузки страницы',source='Наблюдения времени не предоставлены',denominator='неизвестно',uncertainty='не измерялось')
    ru['metrics'][1].update(name='Сценарии в этом примере',unit='сценариев',source='Три записи сценариев в этих учебных данных',denominator='n=3 перечисленных сценария, а не запуска в рабочей среде',uncertainty='точное число записей')
    ru['flow']['nodes'][0]['label']='Проверенные данные';ru['flow']['nodes'][1]['label']='Страница для проверки'
    ru['flow']['edges'][0]['label']='Предложение: одобрить данные, сформировать страницу, проверить'
    sr=copy.deepcopy(en)
    sr.update(
        title='Stranica koju možete predati na pregled — sintetički primer',
        readiness='Samo primer. Lokalno generisanje se proverava; pregled u pregledaču i produkcija još nisu provereni.',
        what='Osoba koja pregleda izmenu ne bi trebalo da je rekonstruiše iz dugog razgovora. Ovaj sintetički primer okuplja obim, razloge i preostale provere na jednoj stranici koja se otvara lokalno. Prikazuje format predaje, a ne objavljenu aplikaciju.',
        why='Objašnjenje je uz dokaze kako bi osoba koja pregleda mogla da izabere sledeći korak. Izabrali smo samostalnu datoteku da pregled ne zavisi od pokrenutog servera. Nismo merili uštedu vremena niti poslovni uticaj.',
        how='Autor priprema tekst i dokaze, proverava tekst, pa od odobrenog JSON-a pravi novu HTML datoteku. Tok ispod prikazuje predloženu predaju. Stranica je napisana na jeziku dokumentacije projekta i ne poziva servis za prevođenje.',
        results='Primer sadrži tri scenarija. Generisanje se može proveriti lokalno, dok pregled u pregledaču i operativni zaključci zahtevaju zasebne dokaze. Otvorite provere ispod, uporedite reviziju i pratite korake provere. Vreme učitavanja ostaje nepoznato jer merenje nije dostavljeno.',
        risks=['Ovo su sintetički podaci, a ne dokaz o objavljenoj funkciji.', 'Rad aplikacije i ugovoreni nivo usluge u produkciji nisu ocenjeni.'])
    sr['evidence'][0]['description']='Sintetički ulaz pripremljen za lokalni pregled generatora; nije potvrđen spoljašnji izvor.'
    test_texts=[
        ('Generisanje odobrenog primera','Privremeni lokalni direktorijum',['Generišite stranicu iz potpunog odobrenog ulaza.','Otvorite datoteku i uporedite sadržaj sa ulazom.'],['Standardna biblioteka Python-a'],'Ovo je lokalni test generatora; ne potvrđuje prihvatanje aplikacije.'),
        ('Pregled stranice u pregledaču','Pregledač na računaru i mobilnom uređaju',['Pročitajte opis i pregledajte dijagrame.','Proverite tastaturu, filtriranje statusa i podsetnike.'],['Generisana HTML datoteka'],'Generator ne označava pregled u pregledaču kao završen.'),
        ('Ocena rada u produkciji','Pokrenuta aplikacija nije dostavljena',['Pribavite zasebno odobrene dokaze o radu aplikacije.','Ocenite stvarni period posmatranja.'],['Određena aplikacija i nezavisni dokazi'],'Ovaj sintetički primer ne potvrđuje ugovoreni nivo usluge.')]
    for test, values in zip(sr['tests'], test_texts):
        test.update(zip(('name','environment','steps','prerequisites','note'),values))
    sr['metrics'][0].update(name='Vreme učitavanja stranice',source='Merenje vremena nije dostavljeno',denominator='nepoznato',uncertainty='nije mereno')
    sr['metrics'][1].update(name='Scenariji u ovom primeru',unit='scenarija',source='Tri zapisa scenarija u ovom sintetičkom ulazu',denominator='n=3 navedena scenarija, a ne izvršavanja u produkciji',uncertainty='tačan broj zapisa')
    sr['flow']['nodes'][0]['label']='Pregledani ulaz';sr['flow']['nodes'][1]['label']='Prenosiva stranica'
    sr['flow']['edges'][0]['label']='Predlog: odobriti ulaz, generisati, zatim pregledati'
    return {locale:dict(content, version=1, language=locale) for locale,content in [('en',en),('ru',ru),('sr-Latn',sr)]}



class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags=[]; self.attrs=[]; self.content=[]

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag); self.attrs.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.content.append(data)


class ArtifactTests(unittest.TestCase):
    def test_real_output_unicode_responsive_accessible_self_contained(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            output=render.render_to_target(fixture(), tmp)
            self.assertEqual(output, Path(tmp)/'artifacts/safe-export/index.html')
            source=output.read_text(); doc=Document(); doc.feed(source)
            self.assertIn('Привет 世界', ''.join(doc.content))
            self.assertIn('@media(max-width:600px)', source)
            self.assertIn('width=device-width', source)
            self.assertTrue(any(tag=='nav' and attrs.get('aria-label') for tag,attrs in doc.attrs))
            self.assertTrue(any(tag=='button' and 'data-filter' in attrs for tag,attrs in doc.attrs))
            self.assertIn('checkbox', source); self.assertIn('focus-visible', source)
            self.assertIn('Flow relationships (full text)', source)
            self.assertIn('Offline render', source)
            self.assertEqual(doc.tags.count('script'), 1)
            self.assertFalse(any('src' in attrs for tag,attrs in doc.attrs))
            self.assertNotIn('fetch(', source); self.assertNotIn('<link', source)
            self.assertEqual(set(Path(tmp).rglob('*')), {output, output.parent, output.parent.parent})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_hostile_text_never_becomes_markup_script_or_attributes(self):
        data=fixture(); attack='</script><img src=x onerror="alert(1)"> & <script>bad()</script>\u2028'
        data['title']=attack; data['what']=attack; data['tests'][0]['name']=attack
        data['flow']['nodes'][0]['label']=attack[:120]
        source=render.render_html(data); doc=Document(); doc.feed(source)
        self.assertNotIn('img', doc.tags)
        self.assertEqual(doc.tags.count('script'), 1)
        self.assertNotIn(attack, source)
        self.assertIn(attack, ''.join(doc.content))
        self.assertIn('&lt;/script&gt;', source)

    def test_unsafe_urls(self):
        for url in ['javascript:alert(1)', 'http://example.com', 'https://user:pass@example.com',
                    'https://example.com/?token=secret', 'https://127.0.0.1/', 'https://127.1/', 'https://[::1]/',
                    'https://private.local/', 'https://host.internal/', 'https://localhost/',
                    'https://example.com:444/', 'https://example.com\\@private.local/',
                    'https://example.com/\nsecret', '//example.com', 'file:///tmp/file']:
            with self.subTest(url=url):
                data=fixture(); data['evidence'][0]['url']=url
                with self.assertRaises(render.ArtifactError): render.render_html(data)

    def test_language_and_na_rationale(self):
        data=fixture(); data['language']='ru'
        self.assertIn('<html lang="ru">', render.render_html(data))
        data['language']='en" onload="bad'
        with self.assertRaises(render.ArtifactError): render.render_html(data)
        data=fixture(); data['tests'][0]['status']='NA'
        with self.assertRaises(render.ArtifactError): render.render_html(data)
        data['tests'][0]['note']='Not applicable: no external service in fixture'
        self.assertIn('Not applicable', render.render_html(data))

    def test_missing_unknown_and_mixed_unit_metrics(self):
        data=fixture(); source=render.render_html(data)
        self.assertIn('Unknown', source); self.assertNotIn('>0 <small>ms', source)
        data['metrics']=[]; data['tests']=[]; data['flow']={'nodes': [], 'edges': []}
        source=render.render_html(data)
        self.assertIn('No measurements supplied', source); self.assertIn('No flow supplied', source)
        self.assertNotIn('<svg', source); self.assertIn('0 listed scenarios', source)
        data=fixture(); metric=copy.deepcopy(data['metrics'][0]); metric.update(value=4, unit='requests', denominator='n=4 requests')
        data['metrics'].append(metric); source=render.render_html(data)
        self.assertIn('4 <small>requests', source)
        self.assertIn('Unknown <small>ms', source)
        del data['metrics'][0]['source']
        with self.assertRaises(render.ArtifactError): render.render_html(data)

    def test_no_overwrite_and_feature_scoping(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            output=render.render_to_target(fixture(), tmp); original=output.read_bytes()
            with self.assertRaises(FileExistsError): render.render_to_target(fixture(), tmp)
            self.assertEqual(output.read_bytes(), original)
            for slug in ['../other', '/tmp/other', 'x/y', 'x\\y', '', 'https:thing', '..']:
                data=fixture(); data['feature']=slug
                with self.assertRaises(render.ArtifactError): render.render_to_target(data, tmp)

    def test_symlinks_input_output_parents_and_target(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            root=Path(tmp); real=root/'real'; real.mkdir(); link=root/'link'; link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(render.ArtifactError): render.render_to_target(fixture(), link)
            (real/'artifacts').symlink_to(root/'outside', target_is_directory=True)
            with self.assertRaises(render.ArtifactError): render.render_to_target(fixture(), real)
            (real/'artifacts').unlink(); (real/'artifacts/safe-export').mkdir(parents=True)
            (real/'artifacts/safe-export/index.html').symlink_to(root/'missing')
            with self.assertRaises(render.ArtifactError): render.render_to_target(fixture(), real)
            inp=root/'input.json'; inp.write_text(json.dumps(fixture())); (root/'alias.json').symlink_to(inp)
            with self.assertRaises(render.ArtifactError): render.load_input(root/'alias.json')
            with self.assertRaises(render.ArtifactError): render.load_input(link/'input.json')

    def test_strict_json_schema_and_size(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            inp=Path(tmp)/'input.json'
            for raw in [b'{"version":1,"version":1}', b'\xff', b'{"x":NaN}', b'['*2000, b' '* (render.MAX_BYTES+1)]:
                inp.write_bytes(raw)
                with self.assertRaises(render.ArtifactError): render.load_input(inp)
            inp.write_text(json.dumps(fixture()), encoding='utf-8')
            self.assertEqual(render.load_input(inp)['revision'], 'abc123')
        for mutate in [lambda d:d.update(extra='unknown'), lambda d:d.update(version=True),
                       lambda d:d.update(approved_for_render=False), lambda d:d.update(privacy_reviewed=False),
                       lambda d:d.update(what=''), lambda d:d.update(title='\ud800'),
                       lambda d:d.update(environment_names=['API_KEY=value']),
                       lambda d:d['metrics'][0].update(value=float('inf')),
                       lambda d:d['metrics'][0].update(value=True),
                       lambda d:d['tests'][0].update(evidence_ids=['missing']),
                       lambda d:d['flow']['edges'][0].update(to='missing'),
                       lambda d:d.update(risks=['x'*2000]*40, evidence=[{'id': 'E'+str(i), 'description':'x'*2000} for i in range(60)])]:
            data=fixture(); mutate(data)
            with self.assertRaises(render.ArtifactError): render.render_html(data)

    def test_plan_no_reads_writes_or_render_even_with_arguments(self):
        with patch.object(render, 'load_input', side_effect=AssertionError('read')), \
             patch.object(render, 'render_to_target', side_effect=AssertionError('write')), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(render.main(['--plan', '--approved', '--input', '/missing', '--target', '/missing']), 0)
            self.assertIn('No input or target read', output.getvalue())

    def test_cli_explicit_approval_and_sanitized_error(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()): render.main([])
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            inp=Path(tmp)/'in.json'; data=fixture(); data['evidence'][0]['url']='https://user:SECRET@example.com'
            inp.write_text(json.dumps(data))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(render.main(['--approved','--input',str(inp),'--target',tmp]),2)
            self.assertNotIn('SECRET', output.getvalue()); self.assertFalse((Path(tmp)/'artifacts').exists())
            inp.write_text(json.dumps(fixture()))
            with redirect_stdout(io.StringIO()): self.assertEqual(render.main(['--approved','--input',str(inp),'--target',tmp]),0)


    def test_three_separate_complete_locales_without_selector(self):
        fixtures=localized_fixtures()
        for locale in ('en','ru','sr-Latn'):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
                data=fixtures[locale]
                output=render.render_to_target(data,tmp)
                source=output.read_text(encoding='utf-8'); doc=Document(); doc.feed(source)
                self.assertIn('<html lang="'+locale+'">',source)
                self.assertEqual(doc.tags.count('main'),1)
                self.assertNotIn('select',doc.tags)
                self.assertNotIn('data-language',source)
                self.assertNotIn('translations',source)
                self.assertIn(data['what'],''.join(doc.content))
                self.assertIn(data['results'],''.join(doc.content))
                self.assertEqual(doc.tags.count('script'),1)
                self.assertEqual(set(render.UI[locale]),set(render.UI['en']))
                ui=render.UI[locale]
                for key in ('what','why','how','results','unknown','revision','PASS','NOT_RUN',
                            'INCONCLUSIVE','steps','prerequisites','classification','source',
                            'denominator','uncertainty','references','footer','no_evidence'):
                    # no_evidence belongs to the absent-reference branch exercised below.
                    if key!='no_evidence': self.assertIn(ui[key],''.join(doc.content))
                for key in ('navigation','chart_aria','flow_aria','filter','reminders'):
                    self.assertTrue(any(attrs.get('aria-label')==ui[key] for tag,attrs in doc.attrs),key)
                if locale!='en':
                    for english in ('Source revision:', 'Remaining risks and blockers', 'Reviewer checklist',
                                    '>Unknown<', '>All statuses<', '>Environment:'):
                        self.assertNotIn(english,source)
                if locale=='ru': self.assertIn('Прочитать описание',source)
                if locale=='sr-Latn': self.assertIn('Pročitajte opis',source)
                # Geometry and byte-for-byte CSS stay identical across languages.
                self.assertIn('viewBox="0 0 700 210"',source)
                self.assertIn('width="153.333"',source)
                self.assertIn(render.CSS,source)

    def test_localized_empty_states_and_live_message_templates(self):
        for locale,data in localized_fixtures().items():
            with self.subTest(locale=locale):
                data['flow']={'nodes':[],'edges':[]};data['evidence']=[]
                data['tests'][0]['evidence_ids']=[]
                for test in data['tests']: test['evidence_ids']=[]
                data['risks']=[]
                source=render.render_html(data);doc=Document();doc.feed(source);ui=render.UI[locale]
                for key in ('none','no_flow','no_evidence','no_references','unknown'):
                    self.assertIn(ui[key],''.join(doc.content))
                self.assertTrue(any(attrs.get('data-template')==ui['shown'] for tag,attrs in doc.attrs))
                self.assertTrue(any(attrs.get('data-template')==ui['checked'] for tag,attrs in doc.attrs))
                data['metrics']=[];data['tests']=[]
                source=render.render_html(data)
                self.assertIn(ui['no_metrics'],source)
                self.assertIn(ui['shown'].replace('{n}','0'),source)

    def test_no_bundle_schema_or_unsupported_locale_and_no_config_reads(self):
        for language in ('sr', 'sr-Cyrl', 'en-US', 'de', '', None, ['en']):
            data=fixture();data['language']=language
            with self.subTest(language=language), self.assertRaises(render.ArtifactError):render.render_html(data)
        for extra in ({'translations':{'ru':{}}},{'version':2},{'language_options':['ru']}):
            data=fixture();data.update(extra)
            with self.subTest(extra=extra),self.assertRaises(render.ArtifactError):render.render_html(data)
        with patch.object(Path,'read_text',side_effect=AssertionError('config read')):
            self.assertIn('<html lang="en">',render.render_html(fixture()))

    def test_localized_text_stays_escaped_and_out_of_script(self):
        attack='</script><img src=x onerror="bad()">Привет & Čačak'
        for locale,data in localized_fixtures().items():
            with self.subTest(locale=locale):
                data['title']=attack;data['metrics'][0]['source']=attack;data['tests'][0]['note']=attack
                data['flow']['nodes'][0]['label']=attack
                source=render.render_html(data);doc=Document();doc.feed(source)
                self.assertEqual(doc.tags.count('script'),1)
                self.assertNotIn('img',doc.tags)
                self.assertIn(attack,''.join(doc.content))
                self.assertNotIn(attack,source)
                self.assertIn('<script>'+render.JS+'</script>',source)
                ids=[attrs['id'] for tag,attrs in doc.attrs if 'id' in attrs]
                self.assertEqual(len(ids),len(set(ids)))


if __name__ == '__main__':
    unittest.main()
