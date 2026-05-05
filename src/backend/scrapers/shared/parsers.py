"""Shared parsing and formatting helpers for odds scraper sources."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Required, TypedDict

from loguru import logger


class GameOdds(TypedDict, total=False):
    """Canonical schema for a single game's odds from any source."""

    date: Required[str]
    home_team: Required[str]
    away_team: Required[str]
    matchup: Required[str]
    spread: Required[str]
    moneyline: Required[str]
    home_moneyline: Required[str]
    over_under: Required[str]
    source: Required[str]
    # Optional enrichment fields (Phase 1)
    home_win_pct: float
    away_win_pct: float
    home_off_rating: float
    home_def_rating: float
    away_off_rating: float
    away_def_rating: float
    home_record: str
    away_record: str
    model_probability_source: str


def extract_first_signed_number(text: str) -> str | None:
    match = re.search(r'(?<!\d)([+-]?\d+(?:\.\d+)?)(?!\d)', text)
    return match.group(1) if match else None


def extract_first_american_odds(text: str) -> str | None:
    match = re.search(r'(?<!\d)([+-]\d{3,})(?!\d)', text)
    return match.group(1) if match else None


def extract_first_total(text: str) -> str | None:
    match = re.search(r'\b(?:over|under|o|u)\s*([0-9]+(?:\.[0-9]+)?)\b', text, re.IGNORECASE)
    if match:
        return match.group(1)

    numbers = re.findall(r'(?<!\d)(\d+(?:\.\d+)?)(?!\d)', text)
    return numbers[0] if numbers else None


def format_american_odds(value: str | int | float | None) -> str:
    if value is None:
        return 'N/A'
    try:
        odds = int(value)
        return f'+{odds}' if odds > 0 else str(odds)
    except (TypeError, ValueError):
        logger.warning('Could not convert odds value to int: {!r}', value)
        return str(value)


def format_line(value: str | int | float | None) -> str:
    if value is None:
        return 'N/A'
    cleaned = re.sub(r'^[ou]', '', str(value), flags=re.IGNORECASE)
    return cleaned if cleaned else 'N/A'


def format_event_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return datetime.now().strftime('%Y-%m-%d')
