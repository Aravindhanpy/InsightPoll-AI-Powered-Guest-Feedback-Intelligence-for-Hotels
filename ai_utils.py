import os
import re
from typing import Optional
from collections import Counter
from dotenv import load_dotenv
from textblob import TextBlob

load_dotenv()

from groq import Groq
_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def analyze_sentiment(text: str):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return label, round(polarity, 4)


def extract_keywords(texts, top_n: int = 5):
    if not texts:
        return []
    combined = " ".join(texts).lower()
    words = re.findall(r'\b[a-z]{4,}\b', combined)
    stopwords = {"this","that","with","have","from","they","were","been","will","your","what","when","hotel","room","stay","very","also","more","just"}
    filtered = [w for w in words if w not in stopwords]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def generate_claude_insight(
    question,
    tally,
    percentages,
    sentiment_summary,
    avg_score,
    keywords,
    total_responses,
    feedback_count,
) -> str:
    if avg_score is None or feedback_count == 0:
        return "No text feedback yet. Submit responses with comments to see AI insights."

    tally_lines = "\n".join(
        f"  - {opt}: {count} votes ({percentages.get(opt, 0)}%)"
        for opt, count in tally.items()
    )
    keywords_str = ", ".join(keywords) if keywords else "none detected"

    prompt = f"""You are an experienced hotel operations analyst reviewing guest feedback data.

Poll question: "{question}"
Voting results ({total_responses} total responses):
{tally_lines}
Sentiment: Positive={sentiment_summary['positive']}, Negative={sentiment_summary['negative']}, Neutral={sentiment_summary['neutral']}
Average sentiment score: {avg_score} (-1.0 to +1.0)
Top keywords: {keywords_str}

Write exactly 2 sentences for the hotel manager:
- Sentence 1: Key finding with specific numbers.
- Sentence 2: One concrete actionable recommendation."""

    try:
        response = _groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=150,
            messages=[
                {"role": "system", "content": "You are a hotel operations analyst. Always respond with exactly 2 sentences."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq error] {e}")
        return _rule_based_insight(avg_score, tally, keywords)


def _rule_based_insight(avg_score, tally, keywords) -> str:
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
    vote_line = f"Most respondents chose '{top_option}'." if top_option else ""
    kw_line = f"Key themes: {', '.join(keywords[:3])}." if keywords else ""
    return f"{mood}. {vote_line} {kw_line}".strip()
