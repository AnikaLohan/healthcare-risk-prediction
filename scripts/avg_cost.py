import sqlite3
import pandas as pd

conn = sqlite3.connect("data/processed/claims.db")
query = """
SELECT AVG(CLM_PMT_AMT) AS avg_cost
FROM inpatient_claims
WHERE CAST(substr(CLM_ADMSN_DT, 1, 4) AS INTEGER) = 2010
"""
df = pd.read_sql(query, conn)
print(df)
conn.close()