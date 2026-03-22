import json

from datetime import datetime
from pathlib import Path
from .models import Message

def _parse_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _parse_record(raw: dict) -> Message:
    return Message(
        type=raw.get("type", "unknown"),
        timestamp=_parse_timestamp(raw.get("timestamp")),
    )


def _parse_jsonl(path: Path) -> list[Message]:
    messages = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            try:
                raw = json.loads(line)
                messages.append(_parse_record(raw))
            except (json.JSONDecodeError, Exception):
                # Prevent crashes if Claude Code was killed mid-write
                continue
    return messages
