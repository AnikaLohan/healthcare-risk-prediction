import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import xgboost as xgb

DB_PATH = "data/processed/claims.db"
conn = sqlite3.connect(DB_PATH)

# --- 1. TARGET: inpatient admission in 2010 ---
target_query = """
SELECT DISTINCT DESYNPUF_ID, 1 AS had_2010_admission
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) = 2010
"""
target_df = pd.read_sql(target_query, conn)

# --- 2. FEATURES: prior inpatient utilization (2008-2009) ---
prior_util_query = """
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_admit_count,
       SUM(CLM_PMT_AMT) AS prior_inpatient_reimb
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) IN (2008, 2009)
GROUP BY DESYNPUF_ID
"""
prior_util_df = pd.read_sql(prior_util_query, conn)

# --- 3. NEW: prior outpatient utilization (2008-2009) ---
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

# --- 4. NEW: prior carrier (doctor visit) utilization (2008-2009) ---
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

# --- 5. Demographics + chronic conditions (2009 beneficiary file) ---
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

# --- 6. Join everything together ---
data = demo_df.merge(prior_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(outp_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(carrier_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(target_df, on="DESYNPUF_ID", how="left")

fill_zero_cols = ["prior_admit_count", "prior_inpatient_reimb",
                   "prior_outp_visit_count", "prior_outp_reimb", "prior_outp_distinct_providers",
                   "prior_carrier_claim_count", "prior_carrier_reimb"]
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
                  "prior_carrier_claim_count", "prior_carrier_reimb"])

X = data[feature_cols]
y = data["had_2010_admission"]

print(f"Dataset shape: {X.shape}  (was 15 features before, now {len(feature_cols)})")
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
auc = roc_auc_score(y_test, y_pred_proba)
print(f"\nAUC on test set: {auc:.3f}  (was 0.690 with beneficiary+inpatient only)")

importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\nTop features:")
print(importance.head(12))

conn.close()