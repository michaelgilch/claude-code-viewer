"""
Pydantic models that define the shape of our parsed data.

Claude Code stores conversation history as JSONL files (one JSON object per
line). Each line is a "record" with a "type" field. We parse those raw dicts
into these structured models so the rest of the app can work with typed
attributes (m.type, m.role) instead of raw dict access (raw["type"]).

We use Pydantic's BaseModel because it gives us:
    - Type validation (catches bad data early)
    - Type coercion (e.g., ISO 8601 string -> datetime object automatically)
    - Clean attribute access (m.timestamp instead of m["timestamp"])
"""

from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    A single record from a JSONL session file.

    Each line in the JSONL file becomes one Message. The "type" field tells
    us what kind of record it is. Examples from real JSONL data:

        {"type": "user", "timestamp": "2026-03-22T01:52:31.309Z",
         "message": {"role": "user", "content": "What does this function do?"}, ...}

        {"type": "assistant", "timestamp": "2026-03-22T01:52:36.129Z",
         "message": {"role": "assistant", "content": [...]}, ...}

        {"type": "progress", "timestamp": "2026-03-22T01:52:37.473Z", ...}

        {"type": "file-history-snapshot", "snapshot": {...}}

    Not all record types have all fields. For example, "progress" records
    have no "message.role", and "file-history-snapshot" may have no timestamp.
    That's why most fields are optional (None by default).
    """

    # The record type. Always present. Values include:
    # "user", "assistant", "progress", "file-history-snapshot",
    # "system", "last-prompt", "custom-title", "summary", "agent-name"
    type: str

    # ISO 8601 timestamp from the record, e.g. "2026-03-22T01:52:31.309Z".
    # Pydantic automatically converts the string to a datetime object.
    # None for some record types like "file-history-snapshot".
    timestamp: datetime | None = None

    # "user" or "assistant". Comes from message.role, not the top-level record.
    # None for non-conversation records (progress, system, etc.).
    role: str | None = None

    # The message text. For user messages, the plain string from message.content.
    # For assistant messages, the first "text" block's content.
    # None for non-conversation records or records with no text block.
    text: str | None = None

    # Whether this record contains a thinking block. Claude Code redacts
    # the actual thinking content in the JSONL, so we just track presence.
    has_thinking: bool = False

    # The tool name from a tool_use block, e.g. "Bash", "Read", "Write".
    # Only present on assistant records that contain a tool call.
    #   {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}
    tool_name: str | None = None

    # Whether this record carries a tool result (output from a tool call).
    # These appear as user records with list content like:
    #   [{"type": "tool_result", "tool_use_id": "toolu_019g...", "content": "..."}]
    has_tool_result: bool = False


class Session(BaseModel):
    """
    One conversation session, parsed from a single JSONL file.

    Session-level fields (session_id, cwd) are the same on every record
    in the file, so we extract them once here rather than duplicating
    them on every Message.

    The JSONL file lives at a path like:
        ~/.claude/projects/-home-michael-git-me-myproject/3ba2f556-5445-...jsonl

    The filename (minus .jsonl) is the session_id (a UUID).
    The cwd comes from records inside the file, e.g.:
        {"cwd": "/home/michael/git/me/myproject", ...}
    """

    # UUID from the filename, e.g. "3ba2f556-5445-4770-b9b3-af99c49b4028"
    session_id: str

    # The real working directory for this session, e.g.
    # "/home/michael/git/me/myproject". Extracted from the first record
    # that has a "cwd" field. This is the actual path on disk, as opposed
    # to the project directory name which encodes slashes as hyphens.
    cwd: str | None = None

    # All records from the JSONL file, in order.
    messages: list[Message] = Field(default_factory=list)

    # Summary fields, computed after parsing all messages.

    # First 200 chars of the first real user prompt (not a tool result).
    # Useful as a preview/title for the session in listings.
    first_prompt: str | None = None

    # Timestamp of the first record with a timestamp.
    first_timestamp: datetime | None = None

    # Timestamp of the last record with a timestamp.
    last_timestamp: datetime | None = None

    # Total number of records in the JSONL file.
    message_count: int = 0

    # Number of real user prompts (excluding tool_result records).
    user_message_count: int = 0

    # Number of tool calls made by the assistant.
    tool_call_count: int = 0
