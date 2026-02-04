from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import requests

TWITTER_API = "https://api.twitter.com/2"


@dataclass
class TweetRecord:
    id: str
    created_at: str
    date: str
    day: str
    time: str
    is_retweet: bool
    is_quote: bool
    text: str


class TwitterClient:
    def __init__(self, bearer_token: str | None = None) -> None:
        token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        if not token:
            raise ValueError("TWITTER_BEARER_TOKEN is required")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, path: str, params: dict[str, str]) -> dict:
        response = self.session.get(f"{TWITTER_API}{path}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def user_id(self, username: str) -> str:
        data = self._get(f"/users/by/username/{username}", params={})
        return data["data"]["id"]

    def tweets(
        self,
        user_id: str,
        max_results: int,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> Iterable[dict]:
        remaining = max_results
        next_token = None
        while remaining > 0:
            page_size = min(100, remaining)
            params: dict[str, str] = {
                "max_results": str(page_size),
                "tweet.fields": "created_at,referenced_tweets",
            }
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if next_token:
                params["pagination_token"] = next_token
            payload = self._get(f"/users/{user_id}/tweets", params=params)
            for item in payload.get("data", []):
                yield item
                remaining -= 1
                if remaining <= 0:
                    break
            next_token = payload.get("meta", {}).get("next_token")
            if not next_token:
                break


def classify_tweet(raw: dict) -> TweetRecord:
    created_at = raw["created_at"].replace("Z", "+00:00")
    created_dt = datetime.fromisoformat(created_at).astimezone(timezone.utc)
    date = created_dt.strftime("%Y-%m-%d")
    day = created_dt.strftime("%A")
    time = created_dt.strftime("%H:%M:%S")

    referenced = raw.get("referenced_tweets", [])
    ref_types = {ref.get("type") for ref in referenced}
    is_retweet = "retweeted" in ref_types
    is_quote = "quoted" in ref_types

    return TweetRecord(
        id=raw["id"],
        created_at=created_dt.isoformat(),
        date=date,
        day=day,
        time=time,
        is_retweet=is_retweet,
        is_quote=is_quote,
        text=raw.get("text", ""),
    )
