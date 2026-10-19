"""Disposable real runtime smoke + control-plane latency acceptance; no providers."""
from contextlib import closing
import json
import math
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrator.engine import create, status, work
from orchestrator.spec import validate
from orchestrator.store import Store


def main():
    flow = json.loads((ROOT / 'examples/product-factory/smoke.json').read_text())
    executable = str(Path(sys.executable).resolve())
    flow['policy']['executables'] = [executable]
    for task in flow['tasks']:
        task['argv'][0] = executable
        for argv in task['verify']:
            argv[0] = executable
    with tempfile.TemporaryDirectory(prefix='factory-acceptance-') as temp:
        base = Path(temp)
        target = base / 'target'; target.mkdir()
        def git(*args):
            subprocess.run(['git', '-C', str(target), *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        git('init'); git('config', 'user.email', 'factory@example.invalid'); git('config', 'user.name', 'Factory Acceptance')
        (target / 'README.md').write_text('Disposable synthetic target\n')
        git('add', '.'); git('commit', '-m', 'baseline')
        state = base / 'state'
        run = create(state, flow, target)
        started = time.monotonic()
        assert work(state, run) == 'verified'
        report = status(state, run)
        assert report['status'] == 'verified'
        assert Path(report['workspace'], 'factory-smoke.txt').read_text() == 'verified\n'
        assert not (target / 'factory-smoke.txt').exists()
        duration = time.monotonic() - started
        # Measure queue transaction service latency only, excluding process startup.
        bench = validate(flow)
        bench['tasks'] = [dict(bench['tasks'][0], id='task_' + str(i), depends_on=[]) for i in range(100)]
        bench['limits']['run_seconds'] = 120
        with closing(Store(base / 'benchmark')) as store:
            store.add('latency', bench, str(target), 'synthetic')
            samples = []
            for i in range(100):
                before = time.monotonic()
                claim = store.claim('latency')
                assert claim is not None
                assert store.finish('latency', claim['id'], claim['token'], True, [])
                samples.append((time.monotonic() - before) * 1000)
        p95 = sorted(samples)[math.ceil(len(samples) * 0.95) - 1]
        result = dict(schema_version=1, python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                      platform=platform.system() + ' ' + platform.machine(), samples=len(samples),
                      control_plane_p95_ms=round(p95, 3), threshold_ms=100,
                      smoke_seconds=round(duration, 3), smoke='PASS', control_plane='PASS' if p95 <= 100 else 'FAIL',
                      live_providers='NOT_RUN', operational_sla='NOT_RUN')
        print(json.dumps(result, indent=2))
        return 0 if p95 <= 100 else 1


if __name__ == '__main__':
    sys.exit(main())
