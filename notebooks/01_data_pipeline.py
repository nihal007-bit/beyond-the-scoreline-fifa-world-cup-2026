import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROC.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
if not API_KEY:
    print("Set FOOTBALL_DATA_API_KEY in .env — register free at football-data.org/client/register")
    sys.exit(1)

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}
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


def api_get(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text}")
        sys.exit(1)
    return resp.json()


def get_venue_country(venue_name, city_name):
    if not venue_name and not city_name:
        return "Unknown"
    search = f"{venue_name or ''} {city_name or ''}"
    for key, country in VENUE_COUNTRY_MAP.items():
        if key.lower() in search.lower():
            return country
    return "Unknown"


matches_data = api_get(f"competitions/{WC_ID}/matches?season=2026")
all_matches = matches_data.get("matches", [])

rows = []
for m in all_matches:
    home_score = m.get("score", {}).get("fullTime", {}).get("home")
    away_score = m.get("score", {}).get("fullTime", {}).get("away")
    venue_name = m.get("venue", "") or ""
    venue_city = ""
    if "," in venue_name:
        venue_city = venue_name.split(",")[-1].strip()

    total_goals = (home_score or 0) + (away_score or 0) if m["status"] == "FINISHED" else None

    rows.append({
        "match_id": m["id"],
        "date": m["utcDate"][:10],
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
        "venue_country": get_venue_country(venue_name, venue_city),
        "total_goals": total_goals,
        "is_draw": home_score == away_score if m["status"] == "FINISHED" else None,
        "is_high_scoring": (total_goals >= 4) if total_goals is not None else None,
    })

df_all = pd.DataFrame(rows)

with open(DATA_RAW / "matches_raw.json", "w") as f:
    json.dump(all_matches, f, indent=2)

df_finished = df_all[df_all["status"] == "FINISHED"].copy()
df_finished.to_csv(DATA_PROC / "matches.csv", index=False)

total = len(df_all)
finished = len(df_finished)
scheduled = len(df_all[df_all["status"].isin(["SCHEDULED", "TIMED"])])
print(f"Matches — total: {total}, finished: {finished}, scheduled: {scheduled}")
if finished > 0:
    print(f"Date range: {df_finished['date'].min()} to {df_finished['date'].max()}")

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
        "group": group,
        "team": team,
        "played": played,
        "won": won,
        "drawn": drawn,
        "lost": lost,
        "goals_for": int(gf),
        "goals_against": int(ga),
        "goal_difference": int(gf - ga),
        "points": won * 3 + drawn,
    })

df_standings = pd.DataFrame(standings_rows)
df_standings = df_standings.sort_values(
    ["group", "points", "goal_difference", "goals_for"],
    ascending=[True, False, False, False]
)
df_standings["position"] = df_standings.groupby("group").cumcount() + 1
df_standings = df_standings[
    ["group", "position", "team", "played", "won", "drawn", "lost",
     "goals_for", "goals_against", "goal_difference", "points"]
]
df_standings.to_csv(DATA_PROC / "standings.csv", index=False)
print(f"Standings: {df_standings.shape[0]} teams across {df_standings['group'].nunique()} groups")

team_rows = []
for _, match in df_finished.iterrows():
    for side in ["home", "away"]:
        team_rows.append({
            "match_id": match["match_id"],
            "date": match["date"],
            "stage": match["stage"],
            "group": match["group"],
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

df_team_goals = pd.DataFrame(team_rows)
df_team_goals.to_csv(DATA_PROC / "team_goals.csv", index=False)
print(f"Team goals dataset: {df_team_goals.shape}")

if finished > 0:
    print(f"\nTop 5 highest-scoring matches:")
    top5 = df_finished.nlargest(5, "total_goals")[
        ["date", "home_team", "away_team", "home_score", "away_score", "total_goals"]
    ]
    print(top5.to_string(index=False))
    print(f"\nMissing values: {df_finished.isnull().sum().sum()}")
