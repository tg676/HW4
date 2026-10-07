# HW4: Campus Customs Shop + "Ask the Bulldog" Chatbot

A customer website for **Campus Customs** (Yale apparel, 57 Broadway, New Haven) with a shopping chatbot.

- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Backend:** Python FastAPI (`backend/main.py`), whose brain is a **Pydantic AI agent**
- **Model:** OpenAI `gpt-5.6-luna` through **Portkey**
- **Data:** a local SQLite database (`campus_customs.db`) with the catalogue, inventory by size, and users

Shoppers can browse products, create an account and log in, chat about merch, see matching items appear on the page as product cards, and get honest price and stock answers straight from the database.

## The agent (4 files in `backend/`)
| File | Role |
|---|---|
| `backend/prompts/prompts.md` | System prompt: voice, tool-use rules, honesty rules, safety rules |
| `backend/agent.py` | Agent entry/wiring: model via Portkey, prompt, tools, structured output, accuracy guard, loop limits, audit |
| `backend/tools.py` | Read-only database tools (`search_products`, `get_product_details`, `check_stock`, `find_similar_products`, …) |
| `backend/models.py` | Pydantic types (`ProductCard`, `ProductDetails`, `StockReport`, `ChatReply`, `CustomerProfile`, …) |

Supporting backend files: `main.py` (FastAPI routes), `auth.py` (signup/login/sessions), `history.py` (saved chats), `safety.py` (rate limit, PII redaction), `audit.py` (append-only audit trail), `db.py`.

Write-ups live in `output/`: `harness.md` (full system spec), `usability.md`, `design.md`, `app_check.html` (screenshots of the live app), `audit_trail.json`. The prompt log is in `AI_prompts.md`.

---

## What is NOT in this repo
These are excluded on purpose (see `.gitignore`):
- **`.env`**: your real API key. Use `.env.example` as the template.
- **The data pack**: `campus_customs.db` and the product images (`data/products/*.jpg`).
- `node_modules/`, `.venv/`, build output.

---

## Setup

### 1. Requirements
- Python 3.12+ (developed on 3.14)
- Node.js 20+ (developed on Node 24)
- A Portkey API key with access to OpenAI models

### 2. Place the data pack
Unzip the course data pack (`data.zip`) **inside this `HW4` folder** so you get:
```
HW4/
  data/
    campus_customs.db
    products/
      2025-yale-vs-harvard-t-shirt.jpg
      ... (102 product images)
  backend/
  frontend/
  ...
```
On first start the backend adds two small things to the DB automatically: a `sessions` table and a `page_title` column on `chat_messages`.

### 3. Add your API key
```bash
cp .env.example .env
```
Windows PowerShell: `copy .env.example .env`

Then edit `.env` and set `PORTKEY_API_KEY=...`. The backend looks for `.env` in `HW4/` (or any parent folder).

### 4. Install dependencies
```bash
# Python (from HW4/)
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

---

## Run

Use two terminals.

**Terminal 1: backend** (run from the `backend/` folder, with the venv activated)
```bash
cd backend
uvicorn main:app --port 8000
```
`uvicorn main:app --reload --port 8000` also works. The API is at http://localhost:8000 (`/api/health`, `/api/stats`, `/docs`).

**Terminal 2: frontend**
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173**. Vite proxies `/api` and `/media` to the backend on port 8000.

### Try it
- **Log in** with the seed user from the data pack: `test@campuscustoms.yale.edu` / `password`, or create a new account.
- Click **Ask the Bulldog** (bottom right) and try:
  - "What hoodies do you have?" The matching product cards appear on the Products page.
  - On a product page: "Is this in medium?" or "Do you have this in pink?"
  - "Is the Crew Left Chest Hoodie in medium?" It's out of stock, so the bot suggests similar in-stock items.
- On **Products**, use the toolbar: category chips, "In stock in M", sort by price.

### Offline test (no API calls)
```bash
cd backend
python test_accuracy_guard.py
```
This checks that the price accuracy guard rejects a made-up price and falls back safely.

---

## Notes
- Every price and stock number the bot gives comes from SQLite via tools. The agent returns only product ids, and the backend rebuilds cards from the DB. An output validator rejects replies that quote a price no tool returned.
- Passwords are stored as salted PBKDF2-SHA256 (600k iterations). Sessions use HttpOnly cookies.
- Agent activity (tool calls, results, stop reasons) is appended to `output/audit_trail.json` and never wiped.
- See **`output/harness.md`** for the full spec: models, tools, safety rules, loop limits, and result caps.
