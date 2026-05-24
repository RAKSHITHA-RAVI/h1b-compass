"""
H1B Compass - Adzuna Job API Integration
Searches for job listings and cross-references with H1B sponsors
"""
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')

if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
    raise ValueError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env file")

# Setup paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# Job titles to search
JOB_TITLES = [
    "Data Analyst",
    "Business Analyst",
    "Business Intelligence Analyst"
]

print("=" * 80)
print("H1B COMPASS - ADZUNA JOB API INTEGRATION")
print("=" * 80)

# ============================================================================
# STEP 1: Fetch live job listings from Adzuna
# ============================================================================
print("\n[STEP 1] Fetching live job listings from Adzuna API...")

all_jobs = []
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

for title in JOB_TITLES:
    print(f"\n  Searching for '{title}'...", end=" ")

    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'what': title,
        'where': 'United States',
        'results_per_page': 50,
        'full_time': 1
    }

    try:
        response = requests.get(ADZUNA_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = data.get('results', [])
        print(f"[OK] Found {len(jobs)} jobs")

        for job in jobs:
            all_jobs.append({
                'title': job.get('title'),
                'company': job.get('company', {}).get('display_name'),
                'location': job.get('location', {}).get('display_name'),
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
                'description': job.get('description'),
                'posted_date': job.get('created'),
                'job_url': job.get('redirect_url'),
                'search_title': title
            })

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {str(e)}")
        continue

live_jobs_df = pd.DataFrame(all_jobs)
print(f"\nTotal jobs found: {len(live_jobs_df):,}")

# Save raw results
live_jobs_file = DATA_DIR / 'live_jobs.csv'
live_jobs_df.to_csv(live_jobs_file, index=False)
print(f"[OK] Saved to {live_jobs_file.name}")

# ============================================================================
# STEP 2: Load H1B cleaned data
# ============================================================================
print("\n[STEP 2] Loading H1B sponsor data...")

h1b_file = RESULTS_DIR / 'h1b_cleaned.csv'
h1b_df = pd.read_csv(h1b_file)
print(f"[OK] Loaded {len(h1b_df):,} H1B records")

# Get unique H1B sponsors
h1b_sponsors = set(h1b_df['EMPLOYER_NAME'].str.strip().str.upper().unique())
print(f"[OK] Identified {len(h1b_sponsors):,} unique H1B sponsors")

# ============================================================================
# STEP 3: Cross-reference live jobs with H1B sponsors
# ============================================================================
print("\n[STEP 3] Cross-referencing live jobs with H1B sponsors...")

def find_h1b_match(company_name, h1b_sponsors):
    """Check if a company is in H1B sponsors (fuzzy matching)."""
    if pd.isna(company_name):
        return None, 0.0

    company_clean = company_name.strip().upper()

    # Exact match
    if company_clean in h1b_sponsors:
        return company_clean, 1.0

    # Partial match (company name contains sponsor or vice versa)
    for sponsor in h1b_sponsors:
        if company_clean in sponsor or sponsor in company_clean:
            # Calculate similarity
            if len(company_clean) > 0 and len(sponsor) > 0:
                overlap = len(set(company_clean) & set(sponsor))
                max_len = max(len(company_clean), len(sponsor))
                similarity = overlap / max_len
                if similarity > 0.6:  # Threshold for fuzzy match
                    return sponsor, similarity

    return None, 0.0

# Add H1B match column
live_jobs_df['H1B_SPONSOR_MATCH'] = live_jobs_df['company'].apply(
    lambda x: find_h1b_match(x, h1b_sponsors)[0]
)
live_jobs_df['MATCH_CONFIDENCE'] = live_jobs_df['company'].apply(
    lambda x: find_h1b_match(x, h1b_sponsors)[1]
)

# Filter to H1B sponsors only
h1b_sponsors_hiring = live_jobs_df[live_jobs_df['H1B_SPONSOR_MATCH'].notna()].copy()
print(f"[OK] Found {len(h1b_sponsors_hiring)} jobs from H1B sponsors")

# Add H1B stats to matched records
def get_h1b_stats(sponsor_name, h1b_df):
    """Get H1B stats for a sponsor."""
    if pd.isna(sponsor_name):
        return None, None, None

    # Find matching records in H1B data
    matching = h1b_df[h1b_df['EMPLOYER_NAME'].str.strip().str.upper() == sponsor_name.upper()]

    if len(matching) == 0:
        return None, None, None

    total = len(matching)
    approved = matching['CERTIFIED'].sum()
    approval_rate = (approved / total * 100) if total > 0 else 0

    return total, approved, approval_rate

# Add H1B stats columns
h1b_sponsors_hiring[['H1B_TOTAL_APPLICATIONS', 'H1B_APPROVED', 'H1B_APPROVAL_RATE']] = \
    h1b_sponsors_hiring['H1B_SPONSOR_MATCH'].apply(
        lambda x: pd.Series(get_h1b_stats(x, h1b_df))
    )

# Reorder columns for clarity
final_cols = [
    'company', 'title', 'location',
    'salary_min', 'salary_max',
    'posted_date',
    'H1B_SPONSOR_MATCH', 'MATCH_CONFIDENCE',
    'H1B_TOTAL_APPLICATIONS', 'H1B_APPROVED', 'H1B_APPROVAL_RATE',
    'description', 'job_url', 'search_title'
]
h1b_sponsors_hiring = h1b_sponsors_hiring[final_cols]

# Sort by approval rate (best sponsors first)
h1b_sponsors_hiring = h1b_sponsors_hiring.sort_values(
    'H1B_APPROVAL_RATE',
    ascending=False,
    na_position='last'
)

# ============================================================================
# STEP 4: Save results
# ============================================================================
print("\n[STEP 4] Saving cross-referenced results...")

output_file = RESULTS_DIR / 'h1b_sponsors_hiring_now.csv'
h1b_sponsors_hiring.to_csv(output_file, index=False)
print(f"[OK] Saved to {output_file.name}")

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY REPORT")
print("=" * 80)

print(f"\nTotal live job listings found: {len(live_jobs_df):,}")
print(f"Job titles searched: {', '.join(JOB_TITLES)}")
print(f"H1B sponsors currently hiring: {len(h1b_sponsors_hiring):,} positions")

if len(h1b_sponsors_hiring) > 0:
    print(f"\nTop companies by approval rate:")
    top_companies = h1b_sponsors_hiring.groupby('company').agg({
        'H1B_APPROVAL_RATE': 'first',
        'title': 'count'
    }).rename(columns={'title': 'open_positions'}).sort_values('H1B_APPROVAL_RATE', ascending=False).head(10)

    for idx, (company, row) in enumerate(top_companies.iterrows(), 1):
        rate = row['H1B_APPROVAL_RATE']
        positions = int(row['open_positions'])
        print(f"  {idx:2}. {company:<50} Approval: {rate:>6.1f}%  Positions: {positions}")

print(f"\nApproval rate distribution:")
print(f"  Excellent (90-100%): {len(h1b_sponsors_hiring[h1b_sponsors_hiring['H1B_APPROVAL_RATE'] >= 90]):,}")
print(f"  Good (70-89%):       {len(h1b_sponsors_hiring[(h1b_sponsors_hiring['H1B_APPROVAL_RATE'] >= 70) & (h1b_sponsors_hiring['H1B_APPROVAL_RATE'] < 90)]):,}")
print(f"  Fair (50-69%):       {len(h1b_sponsors_hiring[(h1b_sponsors_hiring['H1B_APPROVAL_RATE'] >= 50) & (h1b_sponsors_hiring['H1B_APPROVAL_RATE'] < 70)]):,}")
print(f"  Low (<50%):          {len(h1b_sponsors_hiring[h1b_sponsors_hiring['H1B_APPROVAL_RATE'] < 50]):,}")

print("\n[DONE] Adzuna integration complete!")
