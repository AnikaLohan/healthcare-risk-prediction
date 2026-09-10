# Data Setup

This project uses the CMS 2008–2010 DE-SynPUF (Data Entrepreneurs' Synthetic Public Use File).

## Download
1. Go to: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf
2. Pick **one sample** (e.g. "Sample 1") — you don't need all 20.
3. Download all files listed for that sample:
   - Beneficiary Summary File (2008, 2009, 2010) — 3 files
   - Inpatient Claims (ZIP)
   - Outpatient Claims (ZIP)
   - Carrier Claims 1 and 2
   - Prescription Drug Events (PDE)
4. Unzip everything and place the raw CSVs in `data/raw/`.

## Notes
- File names and column layouts are documented in CMS's SynPUF User Guide (linked on the
  download page) — keep it handy, you'll need it to know what each column means.
- These files are synthetic (not real patient data) but structured like real Medicare claims,
  so column names and logic transfer directly to real actuarial/health-analytics work.
- Do not commit these files to git — `data/raw/` and `data/processed/` are gitignored.
