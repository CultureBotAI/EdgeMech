"""Final offline validation receipt for recanary PR76, 2026-11-13.

Inputs: completed private canary state, staged public changes and local tools.
Outputs: private command logs and validation.json; no network or new judgments.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def validate(data, ruff, privacy_only=False):
    directory = data / 'validation'
    directory.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src')}
    checks = [
        ('pytest', [sys.executable, '-m', 'pytest', '-q']),
        ('ruff', [str(ruff), 'check', '--no-cache', 'scripts/adhoc/edge_recanary_20261113', 'tests/test_edge_recanary.py']),
        ('sampling', [sys.executable, 'scripts/adhoc/edge_recanary_20261113/build_recanary.py', '--data-dir', str(data.parent), '--verify']),
        ('packets', [sys.executable, 'scripts/adhoc/edge_recanary_20261113/verify_packets.py', '--manifest', str(data / 'sample/canary.jsonl'), '--retrieval', str(data / 'literature'), '--identifiers', str(data / 'identifiers')]),
        ('staged_whitespace', ['git', 'diff', '--cached', '--check']),
    ]
    receipt = (json.loads((data / 'validation.json').read_text()) if privacy_only else
               {'checked_at': datetime.now(timezone.utc).isoformat(), 'checks': {}})
    if privacy_only and (set(receipt['checks']) != {name for name, _ in checks} or
                         any(item['exit_code'] for item in receipt['checks'].values())):
        raise ValueError('All substantive checks must pass before privacy-only refresh')
    for name, command in ([] if privacy_only else checks):
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        log = directory / (name + '.log')
        log.write_bytes(result.stdout)
        receipt['checks'][name] = {'exit_code': result.returncode,
                                   'log_sha256': hashlib.sha256(result.stdout).hexdigest()}
        print(json.dumps({'check': name, 'exit_code': result.returncode,
                          'tail': result.stdout.decode(errors='replace').splitlines()[-2:]}), flush=True)
        if result.returncode:
            (data / 'validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
            raise SystemExit(result.returncode)
    staged = subprocess.check_output(['git', 'diff', '--cached', '--no-ext-diff', '--unified=0'], cwd=ROOT).decode()
    added = '\n'.join(line[1:] for line in staged.splitlines() if line.startswith('+') and not line.startswith('+++'))
    patterns = {
        'personal_paths': '/' + 'Users/',
        'machine_names': r'\b[^\s/]+' + r'\.' + 'local' + r'\b|Mac' + 'Book',
        'email_addresses': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        'credential_values': r'(?i)(?:api[_-]?key|access[_-]?token|secret)\s*[=:]\s*[\"\x27]?[A-Za-z0-9_\-]{20,}',
        'terminal_selectors': r'\bttys\d+\b',
    }
    findings = {name: len(re.findall(pattern, added)) for name, pattern in patterns.items()}
    receipt['staged_privacy_matches'] = findings
    receipt['privacy_checked_at'] = datetime.now(timezone.utc).isoformat()
    receipt['staged_diff_sha256'] = hashlib.sha256(staged.encode()).hexdigest()
    receipt['status'] = 'passed' if not any(findings.values()) else 'failed_privacy'
    (data / 'validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'privacy_matches': findings}), flush=True)
    if any(findings.values()):
        raise SystemExit('Staged privacy scan failed; inspect privately before committing')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--ruff', required=True, type=Path)
    parser.add_argument('--privacy-only', action='store_true')
    args = parser.parse_args()
    validate(args.data_dir.resolve(), args.ruff, args.privacy_only)
