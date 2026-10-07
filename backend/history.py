"""Per-user chat history in the chat_messages table (logged-in shoppers only)."""

import json

import tools
from db import get_db
from models import ChatTurn, HistoryMessage, ProductCard

RELOAD_LIMIT = 50  # messages sent back to the widget
AGENT_TURNS = 12   # messages replayed to the agent as context


def ensure_schema() -> None:
    """chat_messages ships with the seed DB; add page_title so search results reload on the page too."""
    with get_db() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        if "page_title" not in cols:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN page_title TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, id)")


def save_exchange(user_id: int, user_text: str, reply: str, products: list[ProductCard], page_title: str | None) -> None:
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, user_text)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_title) VALUES (?, 'assistant', ?, ?, ?)",
            (user_id, reply, products_json, page_title),
        )


def _recent_rows(user_id: int, limit: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, page_title, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def load_for_widget(user_id: int) -> list[HistoryMessage]:
    rows = _recent_rows(user_id, RELOAD_LIMIT)
    # Rebuild product cards from the DB (one query) so reloaded prices/stock are current, not stale snapshots.
    ids_per_row = []
    for r in rows:
        try:
            ids = [p["product_id"] for p in json.loads(r["products_json"] or "[]")]
        except (ValueError, TypeError, KeyError):
            ids = []
        ids_per_row.append(ids)
    cards = {c.product_id: c for c in tools.products_by_ids([i for ids in ids_per_row for i in ids])}
    return [
        HistoryMessage(
            role=r["role"], content=r["content"], created_at=r["created_at"],
            products=[cards[i] for i in ids if i in cards], page_title=r["page_title"],
        )
        for r, ids in zip(rows, ids_per_row)
    ]


def load_for_agent(user_id: int) -> list[ChatTurn]:
    return [ChatTurn(role=r["role"], content=r["content"][:4000]) for r in _recent_rows(user_id, AGENT_TURNS)]


def message_count(user_id: int) -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]


def clear(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
