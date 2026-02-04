from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass
class Prediction:
    timestamp: datetime
    expected_count: float


def build_hourly_profile(rows: Iterable[tuple[str, str, str]]):
    by_day_hour: dict[tuple[str, int], list[int]] = defaultdict(list)
    by_hour: dict[int, list[int]] = defaultdict(list)
    all_counts: list[int] = []

    daily_counts = defaultdict(int)
    for created_at, day, time_str in rows:
        hour = int(time_str.split(":")[0])
        date = created_at.split("T")[0]
        daily_counts[(date, day, hour)] += 1

    for (_date, day, hour), count in daily_counts.items():
        by_day_hour[(day, hour)].append(count)
        by_hour[hour].append(count)
        all_counts.append(count)

    return by_day_hour, by_hour, all_counts


def predict_range(
    rows: Iterable[tuple[str, str, str]],
    start: datetime,
    end: datetime,
) -> list[Prediction]:
    by_day_hour, by_hour, all_counts = build_hourly_profile(rows)
    if not all_counts:
        return []

    def average(values: list[int]) -> float:
        return sum(values) / len(values)

    global_avg = average(all_counts)

    predictions: list[Prediction] = []
    current = start
    while current <= end:
        day = current.strftime("%A")
        hour = current.hour
        day_hour_values = by_day_hour.get((day, hour))
        hour_values = by_hour.get(hour)
        if day_hour_values:
            expected = average(day_hour_values)
        elif hour_values:
            expected = average(hour_values)
        else:
            expected = global_avg
        predictions.append(Prediction(timestamp=current, expected_count=expected))
        current += timedelta(hours=1)
    return predictions
