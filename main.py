"""
main.py — InsightPoll API v7.0
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import PollDB, ResponseDB, PollCreate, ResponseCreate
from ai_utils import analyze_sentiment, extract_keywords, generate_claude_insight
import nltk
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('brown', quiet=True)
from visualization import (
    create_sentiment_trend_chart,
    create_sentiment_chart,
    create_sentiment_gauge,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="InsightPoll API", version="7.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

insight_cache: dict = {}
voted_tokens:  set  = set()

@app.get("/")
def home():
    return {"message": "InsightPoll API running", "version": "7.0.0"}

@app.get("/dashboard")
def dashboard():
    return FileResponse("dashboard.html")

@app.post("/create_poll", status_code=201)
def create_poll(poll: PollCreate, session: Session = Depends(get_session)):
    if session.get(PollDB, poll.id):
        raise HTTPException(status_code=400, detail=f"Poll id={poll.id} already exists")
    db_poll = PollDB(id=poll.id, question=poll.question, options=poll.options)
    session.add(db_poll)
    session.commit()
    session.refresh(db_poll)
    return {"message": "Poll created", "poll": db_poll}

@app.get("/polls")
def get_polls(session: Session = Depends(get_session)):
    polls = session.exec(select(PollDB)).all()
    return {"polls": polls, "count": len(polls)}

@app.get("/polls/{poll_id}")
def get_poll(poll_id: int, session: Session = Depends(get_session)):
    poll = session.get(PollDB, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")
    return poll

@app.post("/submit_response", status_code=201)
def submit_response(
    response: ResponseCreate,
    request:  Request,
    session:  Session = Depends(get_session),
):
    voter_token = request.headers.get("X-Voter-Token", "").strip()
    if voter_token:
        key = (response.poll_id, voter_token)
        if key in voted_tokens:
            raise HTTPException(status_code=409, detail="You have already submitted a response for this poll.")

    poll = session.get(PollDB, response.poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {response.poll_id} not found")
    if response.selected_option not in poll.options:
        raise HTTPException(status_code=422, detail=f"'{response.selected_option}' is not valid. Choose from: {poll.options}")

    db_response = ResponseDB(
        poll_id=response.poll_id,
        selected_option=response.selected_option,
        text_feedback=response.text_feedback,
        created_at=datetime.now(timezone.utc),
    )
    session.add(db_response)
    session.commit()
    session.refresh(db_response)

    if voter_token:
        voted_tokens.add((response.poll_id, voter_token))

    return {"message": "Response recorded", "response": db_response}

@app.get("/check_voted/{poll_id}")
def check_voted(poll_id: int, request: Request):
    voter_token = request.headers.get("X-Voter-Token", "").strip()
    if not voter_token:
        return {"voted": False}
    return {"voted": (poll_id, voter_token) in voted_tokens}

@app.get("/responses")
def get_responses(poll_id: int | None = None, session: Session = Depends(get_session)):
    query = select(ResponseDB)
    if poll_id is not None:
        query = query.where(ResponseDB.poll_id == poll_id)
    results = session.exec(query).all()
    return {"responses": results, "count": len(results)}

@app.get("/responses/{poll_id}/summary")
def get_summary(poll_id: int, session: Session = Depends(get_session)):
    poll = session.get(PollDB, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")

    poll_responses = session.exec(
        select(ResponseDB).where(ResponseDB.poll_id == poll_id)
    ).all()

    # Sort in Python — avoids SQLModel order_by issues
    poll_responses = sorted(
        poll_responses,
        key=lambda r: r.created_at or datetime.min.replace(tzinfo=timezone.utc)
    )
    total = len(poll_responses)

    tally = {opt: 0 for opt in poll.options}
    for r in poll_responses:
        tally[r.selected_option] += 1

    percentages = {
        k: round(v / total * 100, 1) if total else 0
        for k, v in tally.items()
    }

    texts             = [r.text_feedback for r in poll_responses if r.text_feedback]
    sentiment_summary = {"positive": 0, "negative": 0, "neutral": 0}
    scores: list[float] = []

    for text in texts:
        label, score = analyze_sentiment(text)
        sentiment_summary[label] += 1
        scores.append(score)

    avg_sentiment_score = round(sum(scores) / len(scores), 4) if scores else None
    keywords            = extract_keywords(texts)

    # Build trend data
    trend_data = []
    for r in poll_responses:
        if r.text_feedback:
            _, score = analyze_sentiment(r.text_feedback)
            trend_data.append({
                "time":   r.created_at.strftime("%H:%M:%S") if r.created_at else "—",
                "score":  score,
                "option": r.selected_option,
            })

    # Cached insight
    cached = insight_cache.get(poll_id)
    if cached and cached["total"] == total and cached["feedback_count"] == len(texts):
        insight = cached["insight"]
    else:
        insight = generate_claude_insight(
            question=poll.question, tally=tally, percentages=percentages,
            sentiment_summary=sentiment_summary, avg_score=avg_sentiment_score,
            keywords=keywords, total_responses=total, feedback_count=len(texts),
        )
        insight_cache[poll_id] = {"total": total, "feedback_count": len(texts), "insight": insight}

    alert = None
    if avg_sentiment_score is not None and avg_sentiment_score < -0.2:
        negative_pct = round(sentiment_summary["negative"] / len(texts) * 100)
        alert = f"⚠️ High negative sentiment detected — {negative_pct}% of feedback is negative."

    charts = {
        "trend_chart":     create_sentiment_trend_chart(trend_data),
        "sentiment_chart": create_sentiment_chart(sentiment_summary),
        "sentiment_gauge": create_sentiment_gauge(avg_sentiment_score),
    }

    return {
        "poll_id": poll_id, "question": poll.question,
        "total_responses": total, "tally": tally, "percentages": percentages,
        "sentiment": sentiment_summary, "avg_sentiment_score": avg_sentiment_score,
        "keywords": keywords, "feedback_count": len(texts),
        "insight": insight, "alert": alert, "charts": charts,
    }
