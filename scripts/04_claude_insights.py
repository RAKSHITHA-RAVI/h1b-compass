"""
H1B Compass - Claude AI Insights Generator
Generates weekly intelligence report using Claude API
"""
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not ANTHROPIC_API_KEY:
    raise ValueError("Missing ANTHROPIC_API_KEY in .env file")

# Setup paths
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("H1B COMPASS - CLAUDE AI INSIGHTS GENERATOR")
print("=" * 80)

# ============================================================================
# STEP 1: Load all analysis data
# ============================================================================
print("\n[STEP 1] Loading analysis data...")

try:
    h1b_cleaned = pd.read_csv(RESULTS_DIR / 'h1b_cleaned.csv')
    print(f"[OK] Loaded h1b_cleaned.csv ({len(h1b_cleaned):,} rows)")
except FileNotFoundError:
    print("[ERROR] h1b_cleaned.csv not found")
    exit(1)

try:
    q1_data_analysts = pd.read_csv(RESULTS_DIR / 'q1_data_analyst_employers.csv')
    print(f"[OK] Loaded q1_data_analyst_employers.csv")
except FileNotFoundError:
    print("[ERROR] q1_data_analyst_employers.csv not found")
    q1_data_analysts = None

try:
    q2_salary_by_state = pd.read_csv(RESULTS_DIR / 'q2_salary_by_state.csv')
    print(f"[OK] Loaded q2_salary_by_state.csv")
except FileNotFoundError:
    print("[ERROR] q2_salary_by_state.csv not found")
    q2_salary_by_state = None

try:
    q4_cities = pd.read_csv(RESULTS_DIR / 'q4_cities_by_volume.csv')
    print(f"[OK] Loaded q4_cities_by_volume.csv")
except FileNotFoundError:
    print("[ERROR] q4_cities_by_volume.csv not found")
    q4_cities = None

try:
    q5_denial_rate = pd.read_csv(RESULTS_DIR / 'q5_denial_rate_by_wage_level.csv')
    print(f"[OK] Loaded q5_denial_rate_by_wage_level.csv")
except FileNotFoundError:
    print("[ERROR] q5_denial_rate_by_wage_level.csv not found")
    q5_denial_rate = None

try:
    sponsors_hiring = pd.read_csv(RESULTS_DIR / 'h1b_sponsors_hiring_now.csv')
    print(f"[OK] Loaded h1b_sponsors_hiring_now.csv ({len(sponsors_hiring)} job openings)")
except FileNotFoundError:
    print("[WARNING] h1b_sponsors_hiring_now.csv not found (Adzuna API may not have been run)")
    sponsors_hiring = None

# ============================================================================
# STEP 2: Prepare context for Claude
# ============================================================================
print("\n[STEP 2] Preparing context for Claude...")

# Build markdown summary of key stats
context_data = f"""
# H1B Compass Analysis Data

## Dataset Overview
- Total H1B applications: {len(h1b_cleaned):,}
- Approval rate: {h1b_cleaned['CERTIFIED'].mean()*100:.1f}%
- States represented: {h1b_cleaned['EMPLOYER_STATE'].nunique()}
- Unique employers: {h1b_cleaned['EMPLOYER_NAME'].nunique()}

## Salary Insights
- Average offered salary: ${h1b_cleaned['ANNUAL_SALARY'].mean():,.0f}
- Median offered salary: ${h1b_cleaned['ANNUAL_SALARY'].median():,.0f}
- Average prevailing wage: ${h1b_cleaned['PREVAILING_WAGE_ANNUAL'].mean():,.0f}

## Top Companies (General)
"""

top_employers = h1b_cleaned['EMPLOYER_NAME'].value_counts().head(5)
for idx, (company, count) in enumerate(top_employers.items(), 1):
    company_stats = h1b_cleaned[h1b_cleaned['EMPLOYER_NAME'] == company]
    approval = company_stats['CERTIFIED'].mean() * 100
    context_data += f"\n{idx}. {company}: {count:,} applications, {approval:.1f}% approval"

if q1_data_analysts is not None and len(q1_data_analysts) > 0:
    context_data += "\n\n## Data Analyst Specialist Companies (by approval rate)\n"
    for idx, row in q1_data_analysts.head(5).iterrows():
        context_data += f"\n{idx+1}. {row['EMPLOYER_NAME']}: {row['APPROVAL_RATE']:.1f}% approval ({row['TOTAL_APPLICATIONS']} applications)"

if q2_salary_by_state is not None and len(q2_salary_by_state) > 0:
    context_data += "\n\n## Top States by Salary & Volume\n"
    for idx, row in q2_salary_by_state.head(5).iterrows():
        salary_offered = row['OFFERED_SALARY_MEAN']
        prevailing = row['PREVAILING_WAGE_MEAN']
        diff_pct = row['SALARY_DIFF_PCT']
        context_data += f"\n{row['STATE']}: ${salary_offered:,.0f} avg (vs ${prevailing:,.0f} prevailing, {diff_pct:+.1f}%), {int(row['APPLICATION_COUNT']):,} applications"

if q4_cities is not None and len(q4_cities) > 0:
    context_data += "\n\n## Hottest Cities for H1B Hiring\n"
    for idx, row in q4_cities.head(5).iterrows():
        context_data += f"\n{idx+1}. {row['CITY_STATE']}: {int(row['TOTAL_APPLICATIONS']):,} applications, {row['APPROVAL_RATE']:.1f}% approval"

if sponsors_hiring is not None and len(sponsors_hiring) > 0:
    context_data += f"\n\n## Companies Currently Hiring (from live job listings)\n"
    context_data += f"Total open positions from H1B sponsors: {len(sponsors_hiring)}\n"

    top_hiring = sponsors_hiring.groupby('company').agg({
        'H1B_APPROVAL_RATE': 'first',
        'title': 'count'
    }).rename(columns={'title': 'open_positions'}).sort_values('open_positions', ascending=False).head(5)

    for idx, (company, row) in enumerate(top_hiring.iterrows(), 1):
        approval = row['H1B_APPROVAL_RATE']
        positions = int(row['open_positions'])
        context_data += f"\n{idx}. {company}: {positions} open positions, {approval:.1f}% H1B approval rate"

print("[OK] Context prepared")

# ============================================================================
# STEP 3: Call Claude API
# ============================================================================
print("\n[STEP 3] Calling Claude API to generate insights...")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

system_prompt = """You are an expert H1B visa sponsorship analyst providing strategic career intelligence.
Your role is to synthesize data on H1B visa patterns, company hiring practices, and salary trends to help job seekers
find the best opportunities for H1B sponsorship.

Generate a weekly intelligence report that is:
- Data-driven and specific with numbers
- Actionable with clear recommendations
- Balanced in tone (neither too optimistic nor pessimistic)
- Focused on helping job seekers make informed decisions

Format your response as a structured report with clear sections."""

user_prompt = f"""Based on the following H1B and job market data, generate a weekly intelligence report:

{context_data}

Please provide:

1. **Top 5 Target Companies This Week** - Companies that are:
   - Currently actively hiring
   - Have strong H1B visa sponsorship history
   - Likely to sponsor foreigners
   - List salary range if available

2. **Salary Benchmarks by City** - For Data Analyst / Business Analyst roles:
   - Top 3 cities by salary
   - Cost of living vs offered salary considerations
   - Prevailing wage context

3. **Approval Rate Warnings** - Companies or regions to be cautious about:
   - Low approval rates that suggest challenges
   - Common reasons why applications might be denied
   - Factors that correlate with denials

4. **Weekly Summary** - A 1-2 paragraph narrative that:
   - Summarizes the current H1B market conditions
   - Identifies key opportunities and risks
   - Provides actionable guidance for job seekers

Be specific with numbers and percentages from the data provided."""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=2000,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}]
)

report = response.content[0].text

# ============================================================================
# STEP 4: Save and display report
# ============================================================================
print("\n[STEP 4] Saving report...")

report_file = RESULTS_DIR / 'weekly_insight_report.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("H1B COMPASS - WEEKLY INTELLIGENCE REPORT\n")
    f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 80 + "\n\n")
    f.write(report)
    f.write("\n\n" + "=" * 80 + "\n")

print(f"[OK] Report saved to {report_file.name}")

# ============================================================================
# DISPLAY REPORT
# ============================================================================
print("\n" + "=" * 80)
print("WEEKLY INTELLIGENCE REPORT")
print("=" * 80)
try:
    print(report)
except UnicodeEncodeError:
    # Fallback for console that doesn't support unicode
    print(report.encode('ascii', errors='replace').decode('ascii'))
print("\n" + "=" * 80)
print("[DONE] Claude insights generation complete!")
