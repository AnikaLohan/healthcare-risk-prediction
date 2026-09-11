import pandas as pd
import sqlite3
import glob
import os

RAW_DIR = "data/raw"
DB_PATH = "data/processed/claims.db"

FILE_TABLE_MAP = {
    "*2008*Beneficiary_Summary*.zip": "beneficiary_2008",
    "*2009*Beneficiary_Summary*.zip": "beneficiary_2009",
    "*2010*Beneficiary_Summary*.zip": "beneficiary_2010",
    "*Inpatient_Claims*.zip": "inpatient_claims",
    "*Outpatient_Claims*.zip": "outpatient_claims",
    "*Carrier_Claims*A.zip": "carrier_claims_a",
    "*Carrier_Claims*B.zip": "carrier_claims_b",
    "*Prescription_Drug*.zip": "pde_claims",
}

def main():
    os.makedirs("data/processed", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    for pattern, table_name in FILE_TABLE_MAP.items():
        matches = glob.glob(os.path.join(RAW_DIR, pattern))
        if not matches:
            print(f"WARNING: no file found matching '{pattern}' - check filenames in data/raw")
            continue
        zip_path = matches[0]
        print(f"Reading {zip_path} ...")
        # pandas reads directly from the zip - no manual extraction needed
        df = pd.read_csv(zip_path, compression="zip")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded {table_name}: {len(df):,} rows")

    conn.close()
    print(f"\nDone. Database created at {DB_PATH}")

if __name__ == "__main__":
    main()