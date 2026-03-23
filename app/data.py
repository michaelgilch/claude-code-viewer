"""
Parsing logic for Claude Code project session files.

Each JSONL file located at ~/.claude/projects/**/*.jsonl is a new session, which
are parsed into our pydantic Session objects. Each session contains multiple 
messages, which are parsed into our pydantic Message objects.
"""

import json

from datetime import datetime
from pathlib import Path

from .models import Message, Session

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def _parse_timestamp(ts: str | None) -> datetime | None:
    """
    Convert an ISO 8601 timestamp string to a datetime object.

    Claude Code timestamps look like: "2026-03-22T01:52:31.309Z"
    The "Z" suffix means UTC, but Python's datetime.fromisoformat() doesn't 
    understand "Z", wanting "+00:00" instead. So we swap it before parsing.

    Returns None if the timestamp is missing or malformed, since some record 
    types (like "file-history-snapshot") don't always have one.
    """
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _parse_record(raw: dict) -> Message:
    """
    Convert a raw JSON dict (one JSONL line) into a Message.

    The tricky part: some fields live at the top level of the record, 
    while others are nested inside a "message" dict. 

    For example:
        {
          "type": "assistant",
          "timestamp": "2026-03-...",
          "message": {
            "role": "assistant",
            "content": [...],
            "model": "claude-opus-4-6",
            "usage": {"input_tokens": 3, ...}
          }
        }

    "type" and "timestamp" come from the top level.
    "role" comes from inside "message".

    The `or {}` on the msg line handles the case where "message" exists 
    but is None (which would cause msg.get() to crash).
    """
    msg = raw.get("message", {}) or {}

    # User messages: content is a plain string like:
    #   "message": {"role": "user", "content": "What does this function do?"}
    # Assistant messages: content is a list of blocks like:
    #   "message": {"content": [{"type": "text", "text": "This function..."}]}
    content = msg.get("content")
    text = None
    has_thinking = False
    tool_name = None
    has_tool_result = False
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and text is None:
                text = block.get("text", "")
            elif block.get("type") == "thinking":
                has_thinking = True
            elif block.get("type") == "tool_use" and tool_name is None:
                tool_name = block.get("name")
            elif block.get("type") == "tool_result":
                has_tool_result = True

    return Message(
        type=raw.get("type", "unknown"),
        timestamp=_parse_timestamp(raw.get("timestamp")),
        role=msg.get("role", ""),
        text=text,
        has_thinking=has_thinking,
        tool_name=tool_name,
        has_tool_result=has_tool_result,
    )


def _parse_jsonl(path: Path) -> Session:
    """
    Parse a JSONL session file into a Session object.

    Takes a path like:
        ~/.claude/projects/-home-michael-git-me-myproject/3ba2f556-...jsonl

    The session_id comes from the filename (path.stem strips the .jsonl
    extension), e.g. "3ba2f556-5445-4770-b9b3-af99c49b4028".

    The cwd is grabbed from the first record that has one. It's the same
    across all records in a file, so we only need to capture it once.
    Example: {"cwd": "/home/michael/git/me/myproject", ...}

    We read line by line rather than loading the whole file at once because
    session files can be large (thousands of records). errors="replace"
    substitutes a replacement character for any malformed bytes instead of
    crashing -- tool output in the JSONL can sometimes contain unexpected
    encodings.

    If a line is blank or has invalid JSON (e.g., the file was truncated
    because Claude Code was killed mid-write), we skip it and continue.
    """
    session_id = path.stem
    cwd = None
    messages = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            try:
                raw = json.loads(line)
                # Grab cwd from the first record that has it.
                # All records in a session share the same cwd.
                if cwd is None:
                    cwd = raw.get("cwd")
                messages.append(_parse_record(raw))
            except (json.JSONDecodeError, Exception):
                # Skip malformed lines rather than crashing
                continue

    # Compute summary fields from the parsed messages.
    first_prompt = None
    first_timestamp = None
    last_timestamp = None
    user_message_count = 0
    tool_call_count = 0

    for m in messages:
        # Track first and last timestamps
        if m.timestamp:
            if first_timestamp is None:
                first_timestamp = m.timestamp
            last_timestamp = m.timestamp

        # Count real user prompts and grab the first one as a preview
        if m.role == "user" and not m.has_tool_result:
            user_message_count += 1
            if first_prompt is None and m.text:
                first_prompt = m.text[:200]

        # Count tool calls
        if m.tool_name:
            tool_call_count += 1

    return Session(
        session_id=session_id,
        cwd=cwd,
        messages=messages,
        first_prompt=first_prompt,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        message_count=len(messages),
        user_message_count=user_message_count,
        tool_call_count=tool_call_count,
    )


def scan_projects_dir(projects_dir: Path = CLAUDE_PROJECTS_DIR) -> list[Session]:
    """
    Walk ~/.claude/projects/ and parse every JSONL file into a Session.

    Directory structure looks like:
        ~/.claude/projects/
        ├── -home-user-git-myproject/
        │   ├── 3ba2f556-5445-...jsonl      <- one session
        │   ├── 94626ce6-1070-...jsonl      <- another session
        │   └── 3ba2f556-.../subagents/     <- subagent data (ignored for now)
        ├── -home-user-git-another/
        │   └── ...

    Each subdirectory is a project (directory name encodes the path with
    hyphens). Each .jsonl file inside is one conversation session.

    Returns a list of Session objects, one per JSONL file found.
    """
    sessions = []

    if not projects_dir.is_dir():
        return sessions

    for project_entry in sorted(projects_dir.iterdir()):
        if not project_entry.is_dir():
            continue
        for jsonl_file in sorted(project_entry.glob("*.jsonl")):
            sessions.append(_parse_jsonl(jsonl_file))

    return sessions
