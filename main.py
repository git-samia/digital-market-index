"""
Digital Market Propensity Index — Pipeline Orchestrator
=======================================================

End-to-end pipeline that:
  1. Loads demographic data for Toronto (ON) and Montreal (QC)
  2. Downloads or falls back to boundary geometries
  3. Computes a Digital Propensity Score (0–100) per area
  4. Generates an interactive Folium map
  5. Exports a Tableau-ready CSV and an Excel QA workbook

Usage:
    python main.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from src.data_loader import load_demographics, load_boundaries
from src.scoring import score_pipeline
from src.mapping import build_map
from src.export import export_tableau_csv, export_qa_workbook

import geopandas as gpd
import pandas as pd


def main() -> None:
    print("=" * 60)
    print("  Digital Market Propensity Index -- ON / QC")
    print("=" * 60)

    # --- 1. Load demographics ---
    print("\n[1/5] Loading demographic data ...")
    toronto_df = load_demographics("toronto")
    montreal_df = load_demographics("montreal")
    print(f"  Toronto : {len(toronto_df):>3} neighbourhoods")
    print(f"  Montreal: {len(montreal_df):>3} boroughs")

    # --- 2. Score ---
    print("\n[2/5] Computing Digital Propensity Scores ...")
    scored_df = score_pipeline(toronto_df, montreal_df)

    tier_counts = scored_df["tier"].value_counts()
    for tier, count in tier_counts.items():
        print(f"  {tier}: {count} areas")

    print(f"\n  Top 5 areas by score:")
    name_col = "neighbourhood" if "neighbourhood" in scored_df.columns else "area_name"
    top5 = scored_df.head(5)
    for _, row in top5.iterrows():
        area = row.get("neighbourhood") if pd.notna(row.get("neighbourhood")) else row.get("borough", "")
        print(f"    {row['rank']:>2}. {area:<45} {row['digital_propensity_score']:>5.1f}  ({row['city']})")

    # --- 3. Load boundaries & merge ---
    print("\n[3/5] Loading geographic boundaries ...")
    toronto_scored = scored_df[scored_df["city"] == "Toronto"].copy()
    montreal_scored = scored_df[scored_df["city"] == "Montreal"].copy()

    toronto_boundaries = load_boundaries("toronto", toronto_scored, "neighbourhood")
    montreal_boundaries = load_boundaries("montreal", montreal_scored, "borough")

    toronto_gdf = _merge_scores_to_geometry(
        toronto_boundaries, toronto_scored, "neighbourhood"
    )
    montreal_gdf = _merge_scores_to_geometry(
        montreal_boundaries, montreal_scored, "borough"
    )

    # --- 4. Build map ---
    print("\n[4/5] Generating interactive map ...")
    map_path = build_map(toronto_gdf, montreal_gdf)

    # --- 5. Export ---
    print("\n[5/5] Exporting deliverables ...")
    csv_path = export_tableau_csv(scored_df)
    xlsx_path = export_qa_workbook(scored_df)

    print("\n" + "=" * 60)
    print("  Pipeline complete!")
    print("=" * 60)
    print(f"\n  Outputs:")
    print(f"    Map       : {map_path!s}")
    print(f"    Tableau   : {csv_path!s}")
    print(f"    QA Excel  : {xlsx_path!s}")
    print()


def _merge_scores_to_geometry(
    boundaries_gdf: gpd.GeoDataFrame,
    scored_df,
    name_col: str,
) -> gpd.GeoDataFrame:
    """
    Try to join scored data to boundary polygons by name. If the boundary
    GeoDataFrame already contains the score columns (fallback path), just
    return it as-is.
    """
    if "digital_propensity_score" in boundaries_gdf.columns:
        return boundaries_gdf

    boundary_name_candidates = [
        "AREA_NAME", "area_name", "NOM", "nom", "NAME", "name",
        "FIELD_7", "FIELD_8", "neighbourhood", "borough",
    ]
    boundary_name_col = None
    for candidate in boundary_name_candidates:
        if candidate in boundaries_gdf.columns:
            boundary_name_col = candidate
            break

    if boundary_name_col is None:
        print(f"  [WARN] Could not find name column in boundaries; using fallback.")
        from src.data_loader import _build_fallback_geodataframe
        return _build_fallback_geodataframe(scored_df, name_col)

    merged = boundaries_gdf.merge(
        scored_df,
        left_on=boundary_name_col,
        right_on=name_col,
        how="inner",
    )

    if len(merged) == 0:
        print(f"  [WARN] No boundary matches for {name_col}; using fallback centroids.")
        from src.data_loader import _build_fallback_geodataframe
        return _build_fallback_geodataframe(scored_df, name_col)

    matched_pct = len(merged) / len(scored_df) * 100
    print(f"  Matched {len(merged)}/{len(scored_df)} areas ({matched_pct:.0f}%) to boundaries.")

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=boundaries_gdf.crs)


if __name__ == "__main__":
    main()
