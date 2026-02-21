"""
NSE Trading Dashboard
─────────────────────
Google Drive auth via Service Account JSON stored in Streamlit secrets.
Secrets required (.streamlit/secrets.toml):

    DRIVE_FOLDER_ID = "your_folder_id_here"

    [gcp_service_account]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "abc123..."
    private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
    client_email = "your-sa@your-project.iam.gserviceaccount.com"
    client_id = "123456789"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

Grant the service account email Viewer access on your TradingData folder.
"""

import streamlit as st
import pandas as pd
import io
import os
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NSE Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# COLUMN RENAME MAP
# ══════════════════════════════════════════════════════════════
COL_RENAME = {
    "Open":"Open","High":"High","Low":"Low",
    "Close":"Close (₹)","Adj Close":"Adj Close","Volume":"Volume","ema20":"EMA 20",
    "SMA200":"SMA 200","SMA50":"SMA 50","SMA100":"SMA 100",
    "ticker":"Ticker","market_cap":"Market Cap","Rank":"Rank","tag":"Category",
    "daily_returns":"Daily Return",
    "Returns_1y":"Returns 1Y (₹)","Returns_pct_1y":"Returns 1Y %",
    "Returns_6m":"Returns 6M (₹)","Returns_pct_6m":"Returns 6M %",
    "Returns_3m":"Returns 3M (₹)","Returns_pct_3m":"Returns 3M %",
    "Returns_1m":"Returns 1M (₹)","Returns_pct_1m":"Returns 1M %",
    "v75":"Log Return 1M",
    "Mean_daily_returns_1y":"Mean Daily Return 1Y","Mean_daily_returns_6m":"Mean Daily Return 6M",
    "Mean_daily_returns_3m":"Mean Daily Return 3M","Mean_daily_returns_1m":"Mean Daily Return 1M",
    "standard_deviation_1y":"Std Dev 1Y","standard_deviation_6m":"Std Dev 6M",
    "standard_deviation_3m":"Std Dev 3M","standard_deviation_1m":"Std Dev 1M",
    "momentum_1y":"Momentum 1Y","momentum_6m":"Momentum 6M",
    "momentum_3m":"Momentum 3M","momentum_1m":"Momentum 1M",
    "Momentum_ratio_1y_6m_3m":"Momentum Ratio 1Y/6M/3M","Momentum_ratio_1y_6m":"Momentum Ratio 1Y/6M",
    "52_WEEK_HIGH":"52-Week High","v22":"% from 52W High",
    "52weeklow":"52-Week Low","52weeklow_pct":"% from 52W Low",
    "v65":"Daily Avg Volume","v67":"Count After Vol+SMA200",
    "v1_vol":"Vol Filter (All)","v2_vol":"Vol Filter (Nifty50+Next50)",
    "v2_vol_nif_100":"Vol Filter (Nifty100)","v2_vol_midcap":"Vol Filter (Midcap)",
    "v2_vol_smallcap":"Vol Filter (Smallcap)","v2_vol_microcap":"Vol Filter (Microcap)",
    "v2_vol_ema_4":"Vol EMA 4","v2_vol_ema_10":"Vol EMA 10","v65_proportion":"Volume Proportion",
    "Z_score_1y":"Z-Score 1Y","Z_score_6m":"Z-Score 6M","Z_score_3m":"Z-Score 3M",
    "z_score_1y":"Z-Score 1Y","z_score_6m":"Z-Score 6M","z_score_3m":"Z-Score 3M",
    "z_score_1m":"Z-Score 1M","z_score_1y_6m_3m":"Z-Score 1Y+6M+3M","z_score_1y_6m":"Z-Score 1Y+6M",
    "v32":"Rank: Returns 1Y","v33":"Rank: Returns 6M","v34":"Rank: Returns 3M",
    "v35":"Rank: Momentum 1Y","v36":"Rank: Momentum 6M","v37":"Rank: Momentum 3M",
    "v38":"Rank: Z-Score 1Y","v39":"Rank: Z-Score 6M","v40":"Rank: Z-Score 3M",
    "v47":"Rank: 52W High %",
    "v48":"Rank: Avg Returns (1Y+6M+52W)","v49":"Rank: Avg Returns (1Y+6M+3M+52W)",
    "v50":"Rank: Avg Momentum (1Y+6M+52W)","v51":"Rank: Avg Momentum (1Y+6M+3M+52W)",
    "v52":"Rank: Avg Z-Score (1Y+6M+52W)","v53":"Rank: Avg Z-Score (1Y+6M+3M+52W)",
    "v58":"Z-Score (1Y+6M)","v59":"Z-Score (1Y+6M+3M)",
    "v60":"Rank: Z-Score (1Y+6M)","v61":"Rank: Z-Score (1Y+6M+3M)",
    "v62":"Returns (6M+3M)","v63":"Rank: Returns (6M+3M)","v64":"Rank: Returns 3M (Alt)",
    "v76":"Rank: Returns 1M","v81":"Rank: Returns (1M+3M)",
    "v84":"Rank: Avg Returns (1Y+6M+3M)","v85":"Rank: Avg Returns (6M+3M+1M)",
    "v86":"Rank: Avg Returns (1Y+6M+3M+1M)",
    "Rank_based_on_Momentum_ratio_1y_3m_6m":"Rank: Mom Ratio (1Y/3M/6M)",
    "Rank_based_on_Momentum_ratio_1y_6m":"Rank: Mom Ratio (1Y/6M)",
    "Rank_based_on_z_score_1y_6m_3m":"Rank: Z-Score (1Y+6M+3M)",
    "Rank_based_on_z_score_1y_6m":"Rank: Z-Score (1Y+6M)",
    "Rank_Based_3m_returns":"Rank: Returns 3M","Rank_Based_1m_returns":"Rank: Returns 1M",
    "Avg_Returns_3m_1m":"Avg Returns (3M+1M)","Rank_Based_avg_3m_1m_returns":"Rank: Avg Returns (3M+1M)",
    "total_account_value":"Total Account Value","total_portfolio_value":"Total Portfolio Value",
    "daily_return":"Daily Return (Portfolio)","cumulative_return":"Cumulative Return",
    "cumulative_return_20EMA":"Cumulative Return 20EMA",
    "allocation":"Allocation %","shares_to_buy":"Shares to Buy","actual_investment":"Investment (₹)",
}

COL_GROUPS = {
    "🏷️ Identity":      ["ticker","tag","market_cap","Rank"],
    "💰 Price & SMAs":  ["Close","Open","High","Low","Volume","Adj Close","ema20","SMA200","SMA50","SMA100"],
    "📈 Returns %":     ["Returns_pct_1y","Returns_pct_6m","Returns_pct_3m","Returns_pct_1m","v62"],
    "📦 Returns Raw":   ["Returns_1y","Returns_6m","Returns_3m","Returns_1m","v75","daily_returns"],
    "🔁 Momentum":      ["momentum_1y","momentum_6m","momentum_3m","momentum_1m","Momentum_ratio_1y_6m_3m","Momentum_ratio_1y_6m"],
    "📐 Z-Scores":      ["Z_score_1y","Z_score_6m","Z_score_3m","z_score_1y","z_score_6m","z_score_3m","z_score_1m","z_score_1y_6m_3m","z_score_1y_6m","v58","v59"],
    "📊 Std Dev & Mean":["standard_deviation_1y","standard_deviation_6m","standard_deviation_3m","standard_deviation_1m","Mean_daily_returns_1y","Mean_daily_returns_6m","Mean_daily_returns_3m","Mean_daily_returns_1m"],
    "📉 52-Week":       ["52_WEEK_HIGH","v22","52weeklow","52weeklow_pct"],
    "📦 Volume":        ["Volume","v65","v67","v1_vol","v2_vol","v2_vol_nif_100","v2_vol_midcap","v2_vol_smallcap","v2_vol_microcap","v2_vol_ema_4","v2_vol_ema_10","v65_proportion"],
    "🏅 Rankings":      ["v32","v33","v34","v35","v36","v37","v38","v39","v40","v47","v48","v49","v50","v51","v52","v53","v60","v61","v63","v64","v76","v81","v84","v85","v86","Rank_based_on_Momentum_ratio_1y_3m_6m","Rank_based_on_Momentum_ratio_1y_6m","Rank_based_on_z_score_1y_6m_3m","Rank_based_on_z_score_1y_6m","Rank_Based_3m_returns","Rank_Based_1m_returns","Rank_Based_avg_3m_1m_returns"],
    "💼 Portfolio":     ["total_account_value","total_portfolio_value","daily_return","cumulative_return","cumulative_return_20EMA","allocation","shares_to_buy","actual_investment"],
}

FILE_MAP = {
    "top5_stocks.csv":                                          "top5",
    "top10_stocks.csv":                                         "top10",
    "top20_stocks.csv":                                         "top20",
    "top30_stocks.csv":                                         "top30",
    "top_100_filtered_latest_based_on_z_score.csv":             "top100_z",
    "top_100_filtered_latest_based_on_momentum_ratio.csv":      "top100_m",
    "top_100_filtered_latest_based_on_momentum_ratio__1_.csv":  "top100_m",
    "bottom_20_filtered_latest.csv":                            "bottom20",
    "daily_portfolio_history_with_all_data.csv":                "portfolio",
}

TAG_COLORS = {
    "Nifty 50":"#38bdf8","Nifty Next 50":"#818cf8",
    "Nifty Midcap 150":"#34d399","Nifty SmallCap 250":"#fbbf24",
    "Nifty MicroCap 250":"#f87171","Other 500 Stocks":"#64748b",
}

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0a0e1a;color:#e2e8f0;}
section[data-testid="stSidebar"]{background:#0d1220;border-right:1px solid #1e2d4a;}
section[data-testid="stSidebar"] *{color:#cbd5e1 !important;}
section[data-testid="stSidebar"] .stRadio label{font-size:.88rem !important;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:1.65rem;font-weight:600;
  background:linear-gradient(90deg,#38bdf8,#818cf8,#34d399);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  margin:.5rem 0 .2rem;letter-spacing:-.5px;}
.page-sub{font-size:.76rem;color:#475569;font-family:'IBM Plex Mono',monospace;
  margin-bottom:1.2rem;letter-spacing:1px;text-transform:uppercase;}
div[data-testid="metric-container"]{background:#0f172a;border:1px solid #1e293b;
  border-radius:10px;padding:.85rem 1rem;transition:border-color .2s,transform .15s;}
div[data-testid="metric-container"]:hover{border-color:#38bdf844;transform:translateY(-1px);}
div[data-testid="stMetricValue"]{font-family:'IBM Plex Mono',monospace !important;font-size:1.35rem !important;color:#38bdf8 !important;}
div[data-testid="stMetricLabel"]{color:#64748b !important;font-size:.7rem !important;}
.stTabs [data-baseweb="tab-list"]{background:#0f172a;border-radius:10px 10px 0 0;padding:5px 6px 0;gap:3px;border-bottom:1px solid #1e293b;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#64748b;border-radius:7px 7px 0 0;font-size:.79rem;font-weight:500;padding:7px 12px;border:none;}
.stTabs [aria-selected="true"]{background:#1e293b !important;color:#38bdf8 !important;border-bottom:2px solid #38bdf8 !important;}
.stTabs [data-baseweb="tab-panel"]{background:#0f172a;border:1px solid #1e293b;border-top:none;border-radius:0 0 10px 10px;padding:1.1rem;}
div[data-testid="stDataFrame"]{border:1px solid #1e293b;border-radius:10px;overflow:hidden;}
div[data-baseweb="select"]>div{background:#0f172a !important;border-color:#1e293b !important;}
div[data-baseweb="input"]>div{background:#0f172a !important;border-color:#1e293b !important;}
div[data-baseweb="select"] span{color:#cbd5e1 !important;}
.stButton>button{background:#1e293b;color:#38bdf8;border:1px solid #38bdf833;border-radius:8px;font-family:'IBM Plex Mono',monospace;font-size:.75rem;transition:all .2s;}
.stButton>button:hover{background:#38bdf811;border-color:#38bdf8;}
.stDownloadButton>button{background:#0f2e1e !important;color:#34d399 !important;border:1px solid #34d39933 !important;border-radius:8px;font-size:.75rem;}
.sec-label{font-family:'IBM Plex Mono',monospace;font-size:.66rem;letter-spacing:2px;text-transform:uppercase;color:#334155;border-bottom:1px solid #1e293b;padding-bottom:4px;margin:1.1rem 0 .65rem;}
.stock-card{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:.85rem .65rem;text-align:center;transition:border-color .2s,transform .15s;}
.stock-card:hover{border-color:#38bdf855;transform:translateY(-2px);}
hr{border-color:#1e293b !important;}
div[data-testid="stAlert"]{border-radius:10px;}
code{background:#1e293b !important;color:#34d399 !important;border-radius:4px;}
pre{background:#0f172a !important;border:1px solid #1e293b !important;border-radius:8px !important;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# GOOGLE DRIVE — Service Account
# ══════════════════════════════════════════════════════════════
def _drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        sa = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            sa, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def _folder_index() -> dict:
    """Returns {app_key: file_id} by listing the Drive folder."""
    folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
    if not folder_id:
        return {}
    svc = _drive_service()
    if svc is None:
        return {}
    try:
        res = svc.files().list(
            q=f"'{folder_id}' in parents and mimeType='text/csv' and trashed=false",
            fields="files(id,name)", pageSize=50,
        ).execute()
        name_to_id = {f["name"]: f["id"] for f in res.get("files", [])}
        return {app_key: name_to_id[fname]
                for fname, app_key in FILE_MAP.items()
                if fname in name_to_id}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_csv(file_id: str) -> pd.DataFrame | None:
    svc = _drive_service()
    if svc is None:
        return None
    try:
        from googleapiclient.http import MediaIoBaseDownload
        req  = svc.files().get_media(fileId=file_id)
        buf  = io.BytesIO()
        dl   = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        buf.seek(0)
        return pd.read_csv(buf)
    except Exception:
        return None


LOCAL = {
    "top5":     "data/top5_stocks.csv",
    "top10":    "data/top10_stocks.csv",
    "top20":    "data/top20_stocks.csv",
    "top30":    "data/top30_stocks.csv",
    "top100_z": "data/top_100_filtered_latest_based_on_z_score.csv",
    "top100_m": "data/top_100_filtered_latest_based_on_momentum_ratio.csv",
    "bottom20": "data/bottom_20_filtered_latest.csv",
    "portfolio":"data/daily_portfolio_history_with_all_data.csv",
}

def load_df(key: str) -> pd.DataFrame | None:
    idx = _folder_index()
    if key in idx:
        df = _fetch_csv(idx[key])
        if df is not None and not df.empty:
            return df
    p = LOCAL.get(key, "")
    if p and os.path.exists(p):
        try: return pd.read_csv(p)
        except Exception: pass
    return None


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def pretty(c):
    return COL_RENAME.get(c, c.replace("_"," ").title())

def ren(df):
    return df.rename(columns={c:pretty(c) for c in df.columns})

def fnum(v):
    try: return float(v)
    except Exception: return None

PBASE = dict(
    paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
    font=dict(color="#94a3b8", family="Inter", size=11),
    title_font=dict(family="IBM Plex Mono", size=12, color="#cbd5e1"),
    xaxis=dict(showgrid=False, color="#475569", tickangle=-35),
    yaxis=dict(showgrid=True, gridcolor="#1e293b", color="#475569"),
    legend=dict(bgcolor="#0f172a", bordercolor="#1e293b", font=dict(size=10)),
    margin=dict(t=44, b=54, l=14, r=14),
)

# ── Charts ─────────────────────────────────────────────────
def ch_returns(df):
    cm = {"Returns_pct_1y":"1Y","Returns_pct_6m":"6M","Returns_pct_3m":"3M","Returns_pct_1m":"1M"}
    cl = {"1Y":"#818cf8","6M":"#38bdf8","3M":"#34d399","1M":"#fbbf24"}
    av = {k:v for k,v in cm.items() if k in df.columns}
    if not av or "ticker" not in df.columns: return None
    p = df.head(25)
    fig = go.Figure()
    for raw,lbl in av.items():
        fig.add_trace(go.Bar(name=lbl, x=p["ticker"].astype(str), y=p[raw],
            marker_color=cl[lbl], opacity=0.85,
            text=p[raw].round(1).astype(str)+"%", textposition="outside", textfont=dict(size=7)))
    fig.update_layout(barmode="group", title="Returns by Period", **PBASE)
    return fig

def ch_momentum(df):
    cm = {"momentum_1y":"1Y","momentum_6m":"6M","momentum_3m":"3M","momentum_1m":"1M"}
    cl = {"1Y":"#818cf8","6M":"#38bdf8","3M":"#34d399","1M":"#fbbf24"}
    av = {k:v for k,v in cm.items() if k in df.columns}
    if not av or "ticker" not in df.columns: return None
    p = df.head(25)
    fig = go.Figure()
    for raw,lbl in av.items():
        fig.add_trace(go.Bar(name=lbl, x=p["ticker"].astype(str), y=p[raw], marker_color=cl[lbl], opacity=0.85))
    fig.update_layout(barmode="group", title="Momentum by Period", **PBASE)
    return fig

def ch_zscore(df):
    z1 = next((c for c in ["Z_score_1y","z_score_1y"] if c in df.columns), None)
    z6 = next((c for c in ["Z_score_6m","z_score_6m"] if c in df.columns), None)
    z3 = next((c for c in ["Z_score_3m","z_score_3m"] if c in df.columns), None)
    av = {k:v for k,v in {"Z 1Y":z1,"Z 6M":z6,"Z 3M":z3}.items() if v}
    if not av or "ticker" not in df.columns: return None
    cl = {"Z 1Y":"#818cf8","Z 6M":"#38bdf8","Z 3M":"#34d399"}
    p = df.head(25)
    fig = go.Figure()
    for lbl,raw in av.items():
        fig.add_trace(go.Bar(name=lbl, x=p["ticker"].astype(str), y=p[raw], marker_color=cl[lbl], opacity=0.85))
    fig.update_layout(barmode="group", title="Z-Scores by Period", **PBASE)
    return fig

def ch_mom_ratio(df):
    av = {v:k for k,v in {"Momentum_ratio_1y_6m":"1Y/6M","Momentum_ratio_1y_6m_3m":"1Y/6M/3M"}.items() if k in df.columns}
    if not av or "ticker" not in df.columns: return None
    cl = {"1Y/6M":"#38bdf8","1Y/6M/3M":"#818cf8"}
    p = df.head(25)
    fig = go.Figure()
    for lbl,raw in av.items():
        fig.add_trace(go.Bar(name=lbl, x=p["ticker"].astype(str), y=p[raw], marker_color=cl.get(lbl,"#64748b"), opacity=0.85))
    fig.update_layout(barmode="group", title="Momentum Ratios", **PBASE)
    return fig

def ch_risk_return(df):
    if "Returns_pct_1y" not in df.columns or "standard_deviation_1y" not in df.columns: return None
    if "ticker" not in df.columns: return None
    p = df.copy()
    try:
        p["_mc"] = pd.to_numeric(p.get("market_cap",1e9), errors="coerce").fillna(1e9)
        p["_sz"] = (p["_mc"]/p["_mc"].max()*38+7).clip(7,45)
        fig = go.Figure()
        if "tag" in p.columns:
            for tag, grp in p.groupby("tag"):
                c = TAG_COLORS.get(str(tag),"#64748b")
                fig.add_trace(go.Scatter(x=grp["standard_deviation_1y"], y=grp["Returns_pct_1y"],
                    mode="markers+text", name=str(tag), text=grp["ticker"],
                    textposition="top center", textfont=dict(size=7, color="#94a3b8"),
                    marker=dict(color=c, size=grp["_sz"], opacity=0.8, line=dict(color="#0f172a",width=1))))
        else:
            fig.add_trace(go.Scatter(x=p["standard_deviation_1y"], y=p["Returns_pct_1y"],
                mode="markers+text", text=p["ticker"], textposition="top center",
                textfont=dict(size=7), marker=dict(color="#38bdf8", size=10, opacity=0.8)))
        fig.update_layout(title="Risk vs Return (1Y)", xaxis_title="Std Dev 1Y (Risk)", yaxis_title="Return 1Y %", **PBASE)
        return fig
    except Exception: return None

def ch_category(df):
    if "tag" not in df.columns: return None
    counts = df["tag"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.45,
        marker=dict(colors=[TAG_COLORS.get(t,"#64748b") for t in counts.index]),
        textinfo="label+percent", textfont=dict(size=10,color="#cbd5e1")))
    fig.update_layout(title="Category Breakdown", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8",family="Inter"),
        title_font=dict(family="IBM Plex Mono",size=12,color="#cbd5e1"),
        legend=dict(bgcolor="#0f172a",bordercolor="#1e293b"), margin=dict(t=44,b=20,l=20,r=20))
    return fig

def kpi_row(df):
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("Stocks", len(df))
    with c2:
        if "Close" in df.columns:
            v = pd.to_numeric(df["Close"],errors="coerce").mean()
            st.metric("Avg Price", f"₹{v:,.0f}" if pd.notna(v) else "—")
    with c3:
        if "Returns_pct_1y" in df.columns:
            v = pd.to_numeric(df["Returns_pct_1y"],errors="coerce").mean()
            st.metric("Avg Return 1Y", f"{v:.1f}%" if pd.notna(v) else "—", delta=f"{v:+.1f}%" if pd.notna(v) else None)
    with c4:
        if "Returns_pct_6m" in df.columns:
            v = pd.to_numeric(df["Returns_pct_6m"],errors="coerce").mean()
            st.metric("Avg Return 6M", f"{v:.1f}%" if pd.notna(v) else "—", delta=f"{v:+.1f}%" if pd.notna(v) else None)
    with c5:
        if "momentum_1y" in df.columns:
            v = pd.to_numeric(df["momentum_1y"],errors="coerce").mean()
            st.metric("Avg Mom 1Y", f"{v:.2f}" if pd.notna(v) else "—")
    with c6:
        if "Rank" in df.columns:
            best = pd.to_numeric(df["Rank"],errors="coerce").min()
            st.metric("Best Rank", int(best) if pd.notna(best) else "—")

def stock_cards(df, n=10):
    if "ticker" not in df.columns: return
    rows = df.head(n)
    cols = st.columns(len(rows))
    for i,(_,row) in enumerate(rows.iterrows()):
        ret=fnum(row.get("Returns_pct_1y")); ret6=fnum(row.get("Returns_pct_6m"))
        mom=fnum(row.get("momentum_1y")); price=fnum(row.get("Close"))
        rc = "#34d399" if (ret is not None and ret>=0) else "#f87171"
        with cols[i]:
            st.markdown(f"""
            <div class="stock-card">
                <div style="font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:#38bdf8;margin-bottom:3px">#{row.get('Rank','')}</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:.92rem;font-weight:600;color:#e2e8f0">{row['ticker']}</div>
                <div style="font-size:.78rem;color:#94a3b8;margin:3px 0">{'₹'+f'{price:,.0f}' if price else '—'}</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:.98rem;font-weight:600;color:{rc}">{f'{ret:+.1f}%' if ret is not None else '—'}</div>
                <div style="font-size:.62rem;color:#475569">1Y Return</div>
                <div style="font-size:.73rem;color:#818cf8;margin-top:3px">{f'6M: {ret6:+.1f}%' if ret6 is not None else ''}</div>
                <div style="font-size:.68rem;color:#334155;margin-top:2px">{f'Mom: {mom:.2f}' if mom is not None else ''}</div>
                <div style="font-size:.62rem;color:#475569;margin-top:3px">{str(row.get('tag',''))}</div>
            </div>""", unsafe_allow_html=True)

def grouped_table(df, key):
    all_cols = set(df.columns)
    gd = {g:[c for c in cs if c in all_cols] for g,cs in COL_GROUPS.items()}
    gd = {g:cs for g,cs in gd.items() if cs}
    sel = st.selectbox("Column Group", ["📋 All Columns"]+list(gd.keys()), key=f"cg_{key}")
    if sel=="📋 All Columns":
        show = list(df.columns)
    else:
        anc = [c for c in ["ticker","tag","Rank","Close"] if c in all_cols]
        show = list(dict.fromkeys(anc+gd.get(sel,[])))
    view = df[[c for c in show if c in all_cols]].copy()
    view = ren(view)
    cfg = {}
    for orig in show:
        if orig not in all_cols: continue
        lbl=pretty(orig)
        if "pct" in orig.lower(): cfg[lbl]=st.column_config.NumberColumn(lbl,format="%.2f%%")
        elif orig in ("Close","Open","High","Low","Adj Close","ema20","SMA200","SMA50","SMA100","52_WEEK_HIGH","52weeklow"):
            cfg[lbl]=st.column_config.NumberColumn(lbl,format="₹%.2f")
        elif "market_cap" in orig: cfg[lbl]=st.column_config.NumberColumn(lbl,format="%.2e")
        elif "volume" in orig.lower() or orig in ("Volume","v65"): cfg[lbl]=st.column_config.NumberColumn(lbl,format="%,.0f")
    st.dataframe(view, use_container_width=True, height=420, column_config=cfg)


# ══════════════════════════════════════════════════════════════
# MAIN PAGE RENDERER
# ══════════════════════════════════════════════════════════════
def render_page(key, title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)
    with st.spinner("Fetching from Google Drive…"):
        df = load_df(key)
    if df is None or df.empty:
        st.warning(f"⚠️ **{title}** data not available. Check Drive access or local `data/` folder.")
        return

    st.markdown('<div class="sec-label">Key Metrics</div>', unsafe_allow_html=True)
    kpi_row(df)

    if len(df)<=30 and "ticker" in df.columns:
        st.markdown('<div class="sec-label">Stocks at a Glance</div>', unsafe_allow_html=True)
        stock_cards(df, n=min(len(df),10))

    st.markdown('<div class="sec-label">Charts</div>', unsafe_allow_html=True)
    t1,t2,t3,t4,t5,t6 = st.tabs(["📈 Returns","🔁 Momentum","📐 Z-Scores","🚀 Mom Ratio","🎯 Risk/Return","🥧 Categories"])
    with t1:
        fig=ch_returns(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("Returns data not available.")
    with t2:
        fig=ch_momentum(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("Momentum data not available.")
    with t3:
        fig=ch_zscore(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("Z-Score data not available.")
    with t4:
        fig=ch_mom_ratio(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("Momentum ratio columns not in this file.")
    with t5:
        fig=ch_risk_return(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("Needs Returns_pct_1y + standard_deviation_1y.")
    with t6:
        fig=ch_category(df)
        st.plotly_chart(fig,use_container_width=True) if fig else st.info("No 'tag' column found.")

    st.markdown('<div class="sec-label">Filter & Explore</div>', unsafe_allow_html=True)
    fc1,fc2,fc3 = st.columns([2,2,2])
    filtered = df.copy()
    with fc1:
        if "ticker" in df.columns:
            q=st.text_input("🔎 Search ticker",key=f"s_{key}")
            if q: filtered=filtered[filtered["ticker"].astype(str).str.upper().str.contains(q.upper(),na=False)]
    with fc2:
        if "tag" in df.columns:
            tags=["All"]+sorted(df["tag"].dropna().unique().tolist())
            sel_t=st.selectbox("Category",tags,key=f"t_{key}")
            if sel_t!="All": filtered=filtered[filtered["tag"]==sel_t]
    with fc3:
        nums=filtered.select_dtypes("number").columns.tolist()
        if nums:
            lbls=[pretty(c) for c in nums]
            sl=st.selectbox("Sort by",lbls,key=f"sb_{key}")
            asc=st.radio("Order",["↓ Desc","↑ Asc"],horizontal=True,key=f"o_{key}")=="↑ Asc"
            try: filtered=filtered.sort_values(nums[lbls.index(sl)],ascending=asc)
            except Exception: pass

    st.markdown('<div class="sec-label">Data Table</div>', unsafe_allow_html=True)
    grouped_table(filtered, key)

    d1,d2,_ = st.columns([1,1,4])
    with d1:
        st.download_button("📥 Download CSV",
            data=filtered.to_csv(index=False).encode(),
            file_name=f"{key}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",key=f"dl_{key}",use_container_width=True)
    with d2: st.metric("Rows", len(filtered))


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="page-title" style="font-size:.95rem;text-align:center;">NSE Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub" style="text-align:center;margin-bottom:.4rem;">Trading Automation</div>', unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("", [
        "🏠  Home","🏆  Top 5","⭐  Top 10","📈  Top 20","📊  Top 30",
        "📐  Top 100 Z-Score","🚀  Top 100 Momentum","🔻  Bottom 20",
        "📜  Portfolio History","ℹ️  Setup & About",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="sec-label">Connection Status</div>', unsafe_allow_html=True)

    sa_ok     = "gcp_service_account" in st.secrets
    folder_ok = bool(st.secrets.get("DRIVE_FOLDER_ID",""))
    idx       = _folder_index()

    def sbadge(ok, lbl):
        c,bg = ("#34d399","#0f2e1e") if ok else ("#f87171","#2d1111")
        sym  = "✓" if ok else "✗"
        return f'<div style="background:{bg};color:{c};border:1px solid {c}33;border-radius:6px;padding:4px 10px;font-family:\'IBM Plex Mono\',monospace;font-size:.65rem;margin:3px 0">{sym} {lbl}</div>'

    st.markdown(sbadge(sa_ok,    "Service Account JSON"), unsafe_allow_html=True)
    st.markdown(sbadge(folder_ok,"Drive Folder ID"),      unsafe_allow_html=True)
    st.markdown(sbadge(len(idx)>0, f"{len(idx)}/8 files found"), unsafe_allow_html=True)

    if idx:
        st.markdown('<div class="sec-label" style="margin-top:.7rem">Files</div>', unsafe_allow_html=True)
        for k,lbl in [("top5","Top 5"),("top10","Top 10"),("top20","Top 20"),("top30","Top 30"),
                      ("top100_z","Z100"),("top100_m","Mom100"),("bottom20","Bot20"),("portfolio","Portfolio")]:
            ok=k in idx
            c,bg=("#34d399","#0f2e1e") if ok else ("#f87171","#2d1111")
            st.markdown(f'<div style="background:{bg};color:{c};border:1px solid {c}22;border-radius:4px;padding:2px 8px;font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;margin:2px 0">{"✓" if ok else "✗"} {lbl}</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Refresh from Drive", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.caption("⏰ Cache TTL: 30 min")


# ══════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════
if page == "🏠  Home":
    st.markdown('<div class="page-title">📈 NSE Trading Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Quantitative Momentum & Factor Analysis · Auto-Updated Daily</div>', unsafe_allow_html=True)

    kc=st.columns(4)
    for i,(k,lbl) in enumerate([("top5","Top 5"),("top10","Top 10"),("top20","Top 20"),("top30","Top 30")]):
        d=load_df(k)
        with kc[i]: st.metric(f"🏆 {lbl}", len(d) if d is not None else "—")

    df5=load_df("top5")
    if df5 is not None and not df5.empty and "ticker" in df5.columns:
        st.markdown("---")
        st.markdown('<div class="sec-label">Today\'s Top 5</div>', unsafe_allow_html=True)
        stock_cards(df5, n=5)

    st.markdown("---")
    st.markdown('<div class="sec-label">All Data Sources</div>', unsafe_allow_html=True)
    sources=[("top5","🏆 Top 5","Elite picks"),("top10","⭐ Top 10","High-conviction"),
             ("top20","📈 Top 20","Quality screen"),("top30","📊 Top 30","Full universe"),
             ("top100_z","📐 Z-Score 100","Z-Score ranked"),("top100_m","🚀 Momentum 100","Mom ratio ranked"),
             ("bottom20","🔻 Bottom 20","Short candidates"),("portfolio","📜 Portfolio","Daily history")]
    r1,r2=st.columns(2)
    for i,(k,lbl,desc) in enumerate(sources):
        d=load_df(k)
        ok=d is not None and not d.empty
        ar=""
        if ok and "Returns_pct_1y" in d.columns:
            v=pd.to_numeric(d["Returns_pct_1y"],errors="coerce").mean()
            ar=f"<span style='color:#34d399;font-weight:600'>{v:+.1f}% avg 1Y</span>"
        stat=(f'<span style="background:#0f2e1e;color:#34d399;border:1px solid #34d39933;font-size:.6rem;padding:1px 6px;border-radius:3px;font-family:\'IBM Plex Mono\'">✓ {len(d)} rows</span>'
              if ok else '<span style="background:#2d1111;color:#f87171;border:1px solid #f8717133;font-size:.6rem;padding:1px 6px;border-radius:3px;font-family:\'IBM Plex Mono\'">✗ Not loaded</span>')
        with (r1 if i%2==0 else r2):
            st.markdown(f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:.85rem;margin-bottom:.5rem">
                <div style="font-weight:600;color:#e2e8f0;font-size:.86rem">{lbl}</div>
                <div style="font-size:.72rem;color:#475569;margin:2px 0 7px">{desc}</div>
                <div style="display:flex;gap:10px;align-items:center">{stat} <span style="font-size:.72rem;color:#94a3b8">{ar}</span></div>
            </div>""", unsafe_allow_html=True)

elif page == "🏆  Top 5":
    render_page("top5","🏆 Top 5 Stocks","Elite Daily Picks · Momentum + Factor Ranked")
elif page == "⭐  Top 10":
    render_page("top10","⭐ Top 10 Stocks","High-Conviction Momentum List")
elif page == "📈  Top 20":
    render_page("top20","📈 Top 20 Stocks","Extended Quality Screen")
elif page == "📊  Top 30":
    render_page("top30","📊 Top 30 Stocks","Full Ranked Universe")
elif page == "📐  Top 100 Z-Score":
    render_page("top100_z","📐 Top 100 — Z-Score","Z-Score Factor Ranked · Multi-Period")
elif page == "🚀  Top 100 Momentum":
    render_page("top100_m","🚀 Top 100 — Momentum Ratio","Momentum Ratio 1Y/6M/3M Ranked")
elif page == "🔻  Bottom 20":
    render_page("bottom20","🔻 Bottom 20 — Short Candidates","Lowest Composite Score · Short Signals")


# ══════════════════════════════════════════════════════════════
# PORTFOLIO HISTORY
# ══════════════════════════════════════════════════════════════
elif page == "📜  Portfolio History":
    st.markdown('<div class="page-title">📜 Portfolio History</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Daily portfolio log with all signals</div>', unsafe_allow_html=True)
    with st.spinner("Loading…"): df=load_df("portfolio")
    if df is None or df.empty:
        st.warning("Portfolio history not available.")
    else:
        st.markdown('<div class="sec-label">Key Metrics</div>', unsafe_allow_html=True)
        kpi_row(df)
        date_col=next((c for c in df.columns if "date" in c.lower()),None)
        cum_col="cumulative_return" if "cumulative_return" in df.columns else None
        if date_col and cum_col and "ticker" in df.columns:
            st.markdown('<div class="sec-label">Cumulative Return Over Time</div>', unsafe_allow_html=True)
            try:
                df[date_col]=pd.to_datetime(df[date_col])
                top_s=df.groupby("ticker")["Returns_pct_1y"].mean().nlargest(10).index.tolist() if "Returns_pct_1y" in df.columns else df["ticker"].unique()[:10]
                pf=df[df["ticker"].isin(top_s)]
                fig=go.Figure()
                for sym,grp in pf.groupby("ticker"):
                    grp=grp.sort_values(date_col)
                    fig.add_trace(go.Scatter(x=grp[date_col],y=grp[cum_col],mode="lines",name=sym,line=dict(width=1.5)))
                fig.update_layout(title="Cumulative Return — Top 10",xaxis_title="Date",yaxis_title="Cum Return",**PBASE)
                st.plotly_chart(fig,use_container_width=True)
            except Exception: pass
        st.markdown('<div class="sec-label">Filter & Explore</div>', unsafe_allow_html=True)
        fc1,fc2,fc3=st.columns([2,2,2])
        filtered=df.copy()
        with fc1:
            if date_col:
                try:
                    df[date_col]=pd.to_datetime(df[date_col])
                    mn,mx=df[date_col].min().date(),df[date_col].max().date()
                    dr=st.date_input("Date range",[mn,mx],key="ph_dr")
                    if len(dr)==2:
                        filtered=filtered[(pd.to_datetime(filtered[date_col]).dt.date>=dr[0])&(pd.to_datetime(filtered[date_col]).dt.date<=dr[1])]
                except Exception: pass
        with fc2:
            if "ticker" in df.columns:
                q=st.text_input("🔎 Search ticker",key="ph_s")
                if q: filtered=filtered[filtered["ticker"].astype(str).str.upper().str.contains(q.upper(),na=False)]
        with fc3:
            nums=filtered.select_dtypes("number").columns.tolist()
            if nums:
                lbls=[pretty(c) for c in nums]
                sl=st.selectbox("Sort by",lbls,key="ph_sort")
                try: filtered=filtered.sort_values(nums[lbls.index(sl)],ascending=False)
                except Exception: pass
        st.markdown('<div class="sec-label">Data Table</div>', unsafe_allow_html=True)
        grouped_table(filtered,"portfolio")
        d1,d2,_=st.columns([1,1,4])
        with d1:
            st.download_button("📥 Download CSV",data=filtered.to_csv(index=False).encode(),
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv",key="ph_dl",use_container_width=True)
        with d2: st.metric("Rows",len(filtered))


# ══════════════════════════════════════════════════════════════
# SETUP & ABOUT
# ══════════════════════════════════════════════════════════════
elif page == "ℹ️  Setup & About":
    st.markdown('<div class="page-title">ℹ️ Setup & About</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Configuration guide & system overview</div>', unsafe_allow_html=True)

    s1,s2=st.columns(2)
    with s1:
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.3rem;margin-bottom:.8rem">
        <h4 style="color:#38bdf8;font-family:'IBM Plex Mono',monospace;margin:0 0 .7rem">① Google Cloud</h4>
        <ol style="color:#94a3b8;font-size:.82rem;line-height:1.9;padding-left:1.1rem">
            <li>Go to <b style="color:#cbd5e1">console.cloud.google.com</b></li>
            <li>Enable <b style="color:#cbd5e1">Google Drive API</b></li>
            <li>IAM → Service Accounts → Create</li>
            <li>Keys → Add Key → <b style="color:#cbd5e1">JSON</b> → Download</li>
        </ol>
        </div>
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.3rem">
        <h4 style="color:#818cf8;font-family:'IBM Plex Mono',monospace;margin:0 0 .7rem">② Share Drive Folder</h4>
        <ol style="color:#94a3b8;font-size:.82rem;line-height:1.9;padding-left:1.1rem">
            <li>Right-click <b style="color:#cbd5e1">TradingData</b> folder → Share</li>
            <li>Paste service account email → <b style="color:#cbd5e1">Viewer</b></li>
            <li>Copy folder ID from URL:<br><code>drive.google.com/drive/folders/<b>FOLDER_ID</b></code></li>
        </ol>
        </div>""", unsafe_allow_html=True)

    with s2:
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.3rem;margin-bottom:.8rem">
        <h4 style="color:#34d399;font-family:'IBM Plex Mono',monospace;margin:0 0 .7rem">③ Streamlit Secrets</h4>
        <p style="color:#94a3b8;font-size:.82rem;margin:0 0 .5rem">App Settings → Secrets → paste:</p>
        </div>""", unsafe_allow_html=True)

        st.code("""# .streamlit/secrets.toml

DRIVE_FOLDER_ID = "1AbCdEfGhIjKlMnOpQrStUvW"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = \"\"\"-----BEGIN RSA PRIVATE KEY-----
...your key...
-----END RSA PRIVATE KEY-----\"\"\"
client_email = "sa@project.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/sa%40project.iam.gserviceaccount.com"
""", language="toml")

        st.markdown("""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.3rem;margin-top:.8rem">
        <h4 style="color:#fbbf24;font-family:'IBM Plex Mono',monospace;margin:0 0 .5rem">④ requirements.txt</h4>
        </div>""", unsafe_allow_html=True)
        st.code("streamlit\npandas\nplotly\ngoogle-api-python-client\ngoogle-auth", language="text")

    st.markdown('<div class="sec-label">How It Works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.3rem">
    <ul style="color:#94a3b8;font-size:.83rem;line-height:2;padding-left:1.2rem;margin:0">
        <li><b style="color:#cbd5e1">Startup:</b> App lists all CSVs in your Drive folder automatically — no hardcoded file IDs</li>
        <li><b style="color:#cbd5e1">Download:</b> Each CSV is streamed into memory via <code>files().get_media()</code></li>
        <li><b style="color:#cbd5e1">Cache:</b> Data cached for 30 minutes — click <em>Refresh from Drive</em> to force reload</li>
        <li><b style="color:#cbd5e1">Fallback:</b> If Drive is unavailable, reads from local <code>data/</code> folder</li>
        <li><b style="color:#cbd5e1">Columns:</b> All v-code columns (v22, v32–v86, v65, v67…) auto-renamed to readable labels</li>
        <li><b style="color:#cbd5e1">Update trigger:</b> GitHub Actions writes new CSVs to Drive at 3 PM IST → app picks them up within 30 min</li>
    </ul>
    </div>""", unsafe_allow_html=True)

    st.warning("⚠️ For educational purposes only. Not financial advice.")