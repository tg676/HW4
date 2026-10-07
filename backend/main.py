"""Campus Customs API: products, images, auth, and the Pydantic AI shop chatbot.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import logging

from fastapi import Cookie, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import auth
import history
import safety
import tools
from agent import MODEL_NAME, build_deps, run_chat, stats_snapshot
from db import DATA_DIR
from models import (
    MAX_CHAT_CARDS, MAX_PAGE_RESULTS, ChatRequest, ChatResponse, CustomerProfile, HistoryMessage, ProductCard,
)

log = logging.getLogger("campus_customs")

auth.ensure_sessions_table()
history.ensure_schema()
app = FastAPI(title="Campus Customs API")
app.include_router(auth.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Only the products folder is public, so the .db file is never downloadable.
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="media")


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL_NAME}


@app.get("/api/stats")
def stats():
    """Assistant speed, token cost, and accuracy-guard activity since the server started."""
    return stats_snapshot()


@app.get("/api/products", response_model=list[ProductCard])
def list_products():
    return tools.all_products()


@app.get("/api/products/{product_id}", response_model=ProductCard)
def get_product(product_id: str):
    cards = tools.products_by_ids([product_id])
    if not cards:
        raise HTTPException(404, "Product not found")
    return cards[0]


def _customer(user: dict) -> CustomerProfile:
    return CustomerProfile(
        first_name=user["first_name"] or "", last_name=user["last_name"] or "", email=user["email"],
        member_since=user["created_at"][:10], saved_messages=history.message_count(user["id"]),
    )


@app.get("/api/chat/history", response_model=list[HistoryMessage])
def chat_history(cc_session: str | None = Cookie(default=None)):
    """Saved conversation for the logged-in shopper (guests get an empty list)."""
    user = auth.current_user(cc_session)
    return history.load_for_widget(user["id"]) if user else []


@app.delete("/api/chat/history")
def clear_chat_history(cc_session: str | None = Cookie(default=None)):
    user = auth.current_user(cc_session)
    if not user:
        raise HTTPException(401, "Not logged in")
    history.clear(user["id"])
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)):
    user = auth.current_user(cc_session)
    # Safety: per-shopper rate limit, then mask card/SSN numbers before anything stores or sees the text.
    if not safety.chat_limiter.allow(f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else '?'}"):
        raise HTTPException(429, "You're sending messages very quickly. Please wait a moment and try again.")
    message, had_pii = safety.redact_pii(req.message)
    if had_pii:
        req.message = message
    # Logged in: identity + history come from the DB (the browser can't spoof them). Guest: browser history.
    customer = _customer(user) if user else None
    past = history.load_for_agent(user["id"]) if user else req.history
    try:
        out = await run_chat(req.message, past, build_deps(customer, req.page, user["id"] if user else None))
    except Exception:
        log.exception("Agent run failed")
        raise HTTPException(502, "The shop assistant is having trouble right now. Please try again.")
    # Cards are rebuilt from the DB, so prices/stock shown on the page are always real.
    # Search results go to the page grid (up to 30); single-item answers stay small in the chat.
    is_search = bool(out.page_title)
    limit = MAX_PAGE_RESULTS if is_search else MAX_CHAT_CARDS
    products = tools.products_by_ids(out.product_ids[:limit])
    page_title = out.page_title.strip() if is_search and products else None
    if user:
        history.save_exchange(user["id"], req.message, out.reply, products, page_title)
    return ChatResponse(reply=out.reply, products=products, page_title=page_title)
