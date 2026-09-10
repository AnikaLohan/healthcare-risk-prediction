# Predicting High-Risk Healthcare Claimants (CMS DE-SynPUF)

## Objective
Identify Medicare beneficiaries at high risk of becoming high-cost or high-utilization
claimants (e.g. inpatient admission, high total spend) in a future period, using
synthetic-but-realistic CMS claims data. Built to practice the core skills used in
actuarial/health-analytics work: SQL-based ETL across multiple linked data sources,
careful feature engineering, leakage-free model validation, and translating model
output into a business-impact narrative.

## Data Source
CMS 2008–2010 Data Entrepreneurs' Synthetic Public Use File (DE-SynPUF):
https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files

Not committed to this repo (see `data/README.md` for download instructions).
Each sample contains:
- Beneficiary Summary files (2008, 2009, 2010) — demographics, chronic conditions
- Inpatient Claims — hospital admissions
- Outpatient Claims — outpatient visits
- Carrier Claims — doctor/physician visits
- Prescription Drug Events (PDE)

## Project Structure
```
healthcare-risk-project/
├── data/
│   ├── raw/            # downloaded CMS files (gitignored)
│   └── processed/      # cleaned, feature-engineered tables (gitignored)
├── sql/                # ETL: cleaning, joins, feature engineering queries
├── notebooks/          # EDA, modeling, evaluation
├── docs/               # write-up, assumptions, data dictionary notes
└── outputs/            # final charts, model metrics, one-pager summary
```

## Roadmap
- [ ] Step 1: Download DE-SynPUF sample, load raw CSVs into SQLite
- [ ] Step 2: SQL ETL — clean + join beneficiary, inpatient, outpatient, carrier tables
- [ ] Step 3: Define target label (e.g. inpatient admission in following year)
- [ ] Step 4: Feature engineering in SQL (utilization counts, cost totals, chronic condition flags)
- [ ] Step 5: Time-based train/test split (no future leakage)
- [ ] Step 6: Baseline model (logistic regression) → XGBoost
- [ ] Step 7: Evaluate (AUC, precision/recall), interpret feature importance
- [ ] Step 8: Business-impact write-up + summary dashboard

## Tech Stack
Python (pandas, scikit-learn, xgboost), SQL (SQLite), Excel (final summary dashboard)

## Status
🚧 In progress — built as a portfolio project for an actuarial internship application.
