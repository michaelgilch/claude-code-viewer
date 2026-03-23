# test_data.py - Quick test script to verify parsing of jsonl files
#
# Usage:
#   .venv/bin/python test_data.py                          # list all projects
#   .venv/bin/python test_data.py sessions                 # list all sessions
#   .venv/bin/python test_data.py <path-to-session.jsonl>  # parse one file

import sys

from pathlib import Path
from app.data import _parse_jsonl, scan_projects_dir, build_projects


def print_session(session):
    """Print a single session's details."""
    print(f"Session:       {session.session_id}")
    print(f"CWD:           {session.cwd}")
    print(f"First prompt:  {(session.first_prompt or '(none)')[:80]}")
    print(f"First time:    {session.first_timestamp}")
    print(f"Last time:     {session.last_timestamp}")
    print(f"Records:       {session.message_count}")
    print(f"User prompts:  {session.user_message_count}")
    print(f"Tool calls:    {session.tool_call_count}")
    print()
    for m in session.messages:
        tags = []
        if m.has_thinking: tags.append("[thinking]")
        if m.tool_name: tags.append(f"[{m.tool_name}]")
        if m.has_tool_result: tags.append("[tool_result]")
        tag_str = " ".join(tags)
        text_preview = (m.text or "")[:30]
        print(f"{m.type:25s} {m.timestamp} {m.role:10s} {tag_str} {text_preview}")


def print_sessions(sessions):
    """Print a one-line summary per session."""
    print(f"Found {len(sessions)} sessions\n")
    for s in sessions:
        prompt = (s.first_prompt or "(none)")[:40]
        print(f"{s.session_id[:8]}  {s.message_count:4d} records  {s.user_message_count:3d} prompts  {s.tool_call_count:3d} tools  {prompt}")


def print_projects(projects):
    """Print a one-line summary per project."""
    print(f"Found {len(projects)} projects\n")
    for p in projects:
        print(f"{p.display_name:30s} {p.session_count:3d} sessions  {p.total_user_messages:4d} prompts  {p.total_tool_calls:4d} tools  {p.original_path}")


if len(sys.argv) == 1:
    # Default: list projects
    sessions = scan_projects_dir()
    print_projects(build_projects(sessions))
elif sys.argv[1] == "sessions":
    # List all sessions
    print_sessions(scan_projects_dir())
elif len(sys.argv) == 2:
    # Single file mode
    print_session(_parse_jsonl(Path(sys.argv[1])))
else:
    print(f"Usage: {sys.argv[0]} [sessions | path-to-session.jsonl]")
    sys.exit(1)
