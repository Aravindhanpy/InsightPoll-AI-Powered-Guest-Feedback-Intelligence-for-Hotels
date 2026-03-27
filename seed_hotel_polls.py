"""
seed_hotel_polls.py
-------------------
Run this once to populate all hotel polls into the database.

Usage:
    python seed_hotel_polls.py

Make sure the API is running first:
    uvicorn main:app --reload
"""

import httpx

API = "https://insightpoll-ai-powered-guest-feedback.onrender.com"

POLLS = [
    {
        "id": 1,
        "question": "How would you rate your overall stay?",
        "options": ["Excellent", "Good", "Average", "Poor"]
    },
    {
        "id": 2,
        "question": "Did your experience meet your expectations?",
        "options": ["Exceeded expectations", "Met expectations", "Below expectations"]
    },
    {
        "id": 3,
        "question": "Would you recommend our hotel to others?",
        "options": ["Definitely yes", "Probably yes", "Probably not", "Definitely not"]
    },
    {
        "id": 4,
        "question": "How clean was your room?",
        "options": ["Very clean", "Clean", "Needs improvement", "Unacceptable"]
    },
    {
        "id": 5,
        "question": "How comfortable was the bed?",
        "options": ["Very comfortable", "Comfortable", "Uncomfortable", "Very uncomfortable"]
    },
    {
        "id": 6,
        "question": "Were the room amenities satisfactory?",
        "options": ["Fully satisfied", "Mostly satisfied", "Partially satisfied", "Not satisfied"]
    },
    {
        "id": 7,
        "question": "How was the food quality at our restaurant?",
        "options": ["Excellent", "Good", "Average", "Poor", "Did not use"]
    },
    {
        "id": 8,
        "question": "Was the menu variety sufficient?",
        "options": ["More than enough", "Sufficient", "Needs more variety", "Very limited"]
    },
    {
        "id": 9,
        "question": "How was the staff behavior during your stay?",
        "options": ["Excellent", "Friendly", "Neutral", "Rude"]
    },
    {
        "id": 10,
        "question": "Was the check-in and check-out process smooth?",
        "options": ["Very smooth", "Smooth", "Slightly delayed", "Very slow"]
    },
    {
        "id": 11,
        "question": "How quickly did staff respond to your requests?",
        "options": ["Immediately", "Within 10 minutes", "Took too long", "Never responded"]
    },
    {
        "id": 12,
        "question": "How long did you wait during check-in?",
        "options": ["Under 5 minutes", "5–10 minutes", "10–20 minutes", "Over 20 minutes"]
    },
    {
        "id": 13,
        "question": "Was room service delivered on time?",
        "options": ["Always on time", "Usually on time", "Often late", "Did not use"]
    },
    {
        "id": 14,
        "question": "Was your stay worth the price?",
        "options": ["Excellent value", "Good value", "Fair value", "Overpriced"]
    },
    {
        "id": 15,
        "question": "How was the WiFi quality during your stay?",
        "options": ["Very fast", "Acceptable", "Slow", "Did not work"]
    },
    {
        "id": 16,
        "question": "Which facility did you enjoy the most?",
        "options": ["Swimming pool", "Gym", "Spa", "Restaurant", "None"]
    },
    {
        "id": 17,
        "question": "Where did you book your stay from?",
        "options": ["Booking.com", "Hotel website", "Walk-in", "Travel agent", "Other"]
    },
    {
        "id": 18,
        "question": "Would you stay with us again?",
        "options": ["Definitely", "Probably", "Unlikely", "Never"]
    },
    {
        "id": 19,
        "question": "What did you love most about your stay?",
        "options": ["Room comfort", "Food & dining", "Staff service", "Location", "Facilities"]
    },
    {
        "id": 20,
        "question": "What should we improve immediately?",
        "options": ["Room cleanliness", "Food quality", "Staff response time", "WiFi", "Check-in speed"]
    },
]


def seed():
    created  = []
    skipped  = []
    failed   = []

    print("\n🏨  InsightPoll — Hotel Polls Seeder")
    print("─" * 42)

    for poll in POLLS:
        try:
            res = httpx.post(f"{API}/create_poll", json=poll, timeout=10)
            if res.status_code == 201:
                created.append(poll["id"])
                print(f"  ✅ Poll {poll['id']:02d}  {poll['question'][:55]}")
            elif res.status_code == 400:
                skipped.append(poll["id"])
                print(f"  ⏭  Poll {poll['id']:02d}  already exists — skipped")
            else:
                failed.append(poll["id"])
                print(f"  ❌ Poll {poll['id']:02d}  {res.json().get('detail','Unknown error')}")
        except Exception as e:
            failed.append(poll["id"])
            print(f"  ❌ Poll {poll['id']:02d}  Connection error: {e}")

    print("─" * 42)
    print(f"  Created : {len(created)}   Skipped : {len(skipped)}   Failed : {len(failed)}")

    if failed:
        print("\n  ⚠️  Some polls failed. Make sure the API is running:")
        print("     uvicorn main:app --reload\n")
    else:
        print("\n  🚀  All polls ready. Open your dashboard and load any poll ID 1–20.\n")


if __name__ == "__main__":
    seed()
