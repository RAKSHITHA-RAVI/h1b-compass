"""
H1B Compass - Intelligence Dashboard v2
Run: python -m streamlit run scripts/05_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(
    page_title="H1B Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #080c14; }
.hero-title { font-size: 2.4rem; font-weight: 700; color: #e2e8f0; margin: 0; line-height: 1.2; }
.hero-sub { color: #64748b; font-size: 1rem; margin: 8px 0 0 0; }
.hero-badge { display: inline-flex; align-items: center; gap: 6px; background: #0f2027; border: 1px solid #1e3a4a; border-radius: 20px; padding: 4px 14px; font-size: 0.75rem; color: #22d3ee; margin-top: 12px; }
.kpi-card { background: #0d1117; border: 1px solid #1e293b; border-radius: 16px; padding: 24px 20px; position: relative; overflow: hidden; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 16px 16px 0 0; }
.kpi-label { font-size: 0.7rem; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin: 0 0 8px 0; }
.kpi-value { font-size: 2rem; font-weight: 700; color: #e2e8f0; margin: 0; line-height: 1; }
.kpi-delta { font-size: 0.75rem; color: #10b981; margin: 6px 0 0 0; }
.section-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 2px; color: #475569; font-weight: 600; margin: 28px 0 14px 0; }
.job-card { background: #0d1117; border: 1px solid #1e293b; border-radius: 12px; padding: 18px 20px; margin-bottom: 12px; }
.job-title-text { font-size: 0.95rem; font-weight: 600; color: #e2e8f0; margin: 0; }
.job-company-text { font-size: 0.82rem; color: #64748b; margin: 3px 0 0 0; }
.job-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.approval-badge { border-radius: 8px; padding: 4px 10px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
.badge-green { background: #052e16; color: #10b981; border: 1px solid #065f46; }
.badge-yellow { background: #2d1b00; color: #f59e0b; border: 1px solid #92400e; }
.badge-red { background: #1f0909; color: #f87171; border: 1px solid #7f1d1d; }
.job-meta-row { display: flex; gap: 16px; flex-wrap: wrap; }
.job-meta-item { font-size: 0.78rem; color: #475569; }
.insight-strip { background: #0f2027; border: 1px solid #1e3a4a; border-left: 3px solid #22d3ee; border-radius: 10px; padding: 14px 16px; margin: 8px 0; font-size: 0.82rem; color: #94a3b8; line-height: 1.6; }
.msg-user { background: #1e293b; border-radius: 12px 12px 2px 12px; padding: 10px 14px; font-size: 0.85rem; color: #e2e8f0; margin: 8px 0 8px 60px; line-height: 1.5; }
.msg-ai { background: #0f2027; border: 1px solid #1e3a4a; border-radius: 12px 12px 12px 2px; padding: 10px 14px; font-size: 0.85rem; color: #94a3b8; margin: 8px 60px 8px 0; line-height: 1.6; white-space: pre-line; }
.msg-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 2px; }
.msg-label-user { color: #3b82f6; text-align: right; }
.msg-label-ai { color: #10b981; }
div[data-testid="stSidebar"] > div { background: #080c14 !important; border-right: 1px solid #1e293b !important; }
</style>
""", unsafe_allow_html=True)

RESULTS = Path(__file__).parent.parent / "results"

def apply_theme(fig, height=400, title=""):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0a0f1a",
        font=dict(family="Inter", color="#64748b", size=12),
        height=height,
        margin=dict(l=16, r=16, t=40, b=16),
        xaxis=dict(gridcolor="#1e293b", linecolor="#1e293b", zerolinecolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b", linecolor="#1e293b", zerolinecolor="#1e293b"),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(color="#64748b", size=13))
    fig.update_layout(**layout)
    return fig

@st.cache_data
def load_all():
    d = {}
    for k, f in [
        ("h1b","h1b_cleaned.csv"),
        ("q1","q1_data_analyst_employers.csv"),
        ("q2","q2_salary_by_state.csv"),
        ("q4","q4_cities_by_volume.csv"),
        ("q5","q5_denial_rate_by_wage_level.csv"),
        ("jobs","h1b_sponsors_hiring_now.csv"),
    ]:
        p = RESULTS / f
        d[k] = pd.read_csv(p) if p.exists() else pd.DataFrame()
    rp = RESULTS / "weekly_insight_report.txt"
    d["report"] = rp.read_text(encoding="utf-8") if rp.exists() else ""
    return d

D = load_all()
h1b=D["h1b"]; q1=D["q1"]; q2=D["q2"]; q4=D["q4"]; q5=D["q5"]; jobs=D["jobs"]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data
def build_system_prompt():
    if h1b.empty:
        return "You are H1B Compass AI. No data is currently loaded."

    prompt = f"""You are H1B Compass AI — a sharp, helpful visa sponsorship intelligence analyst.
You have access to real H1B LCA disclosure data from the US Department of Labor.
Always answer based on this data. Be concise, specific, and cite real numbers.
Never say you don't have data — use what's provided below.
Do not mention you are Llama, Groq, or any other AI — you are H1B Compass AI.

=== DATASET SUMMARY ===
Total H-1B applications: {len(h1b):,}
Overall approval rate: {h1b['CERTIFIED'].mean()*100:.1f}%
Unique employers: {h1b['EMPLOYER_NAME'].nunique():,}
States covered: {h1b['EMPLOYER_STATE'].nunique()}
Median offered salary: ${h1b['ANNUAL_SALARY'].median():,.0f}
Average offered salary: ${h1b['ANNUAL_SALARY'].mean():,.0f}

=== TOP DATA ANALYST EMPLOYERS (by approval rate) ===
"""
    if not q1.empty:
        for _, r in q1.head(12).iterrows():
            prompt += f"- {r['EMPLOYER_NAME']}: {r['APPROVAL_RATE']:.1f}% approval, {int(r['TOTAL_APPLICATIONS'])} applications\n"

    prompt += "\n=== TOP CITIES ===\n"
    if not q4.empty:
        for _, r in q4.head(12).iterrows():
            prompt += f"- {r['CITY_STATE']}: {int(r['TOTAL_APPLICATIONS']):,} applications, {r['APPROVAL_RATE']:.1f}% approval\n"

    prompt += "\n=== SALARY BY STATE ===\n"
    if not q2.empty:
        for _, r in q2.head(10).iterrows():
            prompt += (f"- {r['STATE']}: ${r['OFFERED_SALARY_MEDIAN']:,.0f} median, "
                      f"{r['SALARY_DIFF_PCT']:+.1f}% vs prevailing wage, "
                      f"{int(r['APPLICATION_COUNT']):,} applications\n")

    prompt += "\n=== DENIAL RATE BY WAGE LEVEL ===\n"
    if not q5.empty:
        for _, r in q5.iterrows():
            prompt += f"- Level {r['WAGE_LEVEL']}: {r['DENIAL_RATE']:.1f}% denial rate\n"

    prompt += "\n=== COMPANIES CURRENTLY HIRING (live from Adzuna API) ===\n"
    if not jobs.empty:
        for _, r in jobs.iterrows():
            try:
                sal = f"${float(r.get('salary_min',0)):,.0f}-${float(r.get('salary_max',0)):,.0f}"
            except:
                sal = "salary not listed"
            prompt += (f"- {r.get('company','?')}: {r.get('title','?')} in "
                      f"{r.get('location','?')}, {sal}, "
                      f"{r.get('H1B_APPROVAL_RATE',0):.0f}% H1B approval\n")

    prompt += """
=== HOW TO ANSWER ===
1. Always cite specific numbers from the data
2. Be direct — give a clear recommendation, not just facts
3. Keep answers under 200 words unless the user asks for detail
4. For comparisons, structure clearly (e.g. City A vs City B with bullet points)
5. End every answer with a clear next step or recommendation
6. Tone: confident data analyst, helpful but not verbose
7. If asked about something not in the data, say so briefly then offer what you do know
"""
    return prompt


def get_groq_response(user_message, chat_history):
    if not GROQ_KEY:
        return "Groq API key not found. Please add GROQ_API_KEY to your .env file."
    try:
        client = Groq(api_key=GROQ_KEY)
        system_prompt = build_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[:-1]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"


with st.sidebar:
    st.markdown("## 🧭 H1B Compass")
    st.markdown("<span style='color:#475569;font-size:0.8rem'>Visa Sponsorship Intelligence</span>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", [
        "Overview", "Data Analyst Jobs", "Salary & Cities", "Live Jobs", "AI Chatbot"
    ], label_visibility="collapsed")
    st.markdown("---")
    if not h1b.empty:
        st.markdown(f"**{len(h1b):,}** records analyzed")
        st.markdown(f"**{h1b['CERTIFIED'].mean()*100:.1f}%** overall approval")
        st.markdown(f"**{h1b['EMPLOYER_NAME'].nunique():,}** unique employers")
    st.markdown("---")
    if GROQ_KEY:
        st.markdown("<span style='color:#10b981;font-size:0.75rem'>● AI chatbot active (Groq)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#f87171;font-size:0.75rem'>● Add GROQ_API_KEY to .env</span>", unsafe_allow_html=True)
    st.caption("Data: US DOL LCA\nAPI: Adzuna + Groq/Llama")


# ── OVERVIEW ──────────────────────────────────────────────────
if page == "Overview":
    st.markdown('<p class="hero-title">H1B Compass Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">AI-powered visa sponsorship analysis across 450K+ government records</p>', unsafe_allow_html=True)
    st.markdown('<span class="hero-badge">● LIVE — updated from US Dept of Labor</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not h1b.empty:
        c1,c2,c3,c4 = st.columns(4)
        for col,(lbl,val,delta,color) in zip([c1,c2,c3,c4],[
            ("Total Applications", f"{len(h1b):,}", "3 years of LCA data", "#22d3ee"),
            ("Approval Rate", f"{h1b['CERTIFIED'].mean()*100:.1f}%", "Strong market", "#10b981"),
            ("Unique Employers", f"{h1b['EMPLOYER_NAME'].nunique():,}", "All industries", "#3b82f6"),
            ("States Covered", str(h1b['EMPLOYER_STATE'].nunique()), "Nationwide", "#8b5cf6"),
        ]):
            with col:
                st.markdown(
                    f'<div class="kpi-card">'
                    f'<div class="kpi-accent" style="background:{color}"></div>'
                    f'<p class="kpi-label">{lbl}</p>'
                    f'<p class="kpi-value">{val}</p>'
                    f'<p class="kpi-delta">{delta}</p>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 2])

        with col_a:
            top_emp = (h1b.groupby("EMPLOYER_NAME")
                .agg(apps=("CERTIFIED","count"), approved=("CERTIFIED","sum"))
                .nlargest(12,"apps").reset_index())
            top_emp["rate"] = (top_emp["approved"] / top_emp["apps"] * 100).round(1)
            top_emp["short"] = top_emp["EMPLOYER_NAME"].str[:30]
            fig = go.Figure(go.Bar(
                x=top_emp["apps"], y=top_emp["short"], orientation="h",
                marker=dict(
                    color=top_emp["rate"],
                    colorscale=[[0,"#7f1d1d"],[0.5,"#854d0e"],[1,"#10b981"]],
                    cmin=80, cmax=100,
                    colorbar=dict(
                        title=dict(text="Approval %", font=dict(color="#475569")),
                        tickfont=dict(color="#475569"), thickness=10)
                ),
                text=top_emp["rate"].apply(lambda x: f"{x:.0f}%"),
                textposition="outside", textfont=dict(color="#475569", size=11),
                hovertemplate="<b>%{y}</b><br>Apps: %{x:,}<br>Approval: %{text}<extra></extra>"
            ))
            apply_theme(fig, height=420, title="Top employers by volume (color = approval rate)")
            fig.update_layout(xaxis=dict(title="Applications", gridcolor="#1e293b", linecolor="#1e293b"))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            if not q5.empty:
                fig2 = go.Figure(go.Bar(
                    x=q5["WAGE_LEVEL"], y=q5["DENIAL_RATE"],
                    marker_color=["#f87171","#f59e0b","#10b981","#10b981"],
                    text=q5["DENIAL_RATE"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside", textfont=dict(color="#64748b", size=12),
                    width=0.5,
                    hovertemplate="Level %{x}: %{text} denial<extra></extra>"
                ))
                apply_theme(fig2, height=300, title="Denial rate by wage level")
                fig2.update_layout(yaxis=dict(range=[0,20], title="Denial %", gridcolor="#1e293b", linecolor="#1e293b"))
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown(
                    '<div class="insight-strip">'
                    '<strong style="color:#22d3ee">Key insight:</strong> Level I offers are denied '
                    '<strong style="color:#f87171">2x more often</strong> than Level III/IV. '
                    'Always negotiate to Level II or above.'
                    '</div>', unsafe_allow_html=True)


# ── DATA ANALYST JOBS ─────────────────────────────────────────
elif page == "Data Analyst Jobs":
    st.markdown('<p class="hero-title" style="font-size:1.8rem">Data Analyst Sponsorship</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Companies with the strongest H1B track record for Data Analyst roles</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not q1.empty:
        min_apps = st.slider("Minimum applications filed", 1, 50, 5)
        filtered = q1[q1["TOTAL_APPLICATIONS"] >= min_apps].copy()
        col1, col2 = st.columns([5, 4])

        with col1:
            top15 = filtered.nlargest(15, "TOTAL_APPLICATIONS").copy()
            top15["short"] = top15["EMPLOYER_NAME"].str[:32]
            fig = go.Figure(go.Bar(
                x=top15["APPROVAL_RATE"], y=top15["short"], orientation="h",
                marker=dict(color=top15["APPROVAL_RATE"],
                    colorscale=[[0,"#7f1d1d"],[0.6,"#854d0e"],[1,"#10b981"]], cmin=50, cmax=100),
                text=top15["APPROVAL_RATE"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside", textfont=dict(color="#64748b", size=11), width=0.65,
                hovertemplate="<b>%{y}</b><br>Approval: %{x:.1f}%<extra></extra>"
            ))
            fig.add_vline(x=90.5, line_dash="dash", line_color="#334155",
                annotation_text="Market avg 90.5%",
                annotation_font_color="#475569", annotation_font_size=11)
            apply_theme(fig, height=480, title="Approval rate — Data Analyst roles")
            fig.update_layout(xaxis=dict(range=[0,115], title="Approval Rate %", gridcolor="#1e293b", linecolor="#1e293b"))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<p class="section-label">Full rankings</p>', unsafe_allow_html=True)
            disp = filtered[["EMPLOYER_NAME","TOTAL_APPLICATIONS","APPROVED","APPROVAL_RATE"]].copy()
            disp.columns = ["Company","Apps","Approved","Rate %"]
            disp["Rate %"] = disp["Rate %"].round(1)
            st.dataframe(disp.head(20), use_container_width=True, hide_index=True,
                column_config={"Rate %": st.column_config.ProgressColumn("Rate %", min_value=0, max_value=100, format="%.1f%%")})

        if len(filtered) > 0:
            best = filtered.nlargest(1, "APPROVAL_RATE").iloc[0]
            st.markdown(
                f'<div class="insight-strip">'
                f'<strong style="color:#22d3ee">Top pick:</strong> {best["EMPLOYER_NAME"]} — '
                f'<strong style="color:#10b981">{best["APPROVAL_RATE"]:.1f}%</strong> approval '
                f'across {int(best["TOTAL_APPLICATIONS"])} Data Analyst applications.'
                f'</div>', unsafe_allow_html=True)


# ── SALARY & CITIES ───────────────────────────────────────────
elif page == "Salary & Cities":
    st.markdown('<p class="hero-title" style="font-size:1.8rem">Salary & City Intelligence</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Where to target for maximum salary and best approval odds</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if not q2.empty:
            top10 = q2.head(10).copy()
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Offered (median)", x=top10["STATE"],
                y=top10["OFFERED_SALARY_MEDIAN"]/1000, marker_color="#22d3ee",
                opacity=0.9, width=0.35, offset=-0.18,
                hovertemplate="%{x}: $%{y:.0f}K<extra>Offered</extra>"))
            fig.add_trace(go.Bar(name="Prevailing wage", x=top10["STATE"],
                y=top10["PREVAILING_WAGE_MEDIAN"]/1000, marker_color="#1e293b",
                opacity=0.9, width=0.35, offset=0.18,
                hovertemplate="%{x}: $%{y:.0f}K<extra>Prevailing</extra>"))
            apply_theme(fig, height=340, title="Median salary vs prevailing wage ($K)")
            fig.update_layout(
                barmode="overlay",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color="#64748b")),
                yaxis=dict(title="Salary ($K)", gridcolor="#1e293b", linecolor="#1e293b"))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('<div class="insight-strip"><strong style="color:#22d3ee">NY leads:</strong> New York pays <strong style="color:#10b981">+14.7%</strong> above prevailing wage — highest premium in the dataset.</div>', unsafe_allow_html=True)

    with col2:
        if not q4.empty:
            fig2 = px.scatter(q4.head(20), x="TOTAL_APPLICATIONS", y="APPROVAL_RATE",
                size="TOTAL_APPLICATIONS", hover_name="CITY_STATE", color="APPROVAL_RATE",
                color_continuous_scale=[[0,"#7f1d1d"],[0.5,"#854d0e"],[1,"#10b981"]],
                range_color=[85,100], size_max=50,
                labels={"TOTAL_APPLICATIONS":"Applications","APPROVAL_RATE":"Approval %"})
            fig2.add_hline(y=90.5, line_dash="dash", line_color="#334155",
                annotation_text="Avg 90.5%", annotation_font_color="#475569")
            apply_theme(fig2, height=340, title="City hotspots: volume vs approval")
            fig2.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('<div class="insight-strip"><strong style="color:#22d3ee">Best city:</strong> Seattle — <strong style="color:#10b981">98.2%</strong> approval with 17,661 apps. Best combo of volume + approval.</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Full city rankings</p>', unsafe_allow_html=True)
    if not q4.empty:
        disp = q4[["CITY_STATE","TOTAL_APPLICATIONS","APPROVED","APPROVAL_RATE"]].copy()
        disp.columns = ["City","Applications","Approved","Approval %"]
        disp["Approval %"] = disp["Approval %"].round(1)
        st.dataframe(disp.head(15), use_container_width=True, hide_index=True,
            column_config={"Approval %": st.column_config.ProgressColumn("Approval %", min_value=80, max_value=100, format="%.1f%%")})


# ── LIVE JOBS ─────────────────────────────────────────────────
elif page == "Live Jobs":
    st.markdown('<p class="hero-title" style="font-size:1.8rem">Live Job Openings</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">H1B sponsors actively hiring — cross-referenced from Adzuna API with DOL data</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not jobs.empty:
        col_j, col_r = st.columns([3, 2])
        with col_j:
            st.markdown('<p class="section-label">Active openings</p>', unsafe_allow_html=True)
            for _, row in jobs.iterrows():
                rate = float(row.get("H1B_APPROVAL_RATE", 0))
                if rate >= 95:   bc, bt = "badge-green",  f"✓ {rate:.0f}% H1B"
                elif rate >= 80: bc, bt = "badge-yellow", f"⚠ {rate:.0f}% H1B"
                else:            bc, bt = "badge-red",    f"✗ {rate:.0f}% H1B"
                try:
                    sm = float(row.get("salary_min", 0)); sx = float(row.get("salary_max", 0))
                    sal = f"${sm:,.0f} – ${sx:,.0f}" if sm and sx else "Not disclosed"
                except:
                    sal = "Not disclosed"
                st.markdown(
                    f'<div class="job-card"><div class="job-top">'
                    f'<div><p class="job-title-text">{row.get("title","N/A")}</p>'
                    f'<p class="job-company-text">{row.get("company","N/A")}</p></div>'
                    f'<span class="approval-badge {bc}">{bt}</span></div>'
                    f'<div class="job-meta-row">'
                    f'<span class="job-meta-item">📍 {row.get("location","N/A")}</span>'
                    f'<span class="job-meta-item">💰 {sal}</span>'
                    f'<span class="job-meta-item">📅 {str(row.get("posted_date",""))[:10]}</span>'
                    f'</div></div>', unsafe_allow_html=True)
                st.markdown(f"[View posting →]({row.get('job_url','#')})")

        with col_r:
            st.markdown('<p class="section-label">Weekly AI report</p>', unsafe_allow_html=True)
            report = D.get("report", "")
            if report and len(report) > 200:
                clean = "\n".join(l for l in report.split("\n")
                    if not l.startswith("event:") and not l.startswith("data:")).strip()
                st.text_area("", clean, height=500, label_visibility="collapsed")
            else:
                st.markdown('<div class="insight-strip">Run scripts/04_claude_insights.py to generate your weekly AI report.</div>', unsafe_allow_html=True)
    else:
        st.warning("No live jobs data. Run scripts/03_adzuna_jobs.py first.")


# ── AI CHATBOT ────────────────────────────────────────────────
elif page == "AI Chatbot":
    st.markdown('<p class="hero-title" style="font-size:1.8rem">H1B Intelligence Chatbot</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Ask anything in plain English — powered by Llama 3.3 + real government data</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not GROQ_KEY:
        st.error("Add GROQ_API_KEY to your .env file to activate the AI chatbot.")
    else:
        st.markdown('<p class="section-label">Try asking</p>', unsafe_allow_html=True)
        suggestions = [
            "Best companies for Data Analyst H1B?",
            "Which city has highest approval rate?",
            "Compare NY vs Seattle for H1B",
            "What is Level I vs Level IV wage?",
            "Who is hiring right now?",
        ]
        cols = st.columns(5)
        for col, q in zip(cols, suggestions):
            with col:
                if st.button(q, use_container_width=True, key=f"s_{q[:15]}"):
                    st.session_state.chat_history.append({"role":"user","content":q})
                    st.rerun()

        st.markdown('<p class="section-label">Conversation</p>', unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="msg-label msg-label-user">You</div>'
                    f'<div class="msg-user">{msg["content"]}</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="msg-label msg-label-ai">H1B Compass AI</div>'
                    f'<div class="msg-ai">{msg["content"]}</div>',
                    unsafe_allow_html=True)

        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            user_msg = st.session_state.chat_history[-1]["content"]
            with st.spinner("Analyzing your question..."):
                response = get_groq_response(user_msg, st.session_state.chat_history)
            st.session_state.chat_history.append({"role":"assistant","content":response})
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True):
            ci, cb = st.columns([5,1])
            with ci:
                ui = st.text_input("", placeholder="Ask anything about H1B sponsorship, companies, cities, salaries...", label_visibility="collapsed")
            with cb:
                sub = st.form_submit_button("Send →", use_container_width=True)
        if sub and ui.strip():
            st.session_state.chat_history.append({"role":"user","content":ui.strip()})
            st.rerun()

        col_clear, col_info = st.columns([1,4])
        with col_clear:
            if st.button("Clear chat"):
                st.session_state.chat_history = []
                st.rerun()
        with col_info:
            st.markdown("<span style='color:#475569;font-size:0.75rem'>Powered by Llama 3.3 70B via Groq + 435K real H1B records</span>", unsafe_allow_html=True)
