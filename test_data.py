# test_data.py - Quick test script to verify parsing of jsonl files
#
# Usage:
#   .venv/bin/python test_data.py                          # scan all sessions
#   .venv/bin/python test_data.py <path-to-session.jsonl>  # parse one file

import sys

from pathlib import Path
from app.data import _parse_jsonl, scan_projects_dir


def print_session(session):
    """Print a single session's details."""
    print(f"Session: {session.session_id}")
    print(f"CWD:     {session.cwd}")
    print(f"Records: {len(session.messages)}")
    print()
    for m in session.messages:
        tags = []
        if m.has_thinking: tags.append("[thinking]")
        if m.tool_name: tags.append(f"[{m.tool_name}]")
        if m.has_tool_result: tags.append("[tool_result]")
        tag_str = " ".join(tags)
        text_preview = (m.text or "")[:30]
        print(f"{m.type:25s} {m.timestamp} {m.role:10s} {tag_str} {text_preview}")


def print_summary(sessions):
    """Print a one-line summary per session."""
    print(f"Found {len(sessions)} sessions\n")
    for s in sessions:
        user_msgs = sum(1 for m in s.messages if m.role == "user" and not m.has_tool_result)
        tool_calls = sum(1 for m in s.messages if m.tool_name)
        print(f"{s.session_id[:8]}  {len(s.messages):4d} records  {user_msgs:3d} prompts  {tool_calls:3d} tools  {s.cwd}")


if len(sys.argv) == 2:
    # Single file mode
    print_session(_parse_jsonl(Path(sys.argv[1])))
elif len(sys.argv) == 1:
    # Scan all sessions
    print_summary(scan_projects_dir())
else:
    print(f"Usage: {sys.argv[0]} [path-to-session.jsonl]")
    sys.exit(1)
