"""Agent entry / wiring: model (OpenAI via Portkey) + system prompt file + tools + output type."""

import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
import uuid

from pydantic_ai import Agent, ModelRetry, RunContext, capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

import audit
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import (
    ChatReply, ChatTurn, CustomerProfile, PageContext, ProductDetails, ProductMatch, ProductNotFound, StockReport,
)

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
log = logging.getLogger("uvicorn.error")

BACKEND_DIR = Path(__file__).resolve().parent
# Load the class-wide .env (nearest folder wins).
for folder in [BACKEND_DIR, *BACKEND_DIR.parents]:
    if (folder / ".env").exists():
        load_dotenv(folder / ".env", override=False)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-luna")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
MAX_HISTORY_TURNS = 12


@dataclass
class ShopDeps:
    """Per-request context injected into every agent run (built server-side in main.py)."""
    customer: CustomerProfile | None = None   # None = guest
    user_id: int | None = None                 # for the audit trail only; never shown to the model
    page: PageContext = field(default_factory=PageContext)
    page_product: ProductDetails | None = None  # resolved from page.product_id via the DB, not trusted from the browser


def build_model() -> OpenAIResponsesModel:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from .env")
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL, default_headers={"x-portkey-provider": "openai"})
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


shop_agent = Agent(
    build_model(),
    deps_type=ShopDeps,
    output_type=ChatReply,
    instructions=PROMPT_PATH.read_text(encoding="utf-8"),
    retries=2,  # lets the accuracy guard send the model back to fix a reply up to twice
)

# Live counters exposed at GET /api/stats (speed, token cost, accuracy-guard activity).
STATS = {
    "chat_requests": 0, "failed_requests": 0, "total_seconds": 0.0,
    "input_tokens": 0, "output_tokens": 0, "model_requests": 0, "tool_calls": 0,
    "guard_checks": 0, "guard_corrections": 0, "guard_fallbacks": 0, "limit_stops": 0, "content_filtered": 0,
}


# ---------- accuracy guard (output validator) ----------

PRICE_IN_TEXT = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")
PRICE_IN_TOOL = re.compile(r'"price"\s*:\s*(\d+(?:\.\d+)?)')


def _allowed_prices(ctx: RunContext[ShopDeps]) -> set[float]:
    """Prices the reply may mention: from tool results this run, the page product, the shopper's own words,
    and earlier (already-shown) assistant replies in the history."""
    allowed: set[float] = set()
    if ctx.deps.page_product:
        allowed.add(ctx.deps.page_product.price)
    for msg in ctx.messages:
        for part in msg.parts:
            if isinstance(part, ToolReturnPart):
                allowed |= {float(x) for x in PRICE_IN_TOOL.findall(part.model_response_str())}
            elif isinstance(part, (UserPromptPart, TextPart)) and isinstance(part.content, str):
                allowed |= {float(x.replace(",", "")) for x in PRICE_IN_TEXT.findall(part.content)}
                if isinstance(part, UserPromptPart):  # budgets typed without "$", e.g. "under 60"
                    allowed |= {float(x) for x in re.findall(r"\b(\d{1,4})\b", part.content)}
    return allowed


@shop_agent.output_validator
def accuracy_guard(ctx: RunContext[ShopDeps], out: ChatReply) -> ChatReply:
    STATS["guard_checks"] += 1
    problems = []
    bad_ids = [pid for pid in out.product_ids if pid not in tools.all_product_ids()]
    if bad_ids:
        problems.append(f"product_ids {bad_ids} don't exist. Only use product_id values returned by tools.")
    allowed = _allowed_prices(ctx)
    quoted = {float(x.replace(",", "")) for x in PRICE_IN_TEXT.findall(out.reply)}
    unknown = sorted(p for p in quoted if not any(abs(p - a) < 0.005 for a in allowed))
    if unknown:
        problems.append(
            f"Your reply quotes {', '.join(f'${p:.2f}' for p in unknown)} but no product you looked up has that price. "
            "Call get_product_details / check_stock and quote the exact `price`, or remove the amount."
        )
    if problems:
        STATS["guard_corrections"] += 1
        log.warning("Accuracy guard: %s", " | ".join(problems))
        raise ModelRetry(" ".join(problems))
    return out


@shop_agent.instructions
def shopper_context(ctx: RunContext[ShopDeps]) -> str:
    c = ctx.deps.customer
    if c:
        return (
            "## Current shopper (logged in)\n"
            f"- Name: {c.first_name} {c.last_name}\n- Email: {c.email}\n"
            f"- Member since: {c.member_since}\n"
            "Their earlier conversation (from our database) is included as message history."
        )
    return "## Current shopper\nBrowsing as a guest (not logged in). You don't know their name or email."


@shop_agent.instructions
def page_context(ctx: RunContext[ShopDeps]) -> str:
    page, p = ctx.deps.page, ctx.deps.page_product
    if p:
        return (
            "## Page the shopper is viewing\n"
            f"Product page for **{p.name}** (product_id `{p.product_id}`). "
            "If they say \"this\", \"it\", or \"this one\" without naming an item, they mean this product. "
            "Use its product_id with check_stock / get_product_details for exact stock and price.\n"
            f"- Garment: {p.garment_type}\n- Colors it comes in: {', '.join(p.colors)}\n- Price: ${p.price:.2f}"
        )
    if page.path.startswith("/products") and page.results_title:
        return f"## Page the shopper is viewing\nProducts page showing your earlier search results: \"{page.results_title}\"."
    return f"## Page the shopper is viewing\n`{page.path}` (no specific product)."


# ---------- tools (thin wrappers so the agent sees clean signatures + docstrings) ----------

@shop_agent.tool_plain
def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = False,
    limit: int = 30,
) -> list[ProductMatch]:
    """Search the Campus Customs catalog.

    Args:
        query: Keywords, e.g. "bulldog", "hockey", "Berkeley college", "Harvard game".
        garment_type: e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: e.g. "navy", "gray", "white".
        max_price: Highest price in USD.
        min_price: Lowest price in USD.
        size: Only items with this size in stock (XS, S, M, L, XL, XXL).
        in_stock_only: Only items with any stock.
        limit: Max results (default 30 = all matches; lower it only for "top 3"-style asks).
    """
    return tools.search_products(query, garment_type, color, max_price, min_price, size, in_stock_only, limit)


@shop_agent.tool_plain
def get_product_details(product: str) -> ProductDetails | ProductNotFound:
    """Look up one product's description, colors, exact price, and stock for every size.

    Use for "tell me about X", "how much is X", or before recommending a specific item.

    Args:
        product: The product_id (preferred, from search results) or the product's name.
    """
    return tools.get_product_details(product)


@shop_agent.tool_plain
def check_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Exact stock for one product from the inventory table, with a status per size
    ("in stock", "low stock" = 1-3 left, "out of stock" = 0).

    Args:
        product: The product_id (preferred) or the product's name.
        size: One size (XS, S, M, L, XL, XXL; "medium"/"2XL" also ok). Omit to get every size.
    """
    return tools.check_stock(product, size)


@shop_agent.tool_plain
def find_similar_products(product: str, size: str | None = None, limit: int = 6) -> list[ProductMatch] | ProductNotFound:
    """Find in-stock alternatives in the same category (hoodie, crewneck, tee, quarter-zip, jacket),
    ranked by shared colors/style. Call this when a requested size is out of stock, or when the
    shopper asks for "something similar" / "other options like this".

    Args:
        product: product_id (preferred) or name of the item to find alternatives for.
        size: Only return items in stock in this size (XS-XXL). Pass the size the shopper wanted.
        limit: Max suggestions (default 6).
    """
    return tools.find_similar_products(product, size, limit)


@shop_agent.tool
def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile | str:
    """Who is chatting: the logged-in shopper's name, email, member-since date, and saved message count.

    Only ever returns the current shopper (no arguments, so it can't look up anyone else).
    """
    return ctx.deps.customer or "The shopper is a guest (not logged in); no profile available."


@shop_agent.tool
def get_current_page_product(ctx: RunContext[ShopDeps]) -> ProductDetails | str:
    """The product on the page the shopper is viewing right now (live price + stock), if any."""
    pid = ctx.deps.page.product_id
    if not pid:
        return "The shopper isn't on a product page."
    return tools.get_product_details(pid)


# ---------- running ----------

def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    msgs: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            msgs.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            msgs.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return msgs


def build_deps(customer: CustomerProfile | None, page: PageContext, user_id: int | None = None) -> ShopDeps:
    page_product = None
    if page.product_id:
        found = tools.get_product_details(page.product_id)
        page_product = found if isinstance(found, ProductDetails) else None
    return ShopDeps(customer=customer, page=page, page_product=page_product, user_id=user_id)


# Loop limits per chat message: max model round-trips, tool calls, and tokens.
RUN_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=10, total_tokens_limit=60_000)
LIMIT_REPLY = (
    "That one took me more steps than I'm allowed, so I stopped to be safe. Could you ask about one item "
    "or one type of product at a time?"
)

BLOCKED_REPLY = (
    "I can't help with that request, but I'm happy to help you find Yale gear, check sizes and stock, "
    "or answer questions about our products."
)

FALLBACK_REPLY = (
    "Sorry, I couldn't confirm that from our live inventory just now, and I don't want to give you a wrong "
    "price or stock number. Please check the product page, or ask me again."
)


async def run_chat(message: str, history: list[ChatTurn], deps: ShopDeps) -> ChatReply:
    STATS["chat_requests"] += 1
    run_id = uuid.uuid4().hex[:12]
    past = to_message_history(history)
    user_id = deps.user_id if deps.customer else None
    audit.append([audit.start_event(run_id, user_id, message, deps.page.path, deps.page.product_id)])
    start = time.perf_counter()
    stop_reason, error, usage, output = "final_result", None, None, None
    with capture_run_messages() as messages:
        try:
            result = await shop_agent.run(message, deps=deps, message_history=past, usage_limits=RUN_LIMITS)
            output = result.output
            usage = result.usage() if callable(result.usage) else result.usage
        except UsageLimitExceeded as e:
            # Loop limit hit (too many model steps / tool calls): stop and answer safely.
            stop_reason, error = "usage_limit", str(e)
            STATS["limit_stops"] += 1
            output = ChatReply(reply=LIMIT_REPLY)
        except UnexpectedModelBehavior as e:
            # Guard rejected every attempt: say so honestly rather than show an unverified answer.
            stop_reason, error = "guard_fallback", str(e)
            STATS["guard_fallbacks"] += 1
            log.warning("Accuracy guard: retries exhausted, sent safe fallback")
            output = ChatReply(reply=FALLBACK_REPLY)
        except ModelHTTPError as e:
            if e.status_code == 400 and "filter" in str(e.body).lower():
                # Provider safety filter (e.g. jailbreak detection) blocked the prompt: refuse politely.
                stop_reason, error = "content_filter", str(e)
                STATS["content_filtered"] += 1
                output = ChatReply(reply=BLOCKED_REPLY)
            else:
                stop_reason, error = "error", f"ModelHTTPError: {e}"
                STATS["failed_requests"] += 1
                raise
        except Exception as e:
            stop_reason, error = "error", f"{type(e).__name__}: {e}"
            STATS["failed_requests"] += 1
            raise
        finally:
            seconds = time.perf_counter() - start
            STATS["total_seconds"] += seconds
            try:
                audit.append(audit.run_events(run_id, messages, skip=len(past)) + [audit.end_event(
                    run_id, stop_reason, seconds, usage,
                    output.product_ids if output else None, output.page_title if output else None, error,
                )])
            except Exception:
                log.exception("Audit trail write failed")
    if usage is not None:
        STATS["input_tokens"] += usage.input_tokens
        STATS["output_tokens"] += usage.output_tokens
        STATS["model_requests"] += usage.requests
        STATS["tool_calls"] += usage.tool_calls
    return output


def stats_snapshot() -> dict:
    n = max(STATS["chat_requests"], 1)
    return {
        **STATS,
        "model": MODEL_NAME,
        "avg_seconds_per_chat": round(STATS["total_seconds"] / n, 2),
        "avg_tokens_per_chat": round((STATS["input_tokens"] + STATS["output_tokens"]) / n),
        "avg_tool_calls_per_chat": round(STATS["tool_calls"] / n, 2),
        "total_seconds": round(STATS["total_seconds"], 1),
    }
