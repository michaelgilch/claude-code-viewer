#!/usr/bin/env python3

"""
parse_jsonl.py

Read a Claude Code session file and print record summaries.
"""

import json
import sys
from pathlib import Path

def main():
  path = Path(sys.argv[1])

  with open(path, "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
      line = line.strip()
      try:
        record = json.loads(line)
      except json.JSONDecodeError:
        # Prevent crashes if Claude Code was killed mid-write.
        print(f"  [{i}] INVALID JSON")
        continue

      record_type = record.get("type")
      timestamp = record.get("timestamp")

      print(f"[{i}] {record_type:30s} {timestamp}")

if __name__ == "__main__":
    main()