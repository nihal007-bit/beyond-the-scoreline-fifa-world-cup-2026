import plotly.graph_objects as go


DARK_BG = "#0D1117"
CARD_BG = "#21262D"
GRID_COLOR = "#21262D"
TEXT_PRIMARY = "#E6EDF3"
TEXT_SECONDARY = "#8B949E"


def dark_layout(fig, height=400):
    fig.update_layout(
        plot_bgcolor=DARK_BG,
        paper_bgcolor=DARK_BG,
        font=dict(color=TEXT_SECONDARY),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
    )
    return fig
