# Automated Insight Generation

A Python-only auto-analytics dashboard for district-level healthcare performance data.

## Features
- CSV loading, schema validation, data types, and missing-value report
- Live district, indicator, and insight-type filters
- Trend detection with configurable percentage threshold (default 10%)
- Outlier detection using configurable IQR or Z-score rules
- Pearson correlation matrix and configurable correlation-pair flagging (default |r| >= 0.70)
- Generated insight records with IDs, types, indicators, entities, periods, numeric values, severity, and explanations
- Severity counts, correlation heatmap, district line chart
- CSV downloads for insights and correlation matrix

## Setup (Windows)
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Generate the demo dataset (optional; a sample CSV is already included):
   ```bash
   python generate_dataset.py
   ```
6. Start the dashboard:
   ```bash
   streamlit run app.py
   ```

## CSV schema
Required columns:
- `month` (monthly date such as `2026-07-01`)
- `district` (district name)
- `anc_coverage` (%)
- `institutional_delivery` (%)
- `immunization` (%)
- `high_risk_cases` (raw count)

One row should represent one district-month combination. Missing numeric values are allowed and reported; malformed dates/blank districts are dropped during validation.

## Important limitations
- Correlation is descriptive and does not prove causation.
- Correlations calculated on small datasets can be unstable. Prefer at least 3 months per district and 10 or more districts, as specified in the assignment.
- `data/healthcare.csv` is synthetic data for testing only; replace it with your provided/approved dataset before reporting real findings.
- Severity rules are transparent heuristics and can be adjusted to fit the assignment's interpretation.
