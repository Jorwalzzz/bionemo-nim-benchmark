"""
Antigravity Brain Sync & Token Tracker Utility
"""
import os
import json
import argparse

MEMORY_PATH = r"c:\Users\jorwa\Documents\antigravity\BIONEMO\.agents\memory\MEMORY.md"
STATE_PATH = r"c:\Users\jorwa\Documents\antigravity\BIONEMO\.agents\memory\STATE.json"
MAX_CAP_BYTES = 40960  # 40 KB cap

def check_brain():
    if not os.path.exists(MEMORY_PATH):
        print("[FAIL] MEMORY.md not found.")
        return False
    size = os.path.getsize(MEMORY_PATH)
    status = "OK" if size <= MAX_CAP_BYTES else "OVERSIZED"
    print(f"[BRAIN] Memory Journal: {size} bytes / {MAX_CAP_BYTES} bytes ({status})")
    
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        print(f"[STATE] Active Architecture: {state.get('active_architecture')}")
        print(f"[STATE] Fallback Router: {state.get('fallback_router_active')}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check brain status")
    args = parser.parse_args()
    if args.check:
        check_brain()
