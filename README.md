# Digital Market Propensity Index : Ontario & Quebec

An end-to-end geospatial analytics project that identifies **high-propensity neighbourhoods** for a digital-first insurance product across Toronto (ON) and Montreal (QC).

The index answers a core market-segmentation question:  
> **"Which geographic areas are most receptive to a digitally distributed personal-lines insurance product, and why?"**

---

## Business Context

Digital-only insurance brands (e.g., Sonnet) need to prioritize marketing spend on areas where consumers are most likely to purchase online. This project builds a transparent, reproducible **Digital Propensity Score (0 - 100)** for each neighbourhood/borough using publicly available census-derived demographics.

## Methodology

Five census indicators are min-max normalized **within each city** and combined via a weighted average:

| Indicator | Weight | Rationale |
|---|---|---|
| % Aged 25–44 | 0.25 | Younger adults adopt digital channels faster |
| % Bachelor's degree + | 0.20 | Higher education correlates with online purchasing |
| Median household income | 0.15 | Mid-to-high income = insurance purchasing power |
| % Non-car commute | 0.25 | Transit/bike/WFH commuters are more digitally connected |
| % Renter households | 0.15 | Urban renters tend to use digital-first services |

Areas are bucketed into **Tier A (High)**, **Tier B (Medium)**, and **Tier C (Low)** based on score thresholds at 66 and 33.

Full methodology: [`docs/methodology.md`](docs/methodology.md)

## Outputs

| Deliverable | Description |
|---|---|
| `outputs/digital_propensity_map.html` | Interactive Folium choropleth map with tooltips |
| `outputs/tableau_export.csv` | Flat CSV for Tableau / Power BI dashboards |
| `outputs/qa_workbook.xlsx` | Excel QA workbook (data quality, summary stats, full data) |

## Tech Stack

- **Python** (pandas, geopandas, folium, openpyxl)
- **SQL-ready design** : scoring logic is structured for easy migration to BigQuery / PostgreSQL
- **GIS** : GeoJSON boundary integration with EPSG:4326 projection
- **Excel** : QA workbook with pivot-style summary sheets
- **Tableau / Power BI** : export-ready CSV with denormalized schema

## Project Structure

```
DigitalMarketIndex/
├── main.py                     # pipeline orchestrator
├── requirements.txt
├── data/
│   ├── toronto_demographics.csv
│   └── montreal_demographics.csv
├── src/
│   ├── data_loader.py          # csv + geoJSON loading
│   ├── scoring.py              # propensity score engine
│   ├── mapping.py              # folium map 
│   └── export.py               # excel + csv export
├── outputs/                    # generated deliverables
└── docs/
    └── methodology.md
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Open `outputs/digital_propensity_map.html` in a browser to explore the interactive map.

## Data Sources

- **Demographic data**: Derived from [Statistics Canada 2021 Census of Population](https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm?Lang=E) profiles at the neighbourhood/borough level. Sample data included for demonstration; replace with official census extracts for production use.
- **Geographic boundaries**: Downloaded from [Toronto Open Data](https://open.toronto.ca/) and [Données ouvertes Montréal](https://donnees.montreal.ca/). Fallback centroid coordinates are used when boundary downloads are unavailable.


## Next Steps

- [ ] Migrate scoring SQL to **Google BigQuery** for warehouse-scale analysis
- [ ] Expand to all Ontario and Quebec **Forward Sortation Areas (FSAs)**
- [ ] Integrate **Environics Analytics** or similar third-party segmentation data
- [ ] Build a **Google Looker Studio** dashboard connected to BigQuery
- [ ] Add temporal dimension using census data from multiple years

