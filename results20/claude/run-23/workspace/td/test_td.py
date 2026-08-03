#!/usr/bin/env python3
"""Smoke tests for td. Runs each command through the real CLI entry point
against an isolated temp data dir (via TD_DIR)."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TD = [sys.executable, os.path.join(HERE, "td.py")]

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"ok   {name}")
    else:
        failed += 1
        print(f"FAIL {name}  {detail}")


def main():
    env = dict(os.environ, TD_DIR=tempfile.mkdtemp())

    def cli(*args):
        p = subprocess.run(TD + list(args), capture_output=True, text=True,
                           env=env, cwd=HERE)
        return p

    # --- add ---
    p = cli("add", "Buy milk", "#errands", "-p", "2", "-d", "2099-01-01")
    check("add prints added", p.returncode == 0 and "added" in p.stdout, p.stderr)

    p = cli("add", "Plain task")
    check("add plain", "added [2]" in p.stdout, p.stdout)

    # data persisted with all fields
    import json, glob
    datafiles = glob.glob(os.path.join(env["TD_DIR"], "tasks.json"))
    data = json.load(open(datafiles[0]))
    t1 = data["tasks"][0]
    check("prio stored", t1["prio"] == 2, t1)
    check("tag stored", "errands" in t1["tags"], t1)
    check("due stored", t1["due"] == "2099-01-01", t1)

    # --- list & filters ---
    out = cli("ls").stdout
    check("ls shows 2 open", "2 task(s)" in out, out)
    out = cli("ls", "+errands").stdout
    check("ls +tag filters", "Buy milk" in out and "Plain" not in out, out)
    out = cli("ls", "today").stdout
    check("ls today excludes future", "Plain task" not in out and "Buy milk" not in out, out)
    out = cli("ls", "prio:2").stdout
    check("ls prio:2", "Buy milk" in out and "Plain" not in out, out)

    # --- done / open / clear-done ---
    check("done id", "done [1]" in cli("done", "1").stdout)
    out = cli("ls").stdout
    check("done hides completed", "Buy milk" not in out, out)
    check("reopen", "reopened [1]" in cli("open", "1").stdout)
    cli("done", "1")
    check("clear-done", "cleared 1" in cli("clear-done").stdout)

    # --- errors ---
    p = cli("rm", "999")
    check("rm unknown is a no-op", p.returncode == 0 and "removed 0" in p.stdout, p.stdout)
    p = cli("add", "-d", "not-a-date", "x")
    check("bad date errors", p.returncode != 0 and "valid date" in p.stderr, p.stderr)
    p = cli("add")
    check("empty add errors", p.returncode != 0 and "nothing to add" in p.stderr, p.stderr)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
