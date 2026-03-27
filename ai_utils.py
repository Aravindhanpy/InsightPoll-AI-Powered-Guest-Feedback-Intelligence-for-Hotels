"""
ai_utils.py
-----------
All AI logic lives here. Three functions:

  analyze_sentiment(text)              → (label, polarity_score)
  extract_keywords(texts)              → [keyword, ...]
  generate_claude_insight(...)         → "AI-generated insight paragraph"

Day 1-4: TextBlob for sentiment, KeyBERT for keywords (local, no API key)
Day 5:   Claude API for insight generation (requires ANTHROPIC_API_KEY)

Claude insight falls back to the rule-based version automatically if:
  - No API key is set
  - API call fails for any reason
  - No text feedback exists yet
So the app never breaks even if the API key is missing.
"""

import os
from dotenv import load_dotenv
from textblob import TextBlob


# Load .env file — picks up API keys automatically
load_dotenv()

# Loaded once at startup — slow first time, fast every call after


# ── AI client — swap between providers by changing these 3 lines ──────────
# Option A: Anthropic Claude (paid, best quality)
# _claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Option B: Groq (free, very fast, open source models)
from groq import Groq
_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
AI_PROVIDER = "groq"      # switch to "claude" when you add credits


# ── Sentiment ─────────────────────────────────────────────────────────────────

def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Returns (label, polarity) where:
      label    = "positive" | "negative" | "neutral"
      polarity = float in [-1.0, +1.0]

    Threshold ±0.1 avoids mislabelling borderline-neutral sentences.
    """
    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return label, round(polarity, 4)


# ── Keywords ──────────────────────────────────────────────────────────────────

def extract_keywords(texts: list[str], top_n: int = 5) -> list[str]:
    if not texts:
        return []
    import re
    from collections import Counter
    combined = " ".join(texts).lower()
    words = re.findall(r'\b[a-z]{4,}\b', combined)
    stopwords = {"this","that","with","have","from","they","were","been","will","your","what","when","hotel","room","stay","very","also","more","just"}
    filtered = [w for w in words if w not in stopwords]
    return [w for w, _ in Counter(filtered).most_common(top_n)]
```

**3. In `requirements.txt`, remove this line:**
```
keybert>=0.8.0


# ── Claude AI Insight ─────────────────────────────────────────────────────────

def generate_claude_insight(
    question:          str,
    tally:             dict,
    percentages:       dict,
    sentiment_summary: dict,
    avg_score:         float | None,
    keywords:          list[str],
    total_responses:   int,
    feedback_count:    int,
) -> str:
    """
    Sends poll data to Claude and gets back a 2-sentence human-readable
    insight written for a hotel manager.

    Falls back to rule-based insight if:
      - No API key set
      - No text feedback yet (avg_score is None)
      - API call fails for any reason
    """

    # Fall back immediately if no feedback to analyse
    if avg_score is None or feedback_count == 0:
        return "No text feedback yet. Submit responses with comments to see AI insights."

    # Fall back if no API key configured
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _rule_based_insight(avg_score, tally, keywords)

    # Build the data block sent to Claude
    tally_lines = "\n".join(
        f"  - {opt}: {count} votes ({percentages.get(opt, 0)}%)"
        for opt, count in tally.items()
    )
    sentiment_lines = (
        f"  Positive: {sentiment_summary['positive']} responses\n"
        f"  Negative: {sentiment_summary['negative']} responses\n"
        f"  Neutral:  {sentiment_summary['neutral']} responses"
    )
    keywords_str = ", ".join(keywords) if keywords else "none detected"

    prompt = f"""You are an experienced hotel operations analyst reviewing guest feedback data.

Poll question asked to guests:
"{question}"

Voting results ({total_responses} total responses):
{tally_lines}

Sentiment analysis of written comments ({feedback_count} guests left comments):
{sentiment_lines}
  Average sentiment score: {avg_score} (scale: -1.0 very negative to +1.0 very positive)

Top keywords extracted from guest comments:
{keywords_str}

Write exactly 2 sentences for the hotel manager:
- Sentence 1: State the key finding with specific numbers or percentages. Be direct.
- Sentence 2: Give one concrete, actionable recommendation the hotel can act on immediately.

Rules:
- Be specific — use the actual numbers and keywords from the data
- Do not use generic phrases like "consider improving" — be direct
- Write in professional but clear English
- Do not add any preamble, heading, or explanation — just the 2 sentences"""

    try:
        if AI_PROVIDER == "groq":
            # Groq — free, fast, open source
            response = _groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=150,
                messages=[
                    {"role": "system", "content": "You are a hotel operations analyst. You write short, data-driven insights for hotel managers. Always respond with exactly 2 sentences — no more, no less."},
                    {"role": "user",   "content": prompt}
                ],
            )
            insight = response.choices[0].message.content.strip()
        else:
            # Anthropic Claude — paid, highest quality
            message = _claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                system="You are a hotel operations analyst. You write short, data-driven insights for hotel managers. Always respond with exactly 2 sentences — no more, no less.",
                messages=[{"role": "user", "content": prompt}],
            )
            insight = message.content[0].text.strip()

        print(f"[AI Insight via {AI_PROVIDER}] {insight[:80]}...")
        return insight

    except Exception as e:
        print(f"[AI error — {AI_PROVIDER}] {e} — falling back to rule-based insight")
        return _rule_based_insight(avg_score, tally, keywords)


def _rule_based_insight(
    avg_score: float,
    tally:     dict,
    keywords:  list[str],
) -> str:
    """Fallback insight when Claude API is unavailable."""
    if avg_score > 0.3:
        mood = "Sentiment is strongly positive"
    elif avg_score > 0.1:
        mood = "Overall sentiment is positive"
    elif avg_score < -0.3:
        mood = "Sentiment is strongly negative"
    elif avg_score < -0.1:
        mood = "Overall sentiment is negative"
    else:
        mood = "Sentiment is largely neutral"

    top_option = max(tally, key=tally.get) if tally else None
    vote_line  = f"Most respondents chose '{top_option}'." if top_option else ""
    kw_line    = f"Key themes: {', '.join(keywords[:3])}." if keywords else "No recurring themes detected yet."

    return f"{mood}. {vote_line} {kw_line}".strip()
