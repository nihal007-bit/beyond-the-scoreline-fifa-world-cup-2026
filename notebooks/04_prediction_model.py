import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"

matches = pd.read_csv(DATA_PROC / "matches.csv")
standings = pd.read_csv(DATA_PROC / "standings.csv")
team_goals = pd.read_csv(DATA_PROC / "team_goals.csv")

HOST_TEAMS = ["Mexico", "Canada", "United States"]

r32_teams = set()
r32_matches = matches[matches["stage"] == "LAST_32"]
for _, m in r32_matches.iterrows():
    if m["home_team"]:
        r32_teams.add(m["home_team"])
    if m["away_team"]:
        r32_teams.add(m["away_team"])

if len(r32_teams) == 0:
    qualified_1_2 = standings[standings["position"] <= 2]["team"].tolist()
    third_place = standings[standings["position"] == 3].sort_values(
        ["points", "goal_difference", "goals_for"], ascending=[False, False, False]
    )
    best_thirds = third_place.head(8)["team"].tolist()
    r32_teams = set(qualified_1_2 + best_thirds)

gs_team_goals = team_goals[team_goals["stage"] == "GROUP_STAGE"]

feature_rows = []
for team in r32_teams:
    tm = gs_team_goals[gs_team_goals["team"] == team]
    st = standings[standings["team"] == team]
    if len(st) == 0 or len(tm) == 0:
        continue

    st_row = st.iloc[0]
    games = len(tm)

    feature_rows.append({
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

df_features = pd.DataFrame(feature_rows)
df_features.to_csv(DATA_PROC / "team_features.csv", index=False)
print(f"R32 teams: {len(df_features)}")

wc_2022_gs = {
    "team": ["Netherlands", "Senegal", "Ecuador", "Qatar",
             "England", "USA_2022", "Iran", "Wales",
             "Argentina", "Poland", "Mexico_2022", "Saudi Arabia",
             "France", "Australia", "Tunisia", "Denmark",
             "Japan", "Spain", "Germany_2022", "Costa Rica",
             "Morocco", "Croatia", "Belgium_2022", "Canada_2022",
             "Brazil", "Switzerland", "Cameroon", "Serbia",
             "Portugal", "South Korea", "Uruguay", "Ghana_2022"],
    "goal_difference_gs": [3, 0, 0, -5, 7, 0, -1, -3,
                            3, 0, -1, -2, 5, -3, 0, -3,
                            1, 6, 0, -5, 4, 0, -2, -5,
                            2, 1, 0, -1, 5, -1, 0, -4],
    "group_position": [1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4],
    "is_host": [0] * 32,
    "group_points": [7, 6, 4, 0, 7, 5, 3, 1,
                      6, 4, 4, 3, 6, 6, 4, 1,
                      6, 4, 4, 3, 7, 5, 4, 0,
                      6, 6, 4, 1, 6, 4, 4, 4],
    "advanced_past_round": [1, 0, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0],
}

wc_2018_gs = {
    "team": ["Uruguay_18", "Russia_18", "Saudi_18", "Egypt_18",
             "Spain_18", "Portugal_18", "Iran_18", "Morocco_18",
             "France_18", "Denmark_18", "Peru_18", "Australia_18",
             "Croatia_18", "Argentina_18", "Nigeria_18", "Iceland_18",
             "Brazil_18", "Switzerland_18", "Serbia_18", "CostaRica_18",
             "Sweden_18", "Mexico_18", "SouthKorea_18", "Germany_18",
             "Belgium_18", "England_18", "Tunisia_18", "Panama_18",
             "Colombia_18", "Japan_18", "Senegal_18", "Poland_18"],
    "goal_difference_gs": [4, 4, -4, -3, 2, 2, 0, -3,
                            3, 1, -1, -2, 6, -2, -1, -2,
                            4, 1, -1, -4, 3, 0, -2, -2,
                            7, 6, -4, -6, 2, -1, -1, -3],
    "group_position": [1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4,
                        1, 2, 3, 4, 1, 2, 3, 4],
    "is_host": [0, 1, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0],
    "group_points": [9, 6, 3, 0, 5, 5, 4, 1,
                      7, 5, 3, 1, 9, 4, 3, 1,
                      7, 5, 3, 1, 6, 6, 3, 3,
                      9, 6, 3, 0, 6, 4, 4, 3],
    "advanced_past_round": [1, 1, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0,
                             1, 1, 0, 0, 1, 1, 0, 0],
}

df_train = pd.concat([pd.DataFrame(wc_2022_gs), pd.DataFrame(wc_2018_gs)], ignore_index=True)

feature_cols = ["goal_difference_gs", "group_position", "is_host", "group_points"]
X_train = df_train[feature_cols]
y_train = df_train["advanced_past_round"]

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_scaled, y_train)
print(f"Training accuracy: {model.score(X_train_scaled, y_train):.1%}")

with open(ROOT / "data" / "raw" / "matches_raw.json") as f:
    all_raw = json.load(f)

r32_raw = [m for m in all_raw if m.get("stage") == "LAST_32"]
r32_rows = []
for m in r32_raw:
    r32_rows.append({
        "match_id": m["id"],
        "date": m["utcDate"][:10],
        "home_team": m["homeTeam"]["name"],
        "away_team": m["awayTeam"]["name"],
        "status": m["status"],
        "stage": m["stage"],
        "winner": m.get("score", {}).get("winner", ""),
        "home_score": m.get("score", {}).get("fullTime", {}).get("home"),
        "away_score": m.get("score", {}).get("fullTime", {}).get("away"),
    })
r32_scheduled = pd.DataFrame(r32_rows)

prediction_rows = []
for _, m in r32_scheduled.iterrows():
    home = m["home_team"]
    away = m["away_team"]

    home_feat = df_features[df_features["team"] == home]
    away_feat = df_features[df_features["team"] == away]

    if len(home_feat) == 0 or len(away_feat) == 0:
        prediction_rows.append({
            "match_id": m["match_id"], "date": m["date"],
            "team_1": home, "team_2": away,
            "predicted_winner": "N/A", "confidence": 0, "is_upset": False,
        })
        continue

    hf = home_feat.iloc[0]
    af = away_feat.iloc[0]

    X_home = scaler.transform([[hf["goal_difference_gs"], hf["group_position"],
                                 hf["is_host"], hf["group_points"]]])
    X_away = scaler.transform([[af["goal_difference_gs"], af["group_position"],
                                 af["is_host"], af["group_points"]]])

    home_prob = model.predict_proba(X_home)[0][1]
    away_prob = model.predict_proba(X_away)[0][1]

    total = home_prob + away_prob
    home_conf = home_prob / total if total > 0 else 0.5
    away_conf = away_prob / total if total > 0 else 0.5

    if home_conf >= away_conf:
        predicted_winner, confidence = home, round(home_conf * 100, 1)
    else:
        predicted_winner, confidence = away, round(away_conf * 100, 1)

    is_upset = (
        (predicted_winner == away and hf["group_position"] < af["group_position"]) or
        (predicted_winner == home and af["group_position"] < hf["group_position"])
    )

    prediction_rows.append({
        "match_id": m["match_id"], "date": m["date"],
        "team_1": home, "team_2": away,
        "predicted_winner": predicted_winner,
        "confidence": confidence, "is_upset": is_upset,
    })

df_preds = pd.DataFrame(prediction_rows)
df_preds.to_csv(DATA_PROC / "r32_predictions.csv", index=False)

print(f"\n{'#':<3} {'Team 1':<22} {'Team 2':<22} {'Winner':<22} {'Conf':>5}")
for i, (_, r) in enumerate(df_preds.iterrows(), 1):
    flag = "*" if r["is_upset"] else ""
    print(f"{i:<3} {r['team_1']:<22} {r['team_2']:<22} {r['predicted_winner']:<22} {r['confidence']:>4.1f}%{flag}")


def update_accuracy():
    preds_path = DATA_PROC / "r32_predictions.csv"
    if not preds_path.exists() or preds_path.stat().st_size < 10:
        return
    preds = pd.read_csv(preds_path)
    if len(preds) == 0:
        return
    r32_finished = r32_scheduled[r32_scheduled["status"] == "FINISHED"]
    if len(r32_finished) == 0:
        print("\nNo R32 results yet.")
        return

    correct = total = 0
    for _, result in r32_finished.iterrows():
        pred = preds[preds["match_id"] == result["match_id"]]
        if len(pred) == 0:
            continue
        if result["winner"] == "HOME_TEAM":
            actual_winner = result["home_team"]
        elif result["winner"] == "AWAY_TEAM":
            actual_winner = result["away_team"]
        else:
            actual_winner = "DRAW"
        total += 1
        if pred.iloc[0]["predicted_winner"] == actual_winner:
            correct += 1

    print(f"\nAccuracy: {correct}/{total} ({correct/max(total,1)*100:.0f}%)")


update_accuracy()
