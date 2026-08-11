import streamlit as st
from pathlib import Path


def load_css():
    css_path = Path(__file__).parent.parent / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)


def kpi_card(icon, value, label, delta=None, delta_up=True):
    delta_html = ""
    if delta:
        cls = "up" if delta_up else "down"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def match_card(home, away, home_score, away_score,
               stage="", group="", date_str="", status="FINISHED",
               kickoff_utc=""):
    import math
    from datetime import datetime, timezone, timedelta
    has_score = (home_score is not None and not (isinstance(home_score, float) and math.isnan(home_score)))

    if has_score:
        home_score, away_score = int(home_score), int(away_score)
        h_cls = "team-winner" if home_score > away_score else "team-loser" if away_score > home_score else "team-winner"
        a_cls = "team-winner" if away_score > home_score else "team-loser" if home_score > away_score else "team-winner"
        score_html = f'{home_score}&ndash;{away_score}'
    else:
        h_cls = a_cls = "team-winner"
        score_html = 'vs'

    group = str(group) if group and str(group) != "nan" else ""
    tag = group.replace("GROUP_", "GRP ") if group else stage

    time_str = date_str
    if kickoff_utc and status in ("TIMED", "SCHEDULED", "IN_PLAY", "LIVE", "PAUSED"):
        try:
            utc_dt = datetime.fromisoformat(kickoff_utc.replace("Z", "+00:00"))
            ist = utc_dt + timedelta(hours=5, minutes=30)
            time_str = ist.strftime("%d %b, %I:%M %p IST")
        except (ValueError, AttributeError):
            pass

    if status in ("IN_PLAY", "LIVE"):
        status_badge = ('<span style="display:inline-flex;align-items:center;gap:4px;'
                        'background:rgba(218,54,51,0.1);border:1px solid rgba(218,54,51,0.3);'
                        'padding:2px 8px;border-radius:10px;margin-left:6px;">'
                        '<span style="width:6px;height:6px;background:#DA3633;border-radius:50%;'
                        'display:inline-block;animation:pulse 1.5s infinite;"></span>'
                        '<span style="color:#DA3633;font-size:10px;font-weight:700;">LIVE</span></span>')
    elif status == "PAUSED":
        status_badge = ('<span style="color:#E3B341;font-size:10px;font-weight:700;'
                        'margin-left:6px;">HT</span>')
    elif status in ("TIMED", "SCHEDULED"):
        status_badge = ('<span style="color:#E3B341;font-size:10px;font-weight:600;'
                        'margin-left:6px;">UPCOMING</span>')
    else:
        status_badge = '<span style="color:#3FB950;font-size:10px;margin-left:6px;">FT</span>'

    st.markdown(f"""
    <div class="match-card">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:8px;">
            <span style="font-size:10px;color:var(--text-muted);
                         letter-spacing:1px;">{tag}{status_badge}</span>
            <span style="font-size:10px;color:var(--text-muted);">{time_str}</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="{h_cls}" style="font-size:13px;flex:1;">{home}</span>
            <span class="score-display" style="margin:0 16px;">
                {score_html}</span>
            <span class="{a_cls}" style="font-size:13px;flex:1;text-align:right;">{away}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)


def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def prediction_row(home, away, predicted_winner, confidence):
    conf_cls = "conf-high" if confidence >= 65 else "conf-mid" if confidence >= 55 else "conf-low"
    h_bold = "font-weight:700;" if predicted_winner == home else ""
    a_bold = "font-weight:700;" if predicted_winner == away else ""

    st.markdown(f"""
    <div class="prediction-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:13px;{h_bold}color:var(--text-bright);flex:1;">{home}</span>
            <div style="text-align:center;flex:1;">
                <div style="font-size:10px;color:var(--text-muted);letter-spacing:1px;">
                    PREDICTED</div>
                <div style="font-size:13px;font-weight:700;color:var(--accent);
                            margin:2px 0;">{predicted_winner}</div>
                <div class="{conf_cls}" style="font-size:11px;
                            font-family:'JetBrains Mono',monospace;">{confidence}%</div>
            </div>
            <span style="font-size:13px;{a_bold}color:var(--text-bright);
                         flex:1;text-align:right;">{away}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def bottom_nav():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 9998;
        background: var(--bg-secondary);
        border-top: 1px solid var(--border);
        padding: 8px 20px;
        display: flex; justify-content: center; gap: 6px;
    }
    .bottom-nav a {
        color: var(--text-secondary); text-decoration: none;
        font-size: 11px; font-weight: 600; letter-spacing: 0.8px;
        padding: 8px 18px; border-radius: 6px;
        transition: all 0.15s;
    }
    .bottom-nav a:hover {
        background: var(--card-bg-hover); color: var(--text-bright);
    }
    .stApp > div:first-child { padding-bottom: 56px; }
    </style>
    <div class="bottom-nav">
        <a href="/" target="_self">OVERVIEW</a>
        <a href="/Group_Stage" target="_self">GROUPS</a>
        <a href="/Live_Tracker" target="_self">LIVE</a>
        <a href="/xG_Analysis" target="_self">xG</a>
        <a href="/Predictions" target="_self">PREDICTIONS</a>
    </div>
    """, unsafe_allow_html=True)
