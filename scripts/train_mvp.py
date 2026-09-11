import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import xgboost as xgb

DB_PATH = "data/processed/claims.db"

conn = sqlite3.connect(DB_PATH)

# --- 1. TARGET: did this beneficiary have an inpatient admission in 2010? ---
target_query = """
SELECT DISTINCT DESYNPUF_ID, 1 AS had_2010_admission
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) = 2010
"""
target_df = pd.read_sql(target_query, conn)

# --- 2. FEATURES: prior utilization (2008-2009 only, to avoid leakage) ---
prior_util_query = """
SELECT DESYNPUF_ID,
       COUNT(*) AS prior_admit_count,
       SUM(CLM_PMT_AMT) AS prior_inpatient_reimb
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) IN (2008, 2009)
GROUP BY DESYNPUF_ID
"""
prior_util_df = pd.read_sql(prior_util_query, conn)

# --- 3. FEATURES: demographics + chronic conditions from the 2009 beneficiary file ---
demo_query = """
SELECT DESYNPUF_ID,
       BENE_BIRTH_DT,
       BENE_SEX_IDENT_CD,
       SP_ALZHDMTA, SP_CHF, SP_CHRNKIDN, SP_CNCR, SP_COPD,
       SP_DEPRESSN, SP_DIABETES, SP_ISCHMCHT, SP_OSTEOPRS,
       SP_RA_OA, SP_STRKETIA
FROM beneficiary_2009
"""
demo_df = pd.read_sql(demo_query, conn)

demo_df["birth_year"] = demo_df["BENE_BIRTH_DT"].astype(str).str[:4].astype(int)
demo_df["age_2009"] = 2009 - demo_df["birth_year"]

# --- 4. Join everything into one beneficiary-level dataset ---
data = demo_df.merge(prior_util_df, on="DESYNPUF_ID", how="left")
data = data.merge(target_df, on="DESYNPUF_ID", how="left")

data["prior_admit_count"] = data["prior_admit_count"].fillna(0)
data["prior_inpatient_reimb"] = data["prior_inpatient_reimb"].fillna(0)
data["had_2010_admission"] = data["had_2010_admission"].fillna(0).astype(int)

chronic_cols = ["SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
                 "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
                 "SP_RA_OA", "SP_STRKETIA"]
for col in chronic_cols:
    data[col] = (data[col] == 1).astype(int)

feature_cols = ["age_2009", "BENE_SEX_IDENT_CD", "prior_admit_count",
                 "prior_inpatient_reimb"] + chronic_cols

X = data[feature_cols]
y = data["had_2010_admission"]

print(f"Dataset shape: {X.shape}")
print(f"Positive rate (had 2010 admission): {y.mean():.3%}")

# --- 5. Train/test split and model ---
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

print(f"\nAUC on test set: {auc:.3f}")

importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\nTop features:")
print(importance.head(10))

conn.close()