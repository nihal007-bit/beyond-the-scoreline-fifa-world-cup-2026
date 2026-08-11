import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

WC_GREEN = "#2E7D32"
WC_RED = "#C8102E"
WC_GOLD = "#F2C811"
WC_NAVY = "#1a3c5e"
WC_ORANGE = "#854F0B"
BACKGROUND = "#FAFAF8"

gci = pd.read_csv(DATA_PROC / "gci_analysis.csv")
standings = pd.read_csv(DATA_PROC / "standings.csv")
matches = pd.read_csv(DATA_PROC / "matches.csv")
predictions = pd.read_csv(DATA_PROC / "r32_predictions.csv")

gs_matches = matches[matches["stage"] == "GROUP_STAGE"]
gpg_2026 = gs_matches["total_goals"].sum() / len(gs_matches)

# --- GCI ranking ---
fig, ax = plt.subplots(figsize=(12, 8))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)

gci_sorted = gci.sort_values("GCI", ascending=True)
ax.barh(range(len(gci_sorted)), gci_sorted["GCI"], color=WC_NAVY, edgecolor="white", height=0.7)
ax.set_yticks(range(len(gci_sorted)))
ax.set_yticklabels([g.replace("GROUP_", "Group ") for g in gci_sorted["group"]], fontsize=11)
ax.axvline(gci_sorted["GCI"].mean(), color=WC_RED, linestyle="--", alpha=0.7, label="Mean GCI")

for i, (_, row) in enumerate(gci_sorted.iterrows()):
    ax.text(row["GCI"] + 0.01, i, f'{row["group_winner"]}  ({row["GCI"]:.3f})',
            va="center", fontsize=9, fontweight="bold")

ax.set_xlabel("Group Competitiveness Index (lower = more competitive)", fontsize=12)
ax.set_title("Group Competitiveness Index — 2026 World Cup", fontsize=16, fontweight="bold", pad=15)
ax.legend(fontsize=10)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.2)
fig.savefig(OUTPUTS / "gci_ranking.png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
plt.close(fig)

# --- Goals analysis ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(BACKGROUND)

years = ["2014", "2018", "2022", "2026"]
gpg_values = [2.67, 2.64, 2.69, round(gpg_2026, 2)]

ax1.set_facecolor(BACKGROUND)
bars1 = ax1.bar(years, gpg_values, color=[WC_NAVY, WC_NAVY, WC_NAVY, WC_RED], edgecolor="white", width=0.6)
for bar, val in zip(bars1, gpg_values):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
             f"{val:.2f}", ha="center", fontsize=11, fontweight="bold")
ax1.set_ylabel("Goals Per Game", fontsize=12)
ax1.set_title("Goals Per Game — World Cup History", fontsize=13, fontweight="bold")
ax1.set_ylim(0, max(gpg_values) * 1.2)
ax1.grid(axis="y", alpha=0.2)

high_scoring = gs_matches["is_high_scoring"].sum()
normal = len(gs_matches) - high_scoring
ax2.set_facecolor(BACKGROUND)
ax2.bar(["Normal (0-3 goals)", "High-scoring (4+)"],
        [normal, high_scoring], color=[WC_NAVY, WC_GOLD], edgecolor="white", width=0.5)
ax2.set_title("Match Scoring Distribution — 2026 Group Stage", fontsize=13, fontweight="bold")
ax2.set_ylabel("Number of Matches", fontsize=12)
for i, v in enumerate([normal, high_scoring]):
    ax2.text(i, v + 0.3, str(int(v)), ha="center", fontsize=12, fontweight="bold")
ax2.grid(axis="y", alpha=0.2)

fig.suptitle("2026 World Cup Scoring Analysis", fontsize=16, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUTPUTS / "goals_analysis.png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
plt.close(fig)

# --- Host nation performance ---
host_data = pd.read_csv(DATA_PROC / "host_nations.csv")

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.patch.set_facecolor(BACKGROUND)
fig.suptitle("Host Nation Performance — 2026 vs Historical Average", fontsize=16, fontweight="bold", y=1.02)

for i, (_, row) in enumerate(host_data.iterrows()):
    ax = axes[i]
    ax.set_facecolor(BACKGROUND)
    values = [row["wins"], row["draws"], row["losses"]]
    ax.bar(["Wins", "Draws", "Losses"], values, color=[WC_GREEN, WC_GOLD, WC_RED], edgecolor="white", width=0.5)
    ax.axhline(y=3 * 0.58, color="black", linestyle="--", alpha=0.5, label="Hist. avg wins")
    ax.set_title(f'{row["host"]}', fontsize=14, fontweight="bold")
    ax.set_ylim(0, max(values) + 1)
    for j, v in enumerate(values):
        ax.text(j, v + 0.05, str(int(v)), ha="center", fontsize=12, fontweight="bold")
    ax.grid(axis="y", alpha=0.2)
    if i == 0:
        ax.legend(fontsize=8)

fig.tight_layout()
fig.savefig(OUTPUTS / "host_nation_performance.png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
plt.close(fig)

# --- Final group standings ---
groups = sorted(standings["group"].unique())
n_cols = 4
n_rows = (len(groups) + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 12))
fig.patch.set_facecolor(BACKGROUND)
fig.suptitle("2026 World Cup — Final Group Standings", fontsize=18, fontweight="bold", y=1.01)

for idx, group in enumerate(groups):
    ax = axes[idx // n_cols, idx % n_cols] if n_rows > 1 else axes[idx % n_cols]
    ax.set_facecolor(BACKGROUND)

    grp = standings[standings["group"] == group].sort_values("position")
    bar_colors = [WC_GREEN if r["position"] <= 2 else WC_ORANGE if r["position"] == 3 else WC_RED
                  for _, r in grp.iterrows()]

    ax.barh(range(len(grp)), grp["points"], color=bar_colors, edgecolor="white", height=0.6)
    ax.set_yticks(range(len(grp)))
    ax.set_yticklabels([t[:12] for t in grp["team"]], fontsize=8)
    ax.set_title(group.replace("GROUP_", "Group "), fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, standings["points"].max() + 1)
    for j, (_, r) in enumerate(grp.iterrows()):
        ax.text(r["points"] + 0.1, j, str(int(r["points"])), va="center", fontsize=9, fontweight="bold")
    ax.grid(axis="x", alpha=0.2)

for idx in range(len(groups), n_rows * n_cols):
    ax = axes[idx // n_cols, idx % n_cols] if n_rows > 1 else axes[idx % n_cols]
    ax.set_visible(False)

fig.legend(handles=[
    mpatches.Patch(color=WC_GREEN, label="Qualified (Top 2)"),
    mpatches.Patch(color=WC_ORANGE, label="3rd Place"),
    mpatches.Patch(color=WC_RED, label="Eliminated (4th)"),
], loc="lower center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.02))

fig.tight_layout()
fig.savefig(OUTPUTS / "standings_visual.png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
plt.close(fig)

# --- R32 predictions table ---
fig, ax = plt.subplots(figsize=(14, 10))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)
ax.axis("off")
ax.set_title("Round of 32 Predictions — 2026 World Cup", fontsize=18, fontweight="bold", pad=20)

headers = ["#", "Team 1", "Team 2", "Predicted Winner", "Confidence"]
col_x = [0.02, 0.08, 0.32, 0.56, 0.82]
y_start = 0.92

for j, header in enumerate(headers):
    ax.text(col_x[j], y_start, header, fontsize=11, fontweight="bold",
            transform=ax.transAxes, va="top")
ax.plot([0.01, 0.99], [y_start - 0.015, y_start - 0.015], color="black", linewidth=1.5,
        transform=ax.transAxes, clip_on=False)

for i, (_, row) in enumerate(predictions.iterrows()):
    y = y_start - 0.05 * (i + 1)
    conf = row["confidence"]
    txt_color = WC_GREEN if conf > 65 else WC_ORANGE if conf < 55 else WC_NAVY
    weight = "bold" if conf > 65 else "normal"

    ax.text(col_x[0], y, str(i + 1), fontsize=9, transform=ax.transAxes, va="top")
    ax.text(col_x[1], y, row["team_1"], fontsize=9, transform=ax.transAxes, va="top")
    ax.text(col_x[2], y, row["team_2"], fontsize=9, transform=ax.transAxes, va="top")
    ax.text(col_x[3], y, row["predicted_winner"], fontsize=9, fontweight=weight,
            color=txt_color, transform=ax.transAxes, va="top")
    ax.text(col_x[4], y, f"{conf:.1f}%", fontsize=9, fontweight=weight,
            color=txt_color, transform=ax.transAxes, va="top")

    if i < len(predictions) - 1:
        ax.plot([0.01, 0.99], [y - 0.015, y - 0.015], color="#ddd", linewidth=0.5,
               transform=ax.transAxes, clip_on=False)

fig.savefig(OUTPUTS / "predictions_chart.png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
plt.close(fig)

for fname in ["gci_ranking.png", "goals_analysis.png", "host_nation_performance.png",
              "standings_visual.png", "xg_efficiency.png", "predictions_chart.png"]:
    fpath = OUTPUTS / fname
    status = f"{fpath.stat().st_size / 1024:.0f}KB" if fpath.exists() else "MISSING"
    print(f"  {fname}: {status}")
