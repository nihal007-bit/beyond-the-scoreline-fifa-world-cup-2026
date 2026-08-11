import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

shots_path = DATA_PROC / "shots_2022.csv"

if shots_path.exists():
    shots = pd.read_csv(shots_path)
else:
    from statsbombpy import sb

    matches = sb.matches(competition_id=43, season_id=106)
    print(f"Pulling shots from {len(matches)} matches...")

    all_shots = []
    for i, (_, match) in enumerate(matches.iterrows()):
        match_id = match["match_id"]
        try:
            events = sb.events(match_id=match_id)
            match_shots = events[events["type"] == "Shot"].copy()
            if len(match_shots) > 0:
                keep_cols = [c for c in ["player", "team", "location", "shot_statsbomb_xg",
                            "shot_outcome", "shot_technique", "shot_body_part", "minute"]
                            if c in match_shots.columns]
                match_shots = match_shots[keep_cols].copy()
                match_shots["match_id"] = match_id
                all_shots.append(match_shots)
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(matches)}")
        except Exception as e:
            print(f"  Error on match {match_id}: {e}")

    shots = pd.concat(all_shots, ignore_index=True)
    shots.to_csv(shots_path, index=False)

print(f"Shots loaded: {len(shots)}")

teams = shots["team"].unique()
xg_col = "shot_statsbomb_xg"

team_xg_rows = []
for team in teams:
    team_shots = shots[shots["team"] == team]
    total_xg_for = team_shots[xg_col].sum()
    actual_goals = len(team_shots[team_shots["shot_outcome"] == "Goal"])
    shots_taken = len(team_shots)
    xg_per_shot = total_xg_for / shots_taken if shots_taken > 0 else 0

    team_match_ids = team_shots["match_id"].unique()
    opp_shots_faced = shots[(shots["match_id"].isin(team_match_ids)) & (shots["team"] != team)]
    total_xg_against = opp_shots_faced[xg_col].sum()

    team_xg_rows.append({
        "team": team,
        "total_xg_for": round(total_xg_for, 2),
        "total_xg_against": round(total_xg_against, 2),
        "actual_goals": actual_goals,
        "xg_overperformance": round(actual_goals - total_xg_for, 2),
        "xg_per_shot": round(xg_per_shot, 4),
        "shots_taken": shots_taken,
    })

df_xg = pd.DataFrame(team_xg_rows)
df_xg.to_csv(DATA_PROC / "team_xg_2022.csv", index=False)

print("\nMost clinical:")
for _, r in df_xg.nlargest(5, "xg_overperformance").iterrows():
    print(f"  {r['team']:<20} {r['actual_goals']}g on {r['total_xg_for']:.1f}xG ({r['xg_overperformance']:+.1f})")
print("Most wasteful:")
for _, r in df_xg.nsmallest(5, "xg_overperformance").iterrows():
    print(f"  {r['team']:<20} {r['actual_goals']}g on {r['total_xg_for']:.1f}xG ({r['xg_overperformance']:+.1f})")

semifinalists = ["Argentina", "France", "Croatia", "Morocco"]

for team_name in semifinalists:
    team_shots = shots[shots["team"] == team_name].copy()
    if len(team_shots) == 0:
        continue

    team_shots["x"] = team_shots["location"].apply(
        lambda loc: eval(loc)[0] if isinstance(loc, str) else (loc[0] if isinstance(loc, list) else np.nan)
    )
    team_shots["y"] = team_shots["location"].apply(
        lambda loc: eval(loc)[1] if isinstance(loc, str) else (loc[1] if isinstance(loc, list) else np.nan)
    )
    team_shots = team_shots.dropna(subset=["x", "y"])

    total_xg = team_shots[xg_col].sum()
    goals = len(team_shots[team_shots["shot_outcome"] == "Goal"])

    fig, ax = plt.subplots(figsize=(8, 12))
    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#FAFAF8",
                          line_color="#cccccc")
    pitch.draw(ax=ax)

    for outcome, color in [("Goal", "#C8102E"), ("Saved", "#1a3c5e"),
                           ("Off T", "#1a3c5e"), ("Blocked", "#999999"),
                           ("Wayward", "#1a3c5e"), ("Post", "#1a3c5e")]:
        subset = team_shots[team_shots["shot_outcome"] == outcome]
        if len(subset) > 0:
            pitch.scatter(subset["x"], subset["y"], s=subset[xg_col] * 500 + 20,
                         c=color, alpha=0.7, ax=ax, label=outcome, edgecolors="black", linewidths=0.5)

    ax.set_title(f"{team_name} — 2022 World Cup Shots\nxG: {total_xg:.1f} | Goals: {goals}",
                fontsize=14, fontweight="bold", pad=10)
    ax.legend(loc="lower left", fontsize=8)

    fig.savefig(OUTPUTS / f"shotmap_{team_name.lower()}.png", dpi=150, bbox_inches="tight", facecolor="#FAFAF8")
    plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 10))
fig.patch.set_facecolor("#FAFAF8")
ax.set_facecolor("#FAFAF8")

ax.scatter(df_xg["total_xg_for"], df_xg["actual_goals"],
           s=df_xg["shots_taken"] * 3, c="#1a3c5e", alpha=0.7, edgecolors="black", linewidths=0.5)

max_val = max(df_xg["total_xg_for"].max(), df_xg["actual_goals"].max()) + 2
ax.plot([0, max_val], [0, max_val], "k--", alpha=0.4, linewidth=1)

df_xg["distance_from_line"] = abs(df_xg["actual_goals"] - df_xg["total_xg_for"])
outliers = df_xg.nlargest(8, "distance_from_line")
for _, r in outliers.iterrows():
    ax.annotate(r["team"], (r["total_xg_for"], r["actual_goals"]),
                fontsize=8, fontweight="bold", ha="center",
                xytext=(5, 8), textcoords="offset points")

mid_x = df_xg["total_xg_for"].median()
mid_y = df_xg["actual_goals"].median()
ax.text(mid_x * 0.3, mid_y * 1.8, "Clinical", fontsize=11, alpha=0.3, fontstyle="italic", color="#2E7D32")
ax.text(mid_x * 1.6, mid_y * 0.3, "Wasteful", fontsize=11, alpha=0.3, fontstyle="italic", color="#C8102E")
ax.text(mid_x * 1.6, mid_y * 1.8, "Dominant", fontsize=11, alpha=0.3, fontstyle="italic", color="#1a3c5e")
ax.text(mid_x * 0.3, mid_y * 0.3, "Struggling", fontsize=11, alpha=0.3, fontstyle="italic", color="#854F0B")

ax.set_xlabel("Total xG (Expected Goals)", fontsize=12)
ax.set_ylabel("Actual Goals Scored", fontsize=12)
ax.set_title("xG Efficiency — 2022 World Cup (Benchmark for 2026)",
             fontsize=14, fontweight="bold", pad=15)
ax.grid(True, alpha=0.2)

fig.savefig(OUTPUTS / "xg_efficiency.png", dpi=150, bbox_inches="tight", facecolor="#FAFAF8")
plt.close(fig)
print("\nCharts saved to outputs/")
