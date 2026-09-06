# CREDIT_RISK_DATASET.md
### UCI Default of Credit Card Clients — verified from the OFFICIAL UCI page (16 Aug 2026)
### Source of these fields: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients (fetched via the allowed web tool, not scraped)

| Field | Value |
|---|---|
| Dataset ID | UCI **350** |
| Official title | Default of Credit Card Clients |
| Creator | I-Cheng Yeh |
| Donated | 2016-01-25 |
| DOI | **10.24432/C55S3H** |
| Introductory paper | Yeh & Lien (2009), *Expert Systems with Applications* |
| License | **Creative Commons Attribution 4.0 International (CC BY 4.0)** — sharing/adaptation for any purpose with attribution |
| Instances | **30,000** |
| Features | **23** |
| Missing values | **None** (per official page) |
| Task | Binary classification |
| Target | `default payment next month` (Yes = 1, No = 0) |
| File offered | `default of credit card clients.xls` (5.3 MB, Excel 97-2003) |
| Official download | `https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip` |

## Feature list (authoritative)
- `LIMIT_BAL` (X1) — amount of given credit (NT$)
- `SEX` (X2), `EDUCATION` (X3), `MARRIAGE` (X4), `AGE` (X5) — demographics
- `PAY_0, PAY_2..PAY_6` (X6–X11) — **repayment status, 6 monthly periods Apr–Sep 2005** (−1 = pay duly … 9 = 9+ months late)
- `BILL_AMT1..6` (X12–X17) — bill statement amounts, 6 months
- `PAY_AMT1..6` (X18–X23) — previous payment amounts, 6 months

**Native repeated measures: exactly 6 months.** This is the single most important constraint and drives the temporal design (see `SCENARIO_SHIFT_DESIGN.md`): we do NOT claim 40 real time periods.

## Required attribution / citation (CC BY 4.0)
> Yeh, I. (2009). *Default of Credit Card Clients* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H

Also cite the introductory paper: Yeh & Lien (2009), *Expert Systems with Applications*.

## Download & hashing — **cannot be done in this build environment**
The research sandbox blocks outbound file download (proxy returns 403 on the archive host). Per project rules I did **not** work around this with bash/urllib. Therefore:

- **SHA-256 is not recorded here** — it must be computed on your machine after download.
- The raw dataset is **NOT committed** to the repository (CC BY 4.0 permits redistribution with attribution, but we keep the repo data-free and reproducible-by-download, which is cleaner and avoids shipping a 5.3 MB binary).

**Exact local procedure ($0, no account):**
```bash
cd data/raw
curl -L -o credit.zip "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
unzip credit.zip                 # -> "default of credit card clients.xls"
# export the single sheet to CSV (LibreOffice example):
libreoffice --headless --convert-to csv "default of credit card clients.xls"
mv "default of credit card clients.csv" credit_default.csv
sha256sum credit_default.csv     # record this hash in this file
```
The scenario adapter expects `data/raw/credit_default.csv` (header row of column names, one row per client). Until it is present, the adapter runs only in documented **parameterised-substrate** mode (clearly labelled, not a real-data result).

## Ethics / privacy
De-identified aggregate credit records from a 2016 public research donation; no direct identifiers. Credit scoring is a sensitive domain: framing must avoid implying a deployable scoring system. The scenario uses the data only as an empirical substrate for a controlled feedback study.
