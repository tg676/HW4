"""Structured types shared by the API, the tools, and the Pydantic AI agent."""

from typing import Literal

from pydantic import BaseModel, Field


# ---------- products ----------

class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """Full product as shown on the website (cards, detail page, chat results)."""
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_file_path: str
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int


class ProductMatch(BaseModel):
    """Compact search result handed to the agent (keeps tokens low)."""
    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    total_stock: int
    sizes_in_stock: list[str]
    short_description: str


StockStatus = Literal["in stock", "low stock", "out of stock"]
LOW_STOCK_MAX = 3  # 1-3 left counts as "low stock"


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "out of stock"
    return "low stock" if quantity <= LOW_STOCK_MAX else "in stock"


class SizeAvailability(BaseModel):
    """Stock for one size, with a pre-computed status so the agent never has to interpret 0."""
    size: str
    quantity: int
    status: StockStatus


class ProductDetails(BaseModel):
    """Lookup result for one product: everything needed to answer description/price/stock questions."""
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float = Field(description="Exact price in USD from the catalogue table.")
    stock_by_size: list[SizeAvailability]
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str]
    total_stock: int


class StockReport(BaseModel):
    """Stock lookup for one product: a single size if one was asked for, else every size."""
    product_id: str
    name: str
    price: float
    requested_size: str | None = None
    sizes: list[SizeAvailability]
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str]
    total_stock: int


class ProductNotFound(BaseModel):
    """Returned instead of guessing when a product can't be identified."""
    query: str
    message: str
    suggestions: list[ProductMatch] = Field(default_factory=list)


# ---------- chat ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message (sent by the browser)."""
    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=120, description="Set on /products/:id pages.")
    results_title: str | None = Field(default=None, max_length=120, description="Chat results heading shown on /products, if any.")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Guests send their history; for logged-in users the server loads it from the DB instead.
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    page: PageContext = Field(default_factory=PageContext)


class CustomerProfile(BaseModel):
    """The only customer fields the agent can see (never password_hash)."""
    first_name: str
    last_name: str
    email: str
    member_since: str
    saved_messages: int


class HistoryMessage(BaseModel):
    """One saved chat message, as reloaded into the widget."""
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page_title: str | None = None
    created_at: str


MAX_PAGE_RESULTS = 30
MAX_CHAT_CARDS = 6


class ChatReply(BaseModel):
    """What the agent must return (its structured output)."""
    reply: str = Field(description="Friendly answer to show the shopper. Prices/stock only from tool results.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values from tool results, best match first. For a catalog search include ALL "
        f"relevant matches (up to {MAX_PAGE_RESULTS}); for a single-item answer include just that item.",
    )
    page_title: str | None = Field(
        default=None,
        description="Set ONLY when you ran search_products to answer a browse/search request "
        "(e.g. 'Hoodies', 'Gray crewnecks under $60'); the website then shows product_ids as the page's "
        "product grid under this heading. Leave null for single-product, stock, or non-product replies.",
    )


class ChatResponse(BaseModel):
    """What /api/chat returns to the website (the chat → page API contract)."""
    reply: str
    products: list[ProductCard] = Field(description="Full cards rebuilt from the DB, in the agent's order.")
    page_title: str | None = Field(
        default=None, description="If set, the site shows `products` as the main product grid under this heading."
    )
