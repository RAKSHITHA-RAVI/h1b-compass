"""
H1B Compass Data Loading & Cleaning Pipeline
Loads 3 LCA disclosure files, cleans, filters, and normalizes wages
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


def _normalize_wage(wage_amount, wage_unit):
    """Convert any wage unit to annual salary."""
    if pd.isna(wage_amount) or wage_amount == 0:
        return np.nan

    wage_unit_str = str(wage_unit).strip().upper() if pd.notna(wage_unit) else ''

    if 'YEAR' in wage_unit_str or 'ANNUAL' in wage_unit_str:
        return wage_amount
    elif 'MONTH' in wage_unit_str:
        return wage_amount * 12
    elif 'BI' in wage_unit_str:  # Bi-weekly
        return wage_amount * 26
    elif 'WEEK' in wage_unit_str:
        return wage_amount * 52
    elif 'HOUR' in wage_unit_str:
        return wage_amount * 40 * 52  # 40 hrs/week, 52 weeks/year
    else:
        return wage_amount  # Default to as-is


# Setup paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'results'
OUTPUT_DIR.mkdir(exist_ok=True)

# Excel files to load (in chronological order)
FILES = [
    'LCA_Disclosure_Data_FY2024_Q4.xlsx',
    'LCA_Disclosure_Data_FY2025_Q4.xlsx',
    'LCA_Dislclosure_Data_FY2026_Q2.xlsx',  # Note: typo in filename
]

# Columns to keep
KEEP_COLS = [
    'EMPLOYER_NAME', 'EMPLOYER_STATE', 'EMPLOYER_CITY',
    'CASE_STATUS', 'JOB_TITLE', 'SOC_TITLE',
    'WAGE_RATE_OF_PAY_FROM', 'WAGE_UNIT_OF_PAY', 'PREVAILING_WAGE',
    'PW_WAGE_LEVEL', 'TOTAL_WORKER_POSITIONS', 'NAICS_CODE',
    'VISA_CLASS', 'RECEIVED_DATE', 'DECISION_DATE'
]

print("=" * 80)
print("H1B COMPASS DATA PIPELINE - LOAD & CLEAN")
print("=" * 80)

# Load and stack all files
dfs = []
for file in FILES:
    file_path = DATA_DIR / file
    print(f"\nLoading {file}...", end=" ")
    df = pd.read_excel(file_path)
    print(f"[OK] {len(df):,} rows")
    dfs.append(df)

# Stack all dataframes
print("\nStacking dataframes...", end=" ")
df = pd.concat(dfs, ignore_index=True)
print(f"[OK] Total: {len(df):,} rows, {len(df.columns)} columns")

# Filter to H-1B only
print(f"\nFiltering to H-1B visa class...", end=" ")
initial_rows = len(df)
df = df[df['VISA_CLASS'] == 'H-1B'].copy()
print(f"[OK] {initial_rows:,} -> {len(df):,} rows ({100*len(df)/initial_rows:.1f}%)")

# Keep only required columns
print(f"\nSelecting {len(KEEP_COLS)} columns...", end=" ")
df = df[KEEP_COLS].copy()
print("[OK]")

# Normalize wages to annual salary
print(f"\nNormalizing wages to annual salary...", end=" ")
df['ANNUAL_SALARY'] = df.apply(lambda row: _normalize_wage(
    row['WAGE_RATE_OF_PAY_FROM'],
    row['WAGE_UNIT_OF_PAY']
), axis=1)
print("[OK]")

# Normalize prevailing wage to annual
print(f"Normalizing prevailing wage to annual...", end=" ")
df['PREVAILING_WAGE_ANNUAL'] = df.apply(lambda row: _normalize_wage(
    row['PREVAILING_WAGE'],
    row['WAGE_UNIT_OF_PAY']
), axis=1)
print("[OK]")

# Create CERTIFIED column
print(f"Creating CERTIFIED column...", end=" ")
df['CERTIFIED'] = (df['CASE_STATUS'] == 'Certified').astype(int)
print("[OK]")

# Convert dates
print(f"Converting date columns...", end=" ")
df['RECEIVED_DATE'] = pd.to_datetime(df['RECEIVED_DATE'], errors='coerce')
df['DECISION_DATE'] = pd.to_datetime(df['DECISION_DATE'], errors='coerce')
print("[OK]")

# Extract year from RECEIVED_DATE
print(f"Extracting fiscal year...", end=" ")
df['FISCAL_YEAR'] = df['RECEIVED_DATE'].dt.year
print("[OK]")

# Clean numeric columns
print(f"Cleaning numeric columns...", end=" ")
df['TOTAL_WORKER_POSITIONS'] = pd.to_numeric(df['TOTAL_WORKER_POSITIONS'], errors='coerce')
df['NAICS_CODE'] = df['NAICS_CODE'].astype(str).str.strip()
print("[OK]")

# Reorder columns logically
final_cols = [
    'EMPLOYER_NAME', 'EMPLOYER_STATE', 'EMPLOYER_CITY', 'NAICS_CODE',
    'JOB_TITLE', 'SOC_TITLE',
    'WAGE_RATE_OF_PAY_FROM', 'WAGE_UNIT_OF_PAY', 'ANNUAL_SALARY',
    'PREVAILING_WAGE', 'PREVAILING_WAGE_ANNUAL', 'PW_WAGE_LEVEL',
    'TOTAL_WORKER_POSITIONS',
    'CASE_STATUS', 'CERTIFIED',
    'VISA_CLASS', 'RECEIVED_DATE', 'DECISION_DATE', 'FISCAL_YEAR'
]
df = df[final_cols]

# Save cleaned data
output_file = OUTPUT_DIR / 'h1b_cleaned.csv'
print(f"\nSaving cleaned data to {output_file.name}...", end=" ")
df.to_csv(output_file, index=False)
print("[OK]")

# Print summary stats
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"\nTotal Records: {len(df):,}")
print(f"Fiscal Years: {sorted(df['FISCAL_YEAR'].dropna().unique().astype(int))}")
print(f"Date Range: {df['RECEIVED_DATE'].min().date()} to {df['RECEIVED_DATE'].max().date()}")

print(f"\nCASE STATUS Distribution:")
for status, count in df['CASE_STATUS'].value_counts().items():
    pct = 100 * count / len(df)
    print(f"  {status:<30} {count:>10,}  ({pct:>5.1f}%)")

print(f"\nAPPROVAL RATE: {df['CERTIFIED'].mean()*100:.2f}%")

print(f"\nWAGE STATISTICS (Annual Salary):")
print(f"  Mean:      ${df['ANNUAL_SALARY'].mean():>15,.0f}")
print(f"  Median:    ${df['ANNUAL_SALARY'].median():>15,.0f}")
print(f"  Min:       ${df['ANNUAL_SALARY'].min():>15,.0f}")
print(f"  Max:       ${df['ANNUAL_SALARY'].max():>15,.0f}")

print(f"\nPREVAILING WAGE STATISTICS (Annual):")
print(f"  Mean:      ${df['PREVAILING_WAGE_ANNUAL'].mean():>15,.0f}")
print(f"  Median:    ${df['PREVAILING_WAGE_ANNUAL'].median():>15,.0f}")

print(f"\nTOP 10 EMPLOYERS:")
for idx, (name, count) in enumerate(df['EMPLOYER_NAME'].value_counts().head(10).items(), 1):
    print(f"  {idx:2}. {name:<50} {count:>6,}")

print(f"\nTOP 10 JOB TITLES:")
for idx, (title, count) in enumerate(df['JOB_TITLE'].value_counts().head(10).items(), 1):
    print(f"  {idx:2}. {title:<50} {count:>6,}")

print(f"\nPREVAILING WAGE LEVELS:")
for level, count in sorted(df['PW_WAGE_LEVEL'].dropna().value_counts().items()):
    pct = 100 * count / df['PW_WAGE_LEVEL'].notna().sum()
    print(f"  Level {level:<3} {count:>10,}  ({pct:>5.1f}%)")

print(f"\nTOP 10 STATES:")
for idx, (state, count) in enumerate(df['EMPLOYER_STATE'].value_counts().head(10).items(), 1):
    print(f"  {idx:2}. {state:<2} {count:>10,}")

print("\n[DONE] Pipeline complete!")
