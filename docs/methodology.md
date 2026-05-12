# Methodology — Digital Market Propensity Index

## Objective

Identify geographic areas in Ontario (Toronto) and Quebec (Montreal) with the highest propensity for adoption of a digital-first personal-lines insurance product, using publicly available demographic indicators.

## Scope

- **Toronto, Ontario**: 40 neighbourhoods (city-defined boundaries)
- **Montreal, Quebec**: 19 boroughs (arrondissements)

## Data Sources

### Demographic Indicators

All demographic variables are derived from the **Statistics Canada 2021 Census of Population**, accessed through census profile tables at the neighbourhood (Toronto) and borough (Montreal) level.

| Variable | Census Source | Rationale |
|---|---|---|
| `pct_age_25_44` | Age and sex tables | Core digital-native demographic; highest online purchasing rates |
| `pct_bachelors_plus` | Education tables | Education level correlates with comfort navigating digital services |
| `median_household_income` | Income tables | Insurance is a considered purchase requiring disposable income |
| `pct_non_car_commute` | Commuting tables | Non-car commuters (transit, cycling, WFH) are concentrated in digitally connected urban cores |
| `pct_renters` | Housing tenure tables | Rental-heavy areas skew younger and more urban — traits aligned with digital channel preference |

### Geographic Boundaries

- **Toronto**: City of Toronto Neighbourhoods boundary file (GeoJSON, EPSG:4326)
- **Montreal**: Ville de Montréal arrondissements boundary file (GeoJSON, EPSG:4326)

## Scoring Model

### Step 1 — Min-Max Normalization

Each indicator is normalized to [0, 1] **within each city independently**:

```
x_norm = (x - x_min) / (x_max - x_min)
```

Within-city normalization ensures that each city's internal variation is captured without one city's absolute levels dominating the other.

### Step 2 — Weighted Composite Score

The five normalized indicators are combined via weighted average:

```
score = (0.25 × age_norm + 0.20 × education_norm + 0.15 × income_norm
       + 0.25 × commute_norm + 0.15 × renter_norm) × 100
```

**Weight rationale:**
- Age and commute mode receive the highest weights (0.25 each) because they are the strongest behavioural proxies for digital channel preference in existing insurance-industry research.
- Education receives moderate weight (0.20) as a secondary predictor.
- Income and renter status receive lower weights (0.15 each) as supporting contextual factors.

### Step 3 — Tier Assignment

Areas are classified into three tiers based on score thresholds:

| Tier | Score Range | Interpretation |
|---|---|---|
| Tier A (High) | 66 – 100 | Strong fit for digital-first marketing investment |
| Tier B (Medium) | 33 – 65 | Moderate fit; potential with targeted messaging |
| Tier C (Low) | 0 – 32 | Lower digital propensity; traditional channels may be more effective |

## Quality Assurance

- **Completeness**: All input variables checked for null values before scoring; any area with >1 missing indicator is flagged.
- **Range validation**: All percentage fields validated to [0, 100]; income validated as positive.
- **Join integrity**: Boundary-to-data join rates reported; unmatched areas documented.
- **Reproducibility**: All transformations are deterministic and implemented in version-controlled Python code.

## Limitations and Caveats

1. **Proxy-based scoring**: The index uses demographic proxies, not observed digital behaviour. Validation against actual policy acquisition data is recommended before operational use.
2. **Census vintage**: 2021 Census data may not reflect post-pandemic demographic shifts (e.g., remote work migration patterns).
3. **Within-city normalization**: Scores are relative within each city. A "Tier A" in Toronto is not directly comparable to a "Tier A" in Montreal without cross-city calibration.
4. **Sample data**: The included demographic data is derived from census distributions for demonstration. Official StatsCan extracts should be used for any business decision-making.
5. **Uniform weights**: Weights are based on industry heuristics, not empirically optimized. A future iteration could calibrate weights using actual conversion data.

## Recommended Next Steps

1. **Validation**: Compare index rankings against known high-performing postal codes from internal policy data.
2. **Granularity**: Expand to Forward Sortation Area (FSA) level for finer targeting.
3. **Temporal analysis**: Track score changes across census years to identify emerging opportunities.
4. **Third-party enrichment**: Integrate Environics Analytics PRIZM segments or similar for richer psychographic profiling.
5. **BigQuery migration**: Port scoring logic to SQL for integration with enterprise analytics pipelines.
