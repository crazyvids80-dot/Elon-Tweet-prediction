# Elon Tweet Tracker & Predictor

A lightweight Python app that:

- Fetches Elon Musk tweets, retweets, and quoted tweets from Twitter API v2.
- Stores each tweet with date, day-of-week, and time in SQLite.
- Predicts future tweet volume for a given date/time range using historical averages.

## Requirements

- Python 3.10+
- A Twitter API v2 Bearer Token (set as `TWITTER_BEARER_TOKEN`).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=src

# initialize database
python -m elon_tracker init --db data/elon.db

# fetch tweets
export TWITTER_BEARER_TOKEN=YOUR_TOKEN
python -m elon_tracker fetch --db data/elon.db --max-results 100

# predict for a future range
python -m elon_tracker predict --db data/elon.db \
  --from "2025-01-01T00:00:00" \
  --to "2025-01-03T00:00:00"
```

## Notes

- The predictor estimates the expected number of tweets per hour using historical averages by day-of-week and hour-of-day.
- If no history exists for a given day/hour, it falls back to hour-only and then global averages.
- The app stores tweet text as returned by the API.
