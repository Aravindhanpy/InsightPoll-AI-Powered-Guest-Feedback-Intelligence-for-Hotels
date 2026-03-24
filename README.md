# InsightPoll 🏨

**AI-Powered Guest Feedback Intelligence for Hotels**

> From feedback to action — in seconds.

InsightPoll is a real-time hotel guest feedback system with a full AI pipeline. Guests vote on their experience in 10 seconds. The system analyses sentiment, extracts keywords, and generates a 2-sentence actionable insight for the hotel manager — automatically.

---

## Project Structure

```
insightpoll/
├── main.py               — FastAPI app, all 7 endpoints
├── models.py             — DB table models (SQLModel) + API schemas (Pydantic)
├── database.py           — SQLite connection and session dependency
├── ai_utils.py           — Sentiment (TextBlob) + keywords (KeyBERT) + AI insight (Groq/Claude)
├── visualization.py      — Plotly chart generators (trend, sentiment donut, mood gauge)
├── dashboard.html        — Full frontend: vote page + admin results page
├── seed_hotel_polls.py   — Seeds all 20 hotel polls into the database
├── requirements.txt      — All Python dependencies
└── .env                  — API keys (create this yourself — not committed to git)
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download NLTK data (run once)
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 3. Create `.env` file
Create a file named `.env` in the project root:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx   # optional — only if using Claude
```

Get a free Groq key at: https://console.groq.com

### 4. Start the server
```bash
uvicorn main:app --reload
```

### 5. Seed hotel polls (run once)
```bash
python seed_hotel_polls.py
```

### 6. Open the dashboard
```
http://127.0.0.1:8000/dashboard
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/dashboard` | Serve the dashboard HTML |
| POST | `/create_poll` | Create a new poll |
| GET | `/polls` | List all polls |
| GET | `/polls/{id}` | Get one poll |
| POST | `/submit_response` | Submit a guest response |
| GET | `/check_voted/{poll_id}` | Check if this browser already voted |
| GET | `/responses` | List responses (`?poll_id=1` to filter) |
| GET | `/responses/{id}/summary` | AI-enriched summary + charts |

Interactive API docs: **http://127.0.0.1:8000/docs**

---

## Quick Test (Swagger)

**Create a poll:**
```json
POST /create_poll
{
  "id": 1,
  "question": "How is the mess food?",
  "options": ["Good", "Average", "Bad"]
}
```

**Submit a response:**
```json
POST /submit_response
{
  "poll_id": 1,
  "selected_option": "Bad",
  "text_feedback": "Food is oily and always served cold"
}
```

**Get AI summary:**
```
GET /responses/1/summary
```

---

## The 20 Hotel Questions

Seeds cover 8 business pillars:

| # | Topic |
|---|-------|
| 1–3 | Overall stay, expectations, recommendation |
| 4–6 | Room cleanliness, bed comfort, amenities |
| 7–8 | Food quality, menu variety |
| 9–11 | Staff behavior, check-in/out, response speed |
| 12–13 | Wait time, room service |
| 14 | Value for money |
| 15–16 | WiFi, facilities |
| 17 | Booking source |
| 18–20 | Return visit, best part, what to improve |

---

## AI Layer

| Feature | Library | Output |
|---------|---------|--------|
| Sentiment analysis | TextBlob | positive / negative / neutral + score (-1 to +1) |
| Keyword extraction | KeyBERT | Top 5 meaningful words from all feedback |
| Insight generation | Groq (Llama 3.3 70B) | 2-sentence hotel manager recommendation |
| Insight caching | In-memory dict | Regenerates only when new responses arrive |
| Fallback | Rule-based logic | Used when no API key or no text feedback |

**Switch AI provider** — in `ai_utils.py`, change one line:
```python
AI_PROVIDER = "groq"    # "groq" (free) or "claude" (paid, higher quality)
```

---

## Dashboard

Two tabs in one HTML file:

**🗳 Vote tab (public)**
- Loads all 20 polls as category pills automatically
- Guest taps a topic → question + options appear instantly
- Optional text feedback box
- One vote per browser per poll (enforced via localStorage token + backend)
- Success screen — no path to results

**📊 Results tab (admin only)**
- Password protected (default: `admin123` — change in dashboard.html)
- 4 stat cards: total responses, text feedback count, mood score, top choice
- Sentiment trend line chart — shows mood shifting over time
- Sentiment donut chart — positive / negative / neutral breakdown
- Mood gauge — single -1 to +1 score at a glance
- AI insight paragraph — data-driven recommendation
- Keyword tags — top words from guest comments
- Auto-refreshes every 5 seconds — charts update without blinking

**Change admin password** — find this line in `dashboard.html`:
```javascript
const ADMIN_PASSWORD = "admin123";
```

---

## Making It Accessible on a Network

**Same WiFi (show on phones during demo):**
```bash
uvicorn main:app --reload --host 0.0.0.0
```
Then open `http://YOUR_LOCAL_IP:8000/dashboard` on any device on the same network.

**Find your IP:**
```bash
ipconfig          # Windows
ifconfig          # Mac/Linux
```

**Public internet (share with anyone):**
```bash
ngrok http 8000
```
Gives a public URL like `https://abc123.ngrok.io`. Open that anywhere in the world.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI |
| Server | Uvicorn |
| Database | SQLite via SQLModel |
| Validation | Pydantic v2 |
| Sentiment | TextBlob |
| Keywords | KeyBERT (sentence-transformers) |
| AI insights | Groq API — Llama 3.3 70B (free) |
| Charts | Plotly (Python → JSON → Plotly.js) |
| Frontend | Vanilla HTML + CSS + JS |
| Auth | localStorage voter token + backend set |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for AI insights) | Free at console.groq.com |
| `ANTHROPIC_API_KEY` | No | Only if switching to Claude |

Both are loaded from `.env` via `python-dotenv`. If neither key is set, insights fall back to rule-based logic — the app never crashes.

---

## Database

SQLite file: `insightpoll.db` — created automatically on first run.

**If you add new columns to models.py** (like `created_at`), delete the old DB and restart:
```bash
del insightpoll.db        # Windows
rm insightpoll.db         # Mac/Linux
uvicorn main:app --reload
python seed_hotel_polls.py
```

---

## Future Roadmap

- [ ] QR code generator per department (room, restaurant, reception)
- [ ] Overall executive summary — one AI paragraph across all 20 polls
- [ ] WhatsApp integration — guest votes via message
- [ ] Trend comparison week-over-week
- [ ] JWT-based admin login (replace frontend password check)
- [ ] PostgreSQL migration for multi-property hotel chains
- [ ] Export responses to CSV/Excel

---

## License

Built for hackathon demonstration. Not production-ready without JWT auth, HTTPS, and a production database.
