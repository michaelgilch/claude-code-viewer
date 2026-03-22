#!/usr/bin/env python3

"""
parse_jsonl.py

Read a Claude Code session file and print record summaries.
"""

import json
import sys
from pathlib import Path

def main():
  if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path-to-session.jsonl>")
    sys.exit(1)

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
      timestamp = record.get("timestamp") or ""
      cwd = record.get("cwd")

      msg = record.get("message", {})
      content = msg.get("content")

      if isinstance(content, str):
        content_to_print = content[:80]
      elif isinstance(content, list):
        content_parts = []
        for b in content:
          if not isinstance(b, dict):
            continue
          btype = b.get("type")
          if btype == "thinking":
            content_details = b.get("thinking", "")[:80]
          elif btype == "text":
            content_details = b.get("text", "")[:80]
          elif btype == "tool_use":
            content_details = b.get("name", "")
          else:
            content_details = ""
          content_parts.append(f"[{btype}]: {content_details}")
        content_to_print = "\n      ".join(content_parts)
      else:
        content_to_print = ""

      usage = msg.get("usage", {})
      if usage:
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        usage_line = f"      tokens: {inp} in / {out} out / {cache_write} cache_write / {cache_read} cache_read"
      else:
        usage_line = ""

      print(f"[{i}] {record_type:30s} {timestamp:30s} {cwd}")
      print(f"      {content_to_print}")
      if usage_line:
        print(usage_line)

if __name__ == "__main__":
    main()