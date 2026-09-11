# Healthcare Claims Risk Prediction

Predictive modeling project using CMS DE-SynPUF Medicare synthetic claims data to identify beneficiaries at higher risk of inpatient admission.

## Overview

Healthcare organizations have limited capacity for care-management interventions. A useful predictive model can help prioritize beneficiaries who are most likely to require inpatient care.

This project builds a claims-based risk model using **2008–2009 healthcare utilization and beneficiary information to predict whether a beneficiary has an inpatient admission in 2010**.

The workflow covers data ingestion, SQL-based feature engineering, leakage-aware feature construction, XGBoost modeling, risk ranking, and business-impact estimation.

## Business Problem

Instead of treating every beneficiary equally, the objective is to:

> **Rank beneficiaries by predicted inpatient-admission risk and focus limited intervention capacity on the highest-risk members.**

The model is therefore evaluated not only using AUC, but also by measuring performance when targeting the **top 10% of beneficiaries by predicted risk**.

## Target

The target variable is:

* `1` — beneficiary had at least one inpatient admission in 2010
* `0` — beneficiary had no inpatient admission in 2010

Features are constructed exclusively from **2008–2009 information**, so 2010 claims are not used as predictors of the 2010 outcome.

## Dataset

The project uses **CMS DE-SynPUF (Medicare Synthetic Public Use Files), Sample 1**.

The pipeline loads eight CMS files into SQLite:

* Beneficiary Summary — 2008
* Beneficiary Summary — 2009
* Beneficiary Summary — 2010
* Inpatient Claims
* Outpatient Claims
* Carrier Claims A
* Carrier Claims B
* Prescription Drug Events (PDE)

The resulting SQLite database contains approximately **11.5 million claim records**.

Raw CMS data and the processed SQLite database are excluded from GitHub through `.gitignore`.

## Feature Engineering

A total of **23 features** were engineered across beneficiary information and five claims-related data sources.

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

Carrier Claims A and B are combined using `UNION ALL`.

### Prescription drug utilization

* Prior prescription fill count
* Number of distinct drugs
* Prior prescription drug cost

All utilization features are calculated using **2008–2009 data only**.

## Modeling

An **XGBoost binary classification model** was trained using:

* 100 estimators
* Maximum tree depth: 4
* Learning rate: 0.1
* Evaluation metric: AUC
* Random state: 42

The dataset was divided using an **80/20 stratified train-test split**.

## Results

| Metric                    |    Result |
| ------------------------- | --------: |
| Beneficiaries             |   114,538 |
| Features                  |        23 |
| 2010 admission rate       |   10.228% |
| Test AUC                  | **0.714** |
| Precision @ 0.5 threshold |     66.7% |
| Recall @ 0.5 threshold    |      0.3% |
| Precision @ top 10%       | **22.6%** |
| Recall @ top 10%          | **22.1%** |

### Why Top-10% Targeting?

A fixed 0.5 classification threshold is not necessarily appropriate for a healthcare intervention setting where resources are limited.

Instead, beneficiaries are ranked by predicted probability and the **top 10% highest-risk members** are selected for intervention.

This group captures approximately **22.1% of all beneficiaries who subsequently experience an inpatient admission in 2010**, while 22.6% of the selected beneficiaries actually experience an admission.

This makes the ranking approach more aligned with a limited-capacity care-management use case.

## Feature Importance

The model's most important features include:

| Feature                         | Importance |
| ------------------------------- | ---------: |
| Prior carrier claim count       |      33.7% |
| Prior carrier reimbursement     |       6.8% |
| Prior inpatient admission count |       5.9% |
| Chronic kidney disease          |       5.5% |
| Congestive heart failure        |       5.5% |
| Ischemic heart disease          |       5.2% |
| Prior inpatient reimbursement   |       4.5% |
| Prior outpatient visit count    |       4.3% |
| COPD                            |       3.6% |

The model relies heavily on **prior healthcare utilization**, alongside chronic conditions associated with higher healthcare needs.

Feature importance indicates model reliance and does not establish causal relationships.

## Business Impact Scenario

The model can be translated into a hypothetical intervention scenario.

Using the final cohort and model results:

* Approximately **11,715** beneficiaries experience an inpatient admission in 2010.
* Targeting the top 10% captures approximately **2,588** of these admissions.
* Assuming an illustrative **15% intervention effectiveness**, approximately **388 admissions could potentially be avoided**.
* The average 2010 inpatient payment is approximately **$9,786**.
* This corresponds to approximately **$3.8 million in potential avoided inpatient costs**.

### Important Assumption

The 15% intervention-effectiveness rate is an **illustrative scenario assumption**. It is not estimated from the CMS data and the project does not claim that $3.8 million in savings was actually achieved.

The estimate is intended to demonstrate how a predictive risk-ranking model could be connected to operational and financial decision-making.

## Project Structure

```text
healthcare-risk-project/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
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
├── requirements.txt
└── .gitignore
```

## Reproducibility

1. Download the CMS DE-SynPUF Sample 1 files.
2. Place the raw files in `data/raw/`.
3. Run the data-loading script to create the SQLite database.
4. Run `train_mvp_v3.py` to reproduce the final model and evaluation metrics.
5. Run `avg_cost.py` to calculate the average 2010 inpatient payment.

The raw and processed datasets are intentionally excluded from version control due to file size and data-distribution considerations.

## Key Takeaway

This project demonstrates an end-to-end healthcare predictive analytics workflow:

**Claims Data → SQL Feature Engineering → Risk Modeling → Risk Ranking → Targeted Intervention → Business Impact**

Rather than optimizing only for a classification threshold, the project frames the model as a **resource-allocation tool**: identify the highest-risk beneficiaries, prioritize a constrained intervention population, and estimate the potential operational and financial impact.
