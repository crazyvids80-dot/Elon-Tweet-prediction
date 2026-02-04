from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from elon_tracker.db import ensure_db, load_tweets, upsert_tweets
from elon_tracker.fetch import TwitterClient, classify_tweet
from elon_tracker.model import predict_range

DEFAULT_DB = Path("data/elon.db")


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Datetime must be ISO format, e.g. 2025-01-01T00:00:00"
        ) from exc


def handle_init(args: argparse.Namespace) -> None:
    ensure_db(args.db)
    print(f"Initialized database at {args.db}")


def handle_fetch(args: argparse.Namespace) -> None:
    conn = ensure_db(args.db)
    client = TwitterClient()
    user_id = client.user_id("elonmusk")
    raw_tweets = client.tweets(
        user_id=user_id,
        max_results=args.max_results,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    records = [classify_tweet(item) for item in raw_tweets]
    inserted = upsert_tweets(conn, [record.__dict__ for record in records])
    print(f"Stored {inserted} tweets.")


def handle_predict(args: argparse.Namespace) -> None:
    conn = ensure_db(args.db)
    rows = load_tweets(conn)
    if not rows:
        print("No tweets stored yet. Run fetch first.")
        return
    predictions = predict_range(rows, args.start, args.end)
    if not predictions:
        print("Not enough historical data to make predictions.")
        return

    total = 0.0
    for prediction in predictions:
        total += prediction.expected_count
        timestamp = prediction.timestamp.strftime("%Y-%m-%d %H:%M")
        print(f"{timestamp} -> {prediction.expected_count:.2f} expected tweets")
    print(f"Total expected tweets: {total:.2f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Elon tweet tracker and predictor")
    parser.set_defaults(func=None)
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database",
    )

    subparsers = parser.add_subparsers(title="commands")

    init_parser = subparsers.add_parser("init", help="Initialize the database")
    init_parser.set_defaults(func=handle_init)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch tweets from Twitter API")
    fetch_parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of tweets to fetch (up to 3200)",
    )
    fetch_parser.add_argument(
        "--start-time",
        dest="start_time",
        help="RFC3339 timestamp to start fetching from",
    )
    fetch_parser.add_argument(
        "--end-time",
        dest="end_time",
        help="RFC3339 timestamp to end fetching",
    )
    fetch_parser.set_defaults(func=handle_fetch)

    predict_parser = subparsers.add_parser("predict", help="Predict tweet volume")
    predict_parser.add_argument(
        "--from",
        dest="start",
        type=parse_datetime,
        required=True,
        help="Start datetime (ISO format)",
    )
    predict_parser.add_argument(
        "--to",
        dest="end",
        type=parse_datetime,
        required=True,
        help="End datetime (ISO format)",
    )
    predict_parser.set_defaults(func=handle_predict)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        return
    if hasattr(args, "start") and hasattr(args, "end") and args.start > args.end:
        parser.error("--from must be before --to")
    args.func(args)


if __name__ == "__main__":
    main()
