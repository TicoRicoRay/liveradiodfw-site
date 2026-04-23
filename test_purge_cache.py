#!/usr/bin/env python3
"""Tests for purge_cache.py.

Pure stdlib. No network calls; api_purge is monkey-patched.
Run: python test_purge_cache.py
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure test clones the module's main() with a controlled env
sys.path.insert(0, str(Path(__file__).resolve().parent))
import purge_cache  # noqa: E402


PASS = 0
FAIL = 0


def check(label: str, ok: bool, detail: str = '') -> None:
    global PASS, FAIL
    mark = 'OK  ' if ok else 'FAIL'
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"{mark}  {label}" + (f"  -- {detail}" if detail else ''))


def run_main(argv: list[str], env: dict | None = None) -> tuple[int, str, str]:
    """Invoke purge_cache.main() with argv and env overrides. Returns (rc, out, err)."""
    old_argv = sys.argv[:]
    old_env = dict(os.environ)
    try:
        sys.argv = ['purge_cache.py', *argv]
        if env is not None:
            os.environ.clear()
            os.environ.update(env)
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = purge_cache.main()
        return rc, out_buf.getvalue(), err_buf.getvalue()
    finally:
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_env)


# ---- ASCII gate ----
src = Path(__file__).resolve().parent / 'purge_cache.py'
data = src.read_bytes()
bad = [(i, b) for i, b in enumerate(data) if b > 0x7F]
check("purge_cache.py is pure ASCII", not bad,
      '' if not bad else f'{len(bad)} non-ASCII bytes at {bad[0]}')

# ---- Argument handling ----

# no args -> exit 1
rc, out, err = run_main([], env={})
check("no args returns 1", rc == 1)
check("no args prints nothing-to-purge error", 'nothing to purge' in err)

# >30 URLs -> exit 1
urls_31 = [f'https://www.liveradiodfw.com/x{i}' for i in range(31)]
rc, out, err = run_main(urls_31, env={})
check(">30 URLs returns 1", rc == 1)
check(">30 URLs prints Free-plan limit", '30 URLs per purge call' in err)

# --dry-run --shows works without any env
rc, out, err = run_main(['--dry-run', '--shows'], env={})
check("dry-run --shows returns 0", rc == 0)
check("dry-run prints shows bundle URLs",
      '/shows.json' in out and '/shows' in out)
check("dry-run prints SHOWS_BUNDLE count",
      f'{len(purge_cache.SHOWS_BUNDLE)} URLs' in out)

# --dry-run with explicit URLs
rc, out, err = run_main(
    ['--dry-run', 'https://www.liveradiodfw.com/a',
     'https://www.liveradiodfw.com/b'],
    env={})
check("dry-run with 2 URLs returns 0", rc == 0)
check("dry-run with 2 URLs lists both in body",
      '"https://www.liveradiodfw.com/a"' in out
      and '"https://www.liveradiodfw.com/b"' in out)

# --everything dry-run
rc, out, err = run_main(['--dry-run', '--everything'], env={})
check("dry-run --everything returns 0", rc == 0)
check("dry-run --everything uses purge_everything: true",
      'purge_everything' in out and 'true' in out)

# Missing token -> exit 1 (not dry-run)
rc, out, err = run_main(['--shows'], env={})
check("missing token returns 1", rc == 1)
check("missing token error mentions CLOUDFLARE_API_TOKEN",
      'CLOUDFLARE_API_TOKEN' in err)

# Missing zone id -> exit 1
rc, out, err = run_main(['--shows'], env={'CLOUDFLARE_API_TOKEN': 'fake'})
check("missing zone id returns 1", rc == 1)
check("missing zone id error mentions CLOUDFLARE_ZONE_ID",
      'CLOUDFLARE_ZONE_ID' in err)

# ---- Env file loader ----
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / '.env'
    p.write_text(
        '# comment line\n'
        '\n'
        'FOO_TEST_KEY=foo-value\n'
        'QUOTED_KEY="with-quotes"\n'
        'BAD_LINE_NO_EQUALS\n',
        encoding='utf-8',
    )
    # Prevent pollution from outer env
    for k in ('FOO_TEST_KEY', 'QUOTED_KEY'):
        os.environ.pop(k, None)
    purge_cache.load_env_file(p)
    check("load_env_file reads plain KEY=VALUE",
          os.environ.get('FOO_TEST_KEY') == 'foo-value')
    check("load_env_file strips quotes",
          os.environ.get('QUOTED_KEY') == 'with-quotes')
    check("load_env_file skips lines without '='",
          'BAD_LINE_NO_EQUALS' not in os.environ)

    # Should NOT override existing env
    os.environ['FOO_TEST_KEY'] = 'existing'
    purge_cache.load_env_file(p)
    check("load_env_file does not override existing env",
          os.environ.get('FOO_TEST_KEY') == 'existing')
    os.environ.pop('FOO_TEST_KEY', None)
    os.environ.pop('QUOTED_KEY', None)

# Missing .env path is a no-op
purge_cache.load_env_file(Path('/nonexistent/.env'))
check("load_env_file silently ignores missing file", True)

# ---- api_purge error path (monkeypatched) ----

def _fake_api_fail(token, zone_id, body):
    return {'success': False, '_http_status': 403,
            'errors': [{'message': 'fake denial'}]}

orig_api = purge_cache.api_purge
purge_cache.api_purge = _fake_api_fail
try:
    rc, out, err = run_main(
        ['--shows'],
        env={'CLOUDFLARE_API_TOKEN': 'fake', 'CLOUDFLARE_ZONE_ID': 'fake-zone'},
    )
    check("API failure returns 2", rc == 2)
    check("API failure prints error body", 'fake denial' in err)
finally:
    purge_cache.api_purge = orig_api


# ---- api_purge success path with --no-verify ----

def _fake_api_ok(token, zone_id, body):
    return {'success': True, 'result': {'id': 'purge-abc-123'},
            'errors': [], 'messages': []}

purge_cache.api_purge = _fake_api_ok
try:
    rc, out, err = run_main(
        ['--shows', '--no-verify'],
        env={'CLOUDFLARE_API_TOKEN': 'fake', 'CLOUDFLARE_ZONE_ID': 'fake-zone'},
    )
    check("successful purge with --no-verify returns 0", rc == 0)
    check("successful purge prints Cloudflare request id",
          'purge-abc-123' in out)
finally:
    purge_cache.api_purge = orig_api


print()
print(f"RESULT: {PASS} passed, {FAIL} failed")
sys.exit(0 if FAIL == 0 else 1)
