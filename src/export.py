"""
Export utilities for the Digital Propensity Index.

Generates:
  1. A Tableau / Power BI-ready CSV (flat, denormalized)
  2. An Excel QA workbook with data-quality checks
"""

import pathlib
from datetime import datetime

import pandas as pd

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "outputs"


def export_tableau_csv(df: pd.DataFrame, filename: str = "tableau_export.csv") -> pathlib.Path:
    """Write a flat CSV with all scored data, ready for Tableau import."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / filename

    export_cols = [
        "city", "rank",
        "neighbourhood", "borough",
        "population",
        "pct_age_25_44", "pct_bachelors_plus",
        "median_household_income", "pct_non_car_commute", "pct_renters",
        "population_density_sqkm",
        "digital_propensity_score", "tier",
    ]
    available = [c for c in export_cols if c in df.columns]

    name_col = "neighbourhood" if "neighbourhood" in df.columns else "borough"
    if "area_name" not in available:
        df = df.copy()
        df["area_name"] = df.get("neighbourhood", df.get("borough", ""))
    available = ["area_name" if c in ("neighbourhood", "borough") else c for c in available]
    available = list(dict.fromkeys(available))

    df_export = df.copy()
    if "area_name" not in df_export.columns:
        df_export["area_name"] = df_export.get("neighbourhood", df_export.get("borough", ""))

    final_cols = [
        "city", "rank", "area_name", "population",
        "pct_age_25_44", "pct_bachelors_plus",
        "median_household_income", "pct_non_car_commute", "pct_renters",
        "population_density_sqkm",
        "digital_propensity_score", "tier",
    ]
    final_cols = [c for c in final_cols if c in df_export.columns]
    df_export[final_cols].to_csv(out_path, index=False)
    print(f"Tableau CSV saved -> {out_path}")
    return out_path


def export_qa_workbook(df: pd.DataFrame, filename: str = "qa_workbook.xlsx") -> pathlib.Path:
    """
    Create an Excel workbook with three QA sheets:
      1. Full Data        — all rows with scores
      2. Summary Stats    — descriptive statistics by city and tier
      3. Data Quality     — null counts, value ranges, coverage checks
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / filename

    df = df.copy()
    if "area_name" not in df.columns:
        df["area_name"] = df.get("neighbourhood", df.get("borough", ""))

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        _write_full_data(df, writer)
        _write_summary(df, writer)
        _write_data_quality(df, writer)

    print(f"QA workbook saved -> {out_path}")
    return out_path


def _write_full_data(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    display_cols = [
        "city", "area_name", "population",
        "pct_age_25_44", "pct_bachelors_plus",
        "median_household_income", "pct_non_car_commute", "pct_renters",
        "population_density_sqkm",
        "digital_propensity_score", "tier", "rank",
    ]
    cols = [c for c in display_cols if c in df.columns]
    df[cols].to_excel(writer, sheet_name="Full Data", index=False)


def _write_summary(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    numeric_cols = [
        "population", "pct_age_25_44", "pct_bachelors_plus",
        "median_household_income", "pct_non_car_commute", "pct_renters",
        "digital_propensity_score",
    ]
    numeric_cols = [c for c in numeric_cols if c in df.columns]

    by_city = df.groupby("city")[numeric_cols].agg(["mean", "median", "min", "max"])
    by_city.to_excel(writer, sheet_name="Summary by City")

    by_tier = df.groupby("tier", observed=False)[numeric_cols].agg(["count", "mean", "median"])
    by_tier.to_excel(writer, sheet_name="Summary by Tier")


def _write_data_quality(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    qa_rows = []
    for col in df.columns:
        if df[col].dtype in ("float64", "int64"):
            qa_rows.append({
                "column": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().mean() * 100, 2),
                "min": df[col].min(),
                "max": df[col].max(),
                "mean": round(df[col].mean(), 2),
            })
        else:
            qa_rows.append({
                "column": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().mean() * 100, 2),
                "unique_values": df[col].nunique(),
                "min": "",
                "max": "",
                "mean": "",
            })

    qa_df = pd.DataFrame(qa_rows)

    meta = pd.DataFrame([
        {"check": "Total rows", "value": len(df)},
        {"check": "Total columns", "value": len(df.columns)},
        {"check": "Cities covered", "value": df["city"].nunique()},
        {"check": "Score range", "value": f"{df['digital_propensity_score'].min():.1f} – {df['digital_propensity_score'].max():.1f}"},
        {"check": "Generated at", "value": datetime.now().strftime("%Y-%m-%d %H:%M")},
        {"check": "Data source", "value": "Statistics Canada 2021 Census (derived sample)"},
    ])

    meta.to_excel(writer, sheet_name="Data Quality", index=False, startrow=0)
    qa_df.to_excel(writer, sheet_name="Data Quality", index=False, startrow=len(meta) + 2)
