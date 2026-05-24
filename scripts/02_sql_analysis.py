"""
H1B Compass SQL Analysis - 5 Key Questions
Uses pandas for analysis (foundation for future Snowflake migration)
"""
import pandas as pd
from pathlib import Path

# Setup paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# Load cleaned data
input_file = RESULTS_DIR / 'h1b_cleaned.csv'
print("=" * 80)
print("H1B COMPASS - ANALYSIS PIPELINE")
print("=" * 80)

print(f"\nLoading cleaned data from {input_file.name}...", end=" ")
df = pd.read_csv(input_file)
df['RECEIVED_DATE'] = pd.to_datetime(df['RECEIVED_DATE'])
print(f"[OK] {len(df):,} rows")

# ============================================================================
# QUESTION 1: Top 20 employers sponsoring Data Analyst roles by approval rate
# ============================================================================
print("\n" + "-" * 80)
print("Q1: TOP 20 EMPLOYERS FOR DATA ANALYST ROLES (BY APPROVAL RATE)")
print("-" * 80)

da_data = df[df['JOB_TITLE'].str.contains('Data Analyst', case=False, na=False)].copy()
print(f"Found {len(da_data):,} Data Analyst positions\n")

q1 = da_data.groupby('EMPLOYER_NAME').agg({
    'CERTIFIED': ['sum', 'count']
}).reset_index()
q1.columns = ['EMPLOYER_NAME', 'APPROVED', 'TOTAL_APPLICATIONS']
q1['APPROVAL_RATE'] = (q1['APPROVED'] / q1['TOTAL_APPLICATIONS'] * 100).round(2)
q1 = q1.sort_values('TOTAL_APPLICATIONS', ascending=False)
q1 = q1[q1['TOTAL_APPLICATIONS'] >= 5].head(20)  # Min 5 applications
q1 = q1.reset_index(drop=True)
q1.index = q1.index + 1

output_q1 = RESULTS_DIR / 'q1_data_analyst_employers.csv'
q1.to_csv(output_q1)
print(q1.to_string())
print(f"\n[OK] Saved to {output_q1.name}")

# ============================================================================
# QUESTION 2: Average salary offered vs prevailing wage by state
# ============================================================================
print("\n" + "-" * 80)
print("Q2: SALARY OFFERED VS PREVAILING WAGE BY STATE")
print("-" * 80)

q2 = df.groupby('EMPLOYER_STATE').agg({
    'ANNUAL_SALARY': ['mean', 'median', 'count'],
    'PREVAILING_WAGE_ANNUAL': ['mean', 'median']
}).reset_index()
q2.columns = ['STATE', 'OFFERED_SALARY_MEAN', 'OFFERED_SALARY_MEDIAN',
              'APPLICATION_COUNT', 'PREVAILING_WAGE_MEAN', 'PREVAILING_WAGE_MEDIAN']
q2['SALARY_DIFF'] = (q2['OFFERED_SALARY_MEAN'] - q2['PREVAILING_WAGE_MEAN']).round(0)
q2['SALARY_DIFF_PCT'] = ((q2['OFFERED_SALARY_MEAN'] / q2['PREVAILING_WAGE_MEAN'] - 1) * 100).round(2)

# Round currency columns
for col in ['OFFERED_SALARY_MEAN', 'OFFERED_SALARY_MEDIAN',
            'PREVAILING_WAGE_MEAN', 'PREVAILING_WAGE_MEDIAN', 'SALARY_DIFF']:
    q2[col] = q2[col].round(0)

q2 = q2.sort_values('APPLICATION_COUNT', ascending=False)
q2 = q2.reset_index(drop=True)
q2.index = q2.index + 1

output_q2 = RESULTS_DIR / 'q2_salary_by_state.csv'
q2.to_csv(output_q2, index=True)
print(q2.to_string())
print(f"\n[OK] Saved to {output_q2.name}")

# ============================================================================
# QUESTION 3: Year-over-year sponsorship trend by top employers
# ============================================================================
print("\n" + "-" * 80)
print("Q3: YEAR-OVER-YEAR SPONSORSHIP TREND (TOP 10 EMPLOYERS)")
print("-" * 80)

# Get top 10 employers overall
top_employers = df['EMPLOYER_NAME'].value_counts().head(10).index.tolist()

q3_data = df[df['EMPLOYER_NAME'].isin(top_employers)].copy()
q3 = q3_data.groupby(['FISCAL_YEAR', 'EMPLOYER_NAME']).size().reset_index(name='SPONSORSHIPS')
q3 = q3.sort_values(['EMPLOYER_NAME', 'FISCAL_YEAR'])

output_q3 = RESULTS_DIR / 'q3_yoy_trend.csv'
q3.to_csv(output_q3, index=False)
print("Top 10 employers - sponsorships by year:\n")
for employer in top_employers:
    emp_data = q3[q3['EMPLOYER_NAME'] == employer].sort_values('FISCAL_YEAR')
    years = emp_data['FISCAL_YEAR'].values
    counts = emp_data['SPONSORSHIPS'].values
    trend = " -> ".join([f"FY{int(y)}: {c:,}" for y, c in zip(years, counts)])
    print(f"  {employer:<50} {trend}")
print(f"\n[OK] Saved to {output_q3.name}")

# ============================================================================
# QUESTION 4: Cities with highest H1B volume
# ============================================================================
print("\n" + "-" * 80)
print("Q4: CITIES WITH HIGHEST H1B VOLUME")
print("-" * 80)

q4 = df.groupby(['EMPLOYER_CITY', 'EMPLOYER_STATE']).agg({
    'EMPLOYER_NAME': 'count',
    'CERTIFIED': 'sum'
}).reset_index()
q4.columns = ['CITY', 'STATE', 'TOTAL_APPLICATIONS', 'APPROVED']
q4['APPROVAL_RATE'] = (q4['APPROVED'] / q4['TOTAL_APPLICATIONS'] * 100).round(2)
q4['CITY_STATE'] = q4['CITY'] + ', ' + q4['STATE']
q4 = q4.sort_values('TOTAL_APPLICATIONS', ascending=False).head(30)
q4 = q4[['CITY_STATE', 'STATE', 'TOTAL_APPLICATIONS', 'APPROVED', 'APPROVAL_RATE']]
q4 = q4.reset_index(drop=True)
q4.index = q4.index + 1

output_q4 = RESULTS_DIR / 'q4_cities_by_volume.csv'
q4.to_csv(output_q4, index=True)
print(q4.to_string())
print(f"\n[OK] Saved to {output_q4.name}")

# ============================================================================
# QUESTION 5: Denial rate by wage level (I, II, III, IV)
# ============================================================================
print("\n" + "-" * 80)
print("Q5: DENIAL RATE BY PREVAILING WAGE LEVEL")
print("-" * 80)

q5 = df[df['PW_WAGE_LEVEL'].notna()].copy()
q5_agg = q5.groupby('PW_WAGE_LEVEL').agg({
    'CERTIFIED': 'sum',
    'EMPLOYER_NAME': 'count'
}).reset_index()
q5_agg.columns = ['WAGE_LEVEL', 'APPROVED', 'TOTAL_APPLICATIONS']
q5_agg['DENIED'] = q5_agg['TOTAL_APPLICATIONS'] - q5_agg['APPROVED']
q5_agg['APPROVAL_RATE'] = (q5_agg['APPROVED'] / q5_agg['TOTAL_APPLICATIONS'] * 100).round(2)
q5_agg['DENIAL_RATE'] = (q5_agg['DENIED'] / q5_agg['TOTAL_APPLICATIONS'] * 100).round(2)
q5_agg = q5_agg.sort_values('WAGE_LEVEL')
q5_agg = q5_agg.reset_index(drop=True)
q5_agg.index = q5_agg.index + 1

output_q5 = RESULTS_DIR / 'q5_denial_rate_by_wage_level.csv'
q5_agg.to_csv(output_q5, index=True)
print(q5_agg.to_string())
print(f"\n[OK] Saved to {output_q5.name}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"\n5 analyses saved to {RESULTS_DIR.name}/:")
print(f"  1. q1_data_analyst_employers.csv")
print(f"  2. q2_salary_by_state.csv")
print(f"  3. q3_yoy_trend.csv")
print(f"  4. q4_cities_by_volume.csv")
print(f"  5. q5_denial_rate_by_wage_level.csv")
print(f"\nPlus cleaned data:")
print(f"  • h1b_cleaned.csv ({len(df):,} rows)")
