"""
Data loading utilities for the Digital Market Propensity Index.
Loads demographic CSVs and downloads GeoJSON boundary files from
Toronto and Montreal open-data portals.
"""

import json
import pathlib
from typing import Optional

import geopandas as gpd
import pandas as pd
import requests

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

TORONTO_GEOJSON_URL = (
    "https://services7.arcgis.com/mbC97TSabuNgCnce/ArcGIS/rest/services/"
    "Toronto_Neighbourhoods_158/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&f=geojson&resultRecordCount=200"
)
MONTREAL_GEOJSON_URL = (
    "https://donnees.montreal.ca/fr/dataset/"
    "9797a946-9da8-41ec-8815-f6b276dec7e9/resource/"
    "e18bfd07-edc8-4ce8-8a5a-3b617662a794/download/"
    "limites-administratives-agglomeration.geojson"
)


def load_demographics(city: str) -> pd.DataFrame:
    """Load the cleaned demographic CSV for a given city."""
    filename = f"{city.lower()}_demographics.csv"
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Demographic data not found: {path}")

    df = pd.read_csv(path)
    df["city"] = city.capitalize()
    return df


def _download_geojson(url: str, dest: pathlib.Path, timeout: int = 30) -> bool:
    """Download a GeoJSON file, returning True on success."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        dest.write_text(resp.text, encoding="utf-8")
        return True
    except (requests.RequestException, OSError) as exc:
        print(f"  [WARN] Could not download {dest.name}: {exc}")
        return False


def _build_fallback_geodataframe(df: pd.DataFrame, name_col: str) -> gpd.GeoDataFrame:
    """
    When boundary files are unavailable, create a point-based GeoDataFrame
    using approximate centroids so the pipeline can still produce maps.
    """
    from shapely.geometry import Point

    toronto_centroids = {
        "Harbourfront-CityPlace": (-79.3770, 43.6400),
        "Bay-Cloverhill": (-79.3850, 43.6580),
        "Church-Wellesley": (-79.3800, 43.6650),
        "Kensington-Chinatown": (-79.3970, 43.6530),
        "Annex": (-79.4050, 43.6700),
        "University": (-79.3940, 43.6610),
        "Fort York-Liberty Village": (-79.4190, 43.6380),
        "Trinity-Bellwoods": (-79.4130, 43.6480),
        "South Riverdale": (-79.3350, 43.6600),
        "The Beaches": (-79.2950, 43.6700),
        "High Park-Swansea": (-79.4650, 43.6500),
        "High Park North": (-79.4630, 43.6620),
        "Roncesvalles": (-79.4480, 43.6480),
        "Junction Area": (-79.4640, 43.6680),
        "Corso Italia-Davenport": (-79.4400, 43.6760),
        "Dovercourt Village": (-79.4380, 43.6680),
        "Danforth": (-79.3500, 43.6830),
        "Danforth East York": (-79.3200, 43.6900),
        "Yonge-Eglinton": (-79.3980, 43.7060),
        "North Toronto": (-79.3950, 43.7250),
        "Lawrence Park South": (-79.4050, 43.7300),
        "Forest Hill South": (-79.4150, 43.6950),
        "Rosedale-Moore Park": (-79.3760, 43.6820),
        "East Willowdale": (-79.3900, 43.7650),
        "Willowdale West": (-79.4150, 43.7650),
        "Yonge-Doris": (-79.4130, 43.7680),
        "Scarborough Village": (-79.2300, 43.7400),
        "Agincourt South-Malvern West": (-79.2700, 43.7900),
        "Woburn North": (-79.2350, 43.7850),
        "Malvern West": (-79.2100, 43.8100),
        "West Rouge": (-79.1700, 43.8200),
        "West Humber-Clairville": (-79.5850, 43.7350),
        "Mount Olive-Silverstone-Jamestown": (-79.5700, 43.7500),
        "Downsview": (-79.4800, 43.7400),
        "Etobicoke West Mall": (-79.5300, 43.6400),
        "Mimico-Queensway": (-79.4900, 43.6130),
        "New Toronto": (-79.5000, 43.5990),
        "Long Branch": (-79.5250, 43.5920),
        "Thorncliffe Park": (-79.3450, 43.7100),
        "Flemingdon Park": (-79.3380, 43.7250),
    }
    montreal_centroids = {
        "Ville-Marie": (-73.5600, 45.5100),
        "Le Plateau-Mont-Royal": (-73.5750, 45.5250),
        "Rosemont-La Petite-Patrie": (-73.5850, 45.5400),
        "Outremont": (-73.6050, 45.5200),
        "Le Sud-Ouest": (-73.5700, 45.4800),
        "Mercier-Hochelaga-Maisonneuve": (-73.5300, 45.5500),
        "Villeray-Saint-Michel-Parc-Extension": (-73.6100, 45.5550),
        "Ahuntsic-Cartierville": (-73.6600, 45.5500),
        "C\u00f4te-des-Neiges-Notre-Dame-de-Gr\u00e2ce": (-73.6300, 45.4900),
        "Verdun": (-73.5700, 45.4600),
        "LaSalle": (-73.6300, 45.4350),
        "Lachine": (-73.6800, 45.4350),
        "Saint-Laurent": (-73.6800, 45.5000),
        "Anjou": (-73.5500, 45.6050),
        "Rivi\u00e8re-des-Prairies-Pointe-aux-Trembles": (-73.5100, 45.6400),
        "Montr\u00e9al-Nord": (-73.5500, 45.5850),
        "Pierrefonds-Roxboro": (-73.8200, 45.4900),
        "L'\u00cele-Bizard-Sainte-Genevi\u00e8ve": (-73.8700, 45.5050),
        "Saint-L\u00e9onard": (-73.5900, 45.5850),
    }
    centroids = {**toronto_centroids, **montreal_centroids}
    geometries = [
        Point(centroids.get(name, (0, 0))) for name in df[name_col]
    ]
    return gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")


def load_boundaries(
    city: str, demographics_df: pd.DataFrame, name_col: str
) -> gpd.GeoDataFrame:
    """
    Load GeoJSON boundary polygons for a city. Falls back to centroid
    points if the download fails.
    """
    geojson_map = {
        "toronto": ("toronto_neighbourhoods.geojson", TORONTO_GEOJSON_URL),
        "montreal": ("montreal_boroughs.geojson", MONTREAL_GEOJSON_URL),
    }
    filename, url = geojson_map[city.lower()]
    dest = DATA_DIR / filename

    if not dest.exists():
        print(f"Downloading {city} boundaries ...")
        _download_geojson(url, dest)

    if dest.exists():
        try:
            gdf = gpd.read_file(dest)
            if city.lower() == "montreal" and "TYPE" in gdf.columns:
                gdf = gdf[gdf["TYPE"] == "Arrondissement"].copy()
            return gdf
        except Exception as exc:
            print(f"  [WARN] Failed to parse {dest.name}: {exc}")

    print(f"  Using fallback centroid points for {city}.")
    return _build_fallback_geodataframe(demographics_df, name_col)
