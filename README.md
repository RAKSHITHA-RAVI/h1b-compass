# 🧭 H1B Compass — Visa Sponsorship Intelligence Platform

> AI-powered analytics platform that helps international job seekers find the best H1B sponsorship opportunities using real government data, live job listings, and conversational AI.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=flat-square&logo=streamlit)
![Snowflake](https://img.shields.io/badge/Snowflake-Cloud_DB-blue?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange?style=flat-square)
![DOL](https://img.shields.io/badge/Data-US_Dept_of_Labor-green?style=flat-square)

---

## The Problem

International students on OPT spend months applying to companies that quietly don't sponsor H1B visas — wasting time and missing real opportunities. There's no single tool that tells you *which companies actually approve H1B applications, at what salary, in which cities, right now.*

**H1B Compass solves this.**

---

## What It Does

H1B Compass ingests 450K+ real H1B LCA applications from the US Department of Labor, cross-references them with live job listings via the Adzuna API, and uses Llama 3.3 70B (via Groq) to answer any question about sponsorship in plain English.

**In one sentence:** *It tells you exactly which companies to target, which cities to move to, and which offers to avoid — backed by real government data.*

---

## Key Findings From the Data

| Insight | Finding |
|---|---|
| Overall H1B approval rate | 90.5% across 435,581 applications |
| Best Data Analyst sponsor | Capital One — 100% approval across 85 DA applications |
| Best city for approval | Seattle, WA — 98.2% approval, 17,661 applications |
| Highest salary city | New York, NY — $475,535 avg, +14.7% above prevailing wage |
| Riskiest offer type | Level I wage — 15.2% denial rate (2x higher than Level III) |
| Fastest growing sponsor | Amazon — grew from 3,200 to 5,200 sponsorships YoY |

---

## Architecture

```
US Dept of Labor (LCA Data)          Adzuna Jobs API
        │                                   │
        ▼                                   ▼
  Excel/CSV (FY2024-2026)        Live job listings (REST API)
        │                                   │
        └──────────────┬────────────────────┘
                       ▼
              Python ETL Pipeline
              (pandas, openpyxl)
                       │
                       ▼
                  Snowflake
             (Cloud Data Warehouse)
                       │
                       ▼
            SQL Analysis Layer
         5 key business questions
                       │
              ┌────────┴────────┐
              ▼                 ▼
         Claude API          Power BI
      (insight report)      (dashboard)
              │
              ▼
       Streamlit App
    + Groq/Llama Chatbot
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data ingestion | Python (pandas, requests, openpyxl) |
| Cloud database | Snowflake |
| Job listings API | Adzuna REST API |
| AI insight generation | Claude API (Anthropic) |
| AI chatbot | Llama 3.3 70B via Groq API |
| Dashboard | Streamlit + Plotly |
| Data source | US Dept of Labor LCA Disclosure Dataset |
| Environment | python-dotenv, pathlib |

---

## Project Structure

```
h1b-compass/
├── data/                          # Raw LCA Excel files (not committed)
│   ├── LCA_Disclosure_Data_FY2024_Q4.xlsx
│   ├── LCA_Disclosure_Data_FY2025_Q4.xlsx
│   └── LCA_Dislclosure_Data_FY2026_Q2.xlsx
├── scripts/
│   ├── 01_load_and_clean.py       # ETL: load 450K rows, normalize wages
│   ├── 02_sql_analysis.py         # 5 SQL analyses (approval rates, salary, cities)
│   ├── 03_adzuna_jobs.py          # Live job listings + H1B cross-reference
│   ├── 04_claude_insights.py      # AI-generated weekly intelligence report
│   └── 05_dashboard.py            # Streamlit dashboard + Groq chatbot
├── results/                       # Generated CSVs and reports
│   ├── q1_data_analyst_employers.csv
│   ├── q2_salary_by_state.csv
│   ├── q3_yoy_trend.csv
│   ├── q4_cities_by_volume.csv
│   ├── q5_denial_rate_by_wage_level.csv
│   ├── h1b_sponsors_hiring_now.csv
│   └── weekly_insight_report.txt
├── notebooks/                     # Exploratory analysis
├── .env.example                   # Credential template
├── .gitignore
└── README.md
```

---

## 5 Business Questions Answered

**Q1 — Which companies should I target for Data Analyst H1B?**
Ranks all employers by approval rate with minimum application thresholds to filter statistically reliable data.

**Q2 — What salary should I expect by state?**
Compares offered salary vs DOL prevailing wage by state — identifies where employers pay above and below market.

**Q3 — Which companies are growing or shrinking their sponsorship?**
Year-over-year trend analysis. Amazon grew 62% (3,200 → 5,200). EY exploded from 6 to 3,200 applications.

**Q4 — Which cities have the best H1B environment?**
Volume × approval rate matrix. Seattle dominates: 17,661 apps at 98.2% approval.

**Q5 — What makes an application more likely to be denied?**
Level I wage offers are denied 15.2% of the time vs 7.6% for Level III. Quantifies the exact risk.

---

## The AI Layer

### Weekly Intelligence Report (Claude API)
Every Monday, the pipeline reads all analysis results and sends them to Claude with a structured prompt. Claude generates a plain-English report with:
- Top 5 companies to target this week
- Salary benchmarks by city
- Risk warnings (companies and offer types to avoid)
- Strategic narrative summary

### Conversational Chatbot (Groq + Llama 3.3 70B)
The dashboard includes an AI chatbot that answers any H1B question in natural language. The full dataset summary is injected as system context so the model answers from real data, not hallucinations.

Example questions it handles:
- *"Which companies have the best H1B approval rate for data analysts?"*
- *"Compare Seattle vs New York for international job seekers"*
- *"Is a Level I offer a red flag? What should I do?"*
- *"Who is actively hiring right now with good H1B history?"*

---

## How to Run

### 1. Clone the repo
```bash
git clone https://github.com/RAKSHITHA-RAVI/h1b-compass.git
cd h1b-compass
```

### 2. Install dependencies
```bash
pip install pandas openpyxl requests python-dotenv anthropic streamlit plotly groq
```

### 3. Set up credentials
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
```
ANTHROPIC_API_KEY=sk-ant-...
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key
GROQ_API_KEY=gsk_...
```

### 4. Download the data
Get LCA disclosure files from: https://www.dol.gov/agencies/eta/foreign-labor/performance
Place Excel files in the `data/` folder.

### 5. Run the pipeline
```bash
python scripts/01_load_and_clean.py
python scripts/02_sql_analysis.py
python scripts/03_adzuna_jobs.py
python scripts/04_claude_insights.py
```

### 6. Launch the dashboard
```bash
python -m streamlit run scripts/05_dashboard.py
```

---

## Dashboard Pages

| Page | What It Shows |
|---|---|
| Overview | KPI cards, top employers chart, denial rate by wage level |
| Data Analyst Jobs | Filterable approval rate rankings for DA roles specifically |
| Salary & Cities | State salary vs prevailing wage, city bubble chart |
| Live Jobs | Real-time job openings cross-referenced with H1B data |
| AI Chatbot | Conversational Q&A powered by Llama 3.3 70B + real data |

---

## Data Source

- **US Department of Labor — OFLC LCA Disclosure Data**
  - FY2024 Q4: 120,897 rows
  - FY2025 Q4: 118,580 rows
  - FY2026 Q2: 210,387 rows
  - **Total: 449,864 rows across 98 columns**
  - Source: https://www.dol.gov/agencies/eta/foreign-labor/performance

- **Adzuna Jobs API** — Live job listings for cross-referencing active hiring

---



---

*Data from US Department of Labor is public domain. This tool is for informational purposes only.*
