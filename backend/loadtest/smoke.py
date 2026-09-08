"""Phase 5 uvicorn smoke (brief §10.1a/d/e): real server, stub provider.

Starts uvicorn (N workers) with isolated sqlite + stub LLM, runs concurrent
streams, reports RSS/threads/latency. Instant-stub measures app overhead
only — NOT provider capacity (stated honestly in the report).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.request

PORT = int(os.environ.get("QORA_SMOKE_PORT", 8019))
WORKERS = int(os.environ.get("QORA_SMOKE_WORKERS", 1))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/


def _rss_kb(pid: int) -> int:
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    return 0


def _children(pid: int) -> list[int]:
    kids = []
    import glob as _glob
    for stat in _glob.glob("/proc/[0-9]*/stat"):
        try:
            with open(stat) as f:
                parts = f.read().rsplit(")", 1)[1].split()
            if int(parts[1]) == pid:
                kids.append(int(stat.split("/")[2]))
        except Exception:
            pass
    return kids


def _tree_rss_kb(pid: int) -> int:
    total = _rss_kb(pid)
    for kid in _children(pid):
        total += _rss_kb(kid)
        for grand in _children(kid):
            total += _rss_kb(grand)
    return total


def _threads(pid: int) -> int:
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            if line.startswith("Threads:"):
                return int(line.split()[1])
    return 0


def _api(path, method="GET", body=None, token=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Content-Type": "application/json", **(
            {"Authorization": f"Bearer {token}"} if token else {})},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def main() -> dict:
    env = dict(os.environ,
               DATABASE_URL="sqlite:////tmp/qora_smoke.db",
               LLM_API_KEY="", ENV="test",
               JWT_SECRET="smoke-test-secret-32bytes-minimum!!")
    try:
        os.remove("/tmp/qora_smoke.db")
    except OSError:
        pass
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(PORT),
         "--workers", str(WORKERS)],
        cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if _api("/health")[0] == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("server did not start")
        email = f"smoke{int(time.time())}@t.co"
        _api("/api/auth/signup", "POST",
             {"email": email, "password": "secret12", "full_name": "S"})
        _, login = _api("/api/auth/login", "POST",
                        {"email": email, "password": "secret12"})
        tok = login["data"]["token"]
        _, s = _api("/api/v2/sessions", "POST",
                    {"case_id": "em_anaphylaxis_001", "language": "en"}, tok)
        sid = s["data"]["sessionId"]
        rss0, th0 = _rss_kb(proc.pid), _threads(proc.pid)

        def fire(i, out, firsts):
            t0 = time.time()
            req = urllib.request.Request(
                f"http://127.0.0.1:{PORT}/api/v2/sessions/{sid}/turns/stream",
                data=json.dumps({"text": f"halo {i}"}).encode(), method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {tok}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                got_first = False
                n = 0
                while True:
                    chunk = r.read(64)
                    if not chunk:
                        break
                    n += len(chunk)
                    if not got_first:
                        got_first = True
                        firsts.append(time.time() - t0)
            out.append(n)

        N = 10
        waves = []
        all_firsts = []
        for wave in range(2):
            out, firsts, errs = [], [], []

            def wrap(i):
                try:
                    fire(i, out, firsts)
                except Exception as e:  # noqa: BLE001
                    errs.append(repr(e))

            ts = [threading.Thread(target=wrap, args=(i,)) for i in range(N)]
            t0 = time.time()
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            dt = time.time() - t0
            time.sleep(1)
            waves.append({"wall_s": round(dt, 2), "errors": len(errs),
                          "threads": _threads(proc.pid),
                          "rss_kb": _rss_kb(proc.pid)})
            all_firsts.extend(firsts)
            assert not errs, errs[:2]
        firsts = all_firsts
        dt = waves[-1]["wall_s"]
        res = {
            "workers": WORKERS,
            "streams": N,
            "waves": waves,
            "errors": 0,
            "bytes": "n/a (per-wave discarded)", 
            "wall_s": round(dt, 2),
            "first_chunk_p50_s": round(sorted(firsts)[len(firsts) // 2], 3) if firsts else None,
            "first_chunk_max_s": round(max(firsts), 3) if firsts else None,
            "rss_before_kb": rss0,
            "tree_rss_before_kb": _tree_rss_kb(proc.pid),
            "rss_after_kb": _rss_kb(proc.pid),
            "tree_rss_after_kb": _tree_rss_kb(proc.pid),
            "threads_before": th0,
            "threads_after": _threads(proc.pid),
        }
        print(json.dumps(res, indent=1))
        return res
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    r = main()
    if r["errors"]:
        raise SystemExit(1)
