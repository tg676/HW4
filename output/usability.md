# Campus Customs: Usability Improvements (Problem 9)

Two frontend improvements make the site look better and easier to use. Two agent/backend improvements make the chatbot's answers more accurate and more useful, and make its cost and speed visible. Each one is live in the running app; "Where to see it" says how to find it.

---

## Frontend

### F1. Products toolbar: search, category chips, size filter, in-stock toggle, sort
**What I added:** a sticky toolbar at the top of the Products page (`frontend/src/components/ProductToolbar.tsx`, `frontend/src/filters.ts`):
- **Search box:** live filtering by name, description, colors, and tags (e.g. "hockey", "Berkeley", "bulldog").
- **Category chips:** All · Hoodies · Crewnecks · T-Shirts · Quarter-Zips · Jackets & Fleece. The DB has 22 messy `garment_type` spellings, so the chips group them into the categories a shopper thinks in.
- **Size filter:** "In stock in: XS … XXL" shows only items you can actually buy in your size.
- **In stock only** toggle hides fully sold-out items.
- **Sort:** Featured / Price low→high / Price high→low / Name A–Z.
- A live count ("Showing 18 of 102"), and a **Reset** button when nothing matches.
- It also works on **chat search results** (Problem 7), so a shopper can narrow "Yale Hoodies" to "size M, cheapest first."

**Why it helps:** 102 products in one long grid is a lot to scroll. Shoppers usually know their size and category, so this gets them from landing to "items I can buy in my size" in two clicks, with no chatting required. For the business, fewer dead ends (falling for an item that's sold out in your size) means fewer abandoned visits.

**Where to see it:** Products page, top of the grid.

### F2. Context-aware quick-reply chips in the chat
**What I added:** one-tap suggestion chips above the chat input (`ChatWidget.tsx`). They change with the page:
- **On a product page:** "Is this in medium?", "What colors does this come in?", "Show me similar items in stock"
- **Everywhere else:** "What hoodies do you have?", "Gifts under $50", "Anything with a bulldog?", "Show me quarter-zips"

Tapping a chip sends it immediately.

**Why it helps:** many shoppers don't know what a store chatbot can do, or don't want to type on a phone. Chips show the bot's best features (search-to-page, live stock, page-aware "this") in one tap and teach shoppers how to phrase questions. For the business, more people get value from the assistant, which drives more product views.

**Where to see it:** open the chat on any page, then on a product page.

---

## Agent / backend

### B1. New agent tool: `find_similar_products` (rescue out-of-stock sales)
**What I added:** a new read-only tool (`backend/tools.py` + registered in `backend/agent.py`):
`find_similar_products(product, size=None, limit=6)` finds items in the **same category** (hoodie, crewneck, tee, quarter-zip, jacket) that are **in stock** (in the requested size, if given). It ranks them by shared colors and search tags and leaves out the original item. `prompts.md` tells the agent to call it whenever a requested size is out of stock or the shopper asks for "something similar." The suggestions appear as cards.

**Why it helps:** about 24% of size rows (145 of 612) are at quantity 0. Before, the bot could only say "sorry, out of stock in M" and list other sizes, which is a dead end for someone who needs an M. Now it says "sorry, but these similar hoodies are in stock in M" and shows them. For the business, an out-of-stock moment becomes a sale instead of a lost customer, and the suggestions are always real, in-stock DB items.

**Where to see it:** ask "Do you have the Crew Left Chest Hoodie in medium?" (M = 0), or on any product page tap "Show me similar items in stock".

### B2. Price/product accuracy guard (output validator) + `/api/stats` cost & speed monitor
**What I added:**
1. A Pydantic AI **output validator** (`@shop_agent.output_validator` in `backend/agent.py`) that checks every reply *before* the shopper sees it:
   - Every dollar amount in `reply` must match a `price` that a tool actually returned in this run, the page product's price, or a number the shopper typed themselves (e.g. a budget like "under $60").
   - Every id in `product_ids` must exist in the catalogue.

   If either check fails, the validator raises `ModelRetry` with a specific correction (e.g. *"You quoted $65.00 but no product you looked up costs that. Only quote prices from tool results."*). The model then fixes its own answer, with up to 2 retries.
2. **`GET /api/stats`**: live counters for the assistant: chat requests, average response time, input and output tokens (from Pydantic AI `result.usage()`), tool calls, and how many times the accuracy guard caught and fixed a reply.

**Why it helps:** the biggest risk of a shop chatbot is confidently quoting a wrong price. That's bad for shoppers and a real liability for the business. Prompt rules (Problem 6) make that rare; this guard makes it **checked in code**, so a hallucinated price can't reach the customer. The stats endpoint gives Campus Customs visibility into speed and token spend (cost), and how often the guard fires, so they can tune the prompt or model and know what the assistant costs to run.

**Where to see it:** `http://localhost:8000/api/stats` (or `/api/stats` through the site). The validator is in `agent.py`. Server logs show `Accuracy guard: ...` whenever it forces a correction.

---

## Verification (running app, checked against the DB)

| # | Test | Result |
|---|---|---|
| F1 | Products → **Hoodies** chip | Showing 27 of 102 |
| F1 | + **In stock in M** | Showing 21 of 102. Ice Hockey Left Chest Hoodie correctly hidden (its M = 0) |
| F1 | + **Price: Low → High** | Starts with $45.00 hoodies (Ua Gameday Double Knit Hood, Yale Sports Hoodie Tennis) |
| F1 | + search **"hockey"** | Showing 1 of 102 → Yale Sports Hoodie Hockey; **Reset** → 102 of 102 |
| F2 | Open chat on Home | Chips: "What hoodies do you have?", "Gifts under $50", "Anything with a bulldog?", "Show me quarter-zips" |
| F2 | Tap **Gifts under $50** | Page switched to "Gifts under $50" results; every card ≤ $45.00 |
| F2 | Open chat on a product page | Chips change to "Is this in medium?", "What colors does this come in?", "Show me similar items in stock" |
| B1 | On Crew Left Chest Hoodie page, tap **Is this in medium?** | "Sorry, the Crew Left Chest Hoodie is out of stock in medium… similar navy hoodies available in M include the Sailing Left Chest Hoodie, Fencing Left Chest Hoodie, and Squash Left Chest Hoodie, each priced at $68.00." Four cards shown in the chat (the original + 3 alternatives). DB: all three have M > 0 |
| B2 | `python backend/test_accuracy_guard.py` (scripted model, no API cost) | (1) Model says "$65.00" → guard: *"Your reply quotes $65.00 but no product you looked up has that price…"* → model calls `get_product_details` → final "$68.00" ✅ (2) Model that keeps inventing "$12.99" + fake id → shopper gets the honest fallback, never the wrong price ✅ (3) "Gifts under $50" (shopper's own number) is **not** flagged ✅ |
| B2 | `GET /api/stats` after live chats | `{"chat_requests": 2, "avg_seconds_per_chat": 10.49, "avg_tokens_per_chat": 10812, "avg_tool_calls_per_chat": 2, "guard_checks": 2, "guard_corrections": 0, "model": "gpt-5.6-luna", ...}` |

**What the stats already show:** each chat is roughly 10.8k tokens, nearly all **input** (system prompt + tool results). Output is only about 400 tokens. That points to the next cost win: trim long tool results, or cache the static system prompt. Without this monitor, that would be invisible.
