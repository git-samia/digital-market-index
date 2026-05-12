"""
Digital Propensity Index scoring engine.

Computes a composite score (0–100) for each geographic area that estimates
how receptive a neighbourhood / borough is to a digital-first insurance
product like Sonnet.

Scoring methodology
-------------------
Five census-derived indicators are min-max normalized within each city,
then combined via a weighted average:

  1. pct_age_25_44         (weight 0.25) — younger adults adopt digital channels faster
  2. pct_bachelors_plus    (weight 0.20) — higher education correlates with online purchasing
  3. median_household_income(weight 0.15) — mid-to-high income = insurance purchase power
  4. pct_non_car_commute   (weight 0.25) — non-car commuters are more digitally connected
  5. pct_renters           (weight 0.15) — renters in urban cores use digital services more

The weighted average is scaled to 0–100 and bucketed into three tiers:
  - Tier A (High)   : score >= 66
  - Tier B (Medium) : 33 <= score < 66
  - Tier C (Low)    : score < 33
"""

from typing import Dict, List

import pandas as pd

FEATURES: List[str] = [
    "pct_age_25_44",
    "pct_bachelors_plus",
    "median_household_income",
    "pct_non_car_commute",
    "pct_renters",
]

WEIGHTS: Dict[str, float] = {
    "pct_age_25_44": 0.25,
    "pct_bachelors_plus": 0.20,
    "median_household_income": 0.15,
    "pct_non_car_commute": 0.25,
    "pct_renters": 0.15,
}


def _min_max_normalize(series: pd.Series) -> pd.Series:
    """Scale a series to [0, 1] using min-max normalization."""
    smin, smax = series.min(), series.max()
    if smax == smin:
        return pd.Series(0.5, index=series.index)
    return (series - smin) / (smax - smin)


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add normalized feature columns, a composite digital_propensity_score
    (0–100), and a tier label to the dataframe.
    """
    df = df.copy()

    for feat in FEATURES:
        col_norm = f"{feat}_norm"
        df[col_norm] = _min_max_normalize(df[feat])

    df["digital_propensity_score"] = sum(
        WEIGHTS[feat] * df[f"{feat}_norm"] for feat in FEATURES
    ) * 100

    df["digital_propensity_score"] = df["digital_propensity_score"].round(1)

    df["tier"] = pd.cut(
        df["digital_propensity_score"],
        bins=[-0.1, 33, 66, 100.1],
        labels=["Tier C (Low)", "Tier B (Medium)", "Tier A (High)"],
    )
    return df


def score_pipeline(toronto_df: pd.DataFrame, montreal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Score Toronto and Montreal independently (normalization within city)
    then concatenate into one ranked dataframe.
    """
    toronto_scored = compute_scores(toronto_df)
    montreal_scored = compute_scores(montreal_df)

    combined = pd.concat([toronto_scored, montreal_scored], ignore_index=True)
    combined["rank"] = (
        combined["digital_propensity_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return combined.sort_values("rank")
