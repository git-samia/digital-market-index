"""
Folium map generation for the Digital Propensity Index.

Produces an interactive HTML map with:
- Choropleth shading by digital propensity score
- Tooltips showing area name, score, and tier
- Layer control for Toronto vs Montreal
"""

import pathlib
from typing import Optional

import folium
import geopandas as gpd
import pandas as pd
from branca.colormap import LinearColormap
from folium.plugins import MarkerCluster

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "outputs"


def _create_base_map() -> folium.Map:
    """Create a base Folium map centered between Toronto and Montreal."""
    return folium.Map(
        location=[44.5, -76.5],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )


def _add_choropleth_layer(
    m: folium.Map,
    gdf: gpd.GeoDataFrame,
    name_col: str,
    score_col: str,
    layer_name: str,
) -> folium.Map:
    """
    Add a GeoJSON choropleth layer when polygon boundaries are available.
    """
    colormap = LinearColormap(
        colors=["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
        vmin=0,
        vmax=100,
        caption=f"Digital Propensity Score — {layer_name}",
    )

    feature_group = folium.FeatureGroup(name=layer_name)

    for _, row in gdf.iterrows():
        geo_json = folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, score=row[score_col]: {
                "fillColor": colormap(score),
                "color": "#333333",
                "weight": 1,
                "fillOpacity": 0.7,
            },
        )
        tooltip_html = (
            f"<b>{row[name_col]}</b><br>"
            f"Score: {row[score_col]:.1f} / 100<br>"
            f"Tier: {row['tier']}"
        )
        geo_json.add_child(folium.Tooltip(tooltip_html))
        geo_json.add_to(feature_group)

    feature_group.add_to(m)
    colormap.add_to(m)
    return m


def _add_circle_layer(
    m: folium.Map,
    gdf: gpd.GeoDataFrame,
    name_col: str,
    score_col: str,
    layer_name: str,
) -> folium.Map:
    """
    Fallback: add circle markers sized/coloured by score when only
    centroid points are available.
    """
    colormap = LinearColormap(
        colors=["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
        vmin=0,
        vmax=100,
        caption=f"Digital Propensity Score — {layer_name}",
    )

    feature_group = folium.FeatureGroup(name=layer_name)

    for _, row in gdf.iterrows():
        tooltip_html = (
            f"<b>{row[name_col]}</b><br>"
            f"Score: {row[score_col]:.1f} / 100<br>"
            f"Tier: {row['tier']}"
        )
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=max(5, row[score_col] / 5),
            color="#333333",
            weight=1,
            fill=True,
            fill_color=colormap(row[score_col]),
            fill_opacity=0.75,
            tooltip=tooltip_html,
        ).add_to(feature_group)

    feature_group.add_to(m)
    colormap.add_to(m)
    return m


def build_map(
    toronto_gdf: gpd.GeoDataFrame,
    montreal_gdf: gpd.GeoDataFrame,
    toronto_name_col: str = "neighbourhood",
    montreal_name_col: str = "borough",
    score_col: str = "digital_propensity_score",
    output_filename: str = "digital_propensity_map.html",
) -> pathlib.Path:
    """
    Build a two-layer interactive Folium map and save it to outputs/.
    Automatically detects whether polygons or points are available and
    renders accordingly.
    """
    m = _create_base_map()

    for gdf, name_col, label in [
        (toronto_gdf, toronto_name_col, "Toronto"),
        (montreal_gdf, montreal_name_col, "Montreal"),
    ]:
        has_polygons = any(
            gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
        )
        if has_polygons:
            _add_choropleth_layer(m, gdf, name_col, score_col, label)
        else:
            _add_circle_layer(m, gdf, name_col, score_col, label)

    folium.LayerControl(collapsed=False).add_to(m)

    title_html = """
    <div style="position:fixed; top:10px; left:60px; z-index:9999;
         background:white; padding:12px 20px; border-radius:8px;
         box-shadow:0 2px 8px rgba(0,0,0,.2); font-family:Arial,sans-serif;">
      <h3 style="margin:0 0 4px 0; color:#1a1a2e;">
        Digital Market Propensity Index
      </h3>
      <p style="margin:0; font-size:13px; color:#555;">
        Ontario &amp; Quebec — Toronto &amp; Montreal neighbourhoods
      </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / output_filename
    m.save(str(out_path))
    print(f"Map saved -> {out_path}")
    return out_path
