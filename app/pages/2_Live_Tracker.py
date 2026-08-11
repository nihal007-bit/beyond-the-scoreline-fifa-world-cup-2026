import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.cards import load_css, section_header, divider, match_card, bottom_nav
from data_loader import load_live_data

st.set_page_config(page_title="Live Tracker · WC 2026", page_icon="WC", layout="wide")
load_css()

st.markdown("""
<script>
setTimeout(function(){ window.location.reload(); }, 60000);
</script>
""", unsafe_allow_html=True)

data = load_live_data()
all_matches = data["all_matches"]
finished = data["matches"]

st.markdown("""
<div style="padding:16px 0 12px;border-bottom:1px solid #21262D;margin-bottom:20px;
            display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:20px;font-weight:700;color:#E6EDF3;">Live Knockout Tracker</div>
        <div style="font-size:13px;color:#8B949E;margin-top:2px;">Auto-refreshes every 60 seconds</div>
    </div>
    <span style="background:#DA3633;color:#fff;font-size:11px;font-weight:700;
                 padding:5px 12px;border-radius:20px;">ROUND OF 32</span>
</div>
""", unsafe_allow_html=True)


def render_card(row):
    match_card(
        home=row["home_team"], away=row["away_team"],
        home_score=row["home_score"], away_score=row["away_score"],
        stage=str(row.get("stage", "")), group=str(row.get("group", "")),
        date_str=str(row["date"])[:10], status=row["status"],
        kickoff_utc=str(row.get("kickoff_utc", ""))
    )


if not all_matches.empty:
    live_matches = all_matches[all_matches["status"].isin(["IN_PLAY", "LIVE", "PAUSED"])]
    upcoming = all_matches[all_matches["status"].isin(["TIMED", "SCHEDULED"])].sort_values("date")

    stages = all_matches["stage"].unique().tolist()
    status_options = ["All matches", "Live & Upcoming", "Finished"]
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox("Status", status_options, index=0)
    with col_f2:
        stage_filter = st.selectbox("Stage", ["All stages"] + stages, index=0)

    if status_filter == "Live & Upcoming":
        filtered = all_matches[~all_matches["status"].isin(["FINISHED"])]
    elif status_filter == "Finished":
        filtered = all_matches[all_matches["status"] == "FINISHED"]
    else:
        filtered = all_matches

    if stage_filter != "All stages":
        filtered = filtered[filtered["stage"] == stage_filter]

    col1, col2 = st.columns([1.6, 1])

    with col1:
        if not live_matches.empty:
            section_header("LIVE NOW")
            for _, row in live_matches.iterrows():
                render_card(row)
            divider()

        if not upcoming.empty:
            section_header("UPCOMING")
            for _, row in upcoming.head(6).iterrows():
                render_card(row)
            divider()

        section_header(f"Results — {stage_filter}")
        results = filtered[filtered["status"] == "FINISHED"].sort_values("date", ascending=False)
        for _, row in results.iterrows():
            render_card(row)

    with col2:
        section_header("Stage Summary")
        stage_stats = finished.groupby("stage").agg(
            n_matches=("match_id", "count"),
            goals=("total_goals", "sum"),
            draws=("is_draw", "sum")
        ).reset_index()
        stage_stats["gpg"] = (stage_stats["goals"] / stage_stats["n_matches"]).round(2)

        for _, row in stage_stats.iterrows():
            st.markdown(f"""
            <div class="match-card" style="margin-bottom:6px;">
                <div style="font-size:12px;color:#8B949E;margin-bottom:6px;">{row["stage"]}</div>
                <div style="display:flex;justify-content:space-between;font-size:13px;">
                    <span style="color:#E6EDF3;">{row["n_matches"]} matches</span>
                    <span style="color:#E3B341;">{int(row["goals"])} goals</span>
                    <span style="color:#3FB950;">{row["gpg"]} GPG</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        section_header("Match Status")
        n_finished = len(all_matches[all_matches["status"] == "FINISHED"])
        n_live = len(live_matches)
        n_upcoming = len(upcoming)
        st.markdown(f"""
        <div class="match-card" style="margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;font-size:13px;">
                <span style="color:#3FB950;">Finished: {n_finished}</span>
                <span style="color:#DA3633;">Live: {n_live}</span>
                <span style="color:#E3B341;">Upcoming: {n_upcoming}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No match data available — check your FOOTBALL_DATA_API_KEY in .env")

bottom_nav()
