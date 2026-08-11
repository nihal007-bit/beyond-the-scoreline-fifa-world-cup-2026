import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.cards import load_css, section_header, divider, kpi_card, bottom_nav

st.set_page_config(page_title="xG Analysis · WC 2026", page_icon="WC", layout="wide")
load_css()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
OUTPUTS = Path(__file__).parent.parent.parent / "outputs"

st.markdown("""
<div style="padding:16px 0 12px;border-bottom:1px solid #21262D;margin-bottom:20px;">
    <div style="font-size:20px;font-weight:700;color:#E6EDF3;">xG Analysis</div>
    <div style="font-size:13px;color:#8B949E;margin-top:2px;">
        2022 World Cup benchmark · StatsBomb open data</div>
</div>
""", unsafe_allow_html=True)

xg_path = DATA_DIR / "team_xg_2022.csv"
if xg_path.exists():
    df_xg = pd.read_csv(xg_path)

    clinical = df_xg.nlargest(1, "xg_overperformance").iloc[0]
    wasteful = df_xg.nsmallest(1, "xg_overperformance").iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("T", str(len(df_xg)), "TEAMS")
    with c2:
        kpi_card("S", str(int(df_xg["shots_taken"].sum())), "TOTAL SHOTS")
    with c3:
        kpi_card("+", clinical["team"], "MOST CLINICAL",
                 f"+{clinical['xg_overperformance']:.1f}", True)
    with c4:
        kpi_card("-", wasteful["team"], "MOST WASTEFUL",
                 f"{wasteful['xg_overperformance']:.1f}", False)

    divider()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_xg["total_xg_for"], y=df_xg["actual_goals"],
        mode="markers+text",
        marker=dict(size=df_xg["shots_taken"] / 3, color="#388BFD",
                    opacity=0.7, line=dict(width=1, color="#E6EDF3")),
        text=df_xg["team"], textposition="top center",
        textfont=dict(size=9, color="#8B949E"),
    ))
    max_val = max(df_xg["total_xg_for"].max(), df_xg["actual_goals"].max()) + 2
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines", line=dict(dash="dash", color="#30363D"),
    ))
    fig.update_layout(
        plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
        font=dict(color="#8B949E"),
        xaxis=dict(title="Total xG", gridcolor="#21262D"),
        yaxis=dict(title="Actual Goals", gridcolor="#21262D"),
        height=500, margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text="xG Efficiency — 2022 World Cup",
                   font=dict(color="#E6EDF3", size=14)),
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    <div style="font-size:12px;color:#6E7681;text-align:center;padding:8px 0;">
        Above line = clinical · Below = wasteful · Bubble size = total shots
    </div>
    """, unsafe_allow_html=True)

    shotmaps = sorted(OUTPUTS.glob("shotmap_*.png"))
    if shotmaps:
        divider()
        section_header("Shot Maps — 2022 Semi-finalists")
        cols = st.columns(2)
        for i, sm in enumerate(shotmaps):
            with cols[i % 2]:
                st.image(str(sm), width="stretch")
else:
    st.info("Run notebooks/03_xg_analysis.py")

bottom_nav()
