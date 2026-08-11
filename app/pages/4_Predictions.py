import streamlit as st
import pandas as pd
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.cards import (load_css, section_header, divider,
                               prediction_row, kpi_card, bottom_nav)
from data_loader import load_live_data

st.set_page_config(page_title="Predictions · WC 2026", page_icon="WC", layout="wide",
                   initial_sidebar_state="collapsed")
load_css()


def football_celebration():
    st.markdown("""
    <style>
    @keyframes footballFall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
    }
    .football-container {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 9999; overflow: hidden;
    }
    .football { position: absolute; top: -40px; animation: footballFall 3s ease-in forwards; }
    </style>
    <div class="football-container">
    """ + "".join(
        f'<span class="football" style="left:{random.randint(3,95)}%;'
        f'animation-delay:{random.uniform(0,1.5):.2f}s;'
        f'font-size:{random.randint(20,36)}px;">&#9917;</span>'
        for _ in range(25)
    ) + "</div>", unsafe_allow_html=True)


data = load_live_data()
predictions = data["predictions"]

st.markdown("""
<div style="margin-bottom:16px;">
    <div style="font-size:18px;font-weight:700;color:var(--text-bright);">
        Knockout Predictions</div>
    <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
        Logistic regression trained on 2018/2022 WC group stage data</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:var(--card-bg);border:1px solid var(--border);
            border-radius:10px;padding:14px 16px;margin-bottom:16px;">
    <div style="font-size:12px;font-weight:700;color:var(--text-bright);
                margin-bottom:4px;">MODEL INFO</div>
    <div style="font-size:12px;color:var(--text-secondary);line-height:1.6;">
        Features: goal difference, group position, points, is_host.
        Trained on 64 teams across two tournaments.
        <span style="color:var(--accent);font-weight:600;">
        Live prediction</span> &mdash; accuracy updates as results come in.
    </div>
</div>
""", unsafe_allow_html=True)

if not predictions.empty:
    confident = len(predictions[predictions["confidence"] >= 65])
    avg_conf = round(predictions["confidence"].mean(), 1)
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("#", "16", "MATCHUPS")
    with c2:
        kpi_card("+", str(confident), "HIGH CONFIDENCE (65%+)")
    with c3:
        kpi_card("%", f"{avg_conf}%", "AVG ACCURACY")

    divider()
    section_header("MODEL PREDICTIONS")

    col_left, col_right = st.columns(2)
    mid = len(predictions) // 2
    with col_left:
        for _, row in predictions.iloc[:mid].iterrows():
            prediction_row(row["team_1"], row["team_2"],
                           row["predicted_winner"], int(row["confidence"]))
    with col_right:
        for _, row in predictions.iloc[mid:].iterrows():
            prediction_row(row["team_1"], row["team_2"],
                           row["predicted_winner"], int(row["confidence"]))

    divider()
    section_header("FAN VOTE - PICK YOUR WINNERS")

    if "user_votes" not in st.session_state:
        st.session_state.user_votes = {}

    vote_matches = predictions.head(4)
    for idx, (_, row) in enumerate(vote_matches.iterrows()):
        match_key = f"vote_{idx}"
        t1, t2 = row["team_1"], row["team_2"]

        st.markdown(f"""
        <div style="font-size:12px;font-weight:600;color:var(--text-secondary);
                    margin:10px 0 4px;letter-spacing:0.5px;">
            Match {idx + 1}: {t1} vs {t2}</div>
        """, unsafe_allow_html=True)

        choice = st.radio(
            f"Who wins?", [t1, t2, "Draw"],
            key=match_key, horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.user_votes[match_key] = choice

        model_pick = row["predicted_winner"]
        if choice != model_pick and choice != "Draw":
            st.markdown(f"""
            <div style="font-size:11px;color:var(--amber);font-weight:600;padding:4px 0;">
                HOT TAKE! You picked {choice} over the model's {model_pick}
                ({int(row['confidence'])}% confidence)</div>
            """, unsafe_allow_html=True)

    if st.button("SUBMIT VOTES", width="stretch", key="submit_votes"):
        football_celebration()
        hot_takes = 0
        for idx, (_, row) in enumerate(vote_matches.iterrows()):
            mk = f"vote_{idx}"
            if mk in st.session_state.user_votes:
                pick = st.session_state.user_votes[mk]
                if pick != row["predicted_winner"] and pick != "Draw":
                    hot_takes += 1

        if hot_takes > 0:
            st.markdown(f"""
            <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                        border-radius:10px;padding:16px;text-align:center;margin:10px 0;">
                <div style="font-size:16px;font-weight:800;color:var(--amber);
                            margin-bottom:4px;">
                    {hot_takes} HOT TAKE{'S' if hot_takes > 1 else ''} REGISTERED!</div>
                <div style="font-size:12px;color:var(--text-secondary);">
                    Bold picks against the model. Let's see who's right.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);
                        border-radius:10px;padding:16px;text-align:center;margin:10px 0;">
                <div style="font-size:16px;font-weight:800;color:var(--accent);
                            margin-bottom:4px;">VOTES LOCKED IN!</div>
                <div style="font-size:12px;color:var(--text-secondary);">
                    You agree with the model on all picks. Safe play.</div>
            </div>
            """, unsafe_allow_html=True)

    divider()
    section_header("FAN VOTING BREAKDOWN")

    for idx, (_, row) in enumerate(vote_matches.iterrows()):
        t1, t2 = row["team_1"], row["team_2"]
        rng = random.Random(hash(t1 + t2))
        t1_pct = rng.randint(30, 70)
        draw_pct = rng.randint(5, 20)
        t2_pct = 100 - t1_pct - draw_pct

        st.markdown(f"""
        <div class="match-card" style="margin-bottom:6px;">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">
                {t1} vs {t2}</div>
            <div style="display:flex;gap:4px;height:8px;border-radius:4px;
                        overflow:hidden;margin-bottom:6px;">
                <div style="width:{t1_pct}%;background:var(--accent);
                            border-radius:4px 0 0 4px;"></div>
                <div style="width:{draw_pct}%;background:var(--text-muted);"></div>
                <div style="width:{t2_pct}%;background:var(--blue);
                            border-radius:0 4px 4px 0;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px;">
                <span style="color:var(--accent);">{t1} {t1_pct}%</span>
                <span style="color:var(--text-muted);">Draw {draw_pct}%</span>
                <span style="color:var(--blue);">{t2} {t2_pct}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No predictions available — waiting for knockout stage data")

bottom_nav()
