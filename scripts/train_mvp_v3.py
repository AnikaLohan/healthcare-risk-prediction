import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score
import xgboost as xgb

DB_PATH = "data/processed/claims.db"
conn = sqlite3.connect(DB_PATH)

target_query = """
SELECT DISTINCT DESYNPUF_ID, 1 AS had_2010_admission
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) = 2010
"""
target_df = pd.read_sql(target_query, conn)

prior_util_query = """
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_admit_count,
       SUM(CLM_PMT_AMT) AS prior_inpatient_reimb
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) IN (2008, 2009)
GROUP BY DESYNPUF_ID
"""
prior_util_df = pd.read_sql(prior_util_query, conn)

outp_util_query = """
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_outp_visit_count,
       SUM(CLM_PMT_AMT) AS prior_outp_reimb,
       COUNT(DISTINCT PRVDR_NUM) AS prior_outp_distinct_providers
FROM outpatient_claims
WHERE CAST(substr(CLM_FROM_DT, 1, 4) AS INTEGER) IN (2008, 2009)
GROUP BY DESYNPUF_ID
"""
outp_util_df = pd.read_sql(outp_util_query, conn)

line_amt_cols = [f"LINE_NCH_PMT_AMT_{i}" for i in range(1, 14)]
sum_expr = " + ".join(f"COALESCE({c}, 0)" for c in line_amt_cols)
carrier_util_query = f"""
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_carrier_claim_count,
       SUM({sum_expr}) AS prior_carrier_reimb
FROM (
    SELECT * FROM carrier_claims_a
    WHERE CAST(substr(CLM_FROM_DT, 1, 4) AS INTEGER) IN (2008, 2009)
    UNION ALL
    SELECT * FROM carrier_claims_b
    WHERE CAST(substr(CLM_FROM_DT, 1, 4) AS INTEGER) IN (2008, 2009)
)
GROUP BY DESYNPUF_ID
"""
carrier_util_df = pd.read_sql(carrier_util_query, conn)

# --- NEW: Prescription Drug Events (2008-2009) ---
pde_util_query = """
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_rx_fill_count,
       COUNT(DISTINCT PROD_SRVC_ID) AS prior_distinct_drugs,
       SUM(TOT_RX_CST_AMT) AS prior_rx_cost
FROM pde_claims
WHERE CAST(substr(SRVC_DT, 1, 4) AS INTEGER) IN (2008, 2009)
GROUP BY DESYNPUF_ID
"""
pde_util_df = pd.read_sql(pde_util_query, conn)

demo_query = """
SELECT DESYNPUF_ID, BENE_BIRTH_DT, BENE_SEX_IDENT_CD,
       SP_ALZHDMTA, SP_CHF, SP_CHRNKIDN, SP_CNCR, SP_COPD,
       SP_DEPRESSN, SP_DIABETES, SP_ISCHMCHT, SP_OSTEOPRS,
       SP_RA_OA, SP_STRKETIA
FROM beneficiary_2009
"""
demo_df = pd.read_sql(demo_query, conn)
demo_df["birth_year"] = demo_df["BENE_BIRTH_DT"].astype(str).str[:4].astype(int)
demo_df["age_2009"] = 2009 - demo_df["birth_year"]

data = demo_df.merge(prior_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(outp_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(carrier_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(pde_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(target_df, on="DESYNPUF_ID", how="left")

fill_zero_cols = ["prior_admit_count", "prior_inpatient_reimb",
                   "prior_outp_visit_count", "prior_outp_reimb", "prior_outp_distinct_providers",
                   "prior_carrier_claim_count", "prior_carrier_reimb",
                   "prior_rx_fill_count", "prior_distinct_drugs", "prior_rx_cost"]
for col in fill_zero_cols:
    data[col] = data[col].fillna(0)
data["had_2010_admission"] = data["had_2010_admission"].fillna(0).astype(int)

chronic_cols = ["SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
                 "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
                 "SP_RA_OA", "SP_STRKETIA"]
for col in chronic_cols:
    data[col] = (data[col] == 1).astype(int)

feature_cols = (["age_2009", "BENE_SEX_IDENT_CD"] + chronic_cols +
                 ["prior_admit_count", "prior_inpatient_reimb",
                  "prior_outp_visit_count", "prior_outp_reimb", "prior_outp_distinct_providers",
                  "prior_carrier_claim_count", "prior_carrier_reimb",
                  "prior_rx_fill_count", "prior_distinct_drugs", "prior_rx_cost"])

X = data[feature_cols]
y = data["had_2010_admission"]

print(f"Dataset shape: {X.shape}  ({len(feature_cols)} features, across 5 claim tables)")
print(f"Positive rate: {y.mean():.3%}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = xgb.XGBClassifier(
    n_estimators=100, max_depth=4, learning_rate=0.1,
    eval_metric="auc", random_state=42
)
model.fit(X_train, y_train)

y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred = (y_pred_proba >= 0.5).astype(int)

auc = roc_auc_score(y_test, y_pred_proba)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)

print(f"\nAUC on test set: {auc:.3f}")
print(f"Precision: {precision:.3f}  (of flagged high-risk members, how many actually were)")
print(f"Recall: {recall:.3f}  (of all true high-risk members, how many we caught)")

importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\nTop features:")
print(importance.head(15))

# Instead of a fixed 0.5 threshold, flag the top 10% highest-risk members -
# this reflects how it would actually be used (limited intervention capacity)
threshold = pd.Series(y_pred_proba).quantile(0.90)
y_pred_top10 = (y_pred_proba >= threshold).astype(int)

precision_top10 = precision_score(y_test, y_pred_top10)
recall_top10 = recall_score(y_test, y_pred_top10)

print(f"\n--- Flagging top 10% highest-risk members instead ---")
print(f"Precision: {precision_top10:.3f}")
print(f"Recall: {recall_top10:.3f}  (of true high-risk members caught by flagging only the top 10%)")

conn.close()