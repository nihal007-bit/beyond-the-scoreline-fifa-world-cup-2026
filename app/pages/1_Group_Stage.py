import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.cards import load_css, section_header, divider, kpi_card, bottom_nav
from data_loader import load_live_data

st.set_page_config(page_title="Group Stage · WC 2026", page_icon="WC", layout="wide")
load_css()

data = load_live_data()
standings = data["standings"]
gci = data["gci"]
matches = data["matches"]

st.markdown("""
<div style="padding:16px 0 12px;border-bottom:1px solid #21262D;margin-bottom:20px;">
    <div style="font-size:20px;font-weight:700;color:#E6EDF3;">Group Stage Analysis</div>
    <div style="font-size:13px;color:#8B949E;margin-top:2px;">48 teams · 12 groups · Complete</div>
</div>
""", unsafe_allow_html=True)

tab_standings, tab_gci, tab_goals = st.tabs(["Standings", "Competitiveness", "Goals"])

with tab_standings:
    if not standings.empty:
        groups = sorted(standings["group"].unique())
        cols = st.columns(3)
        for i, group in enumerate(groups):
            with cols[i % 3]:
                grp_label = group.replace("GROUP_", "Group ")
                st.markdown(f'<div style="font-size:13px;font-weight:600;color:#E6EDF3;'
                            f'margin:12px 0 6px;">{grp_label}</div>', unsafe_allow_html=True)
                grp = standings[standings["group"] == group].sort_values("position")
                for _, row in grp.iterrows():
                    pos = int(row["position"])
                    border = "#3FB950" if pos <= 2 else "#E3B341" if pos == 3 else "#F85149"
                    opacity = "1" if pos <= 2 else "0.9" if pos == 3 else "0.5"
                    weight = "600" if pos <= 2 else "400"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:7px 10px;margin-bottom:4px;background:#21262D;
                                border-radius:6px;border-left:3px solid {border};opacity:{opacity};">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="color:#6E7681;font-size:12px;width:14px;">{pos}</span>
                            <span style="font-size:13px;color:#E6EDF3;font-weight:{weight};">
                                {row["team"]}</span>
                        </div>
                        <div style="display:flex;gap:12px;font-size:12px;">
                            <span style="color:#8B949E;">{row["played"]}GP</span>
                            <span style="color:#8B949E;">{row["goals_for"]}:{row["goals_against"]}</span>
                            <span style="color:#E6EDF3;font-weight:600;width:20px;text-align:right;">
                                {row["points"]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

with tab_gci:
    if not gci.empty:
        st.markdown("""
        <div style="background:#21262D;border:1px solid #30363D;border-radius:8px;
                    padding:14px 16px;margin-bottom:16px;">
            <div style="font-size:13px;color:#E6EDF3;font-weight:600;margin-bottom:6px;">
                What is the Group Competitiveness Index?</div>
            <div style="font-size:13px;color:#8B949E;line-height:1.6;">
                GCI = std(points) / mean(points).<br/>
                <strong style="color:#E6EDF3;">Lower = more competitive</strong>
                (teams closely bunched). Higher = dominant winner.
            </div>
        </div>
        """, unsafe_allow_html=True)

        gci_sorted = gci.sort_values("GCI")
        fig = go.Figure(go.Bar(
            y=[g.replace("GROUP_", "") for g in gci_sorted["group"]],
            x=gci_sorted["GCI"], orientation="h",
            marker_color=["#3FB950" if v < 0.5 else "#E3B341" if v < 0.65 else "#F85149"
                          for v in gci_sorted["GCI"]],
            text=[f"{v:.2f}" for v in gci_sorted["GCI"]],
            textposition="outside", textfont=dict(color="#E6EDF3", size=12),
        ))
        fig.update_layout(
            plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
            font=dict(color="#8B949E"),
            xaxis=dict(gridcolor="#21262D", title="GCI"),
            yaxis=dict(gridcolor="#21262D"), height=420,
            margin=dict(l=10, r=60, t=20, b=20),
        )
        st.plotly_chart(fig, width="stretch")

        most = gci_sorted.iloc[0]
        least = gci_sorted.iloc[-1]
        c1, c2 = st.columns(2)
        with c1:
            kpi_card("<<", f"Group {most['group'].replace('GROUP_','')}", "MOST COMPETITIVE",
                     f"GCI = {most['GCI']:.2f}", True)
        with c2:
            kpi_card(">>", f"Group {least['group'].replace('GROUP_','')}", "LEAST COMPETITIVE",
                     f"GCI = {least['GCI']:.2f}", False)

with tab_goals:
    if not matches.empty:
        gs = matches[matches["stage"] == "GROUP_STAGE"]
        gpg_2026 = round(gs["total_goals"].sum() / len(gs), 2) if len(gs) > 0 else 0

        hist = {"2014": 2.67, "2018": 2.64, "2022": 2.69, "2026": gpg_2026}
        fig = go.Figure(go.Bar(
            x=list(hist.keys()), y=list(hist.values()),
            marker_color=["#3f3f46", "#3f3f46", "#3f3f46", "#6366f1"],
            text=[f"{v:.2f}" for v in hist.values()],
            textposition="outside", textfont=dict(color="#e4e4e7"),
        ))
        fig.update_layout(
            plot_bgcolor="#09090b", paper_bgcolor="#09090b",
            font=dict(color="#63636e"),
            yaxis=dict(range=[2.3, 3.3], gridcolor="#1e1e26", title="Goals per game"),
            xaxis=dict(gridcolor="#1e1e26"), height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            title=dict(text="Goals Per Game - Historical", font=dict(color="#e4e4e7", size=13)),
        )
        st.plotly_chart(fig, width="stretch")

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("AVG", str(gpg_2026), "2026 GPG",
                     f"{gpg_2026 - 2.69:+.2f} vs 2022", gpg_2026 > 2.69)
        with c2:
            kpi_card("NET", str(int(gs["total_goals"].sum())), "TOTAL GOALS")
        with c3:
            kpi_card("!!", str(int(gs["is_high_scoring"].sum())), "HIGH-SCORING (4+)")

bottom_nav()
