#!/usr/bin/env python3
"""
Root forwarder executing scripts/audit/run_all_audits.py.
Preserves backwards compatibility for direct execution from scripts/ root.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    target_script = Path(__file__).resolve().parent / "audit" / "run_all_audits.py"
    if not target_script.is_file():
        sys.stderr.write(f"Error: Audit script not found at {target_script}\n")
        sys.exit(1)
    runpy.run_path(str(target_script), run_name="__main__")
