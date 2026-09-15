import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Channel Trends Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# STYLE (same dark-sidebar pattern as the Meta dashboard)
# ════════════════════════════════════════════════════════════
ACCENT = "#8b5cf6"  # purple accent for this dashboard — change to match your brand if you like

st.markdown(f"""
<style>
#MainMenu, footer {{ display:none!important }}
header[data-testid="stHeader"] {{ display:none!important }}
[data-testid="collapsedControl"] {{ display:none!important }}

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {{
    background-color: #111111 !important;
}}
[data-testid="stSidebar"] .stMarkdown p {{
    color: #777777 !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}}
[data-testid="stSidebar"] label {{ color: #cccccc !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: #1e1e1e !important;
    border-color: #333 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {{ color: white !important; }}
[data-testid="stSidebar"] input {{ background: #1e1e1e !important; color: white !important; }}
[data-testid="stSidebar"] hr {{ border-color: #333 !important; }}
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio label span,
[data-testid="stSidebar"] .stRadio div {{ color: #dddddd !important; font-size: 0.8rem !important; }}
[data-testid="stSidebar"] .stRadio input[type="radio"] {{ accent-color: {ACCENT} !important; }}

[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: #aaaaaa !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: {ACCENT} !important;
    color: white !important;
    font-weight: 600 !important;
}}
</style>
""", unsafe_allow_html=True)

COLORS = ["#8b5cf6", "#10b981", "#f59e0b", "#06b6d4", "#ef4444",
          "#1877F2", "#f97316", "#ec4899", "#22c55e", "#a78bfa"]

CHANNEL_COLORS = {
    "Direct": "#8b5cf6",
    "Organic": "#10b981",
    "Google Brand": "#f59e0b",
    "Bing Brand": "#06b6d4",
}

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)}
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def fn(n):
    if pd.isna(n): return "—"
    if abs(n) >= 1_000_000: return f"{n/1e6:.1f}M"
    if abs(n) >= 1_000: return f"{n/1e3:.1f}K"
    return f"{n:,.0f}"

def fc(n):
    if pd.isna(n) or n == 0: return "$0"
    if abs(n) >= 1_000_000: return f"${n/1e6:.1f}M"
    if abs(n) >= 1_000: return f"${n/1e3:.1f}K"
    return f"${n:,.0f}"

def sh(t):
    return (f'<div style="background:{ACCENT};color:white;padding:8px 14px;'
            'border-radius:8px 8px 0 0;font-weight:600;font-size:0.82rem">' + t + '</div>')

def sb_o():
    return '<div style="background:white;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;padding:14px;margin-bottom:24px">'

def sb_c():
    return "</div>"

# ════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════
SHEET_ID = "1QqSKMHNExUGUTEfLojQ5mQOSktcFk-OpoqIhln5lyMc"
TAB_NAMES = ["Direct", "Organic", "Google Brand", "Bing Brand"]

@st.cache_data(ttl=1800)
def load_data():
    import gspread
    from google.oauth2.service_account import Credentials

    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
        )
    except Exception:
        creds = Credentials.from_service_account_file(
            "lsw-marketing-b9a13bd21034.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
        )

    gc = gspread.authorize(creds)
    sh_ = gc.open_by_key(SHEET_ID)

    frames = []
    for tab in TAB_NAMES:
        records = sh_.worksheet(tab).get_all_records()
        df = pd.DataFrame(records)
        df["channel"] = tab
        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)

    numeric_cols = ["unique_leads", "new_leads", "apt", "quote", "customers",
                     "sales_amount", "new_leads_customers", "new_leads_sales_amount", "year"]
    for col in numeric_cols:
        if col in all_df.columns:
            all_df[col] = pd.to_numeric(
                all_df[col].astype(str).str.replace("[$,%]", "", regex=True).str.strip(),
                errors="coerce"
            ).fillna(0)

    all_df["month_num"] = all_df["month"].astype(str).str.strip().str.title().map(MONTH_NUM).fillna(0).astype(int)
    all_df["year"] = all_df["year"].astype(int)
    all_df["Period"] = pd.to_datetime(
        all_df.apply(lambda r: f"{int(r['year'])}-{int(r['month_num']):02d}-01"
                     if r["month_num"] > 0 else None, axis=1)
    )
    return all_df

try:
    data = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# ════════════════════════════════════════════════════════════
# BUDGET DATA (TV/Radio spend by region, from the quarterly plan tabs)
# ════════════════════════════════════════════════════════════
# Maps a market row LABEL in the budget tabs -> the Region_Clean value(s) it feeds into.
# "Arizona" combines two budget rows (Phoenix + Tucson) since your leads data doesn't
# split those two cities separately. Sirius (satellite radio, national) and the tiny
# Bullhead City / Bakersfield / Monterey-Salinas rows are intentionally excluded, since
# they aren't tied to one specific leads region. NOTE: "Austin" has no row at all in the
# budget tabs, meaning there's currently no TV/Radio spend tracked for that market —
# any Austin trend can't be explained by TV/Radio spend with this data.
BUDGET_REGION_MAP = {
    "TOTAL LOS ANGELES": "Los Angeles",
    "TOTAL BAY AREA": "Bay Area",
    "TOTAL SACRAMENTO": "Sacramento",
    "TOTAL PHOENIX": "Arizona",
    "TUCSON": "Arizona",
    "TOTAL LAS VEGAS": "Las Vegas",
    "FRESNO": "Fresno",
    "SAN DIEGO": "San Diego",
}

# column layout is hardcoded per quarter tab, since each one has a different number of
# sub-columns per month (Q1 has REC/Budget/Final-Spend columns; Q2's April block is
# shorter than May/June; Q3 is uniform). Columns are 1-indexed, matching spreadsheet
# column letters. Each entry is (month_name, month_num, col_2025, col_2026).
BUDGET_TABS = {
    "Radio-TV Q1 Plan": [
        ("January", 1, 4, 7),     # Jan 2026 uses FINAL SPEND (col 7) — a confirmed actual
        ("February", 2, 12, 13),  # Feb/Mar 2026 have no Final Spend yet in this tab —
        ("March", 3, 20, 21),     # using the planned "2026" column as the best available number
    ],
    "Radio -TV Q2 Plan": [
        ("April", 4, 2, 3),
        ("May", 5, 8, 9),
        ("June", 6, 14, 15),
    ],
    "Radio - TV Q3 Plan": [
        ("July", 7, 4, 5),
        ("August", 8, 10, 11),
        ("September", 9, 16, 17),
    ],
    "Radio - TV Q4 Plan": [
        ("October", 10, 4, 5),
        ("November", 11, 10, 11),
        ("December", 12, 16, 17),
    ],
}

def _parse_money(v):
    if v is None:
        return 0.0
    s = str(v).replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    if s in ("", "-", "—"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

@st.cache_data(ttl=1800)
def load_budget_data():
    import gspread
    from google.oauth2.service_account import Credentials

    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly"]
        )
    except Exception:
        creds = Credentials.from_service_account_file(
            "lsw-marketing-b9a13bd21034.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly"]
        )
    gc = gspread.authorize(creds)
    sh_ = gc.open_by_key(SHEET_ID)

    rows = []
    for tab_name, month_cols in BUDGET_TABS.items():
        try:
            grid = sh_.worksheet(tab_name).get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            continue

        for r in grid:
            if not r:
                continue
            label = str(r[0]).strip().upper()
            region = BUDGET_REGION_MAP.get(label)
            if not region:
                continue
            for month_name, month_num, col_2025, col_2026 in month_cols:
                v2025 = _parse_money(r[col_2025 - 1]) if len(r) >= col_2025 else 0.0
                v2026 = _parse_money(r[col_2026 - 1]) if len(r) >= col_2026 else 0.0
                rows.append({"Region_Clean": region, "year": 2025, "month_num": month_num, "spend": v2025})
                rows.append({"Region_Clean": region, "year": 2026, "month_num": month_num, "spend": v2026})

    if not rows:
        return pd.DataFrame(columns=["Region_Clean", "year", "month_num", "spend", "Period"])

    budget_df = pd.DataFrame(rows).groupby(
        ["Region_Clean", "year", "month_num"], as_index=False
    )["spend"].sum()
    budget_df["Period"] = pd.to_datetime(
        budget_df["year"].astype(str) + "-" + budget_df["month_num"].astype(str).str.zfill(2) + "-01"
    )
    return budget_df

try:
    budget_data = load_budget_data()
except Exception as e:
    budget_data = pd.DataFrame(columns=["Region_Clean", "year", "month_num", "spend", "Period"])
    st.warning(f"⚠️ Could not load TV/Radio budget data: {e}")

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="background:#111111;margin:-1rem -1rem 1rem -1rem;padding:20px 16px 16px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="background:{ACCENT};border-radius:8px;width:36px;height:36px;
                    display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <span style="color:white;font-weight:700;font-size:1rem">📈</span>
        </div>
        <div>
          <div style="color:white;font-size:1rem;font-weight:700">Channel Trends</div>
          <div style="color:#888;font-size:0.72rem">Dashboard</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    all_years = sorted(data["year"].unique().tolist()) if not data.empty else [2025, 2026]

    st.markdown("<p>View</p>", unsafe_allow_html=True)
    view_mode = st.radio(
        "View", ["Combined (All)", "By Channel"], index=0,
        label_visibility="collapsed", horizontal=True, key="view_mode"
    )

    if view_mode == "By Channel":
        st.markdown("<p>Channels</p>", unsafe_allow_html=True)
        sel_channels = st.multiselect(
            "Channels", TAB_NAMES, default=TAB_NAMES, label_visibility="collapsed"
        )
    else:
        sel_channels = TAB_NAMES

    regions = sorted(data["Region_Clean"].dropna().unique().tolist())
    st.markdown("<p>Region</p>", unsafe_allow_html=True)
    sel_regions = st.multiselect(
        "Region", ["All"] + regions, default=["All"], label_visibility="collapsed"
    )

    st.markdown("<p>From</p>", unsafe_allow_html=True)
    fc1, fc2 = st.columns(2)
    from_month = fc1.selectbox("FM", MONTH_ABBR, index=0, label_visibility="collapsed", key="from_month")
    from_year = fc2.selectbox("FY", all_years, index=0, label_visibility="collapsed", key="from_year")

    st.markdown("<p>To</p>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    to_month = tc1.selectbox("TM", MONTH_ABBR, index=len(MONTH_ABBR)-1, label_visibility="collapsed", key="to_month")
    to_year = tc2.selectbox("TY", all_years, index=len(all_years)-1, label_visibility="collapsed", key="to_year")

    from_m = MONTH_ABBR.index(from_month) + 1
    to_m = MONTH_ABBR.index(to_month) + 1
    from_year = int(from_year)
    to_year = int(to_year)

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ════════════════════════════════════════════════════════════
# FILTER DATA
# ════════════════════════════════════════════════════════════
df = data.copy()
if sel_channels:
    df = df[df["channel"].isin(sel_channels)]
if sel_regions and "All" not in sel_regions:
    df = df[df["Region_Clean"].isin(sel_regions)]

df = df[
    ((df["year"] > from_year) | ((df["year"] == from_year) & (df["month_num"] >= from_m))) &
    ((df["year"] < to_year) | ((df["year"] == to_year) & (df["month_num"] <= to_m)))
]

# Budget data filtered the same way (region + date range) so the overlay always matches
# whatever's currently shown in the leads chart. Regions with no budget rows (e.g. Austin)
# simply contribute $0 rather than breaking the filter.
budget_df = budget_data.copy()
if sel_regions and "All" not in sel_regions:
    budget_df = budget_df[budget_df["Region_Clean"].isin(sel_regions)]
budget_df = budget_df[
    ((budget_df["year"] > from_year) | ((budget_df["year"] == from_year) & (budget_df["month_num"] >= from_m))) &
    ((budget_df["year"] < to_year) | ((budget_df["year"] == to_year) & (budget_df["month_num"] <= to_m)))
]
budget_trend = budget_df.groupby("Period", as_index=False)["spend"].sum().sort_values("Period")

# ════════════════════════════════════════════════════════════
# TOP BAR
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="background:{ACCENT};padding:10px 20px;border-radius:8px;'
    'display:flex;align-items:center;gap:10px;margin-bottom:18px">'
    '<span style="color:white;font-weight:700;font-size:1rem">Channel Trends</span>'
    '<span style="width:1px;height:22px;background:rgba(255,255,255,0.35);display:inline-block"></span>'
    f'<span style="margin-left:auto;color:rgba(255,255,255,0.85);font-size:0.8rem">{from_month} {from_year} – {to_month} {to_year}</span>'
    '</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# KPI CARDS
# ════════════════════════════════════════════════════════════
sums = df[["unique_leads", "new_leads", "apt", "quote", "customers", "sales_amount"]].sum()

def kpi_card(label, value, color):
    return (f'<div style="background:white;border:1px solid #e5e7eb;border-radius:10px;'
            'padding:14px 14px 12px;position:relative;overflow:hidden">'
            f'<div style="position:absolute;top:0;left:0;right:0;height:4px;border-radius:10px 10px 0 0;background:{color}"></div>'
            f'<div style="font-size:0.58rem;color:#9ca3af;font-weight:600;text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px">{label}</div>'
            f'<div style="font-size:1.3rem;font-weight:500;color:#111827">{value}</div></div>')

st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:26px">' +
    kpi_card("Unique Leads", fn(sums["unique_leads"]), "#8b5cf6") +
    kpi_card("New Leads", fn(sums["new_leads"]), "#10b981") +
    kpi_card("Appointments", fn(sums["apt"]), "#f59e0b") +
    kpi_card("Customers", fn(sums["customers"]), "#06b6d4") +
    kpi_card("Sales Amount", fc(sums["sales_amount"]), "#22c55e") +
    kpi_card("Quote", fn(sums["quote"]), "#ef4444") +
    '</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TREND CHART (one line per selected channel, metric toggle)
# ════════════════════════════════════════════════════════════
st.markdown(sh("📈 Trend by Channel") + sb_o(), unsafe_allow_html=True)

metric_opts = ["unique_leads", "new_leads", "apt", "customers", "sales_amount"]
metric_labels = ["Unique Leads", "New Leads", "APT", "Customers", "Sales Amount"]

if "trend_metric" not in st.session_state:
    st.session_state.trend_metric = "unique_leads"

cols = st.columns(len(metric_opts))
for i, (m, lbl) in enumerate(zip(metric_opts, metric_labels)):
    if cols[i].button(lbl, key=f"metric_{m}", use_container_width=True,
                       type="primary" if st.session_state.trend_metric == m else "secondary"):
        st.session_state.trend_metric = m
        st.rerun()

metric = st.session_state.trend_metric
metric_label = metric_labels[metric_opts.index(metric)]

show_spend = st.checkbox("📻 Overlay TV/Radio spend", value=False)

fig = go.Figure()

if view_mode == "Combined (All)":
    combined = df.groupby("Period").agg({metric: "sum"}).reset_index().sort_values("Period")
    fig.add_trace(go.Scatter(
        x=combined["Period"], y=combined[metric],
        mode="lines+markers",
        name="All Channels",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(139,92,246,0.08)",
        hovertemplate=f"<b>All Channels</b><br>%{{x|%b %Y}}<br>{metric_label}: %{{y:,.0f}}<extra></extra>"
    ))
else:
    agg = df.groupby(["channel", "Period"]).agg({metric: "sum"}).reset_index().sort_values("Period")
    for channel in sel_channels:
        cdf = agg[agg["channel"] == channel]
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["Period"], y=cdf[metric],
            mode="lines+markers",
            name=channel,
            line=dict(color=CHANNEL_COLORS.get(channel, "#888"), width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{channel}</b><br>%{{x|%b %Y}}<br>{metric_label}: %{{y:,.0f}}<extra></extra>"
        ))

fig.update_layout(
    height=380,
    margin=dict(t=20, b=40, l=55, r=20),
    paper_bgcolor="white", plot_bgcolor="white",
    xaxis=dict(showgrid=False, tickformat="%b %Y", dtick="M1"),
    yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title=metric_label),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    uirevision=f"{view_mode}-{'-'.join(sorted(sel_channels))}",
)

if show_spend and not budget_trend.empty:
    fig.add_trace(go.Bar(
        x=budget_trend["Period"], y=budget_trend["spend"],
        name="TV/Radio Spend",
        marker=dict(color="rgba(120,120,120,0.35)"),
        yaxis="y2",
        hovertemplate="<b>TV/Radio Spend</b><br>%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        yaxis2=dict(title="TV/Radio Spend ($)", overlaying="y", side="right", showgrid=False),
        barmode="overlay",
    )
elif show_spend and budget_trend.empty:
    st.caption("No TV/Radio budget data found for the currently selected region(s)/date range — this can happen for regions like Austin that have no tracked TV/Radio spend.")

st.plotly_chart(fig, use_container_width=True)
st.markdown(sb_c(), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# BREAKDOWN TABLE BY CHANNEL
# ════════════════════════════════════════════════════════════
st.markdown(sh("📋 Channel Breakdown") + sb_o(), unsafe_allow_html=True)

table = df.groupby("channel").agg({
    "unique_leads": "sum", "new_leads": "sum", "apt": "sum",
    "quote": "sum", "customers": "sum", "sales_amount": "sum",
}).reset_index()
table["APT / Leads"] = (table["apt"] / table["unique_leads"].replace(0, 1) * 100).round(1).astype(str) + "%"
table["Customers / Leads"] = (table["customers"] / table["unique_leads"].replace(0, 1) * 100).round(1).astype(str) + "%"

disp = table.copy()
disp["sales_amount"] = disp["sales_amount"].apply(fc)
for col in ["unique_leads", "new_leads", "apt", "quote", "customers"]:
    disp[col] = disp[col].apply(fn)
disp = disp.rename(columns={
    "channel": "Channel", "unique_leads": "Unique Leads", "new_leads": "New Leads",
    "apt": "APT", "quote": "Quote", "customers": "Customers", "sales_amount": "Sales Amount"
})
st.dataframe(disp, use_container_width=True, hide_index=True)
st.markdown(sb_c(), unsafe_allow_html=True)
