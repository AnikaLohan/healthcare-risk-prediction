-- Step 1: Load raw CSVs into SQLite and sanity-check them.
-- Run this via the sqlite3 CLI, or load these tables from Python with pandas.to_sql().
--
-- Example (from terminal, after downloading + unzipping into data/raw/):
--   sqlite3 data/processed/claims.db
--   .mode csv
--   .import data/raw/DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv beneficiary_2008
--   .import data/raw/DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv inpatient_claims
--   .import data/raw/DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv outpatient_claims

-- Sanity check: row counts per table
SELECT 'beneficiary_2008' AS table_name, COUNT(*) AS row_count FROM beneficiary_2008
UNION ALL
SELECT 'inpatient_claims', COUNT(*) FROM inpatient_claims
UNION ALL
SELECT 'outpatient_claims', COUNT(*) FROM outpatient_claims;

-- Peek at the beneficiary table structure (demographics + chronic condition flags)
SELECT *
FROM beneficiary_2008
LIMIT 10;
