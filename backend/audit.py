"""Append-only audit trail of agent loop activity: output/audit_trail.json.

The file is always a valid JSON array. New events are appended by overwriting only the
closing "]" at the end of the file, so earlier entries are never rewritten or wiped.
Each agent run writes: run_start -> model_response / tool_call / tool_result / guard_retry ... -> run_end.
Privacy: logs user_id (never email/password), and shopper text is already PII-redacted upstream.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart,
)

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 240  # "short" args/results
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def short(value: Any, limit: int = MAX_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append(events: list[dict]) -> None:
    """Append events without rewriting existing ones."""
    if not events:
        return
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text("[\n]\n", encoding="utf-8")
        body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in events)
        with open(AUDIT_PATH, "r+b") as f:
            f.seek(0, 2)
            end = f.tell()
            # Find the closing bracket by scanning back from the end of the file.
            pos = end - 1
            while pos >= 0:
                f.seek(pos)
                ch = f.read(1)
                if ch == b"]":
                    break
                pos -= 1
            if pos < 0:
                raise RuntimeError("audit_trail.json is not a JSON array; refusing to modify it")
            # Back up over whitespace before "]" so entries stay one per line.
            while pos > 0:
                f.seek(pos - 1)
                if f.read(1) not in (b"\n", b"\r", b" ", b"\t"):
                    break
                pos -= 1
            f.seek(pos - 1)
            empty = f.read(1) == b"["  # nothing appended yet
            f.seek(pos)
            f.truncate()
            f.write((("\n" if empty else ",\n") + body + "\n]\n").encode("utf-8"))


def run_events(run_id: str, messages: list[ModelMessage], skip: int) -> list[dict]:
    """Turn this run's new messages (after `skip` history messages) into audit events."""
    events: list[dict] = []
    for msg in messages[skip:]:
        if isinstance(msg, ModelResponse):
            ts = msg.timestamp.isoformat(timespec="milliseconds") if msg.timestamp else _now()
            calls = [p for p in msg.parts if isinstance(p, ToolCallPart)]
            events.append({
                "time": ts, "run_id": run_id, "event": "model_response",
                "model": msg.model_name, "finish_reason": msg.finish_reason,
                "tokens_in": msg.usage.input_tokens, "tokens_out": msg.usage.output_tokens,
                "tool_calls": [c.tool_name for c in calls],
            })
            for c in calls:
                events.append({
                    "time": ts, "run_id": run_id, "event": "tool_call",
                    "tool": c.tool_name, "args": short(c.args_as_dict() if c.args else {}),
                })
        else:
            for part in msg.parts:
                ts = getattr(part, "timestamp", None)
                ts = ts.isoformat(timespec="milliseconds") if ts else _now()
                if isinstance(part, ToolReturnPart):
                    events.append({
                        "time": ts, "run_id": run_id, "event": "tool_result",
                        "tool": part.tool_name, "result": short(part.model_response_str()),
                    })
                elif isinstance(part, RetryPromptPart):
                    events.append({
                        "time": ts, "run_id": run_id, "event": "guard_retry" if part.tool_name in (None, "final_result") or "price" in str(part.content) else "tool_retry",
                        "tool": part.tool_name, "reason": short(part.content if isinstance(part.content, str) else part.model_response()),
                    })
    return events


def start_event(run_id: str, user_id: int | None, message: str, page_path: str, product_id: str | None) -> dict:
    return {
        "time": _now(), "run_id": run_id, "event": "run_start",
        "user": f"user:{user_id}" if user_id else "guest",
        "message": short(message, 160), "page": page_path, "page_product": product_id,
    }


def end_event(run_id: str, stop_reason: str, seconds: float, usage=None, product_ids=None, page_title=None, error=None) -> dict:
    e = {
        "time": _now(), "run_id": run_id, "event": "run_end", "stop_reason": stop_reason,
        "seconds": round(seconds, 2),
    }
    if usage is not None:
        e.update(model_requests=usage.requests, tool_calls=usage.tool_calls,
                 tokens_in=usage.input_tokens, tokens_out=usage.output_tokens)
    if product_ids is not None:
        e.update(products_returned=len(product_ids), page_title=page_title)
    if error:
        e["error"] = short(error, 160)
    return e
