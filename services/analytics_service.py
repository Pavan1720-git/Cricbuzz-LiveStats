"""
services/analytics_service.py — Cricket formula calculations and validation helpers.

All formulas follow official cricket rules.
Zero-denominator cases always return None (not 0 or ∞).
"""

from typing import Optional
import pandas as pd


# ── Cricket Formulas ──────────────────────────────────────────────────────────

def batting_strike_rate(runs: int, balls_faced: int) -> Optional[float]:
    """Strike rate = (runs / balls_faced) × 100.  Returns None if no balls faced."""
    if balls_faced is None or balls_faced == 0:
        return None
    return round(100.0 * runs / balls_faced, 2)


def batting_average(total_runs: int, dismissals: int) -> Optional[float]:
    """Average = total_runs / dismissals.  Not-outs excluded from denominator."""
    if dismissals is None or dismissals == 0:
        return None
    return round(total_runs / dismissals, 2)


def bowling_economy(runs_conceded: int, balls_bowled: int) -> Optional[float]:
    """Economy = runs_conceded / legal_overs_bowled.
    Legal overs = balls_bowled / 6 (exact integer division of balls).
    """
    if balls_bowled is None or balls_bowled == 0:
        return None
    legal_overs = balls_bowled / 6.0
    return round(runs_conceded / legal_overs, 2)


def bowling_average(runs_conceded: int, wickets: int) -> Optional[float]:
    if wickets is None or wickets == 0:
        return None
    return round(runs_conceded / wickets, 2)


def bowling_strike_rate(balls_bowled: int, wickets: int) -> Optional[float]:
    if wickets is None or wickets == 0:
        return None
    return round(balls_bowled / wickets, 2)


def win_percentage(wins: int, matches_with_result: int) -> Optional[float]:
    """Win % = wins / matches_with_result × 100.
    Denominator is matches where a winner was declared (no abandoned/NR).
    """
    if matches_with_result is None or matches_with_result == 0:
        return None
    return round(100.0 * wins / matches_with_result, 2)


def overs_to_balls(overs_decimal: float) -> int:
    """Convert 19.5 overs to 119 balls (19*6 + 5).
    Cricket convention: the decimal part represents balls, not fractional overs.
    """
    if overs_decimal is None:
        return 0
    full_overs = int(overs_decimal)
    extra_balls = round((overs_decimal - full_overs) * 10)  # e.g. .5 → 5 balls
    return full_overs * 6 + extra_balls


def balls_to_overs(balls: int) -> str:
    """Convert 119 balls to '19.5' (19 overs 5 balls)."""
    if balls is None or balls < 0:
        return "0.0"
    return f"{balls // 6}.{balls % 6}"


# ── Validation ────────────────────────────────────────────────────────────────

def validate_player_stat(stat: dict) -> list[str]:
    """Return a list of validation error messages (empty = valid)."""
    errors = []
    for field in ("runs", "balls_faced", "fours", "sixes", "wickets",
                  "runs_conceded", "balls_bowled", "maidens"):
        val = stat.get(field)
        if val is not None and (not isinstance(val, (int, float)) or val < 0):
            errors.append(f"'{field}' must be a non-negative number, got {val!r}")

    runs = stat.get("runs", 0) or 0
    balls = stat.get("balls_faced", 0) or 0
    fours = stat.get("fours", 0) or 0
    sixes = stat.get("sixes", 0) or 0

    if runs < fours * 4 + sixes * 6:
        errors.append("Runs cannot be less than boundary contribution (4s×4 + 6s×6)")
    if balls < fours + sixes:
        errors.append("Balls faced cannot be less than total boundaries hit")

    return errors


def validate_match_date(date_str: str) -> bool:
    """Check ISO-8601 date format YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return False
    from datetime import datetime
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_overs(overs_str: str) -> bool:
    """Validate a cricket overs string like '19.5' (balls part 0-5 only)."""
    try:
        parts = str(overs_str).split(".")
        if len(parts) == 1:
            return int(parts[0]) >= 0
        if len(parts) == 2:
            return int(parts[0]) >= 0 and 0 <= int(parts[1]) <= 5
    except (ValueError, TypeError):
        pass
    return False


# ── Aggregation helpers ────────────────────────────────────────────────────────

def compute_batting_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate player_match_stats rows into per-player batting summary.
    Input df must have columns: player_id, full_name, team_name,
    runs, balls_faced, fours, sixes, dismissal_type.
    """
    if df.empty:
        return pd.DataFrame()

    def _dismissals(group):
        return group["dismissal_type"].apply(
            lambda x: x not in ("not out", "", None) if pd.notna(x) else False
        ).sum()

    agg = df.groupby(["player_id", "full_name", "team_name"]).apply(
        lambda g: pd.Series({
            "innings":       len(g),
            "total_runs":    g["runs"].sum(),
            "highest_score": g["runs"].max(),
            "total_balls":   g["balls_faced"].sum(),
            "total_fours":   g["fours"].sum(),
            "total_sixes":   g["sixes"].sum(),
            "dismissals":    _dismissals(g),
        })
    ).reset_index()

    agg["batting_average"] = agg.apply(
        lambda r: batting_average(r["total_runs"], r["dismissals"]), axis=1
    )
    agg["strike_rate"] = agg.apply(
        lambda r: batting_strike_rate(r["total_runs"], r["total_balls"]), axis=1
    )
    return agg.sort_values("total_runs", ascending=False)


def compute_bowling_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate into per-player bowling summary."""
    if df.empty:
        return pd.DataFrame()

    agg = df[df["balls_bowled"] > 0].groupby(
        ["player_id", "full_name", "team_name"]
    ).agg(
        matches=("match_id", "nunique"),
        total_wickets=("wickets", "sum"),
        total_runs_conceded=("runs_conceded", "sum"),
        total_balls_bowled=("balls_bowled", "sum"),
        total_maidens=("maidens", "sum"),
    ).reset_index()

    agg["economy"] = agg.apply(
        lambda r: bowling_economy(r["total_runs_conceded"], r["total_balls_bowled"]), axis=1
    )
    agg["bowling_average"] = agg.apply(
        lambda r: bowling_average(r["total_runs_conceded"], r["total_wickets"]), axis=1
    )
    agg["bowling_sr"] = agg.apply(
        lambda r: bowling_strike_rate(r["total_balls_bowled"], r["total_wickets"]), axis=1
    )
    return agg.sort_values("total_wickets", ascending=False)
