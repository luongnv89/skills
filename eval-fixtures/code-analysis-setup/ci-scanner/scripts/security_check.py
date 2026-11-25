"""Fixture stand-in for the runner security-setup generates.

It only lists the configured checks; the real runner is written by the
security-setup skill. Eval runs read this repo and do not execute it.
"""
import json
from pathlib import Path

config = json.loads(Path("security/security-tools.json").read_text(encoding="utf-8"))
for check in config["checks"]:
    print(f"{check['name']} ({check['category']})")
