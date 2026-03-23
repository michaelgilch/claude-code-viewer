# test_data.py - Quick test script to verify parsing of jsonl files
# 
# Usage: 
#   .venv/bin/python test_data.py <path-to-session.jsonl>
# 
# Imports _parse_jsonl from data module, which reads the JSONL file and returns 
# a Session object. Print the session-level info (extracted once from the file)
# and each message's per-record fields to verify they're being parsed correctly.

import sys

from pathlib import Path
from app.data import _parse_jsonl

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path-to-session.jsonl>")
    sys.exit(1)

# _parse_jsonl returns a Session object containing:
#   - session_id: UUID from the filename
#   - cwd: working directory, same across all records
#   - messages: list of Message objects, one per JSONL line
session = _parse_jsonl(Path(sys.argv[1]))

# Print session-level info (extracted once, not per-record)
print(f"Session: {session.session_id}")
print(f"CWD:     {session.cwd}")
print(f"Records: {len(session.messages)}")
print()

# Print each record's per-message fields.
# type:      the record type (user, assistant, progress, etc.)
# timestamp: when it was recorded (None for some types)
# role:      "user" or "assistant" (None for non-conversation records)
# text:      message contents
for m in session.messages:
    tags = []
    if m.has_thinking: tags.append("[thinking]")
    if m.tool_name: tags.append(f"[{m.tool_name}]")
    tag_str = " ".join(tags)
    text_preview = (m.text or "")[:30]
    print(f"{m.type:25s} {m.timestamp} {m.role:10s} {tag_str} {text_preview}")
