import sys
from pathlib import Path
from app.data import _parse_jsonl

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path-to-session.jsonl>")
    sys.exit(1)

msgs = _parse_jsonl(Path(sys.argv[1]))
for m in msgs:
    print(f"{m.type:25s} {m.timestamp}")
