# HW 4 AI Prompt Log

This log records the prompts I gave the vibe coder and the follow-up prompts used to refine the work. The running site, database writes, and screenshots are the evidence that each problem was completed.

---

## Setup

### Prompts I typed
- Okay, today we're going to be working on homework four, so get a virtual environment set up there, um, and put a sample.txt file there to prove that we're ready to save things.
- I put the data in homework four, unzip it.

### Scenario context
- Okay, I'm going to start by giving you the scenario. Uh, and the context before we dive into the problems. So I, I, just for context, we need to be working fast today. So keep speed in mind when creating your code. Um, so the scenario is campus customs needs a real customer website with a helpful chat bot. You're going to build a React plus V TypeScript front end and a Python fast API backend whose brain is a Pydantic AI agent. Um, shoppers need to be able to browse products, create an account, Uh, chat about merch, see matching items appear on the page, and give honest answers, get honest answers about price and stock from a local database. Um, we're given campus customs.db, with tables for the product catalog, inventory by size and users with hash passwords, product image file paths are in the catalog table, um, and yeah, we're going to research a website. Use the port key API key, uh, for the agent's AI calls. If we're using OpenAI through port key, use any models in the 5.6 or 6 series. Um, we're going to work one problem at a time. Uh, and type, I'm going to type each problem in my own words here. Um, and yeah, I'll give you the, data file to unzip to start. Don't do anything yet.

---

## Problem 1: AI prompts log

### Prompt I typed
- Okay, problem one. So uh, create AI prompts.md at the start of this assignment and we're gonna keep it updated as I work. Uh, this file is gonna be the log of what instructions I give you. Um, put one section for each problem, one through 13. Each section needs to include the problem number and title. At least one prompt uh, that I give you. Uh, one follow-up prompt if I need to give one. Um, and a sentence on what was lacking after the first. Um, the running site database writes and screenshots uh, will be the evidence um, I don't need any extra proof uh, beyond the prompts that I give you

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt fully specified the log's structure and purpose.

---

## Problem 2: Analyze the database

### Prompt I typed
- Okay, problem two. Uh, look, we're going to analyze the database. So look at the database data slash campus customs.db and understand the fields of each table. Um, at a minimum, we need to understand catalog, inventory, and users. Uh, start the file output slash harness.md Uh, write down each table and the fields and one short line on why each field matters for the shop or the chatbot. We're going to keep growing this harness file in later problems. Um, so models, tools, safety, specs, etc.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt fully specified the tables to cover and the harness format.

---

## Problem 3: Build the Campus Customs website

### Prompt I typed
- Okay, problem three. We're going to build the campus customs website. So scaffold a React plus Vite plus TypeScript front end for campus customs. Put a nav bar at the top that links to the main pages. Uh, which are home, products, about us, login, and create account. Uh, use custom style wording from Yale Bulldog Blue.com for home and about us, but write these pages in your own voice. So don't copy the original site text. On the products page, show product images from the catalog. So use the image paths in the database. With basic product info, so name, price, short description. Make each product open a single item page, so a large image on one side, full product text on the other, description, price, sizes, slash stock when you have them. Clicking a card on the on products should take the shopper there. Add a chat interface in the bottom right of the site. Um, so a floating chat panel is fine. It doesn't need to talk to an agent yet. A stub that will call your back end later is enough for this problem. You'll need a small API soon to read the database. It's fine to start a simple, fast API app in backend slash main.py just to serve products and images and then grow it into the agent backend in problem five.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified every page, the product card and detail layouts, and the chat stub.

---

## Problem 4: Create account and login

### Prompt I typed
- Okay, problem four. Uh, we're going to create an account and login. So build a normal create account slash login flow. Create account should be first name, last name, email, password. Confirm password is a nice touch. And login should be email and password. New accounts go into the users table. Make sure to store passwords securely. So hackers, human, or AI cannot access them. The seed database already has a, a user you can use when building. Uh, so the email is test at campuscustoms.yale.edu. And the password is password, all lowercase. Uh, confirm you can log in as that user and that a brand new account you create also works. Uh, finally, update output slash harness.md with how auth works. Uh, what you store for a user and how passwords are protected.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the form fields, the storage and security requirements, the accounts to test, and the harness update.

---

## Problem 5: Pydantic AI agent backend

### Prompt I typed
- Okay, problem five. So uh, this will be Pydantic AI agent backend. So build the chat shop chatbot as a Pydantic AI agent behind fast API plugged into your front end chat widget. Put the API app in backend slash main.py that is the file you run with UVCorn keep the agent as these four files next to it uh, so the first one is backend slash prompts slash prompts.md this is the system prompt we're going to grow this same file later second one is backend slash agent.py which is the agent entry slash wiring third one is backend slash tools.py which are the tools the agent can call And the fourth one is backend slash models.py, which is the Pydantic slash Pydantic AI structured types. In main.py, expose a chat route, so a message from the website returns a reply from the agent and whatever else you need for products and authentication. You will need your AI model, API key for the agent. Put a campus, put campus customs voice and safety basics into prompts slash prompt.md. You'll expand tools and safety later. Start or update types in models.py for chat replies and product cards as needed. In output slash harness.md, note how the front end talks to fast API and how the agent is loaded. Uh, the prompt file plus model. Make sure the back end runs from the back end slash folder like this. Terminal command, I'll paste below.

  uvicorn main:app --reload --port 8000

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the four agent files, the chat route, the prompt contents, the harness notes, and the exact run command.

---

## Problem 6: Tools for product info and stock

### Prompt I typed
- Okay, problem six, uh, which will be tools, product info, and stock. So give the agent tools that look up real information from campus underscore customs dot DB. Uh, so the product description, the price, and how many are in stock by size when the customer asks. The agent must use the database. It should not invent prices or quantities. If a size is out of stock, say so clearly. Expand prompts slash prompts.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In output slash harness.md, list each tool and explain which model fields you chose for lookup results and why.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the data to look up, the out-of-stock behavior, and the prompt, models, and harness updates.

---

## Problem 7: Chat search that updates the page

### Prompt I typed
- Okay, problem seven. So chat search that updates the page. Now we will add a neat feature to the site. So when a customer asks, asks about a type of item, for example, what hoodies do you have? The agent should search the catalog and the website should dynamically show those matching items as product cards. So image, name, price, short info. This is an API contract. So the agent returns structured product matches and then the front end renders them on the website. So after the dynamic product cards are loaded by your new feature, make sure the same single item page behavior we built in problem three still works. So each product card, including the ones the chat just put on the page, should still open that detail view, large image plus full info when clicked. Update prompts slash prompts.md and output slash harness.md so it's clear how search results reach, reach the page.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the feature, the structured API contract, the detail-page requirement, and the docs to update.

---

## Problem 8: Customer memory

### Prompt I typed
- Okay, problem eight. So customer memory. When a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting, so their name and their email. Put that in agent depths or an equivalent clear pattern and or tools the agent can call. Also pass enough page context that if someone is on a product page and asks, do you have this in pink? The agent knows which item they mean. So you can put code into the agent context if that's a helpful hint. Guests can still chat, but history only needs to persist for logged in users. Document in output slash harness.md uh, how user chat history is stored, what customer fields the agent sees, and how page context is passed.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the persistence, the identity fields, the page-context example, guest behavior, and what to document.

---

## Problem 9: Usability improvements

### Prompt I typed
- Problem nine, which covers usability improvements. So now that the core shop works, improve it. Choose and implement uh, two front-end usability improvements and two agent slash back-end usability improvements. Front-end uh, improvements will make the site look better and easier to use. Uh, the agent and backend improvements will make the agent output better and more accurate. Um, write output slash usability.md before or as you build. Um, and for each of the improvements, say what you added and why it helps a campus customs shopper or the business. Then make sure all improvements actually show up in the running app. Uh, the graders are going to read the write-up and look for the features. Um, so a couple of suggestions for the back-end improvements. Those could be new agent tools or things that make the agent run faster or cheaper.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the number and type of improvements, the write-up contents, and that they had to be visible in the running app.

---

## Problem 10: Style the website

### Prompt I typed
- Problem 10, style the website. So add a creative design so the site feels like a real campus custom storefront. So fonts, color, hierarchy, motion, product presentation, chat feel. Uh, we're going to get more points for imaginative and innovative design, so um, don't, don't be shy. And write output slash design.md, uh, what we changed and why it should help customers stick around and buy. Keep it concrete and short.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the design areas to cover, the creative bar, and the design.md write-up.

---

## Problem 11: Site testing (app check)

### Prompt I typed
- Okay, problem 11, site testing, which is an app check. So test the live site and document it in output slash app underscore check dot HTML, a page you can double click open. Include clear screenshots and short captions for one chat checking the inventory level of an item uh, on a stock slash price from the database to the dynamic search result cards that are appearing after a category question, for example, hoodies. And three, one of the usability features we added in problem nine. Make the HTML easy to grade. So a heading for each check, screenshot, one or two sentences on what the screenshot proves. Put the screenshot image files in output slash app underscore check underscore images slash and link them from app underscore check dot HTML with relative paths, uh, for example, app underscore check underscore images slash inventory dot png.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the three checks, the HTML layout, and the image folder and relative-path format.

---

## Problem 12: Audit trail, safety, and finishing the harness

### Prompt I typed
- Now we're going to do problem 12, which is an audit trail, safety, and finishing the harness. So keep an append only output slash audit underscore trail dot JSON of agent loop activity. So time, tool name, short arguments slash result, stop reason. Do not wipe it between runs. Also think of some safety rules to give the agent and put them in prompts slash prompt dot MD. Finish output slash harness dot MD so it is clear how the system works. Uh, model fields in models.py and why you chose them, tools and abilities, safety rules, and specs. So loop limits, results, result caps, models, and how to run front and back.

### Follow-up prompt
- None needed.
- What was lacking in the first prompt: Nothing; the first prompt specified the audit fields, the append-only rule, the safety rules, and every harness section to finish.

---

## Problem 13: Push to GitHub and submit the URL

### Prompt I typed
- Perfect. Problem 13 is going to be pushing to GitHub and submitting the URL. So we're going to put the code in a folder named HW4 and push it to a public GitHub repository. Um, and then I'm going to submit on Canvas the repo URL. Uh, which is a link that the graders can open and clone. Uh, I'm not going to upload a zip for this homework. Um, so make sure to not put the real.env or campus underscore customs.db or product images in the GitHub repo. Use gitignore um, and include.env.example with placeholders only. Um, And the agent itself is four files under backend slash uh, prompts slash prompts.md agent.py tools.py and models.py. Um, and readme.md should explain how to run the front end and back end after placing the data pack. Um, so tell me what I need to do to create a public GitHub repo um, and then push it there.

### Follow-up prompt
- (Before Problem 13) Okay, this isn't problem 13 yet, but just give me a link that I can click on to open the website to check that it works.
- What was lacking in the first prompt: Nothing for Problem 13 itself; the earlier follow-up was a separate request for a clickable link to check the running site before publishing.
