import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"

matches = pd.read_csv(DATA_PROC / "matches.csv")
standings = pd.read_csv(DATA_PROC / "standings.csv")
team_goals = pd.read_csv(DATA_PROC / "team_goals.csv")

gs_matches = matches[matches["stage"] == "GROUP_STAGE"].copy()

gci_rows = []
for group in sorted(standings["group"].unique()):
    grp = standings[standings["group"] == group].sort_values("position")
    pts = grp["points"].values
    gci = np.std(pts) / np.mean(pts) if np.mean(pts) > 0 else np.nan
    gci_rows.append({
        "group": group,
        "GCI": round(gci, 4),
        "most_points": int(pts[0]),
        "least_points": int(pts[-1]),
        "points_spread": int(pts[0] - pts[-1]),
        "group_winner": grp.iloc[0]["team"],
        "group_runner_up": grp.iloc[1]["team"],
    })

df_gci = pd.DataFrame(gci_rows).sort_values("GCI")
df_gci.to_csv(DATA_PROC / "gci_analysis.csv", index=False)

most_comp = df_gci.iloc[0]
least_comp = df_gci.iloc[-1]
print(f"Most competitive: {most_comp['group']} (GCI={most_comp['GCI']:.4f})")
print(f"Least competitive: {least_comp['group']} (GCI={least_comp['GCI']:.4f})")

total_goals_gs = gs_matches["total_goals"].sum()
total_matches_gs = len(gs_matches)
gpg_2026 = total_goals_gs / total_matches_gs
print(f"\nGoals per game: {gpg_2026:.2f} (2022: 2.69, 2018: 2.64, 2014: 2.67)")

gpg_by_country = gs_matches.groupby("venue_country").agg(
    total_goals=("total_goals", "sum"),
    matches=("match_id", "count"),
).reset_index()
gpg_by_country["gpg"] = (gpg_by_country["total_goals"] / gpg_by_country["matches"]).round(2)
gpg_by_country.to_csv(DATA_PROC / "scoring_analysis.csv", index=False)

host_names_map = {}
all_teams = team_goals["team"].unique()
for t in all_teams:
    t_lower = t.lower()
    if "united states" in t_lower or "usa" in t_lower:
        host_names_map["USA"] = t
    elif "mexico" in t_lower or "méxico" in t_lower:
        host_names_map["Mexico"] = t
    elif "canada" in t_lower:
        host_names_map["Canada"] = t

host_rows = []
for label, team_name in host_names_map.items():
    tm = team_goals[team_goals["team"] == team_name]
    gs_tm = tm[tm["stage"] == "GROUP_STAGE"]
    wins = len(gs_tm[gs_tm["result"] == "W"])
    draws = len(gs_tm[gs_tm["result"] == "D"])
    losses = len(gs_tm[gs_tm["result"] == "L"])
    gf = int(gs_tm["goals_scored"].sum())
    ga = int(gs_tm["goals_conceded"].sum())
    grp_pos = standings[standings["team"] == team_name]["position"].values
    grp_pos = int(grp_pos[0]) if len(grp_pos) > 0 else None
    qualified = grp_pos is not None and grp_pos <= 3

    host_rows.append({
        "host": label,
        "team_api_name": team_name,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "group_position": grp_pos,
        "qualified_r32": qualified,
        "win_pct": round(wins / max(len(gs_tm), 1) * 100, 1),
    })
    print(f"{label}: {wins}W-{draws}D-{losses}L (GF:{gf} GA:{ga}, pos:{grp_pos})")

df_hosts = pd.DataFrame(host_rows)
df_hosts.to_csv(DATA_PROC / "host_nations.csv", index=False)

avg_win_pct = np.mean([r["win_pct"] for r in host_rows])
print(f"Host avg win rate: {avg_win_pct:.1f}% (historical: ~58%)")

third_place = standings[standings["position"] == 3].copy()
third_place = third_place.sort_values(
    ["points", "goal_difference", "goals_for"],
    ascending=[False, False, False]
)
best_thirds = third_place.head(8)
eliminated_thirds = third_place.tail(len(third_place) - 8)

avg_third_pts = best_thirds["points"].mean()
print(f"\nAdvancing 3rd-place teams avg points: {avg_third_pts:.1f}")

matchdays = gs_matches.groupby("group")["date"].max().reset_index()
matchdays.columns = ["group", "final_matchday"]

total_final_matches = 0
for _, md in matchdays.iterrows():
    final_matches = gs_matches[
        (gs_matches["group"] == md["group"]) & (gs_matches["date"] == md["final_matchday"])
    ]
    total_final_matches += len(final_matches)

format_data = {
    "metric": [
        "total_teams", "groups", "matches_to_win_trophy_48", "matches_to_win_trophy_32",
        "advancing_third_place_teams", "avg_third_place_points",
        "total_final_matchday_games", "total_group_matches",
    ],
    "value": [
        48, 12, 8, 7,
        8, round(avg_third_pts, 1),
        total_final_matches, len(gs_matches),
    ],
}
pd.DataFrame(format_data).to_csv(DATA_PROC / "format_analysis.csv", index=False)
print(f"Group matches: {len(gs_matches)}, final matchday games: {total_final_matches}")
