# Healthcare Claims Risk Prediction

Predicting future inpatient hospital admissions using historical Medicare healthcare claims.

## Overview

This project uses the **CMS DE-SynPUF (Data Entrepreneurs' Synthetic Public Use File)** to predict whether a Medicare beneficiary will experience an inpatient hospital admission in 2010.

The model uses beneficiary characteristics and healthcare utilization from **2008–2009** to generate beneficiary-level risk features. The project combines information across beneficiary, inpatient, outpatient, carrier, and prescription drug claims and evaluates an XGBoost classifier.

The intended business use case is **risk prioritization**: identifying a limited high-risk segment of beneficiaries that could be prioritized for proactive care management or intervention.

## Problem

Healthcare providers and insurers have limited resources for proactive intervention. Rather than treating all beneficiaries equally, the objective is to identify beneficiaries who are more likely to experience a future inpatient admission.

### Prediction target

* `1` → beneficiary had ≥1 inpatient admission during 2010
* `0` → beneficiary did not have an inpatient admission during 2010

### Prediction timeline

```text
2008–2009 historical information
          ↓
   Feature engineering
          ↓
       XGBoost
          ↓
Predicted 2010 admission risk
          ↓
     Actual 2010 outcome
```

Only historical 2008–2009 information is used to construct the model features.

## Dataset

The project uses CMS DE-SynPUF Sample 1, containing:

* 2008 Beneficiary Summary
* 2009 Beneficiary Summary
* 2010 Beneficiary Summary
* Inpatient Claims
* Outpatient Claims
* Carrier Claims A
* Carrier Claims B
* Prescription Drug Events (PDE)

The raw files are loaded into SQLite as `claims.db` using Python and pandas.

The raw CMS data and processed database are excluded from GitHub.

## Feature Engineering

Claims-level records are aggregated to the beneficiary level using SQL queries.

The final model contains **23 features** across five healthcare data sources.

### Beneficiary features

* Age in 2009
* Sex
* 11 chronic-condition indicators

### Inpatient utilization

* Prior inpatient admission count
* Prior inpatient reimbursement

### Outpatient utilization

* Prior outpatient visit count
* Prior outpatient reimbursement
* Number of distinct outpatient providers

### Carrier utilization

* Prior carrier claim count
* Prior carrier reimbursement

### Prescription utilization

* Prior prescription fill count
* Number of distinct drugs
* Prior prescription cost

All utilization features are calculated from **2008–2009** claims.

## Modeling

### Algorithm

**XGBoost Classifier**

Configuration:

* `n_estimators = 100`
* `max_depth = 4`
* `learning_rate = 0.1`

### Evaluation

The model uses an 80/20 stratified train/test split at the beneficiary level.

Primary evaluation metrics:

* ROC-AUC
* Precision
* Recall

Because intervention capacity is limited, the project also evaluates a **top-10% risk strategy**, ranking beneficiaries by predicted probability and selecting the highest-risk 10%.

## Results

### Overall model

| Metric              |    Result |
| ------------------- | --------: |
| Beneficiaries       |   114,538 |
| Features            |        23 |
| 2010 admission rate |   10.228% |
| ROC-AUC             | **0.714** |

### Top 10% risk cohort

| Metric              |    Result |
| ------------------- | --------: |
| Population selected |   ~11,454 |
| Precision           | **22.6%** |
| Recall              | **22.1%** |

The top 10% strategy captures approximately 22.1% of all observed 2010 inpatient admissions while restricting intervention to approximately 10% of beneficiaries.

## Feature Importance

The most influential model features include:

1. Prior carrier claim count
2. Prior carrier reimbursement
3. Prior inpatient admission count
4. Chronic kidney disease indicator
5. Congestive heart failure indicator
6. Ischemic heart disease indicator
7. Prior inpatient reimbursement
8. Prior outpatient visit count
9. COPD indicator
10. Distinct prescription drugs

Prior carrier claim count was the strongest feature according to the XGBoost feature-importance output.

## Business Impact Scenario

The project translates model performance into an illustrative intervention scenario.

The analysis uses:

* ~11,454 beneficiaries selected in the top 10%
* ~22.1% recall
* ~2,589 observed admissions identified within that cohort
* $9,786.36 average 2010 inpatient payment
* 15% assumed intervention effectiveness

Under these assumptions:

**Estimated potential avoided inpatient cost ≈ $3.8M**

This is a **scenario estimate, not measured savings**. The 15% intervention-effectiveness figure is an assumption used to illustrate potential impact; it is not directly estimated from the CMS DE-SynPUF data.

## Project Structure

```text
healthcare-risk-project/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── scripts/
│   ├── load_data.py
│   ├── train_mvp.py
│   ├── train_mvp_v2.py
│   ├── train_mvp_v3.py
│   └── avg_cost.py
│
├── outputs/
│   └── project_summary.xlsx
│
├── README.md
├── .gitignore
└── requirements.txt
```

## Reproducibility

1. Download CMS DE-SynPUF Sample 1 files.
2. Place the source files in `data/raw/`.
3. Run:

```bash
python scripts/load_data.py
```

4. Train the final model:

```bash
python scripts/train_mvp_v3.py
```

5. Calculate average 2010 inpatient payment:

```bash
python scripts/avg_cost.py
```

## Key Takeaway

The project demonstrates how historical claims data can be transformed from millions of transaction-level records into beneficiary-level predictive features and used to prioritize a high-risk population for potential healthcare intervention.

The model achieved **0.714 ROC-AUC**, and ranking the highest-risk 10% of beneficiaries captured **22.1% of future inpatient admissions**.
