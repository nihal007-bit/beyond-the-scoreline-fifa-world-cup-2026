import streamlit as st
import pandas as pd
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from components.cards import (load_css, kpi_card, match_card, section_header,
                               divider, bottom_nav)
from data_loader import load_live_data

st.set_page_config(page_title="WC 2026 Analytics", page_icon="WC", layout="wide",
                   initial_sidebar_state="collapsed")
load_css()

GREEN_DIM = "#16a34a"
RED = "#ef4444"
AMBER = "#f59e0b"
TXT_MUTED = "#3f3f46"

data = load_live_data()
matches = data["matches"]
all_matches = data["all_matches"]
gci = data["gci"]
hosts = data["hosts"]

st.markdown("""
<div class="stadium-header">
    <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:28px;
                        font-weight:900;color:var(--text-bright);">
                WC 2026</div>
            <div>
                <div style="font-size:17px;font-weight:700;color:var(--text-bright);">
                    FIFA World Cup 2026</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                    Live analytics dashboard &middot; USA / Mexico / Canada</div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="display:inline-flex;align-items:center;gap:6px;
                        background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
                        padding:5px 14px;border-radius:20px;">
                <span class="live-pulse"></span>
                <span style="font-size:10px;font-weight:700;color:var(--red);
                             letter-spacing:1.5px;">ROUND OF 32</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not matches.empty:
    total_goals = int(matches["total_goals"].sum())
    total_matches = len(matches)
    gpg = round(total_goals / total_matches, 2)
    high_scoring = int(matches["is_high_scoring"].sum())
else:
    total_goals = total_matches = high_scoring = 0
    gpg = 0.0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("48", "48", "TEAMS", "First 48-team WC", True)
with c2:
    kpi_card("90'", str(total_matches), "MATCHES PLAYED")
with c3:
    kpi_card("NET", str(total_goals), "GOALS SCORED")
with c4:
    delta = f"{gpg - 2.69:+.2f} vs 2022" if gpg > 0 else ""
    kpi_card("AVG", str(gpg), "GOALS / GAME", delta, gpg > 2.69)
with c5:
    kpi_card("!!", str(high_scoring), "HIGH-SCORING (4+)")

divider()

col_left, col_right = st.columns([1.5, 1])

with col_left:
    live_now = all_matches[all_matches["status"].isin(["IN_PLAY", "LIVE", "PAUSED"])]
    upcoming = all_matches[all_matches["status"].isin(["TIMED", "SCHEDULED"])].sort_values("date")

    if not live_now.empty:
        section_header("LIVE NOW")
        for _, row in live_now.iterrows():
            match_card(
                home=row["home_team"], away=row["away_team"],
                home_score=row["home_score"], away_score=row["away_score"],
                stage=row.get("stage", ""), group=row.get("group", ""),
                date_str=str(row["date"])[:10], status=row["status"],
                kickoff_utc=str(row.get("kickoff_utc", ""))
            )
        divider()

    if not upcoming.empty:
        section_header("UPCOMING")
        for _, row in upcoming.head(4).iterrows():
            match_card(
                home=row["home_team"], away=row["away_team"],
                home_score=row["home_score"], away_score=row["away_score"],
                stage=row.get("stage", ""), group=row.get("group", ""),
                date_str=str(row["date"])[:10], status=row["status"],
                kickoff_utc=str(row.get("kickoff_utc", ""))
            )
        divider()

    section_header("LATEST RESULTS")
    if not matches.empty:
        recent = matches.sort_values("date", ascending=False).head(8)
        for _, row in recent.iterrows():
            match_card(
                home=row["home_team"], away=row["away_team"],
                home_score=row["home_score"], away_score=row["away_score"],
                stage=row.get("stage", ""), group=row.get("group", ""),
                date_str=str(row["date"])[:10]
            )

with col_right:
    section_header("HOST NATIONS")
    if not hosts.empty:
        for _, h in hosts.iterrows():
            w, d, l = int(h["wins"]), int(h["draws"]), int(h["losses"])
            gf, ga = int(h["goals_for"]), int(h["goals_against"])
            total_pts = w * 3 + d
            st.markdown(f"""
            <div class="match-card" style="margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:14px;font-weight:700;
                                    color:var(--text-bright);">{h["host"]}</div>
                        <div style="font-size:11px;color:var(--text-secondary);margin-top:2px;">
                            {w}W {d}D {l}L &middot; {gf}:{ga} &middot; {total_pts}pts</div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                                color:var(--green);background:var(--green-muted);
                                padding:3px 10px;border-radius:4px;font-weight:700;">
                        ADVANCED</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    section_header("TOURNAMENT TIMELINE")
    stages_tl = [
        ("done", "Group Stage", "Jun 11-27"),
        ("now", "Round of 32", "Jun 28-Jul 3"),
        ("", "Round of 16", "Jul 4-7"),
        ("", "Quarter-finals", "Jul 9-11"),
        ("", "Semi-finals", "Jul 14-15"),
        ("final", "Final", "Jul 19 MetLife"),
    ]
    for tag, name, dates in stages_tl:
        if tag == "done":
            dot_color = GREEN_DIM
            label_style = "color:var(--text-secondary);"
        elif tag == "now":
            dot_color = RED
            label_style = "color:var(--text-bright);font-weight:700;"
        elif tag == "final":
            dot_color = AMBER
            label_style = "color:var(--text-secondary);"
        else:
            dot_color = TXT_MUTED
            label_style = "color:var(--text-muted);"

        pulse_cls = 'class="live-pulse"' if tag == "now" else ""
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:5px 0;">
            <span {pulse_cls} style="width:8px;height:8px;border-radius:50%;
                   background:{dot_color};display:inline-block;flex-shrink:0;"></span>
            <span style="font-size:12px;{label_style}flex:1;">{name}</span>
            <span style="font-size:11px;color:var(--text-muted);
                         font-family:'JetBrains Mono',monospace;">{dates}</span>
        </div>
        """, unsafe_allow_html=True)

divider()
st.markdown("""
<div style="text-align:center;padding:14px 0;font-size:11px;color:var(--text-muted);
            letter-spacing:0.5px;">
    Built by <strong style="color:var(--text-secondary);">Nihal</strong>
    &middot; MIT Bengaluru &middot; July 2026
    &middot; Data: football-data.org + StatsBomb
</div>
""", unsafe_allow_html=True)

bottom_nav()
