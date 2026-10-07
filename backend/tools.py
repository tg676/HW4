"""Read-only database tools for the shop agent (and product helpers for the API).

Every price and stock number the chatbot mentions comes from here, straight from SQLite.
None of these touch the users/sessions tables.
"""

import json
import re
import sqlite3

from db import get_db
from models import (
    ProductCard, ProductDetails, ProductMatch, ProductNotFound, SizeAvailability, SizeStock,
    StockReport, stock_status,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
STOPWORDS = {"a", "an", "the", "and", "or", "with", "for", "in", "of", "do", "you", "have", "any", "some", "me", "show", "i", "want", "yale"}


# ---------- loading ----------

def _inventory(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[SizeStock]]:
    inv: dict[str, list[SizeStock]] = {pid: [] for pid in product_ids}
    if not product_ids:
        return inv
    marks = ",".join("?" * len(product_ids))
    for r in conn.execute(
        f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})", product_ids
    ):
        inv[r["product_id"]].append(SizeStock(size=r["size"], quantity=r["quantity"]))
    for sizes in inv.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)
    return inv


def _cards(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[ProductCard]:
    inv = _inventory(conn, [r["product_id"] for r in rows])
    cards = []
    for r in rows:
        sizes = inv[r["product_id"]]
        cards.append(ProductCard(
            product_id=r["product_id"], name=r["name"], garment_type=r["garment_type"],
            description=r["description"], colors=json.loads(r["colors"]),
            search_tags=json.loads(r["search_tags"]), image_file_path=r["image_file_path"],
            image_url="/media/" + r["image_file_path"], price=r["price"],
            inventory=sizes, total_stock=sum(s.quantity for s in sizes),
        ))
    return cards


def all_products() -> list[ProductCard]:
    with get_db() as conn:
        return _cards(conn, conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall())


def all_product_ids() -> set[str]:
    with get_db() as conn:
        return {r[0] for r in conn.execute("SELECT product_id FROM catalogue")}


def products_by_ids(product_ids: list[str]) -> list[ProductCard]:
    """Cards in the given order; unknown ids are dropped (guards against invented ids)."""
    if not product_ids:
        return []
    with get_db() as conn:
        marks = ",".join("?" * len(product_ids))
        rows = conn.execute(f"SELECT * FROM catalogue WHERE product_id IN ({marks})", product_ids).fetchall()
        by_id = {c.product_id: c for c in _cards(conn, rows)}
    return [by_id[pid] for pid in dict.fromkeys(product_ids) if pid in by_id]


def _match(card: ProductCard) -> ProductMatch:
    desc = card.description
    return ProductMatch(
        product_id=card.product_id, name=card.name, garment_type=card.garment_type,
        colors=card.colors, price=card.price, total_stock=card.total_stock,
        sizes_in_stock=[s.size for s in card.inventory if s.quantity > 0],
        short_description=desc if len(desc) <= 160 else desc[:157] + "...",
    )


# ---------- agent tools ----------

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
    """Keyword search over name, garment type, description, colors, and tags, with optional filters.

    Results are ranked by how many query words match (name/tag hits weigh more).
    """
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in STOPWORDS]
    size = normalize_size(size) if size else None
    scored: list[tuple[float, ProductCard]] = []

    for card in all_products():
        gt = card.garment_type.lower()
        colors = " ".join(card.colors).lower()
        if garment_type and not _loose_in(garment_type, gt + " " + card.name.lower()):
            continue
        if color and color.lower() not in colors:
            continue
        if max_price is not None and card.price > max_price:
            continue
        if min_price is not None and card.price < min_price:
            continue
        if size and not any(s.size == size and s.quantity > 0 for s in card.inventory):
            continue
        if in_stock_only and card.total_stock == 0:
            continue

        score = 0.0
        if words:
            name = card.name.lower()
            tags = " ".join(card.search_tags).lower()
            desc = card.description.lower()
            for w in words:
                stem = w.rstrip("s") if len(w) > 3 else w
                if stem in name or stem in tags:
                    score += 2
                elif stem in desc or stem in colors or stem in gt:
                    score += 1
            if score == 0:
                continue
        scored.append((score, card))

    scored.sort(key=lambda x: (-x[0], x[1].name))
    return [_match(c) for _, c in scored[: max(1, min(limit, 30))]]


def _loose_in(needle: str, haystack: str) -> bool:
    """'tee'/'t-shirt'/'tshirt' all match; 'sweatshirt' matches crewnecks too."""
    n = re.sub(r"[^a-z]", "", needle.lower()).rstrip("s")
    h = re.sub(r"[^a-z]", "", haystack)
    aliases = {"tee": "tshirt", "shirt": "shirt", "sweater": "sweatshirt", "quarterzip": "quarterzip", "14zip": "quarterzip"}
    n = aliases.get(n, n)
    if n == "tshirt":
        h = h.replace("sweatshirt", "")  # "sweatshirt" contains "tshirt"
    if n in ("hoodie", "hood", "hooded", "hoody"):
        return "hood" in h  # pullover hoodie, full-zip hooded sweatshirt, full-zip hood
    return n in h


SIZE_ALIASES = {
    "XSMALL": "XS", "EXTRASMALL": "XS", "SMALL": "S", "MEDIUM": "M", "MED": "M", "LARGE": "L",
    "XLARGE": "XL", "EXTRALARGE": "XL", "XXLARGE": "XXL", "2XL": "XXL", "2X": "XXL", "XXXL": "XXL",
}


def normalize_size(size: str) -> str:
    s = re.sub(r"[^A-Z0-9]", "", size.upper())
    return SIZE_ALIASES.get(s, s)


def resolve_product(product: str) -> ProductCard | ProductNotFound:
    """Find one product by exact product_id, then exact name, then closest keyword match."""
    q = product.strip()
    cards = products_by_ids([q])
    if cards:
        return cards[0]
    with get_db() as conn:
        row = conn.execute("SELECT product_id FROM catalogue WHERE lower(name) = lower(?)", (q,)).fetchone()
    if row:
        return products_by_ids([row["product_id"]])[0]
    # Fuzzy: accept the top keyword hit only if it clearly wins; otherwise ask the agent to clarify.
    hits = search_products(q, limit=5)
    if len(hits) == 1:
        return products_by_ids([hits[0].product_id])[0]
    return ProductNotFound(
        query=q,
        message="No exact product match. Ask the shopper which one they mean (suggestions below), "
        "or say we don't carry it if none fit. Do not guess a price or stock.",
        suggestions=hits,
    )


def _availability(card: ProductCard) -> list[SizeAvailability]:
    return [SizeAvailability(size=s.size, quantity=s.quantity, status=stock_status(s.quantity)) for s in card.inventory]


def get_product_details(product: str) -> ProductDetails | ProductNotFound:
    """Description, colors, exact price, and stock for every size of one product."""
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    sizes = _availability(card)
    return ProductDetails(
        product_id=card.product_id, name=card.name, garment_type=card.garment_type,
        description=card.description, colors=card.colors, price=card.price,
        stock_by_size=sizes,
        sizes_in_stock=[s.size for s in sizes if s.quantity > 0],
        sizes_out_of_stock=[s.size for s in sizes if s.quantity == 0],
        total_stock=card.total_stock,
    )


def garment_family(garment_type: str) -> str:
    """Collapse the DB's 22 garment_type spellings into shopper categories."""
    g = garment_type.lower()
    if "hood" in g:
        return "hoodie"
    if "quarter" in g or "1/4" in g:
        return "quarter-zip"
    if "jacket" in g or "fleece" in g:
        return "jacket"
    if "crew" in g or "sweatshirt" in g or "mockneck" in g:
        return "crewneck"
    if "shirt" in g or "tee" in g:
        return "tee"
    return "other"


def find_similar_products(product: str, size: str | None = None, limit: int = 6) -> list[ProductMatch] | ProductNotFound:
    """In-stock items in the same category as `product`, ranked by shared colors/tags (excludes the item itself)."""
    base = resolve_product(product)
    if isinstance(base, ProductNotFound):
        return base
    family = garment_family(base.garment_type)
    wanted = normalize_size(size) if size else None
    base_colors = {c.lower() for c in base.colors}
    base_tags = {t.lower() for t in base.search_tags}
    scored = []
    for card in all_products():
        if card.product_id == base.product_id or garment_family(card.garment_type) != family:
            continue
        if wanted:
            if not any(s.size == wanted and s.quantity > 0 for s in card.inventory):
                continue
        elif card.total_stock == 0:
            continue
        score = 2 * len(base_colors & {c.lower() for c in card.colors}) + len(base_tags & {t.lower() for t in card.search_tags})
        scored.append((score, card))
    scored.sort(key=lambda x: (-x[0], abs(x[1].price - base.price), x[1].name))
    return [_match(c) for _, c in scored[: max(1, min(limit, 12))]]


def check_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Exact stock for one product: one size if given (XS-XXL, 'medium', '2XL' ok), else all sizes."""
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    all_sizes = _availability(card)
    wanted = normalize_size(size) if size else None
    if wanted:
        picked = [s for s in all_sizes if s.size == wanted]
        # Sizes we never carry count as out of stock, not as an error.
        sizes = picked or [SizeAvailability(size=wanted, quantity=0, status="out of stock")]
    else:
        sizes = all_sizes
    return StockReport(
        product_id=card.product_id, name=card.name, price=card.price, requested_size=wanted,
        sizes=sizes,
        sizes_in_stock=[s.size for s in all_sizes if s.quantity > 0],
        sizes_out_of_stock=[s.size for s in all_sizes if s.quantity == 0],
        total_stock=card.total_stock,
    )
