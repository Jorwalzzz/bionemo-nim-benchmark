#!/usr/bin/env python3
"""
Antigravity Token Tracker & Analytics CLI
Audits and calculates historical token consumption across all Antigravity sessions.
"""

import os
import sys
import glob
import json
import argparse
from datetime import datetime

# Ensure clean UTF-8 output on Windows PowerShell
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def analyze_token_usage(verbose=False, limit=10):
    brain_path = os.path.expanduser("~/.gemini/antigravity-ide/brain")
    transcripts = glob.glob(os.path.join(brain_path, "*", ".system_generated", "logs", "transcript_full.jsonl"))

    if not transcripts:
        print("No Antigravity session transcripts found in brain directory.")
        return

    total_input_chars = 0
    total_output_chars = 0
    total_turns = 0
    session_stats = []

    for t_path in transcripts:
        parts = t_path.split(os.sep)
        conv_id = parts[-4] if len(parts) >= 4 else "unknown"
        s_in_chars = 0
        s_out_chars = 0
        s_turns = 0
        last_modified = os.path.getmtime(t_path)
        last_date = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M")

        try:
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        step = json.loads(line)
                        s_turns += 1
                        content = str(step.get("content", ""))
                        tool_calls = json.dumps(step.get("tool_calls", "")) if "tool_calls" in step else ""
                        src = step.get("source", "")
                        stype = step.get("type", "")
                        chars = len(content) + len(tool_calls)

                        if src == "MODEL" or stype == "PLANNER_RESPONSE":
                            s_out_chars += chars
                        else:
                            s_in_chars += chars
                    except Exception:
                        pass
        except Exception:
            continue

        in_tokens = int(s_in_chars / 3.8)
        out_tokens = int(s_out_chars / 3.8)
        tot_tokens = in_tokens + out_tokens

        session_stats.append({
            "conv_id": conv_id,
            "date": last_date,
            "turns": s_turns,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "total_tokens": tot_tokens,
            "avg_step": int(tot_tokens / max(1, s_turns))
        })

        total_input_chars += s_in_chars
        total_output_chars += s_out_chars
        total_turns += s_turns

    total_in = int(total_input_chars / 3.8)
    total_out = int(total_output_chars / 3.8)
    grand_total = total_in + total_out
    avg_per_step = int(grand_total / max(1, total_turns))
    avg_per_session = int(grand_total / max(1, len(session_stats)))

    print("=" * 65)
    print(" 🚀 ANTIGRAVITY TOKEN CONSUMPTION AUDIT")
    print("=" * 65)
    print(f" • Total Sessions Analyzed : {len(session_stats)}")
    print(f" • Total Conversation Steps : {total_turns:,}")
    print(f" • Total Input/Prompt Tokens : {total_in:,}")
    print(f" • Total Output/Code Tokens  : {total_out:,}")
    print(f" • GRAND TOTAL BURNED TOKENS : {grand_total:,} (~{grand_total/1_000_000:.2f}M)")
    print(f" • Average Tokens per Step   : {avg_per_step:,}")
    print(f" • Average Tokens per Session: {avg_per_session:,}")
    print("=" * 65)

    session_stats.sort(key=lambda x: x["total_tokens"], reverse=True)

    print(f"\n📋 TOP {min(limit, len(session_stats))} SESSIONS BY TOKEN CONSUMPTION:")
    print(f"{'Session ID':<20} {'Last Active':<17} {'Steps':<7} {'In Tokens':<12} {'Out Tokens':<12} {'Total'}")
    print("-" * 80)
    for s in session_stats[:limit]:
        print(f"{s['conv_id'][:18]+'..':<20} {s['date']:<17} {s['turns']:<7} {s['in_tokens']:<12,}"
              f" {s['out_tokens']:<12,} {s['total_tokens']:,}")

    print("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Token Usage Tracker")
    parser.add_argument("--limit", type=int, default=8, help="Number of top sessions to display")
    parser.add_argument("--verbose", action="store_true", help="Display verbose step logs")
    args = parser.parse_args()

    analyze_token_usage(verbose=args.verbose, limit=args.limit)
