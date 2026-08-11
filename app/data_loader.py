import os
import json
import requests
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"

load_dotenv(ROOT / ".env")

BASE_URL = "https://api.football-data.org/v4"
WC_ID = "WC"

VENUE_COUNTRY_MAP = {
    "East Rutherford": "USA", "New York": "USA", "MetLife": "USA",
    "Pasadena": "USA", "Los Angeles": "USA", "Rose Bowl": "USA",
    "Miami": "USA", "Hard Rock": "USA", "Miami Gardens": "USA",
    "Houston": "USA", "NRG": "USA",
    "Dallas": "USA", "AT&T": "USA", "Arlington": "USA",
    "Atlanta": "USA", "Mercedes-Benz": "USA",
    "Philadelphia": "USA", "Lincoln Financial": "USA",
    "Seattle": "USA", "Lumen": "USA",
    "San Francisco": "USA", "Levi's": "USA", "Santa Clara": "USA",
    "Boston": "USA", "Gillette": "USA", "Foxborough": "USA",
    "Kansas City": "USA", "Arrowhead": "USA", "GEHA": "USA",
    "Mexico City": "MEX", "Azteca": "MEX", "Estadio Azteca": "MEX",
    "Monterrey": "MEX", "BBVA": "MEX", "Estadio BBVA": "MEX",
    "Guadalajara": "MEX", "Akron": "MEX", "Estadio Akron": "MEX",
    "Toronto": "CAN", "BMO": "CAN",
    "Vancouver": "CAN", "BC Place": "CAN",
}

HOST_TEAMS = ["Mexico", "Canada", "United States"]


def _get_venue_country(venue_name, city_name):
    if not venue_name and not city_name:
        return "Unknown"
    search = f"{venue_name or ''} {city_name or ''}"
    for key, country in VENUE_COUNTRY_MAP.items():
        if key.lower() in search.lower():
            return country
    return "Unknown"


def _fetch_from_api():
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["FOOTBALL_DATA_API_KEY"]
        except (KeyError, FileNotFoundError):
            pass
    if not api_key:
        return None
    headers = {"X-Auth-Token": api_key}
    try:
        resp = requests.get(
            f"{BASE_URL}/competitions/{WC_ID}/matches?season=2026",
            headers=headers, timeout=15,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("matches", [])
    except requests.RequestException:
        return None


def _parse_matches(all_matches):
    rows = []
    for m in all_matches:
        home_score = m.get("score", {}).get("fullTime", {}).get("home")
        away_score = m.get("score", {}).get("fullTime", {}).get("away")
        venue_name = m.get("venue", "") or ""
        venue_city = ""
        if "," in venue_name:
            venue_city = venue_name.split(",")[-1].strip()

        total_goals = (
            (home_score or 0) + (away_score or 0)
            if m["status"] == "FINISHED" else None
        )

        rows.append({
            "match_id": m["id"],
            "date": m["utcDate"][:10],
            "kickoff_utc": m["utcDate"],
            "stage": m.get("stage", ""),
            "group": m.get("group", ""),
            "home_team": m.get("homeTeam", {}).get("name", ""),
            "away_team": m.get("awayTeam", {}).get("name", ""),
            "home_score": home_score,
            "away_score": away_score,
            "status": m["status"],
            "winner": m.get("score", {}).get("winner", ""),
            "venue": venue_name,
            "venue_city": venue_city,
            "venue_country": _get_venue_country(venue_name, venue_city),
            "total_goals": total_goals,
            "is_draw": home_score == away_score if m["status"] == "FINISHED" else None,
            "is_high_scoring": (total_goals >= 4) if total_goals is not None else None,
        })

    df_all = pd.DataFrame(rows)
    return df_all, all_matches


def _compute_standings(df_finished):
    gs_finished = df_finished[df_finished["stage"] == "GROUP_STAGE"].copy()
    team_group_map = {}
    for _, m in gs_finished.iterrows():
        if m["group"]:
            team_group_map[m["home_team"]] = m["group"]
            team_group_map[m["away_team"]] = m["group"]

    standings_rows = []
    for team, group in team_group_map.items():
        team_matches = gs_finished[
            (gs_finished["home_team"] == team) | (gs_finished["away_team"] == team)
        ]
        played = len(team_matches)
        won = drawn = lost = gf = ga = 0
        for _, m in team_matches.iterrows():
            if m["home_team"] == team:
                gf += m["home_score"]
                ga += m["away_score"]
                if m["winner"] == "HOME_TEAM":
                    won += 1
                elif m["winner"] == "AWAY_TEAM":
                    lost += 1
                else:
                    drawn += 1
            else:
                gf += m["away_score"]
                ga += m["home_score"]
                if m["winner"] == "AWAY_TEAM":
                    won += 1
                elif m["winner"] == "HOME_TEAM":
                    lost += 1
                else:
                    drawn += 1
        standings_rows.append({
            "group": group, "team": team, "played": played,
            "won": won, "drawn": drawn, "lost": lost,
            "goals_for": int(gf), "goals_against": int(ga),
            "goal_difference": int(gf - ga), "points": won * 3 + drawn,
        })

    df = pd.DataFrame(standings_rows)
    if df.empty:
        return df
    df = df.sort_values(
        ["group", "points", "goal_difference", "goals_for"],
        ascending=[True, False, False, False],
    )
    df["position"] = df.groupby("group").cumcount() + 1
    return df[["group", "position", "team", "played", "won", "drawn", "lost",
               "goals_for", "goals_against", "goal_difference", "points"]]


def _compute_team_goals(df_finished):
    rows = []
    for _, match in df_finished.iterrows():
        for side in ["home", "away"]:
            rows.append({
                "match_id": match["match_id"], "date": match["date"],
                "stage": match["stage"], "group": match["group"],
                "team": match[f"{side}_team"],
                "opponent": match["away_team"] if side == "home" else match["home_team"],
                "goals_scored": match[f"{side}_score"],
                "goals_conceded": match["away_score"] if side == "home" else match["home_score"],
                "result": (
                    "W" if (side == "home" and match["winner"] == "HOME_TEAM")
                         or (side == "away" and match["winner"] == "AWAY_TEAM")
                    else "L" if (side == "home" and match["winner"] == "AWAY_TEAM")
                              or (side == "away" and match["winner"] == "HOME_TEAM")
                    else "D"
                ),
                "is_home": side == "home",
                "venue_country": match["venue_country"],
            })
    return pd.DataFrame(rows)


def _compute_gci(standings):
    if standings.empty:
        return pd.DataFrame()
    rows = []
    for group in sorted(standings["group"].unique()):
        grp = standings[standings["group"] == group].sort_values("position")
        pts = grp["points"].values
        gci = np.std(pts) / np.mean(pts) if np.mean(pts) > 0 else np.nan
        rows.append({
            "group": group, "GCI": round(gci, 4),
            "most_points": int(pts[0]), "least_points": int(pts[-1]),
            "points_spread": int(pts[0] - pts[-1]),
            "group_winner": grp.iloc[0]["team"],
            "group_runner_up": grp.iloc[1]["team"] if len(grp) > 1 else "",
        })
    return pd.DataFrame(rows).sort_values("GCI")


def _compute_host_nations(team_goals, standings):
    if team_goals.empty or standings.empty:
        return pd.DataFrame()
    host_names_map = {}
    for t in team_goals["team"].unique():
        t_lower = t.lower()
        if "united states" in t_lower or "usa" in t_lower:
            host_names_map["USA"] = t
        elif "mexico" in t_lower or "méxico" in t_lower:
            host_names_map["Mexico"] = t
        elif "canada" in t_lower:
            host_names_map["Canada"] = t

    rows = []
    for label, team_name in host_names_map.items():
        gs_tm = team_goals[
            (team_goals["team"] == team_name) & (team_goals["stage"] == "GROUP_STAGE")
        ]
        wins = len(gs_tm[gs_tm["result"] == "W"])
        draws = len(gs_tm[gs_tm["result"] == "D"])
        losses = len(gs_tm[gs_tm["result"] == "L"])
        gf = int(gs_tm["goals_scored"].sum())
        ga = int(gs_tm["goals_conceded"].sum())
        grp_pos = standings[standings["team"] == team_name]["position"].values
        grp_pos = int(grp_pos[0]) if len(grp_pos) > 0 else None
        rows.append({
            "host": label, "team_api_name": team_name,
            "wins": wins, "draws": draws, "losses": losses,
            "goals_for": gf, "goals_against": ga,
            "group_position": grp_pos,
            "qualified_r32": grp_pos is not None and grp_pos <= 3,
            "win_pct": round(wins / max(len(gs_tm), 1) * 100, 1),
        })
    return pd.DataFrame(rows)


def _compute_predictions(df_all, df_features, standings):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    wc_2022_gs = {
        "goal_difference_gs": [3,0,0,-5,7,0,-1,-3,3,0,-1,-2,5,-3,0,-3,1,6,0,-5,4,0,-2,-5,2,1,0,-1,5,-1,0,-4],
        "group_position": [1,2,3,4]*8,
        "is_host": [0]*32,
        "group_points": [7,6,4,0,7,5,3,1,6,4,4,3,6,6,4,1,6,4,4,3,7,5,4,0,6,6,4,1,6,4,4,4],
        "advanced_past_round": [1,0,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0],
    }
    wc_2018_gs = {
        "goal_difference_gs": [4,4,-4,-3,2,2,0,-3,3,1,-1,-2,6,-2,-1,-2,4,1,-1,-4,3,0,-2,-2,7,6,-4,-6,2,-1,-1,-3],
        "group_position": [1,2,3,4]*8,
        "is_host": [0,1,0,0]+[0]*28,
        "group_points": [9,6,3,0,5,5,4,1,7,5,3,1,9,4,3,1,7,5,3,1,6,6,3,3,9,6,3,0,6,4,4,3],
        "advanced_past_round": [1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0],
    }
    df_train = pd.concat([pd.DataFrame(wc_2022_gs), pd.DataFrame(wc_2018_gs)], ignore_index=True)
    feature_cols = ["goal_difference_gs", "group_position", "is_host", "group_points"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_train[feature_cols])
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_scaled, df_train["advanced_past_round"])

    r32_matches = df_all[df_all["stage"] == "LAST_32"]
    if r32_matches.empty:
        return pd.DataFrame()

    rows = []
    for _, m in r32_matches.iterrows():
        home, away = m["home_team"], m["away_team"]
        hf = df_features[df_features["team"] == home]
        af = df_features[df_features["team"] == away]
        if hf.empty or af.empty:
            rows.append({"match_id": m["match_id"], "date": m["date"],
                         "team_1": home, "team_2": away,
                         "predicted_winner": "N/A", "confidence": 0, "is_upset": False})
            continue

        hf, af = hf.iloc[0], af.iloc[0]
        hp = model.predict_proba(scaler.transform(pd.DataFrame([[hf["goal_difference_gs"], hf["group_position"], hf["is_host"], hf["group_points"]]], columns=feature_cols)))[0][1]
        ap = model.predict_proba(scaler.transform(pd.DataFrame([[af["goal_difference_gs"], af["group_position"], af["is_host"], af["group_points"]]], columns=feature_cols)))[0][1]
        total = hp + ap
        hc = hp / total if total > 0 else 0.5
        ac = ap / total if total > 0 else 0.5

        if hc >= ac:
            winner, conf = home, round(hc * 100, 1)
        else:
            winner, conf = away, round(ac * 100, 1)

        rows.append({"match_id": m["match_id"], "date": m["date"],
                     "team_1": home, "team_2": away,
                     "predicted_winner": winner, "confidence": conf,
                     "is_upset": (winner == away and hf["group_position"] < af["group_position"])
                                 or (winner == home and af["group_position"] < hf["group_position"])})
    return pd.DataFrame(rows)


def _compute_team_features(team_goals, standings, df_all):
    if standings.empty or team_goals.empty:
        return pd.DataFrame()

    r32_teams = set()
    r32_matches = df_all[df_all["stage"] == "LAST_32"]
    for _, m in r32_matches.iterrows():
        if m["home_team"]:
            r32_teams.add(m["home_team"])
        if m["away_team"]:
            r32_teams.add(m["away_team"])

    if not r32_teams:
        qualified = standings[standings["position"] <= 2]["team"].tolist()
        third = standings[standings["position"] == 3].sort_values(
            ["points", "goal_difference", "goals_for"], ascending=[False, False, False]
        )
        best_thirds = third.head(8)["team"].tolist()
        r32_teams = set(qualified + best_thirds)

    gs_tg = team_goals[team_goals["stage"] == "GROUP_STAGE"]
    rows = []
    for team in r32_teams:
        tm = gs_tg[gs_tg["team"] == team]
        st_row = standings[standings["team"] == team]
        if st_row.empty or tm.empty:
            continue
        st_row = st_row.iloc[0]
        games = len(tm)
        rows.append({
            "team": team,
            "group_position": int(st_row["position"]),
            "group_points": int(st_row["points"]),
            "goals_scored_gs": int(tm["goals_scored"].sum()),
            "goals_conceded_gs": int(tm["goals_conceded"].sum()),
            "goal_difference_gs": int(tm["goals_scored"].sum() - tm["goals_conceded"].sum()),
            "wins_gs": int(len(tm[tm["result"] == "W"])),
            "draws_gs": int(len(tm[tm["result"] == "D"])),
            "losses_gs": int(len(tm[tm["result"] == "L"])),
            "is_host": 1 if team in HOST_TEAMS else 0,
            "gpg_for": round(tm["goals_scored"].sum() / max(games, 1), 2),
            "gpg_against": round(tm["goals_conceded"].sum() / max(games, 1), 2),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def load_live_data():
    """Fetch from API and compute all datasets. Auto-refreshes every 60 seconds."""
    raw_matches = _fetch_from_api()

    if raw_matches is not None:
        df_all, _ = _parse_matches(raw_matches)
        df_finished = df_all[df_all["status"] == "FINISHED"].copy()
        standings = _compute_standings(df_finished)
        team_goals = _compute_team_goals(df_finished)
        gci = _compute_gci(standings)
        hosts = _compute_host_nations(team_goals, standings)
        features = _compute_team_features(team_goals, standings, df_all)
        predictions = _compute_predictions(df_all, features, standings) if not features.empty else pd.DataFrame()
        return {
            "matches": df_finished,
            "all_matches": df_all,
            "standings": standings,
            "team_goals": team_goals,
            "gci": gci,
            "hosts": hosts,
            "predictions": predictions,
            "source": "live",
        }

    return _load_from_csv()


def _load_from_csv():
    """Fallback: load from pre-generated CSV files."""
    def _read(name):
        p = DATA_PROC / name
        return pd.read_csv(p) if p.exists() else pd.DataFrame()

    return {
        "matches": _read("matches.csv"),
        "all_matches": _read("matches.csv"),
        "standings": _read("standings.csv"),
        "team_goals": _read("team_goals.csv"),
        "gci": _read("gci_analysis.csv"),
        "hosts": _read("host_nations.csv"),
        "predictions": _read("r32_predictions.csv"),
        "source": "csv",
    }
