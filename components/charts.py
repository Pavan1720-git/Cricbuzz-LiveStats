"""
components/charts.py — Reusable Plotly chart builders.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

_THEME = {"template": "plotly_dark", "color_discrete_sequence": px.colors.qualitative.Set2}


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = None,
              orientation: str = "v") -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, color=color, orientation=orientation, **_THEME)
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(df, names=names, values=values, title=title, **_THEME)
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    return fig


def scatter_chart(df: pd.DataFrame, x: str, y: str, title: str,
                  color: str = None, hover_data: list = None) -> go.Figure:
    fig = px.scatter(df, x=x, y=y, title=title, color=color,
                     hover_data=hover_data or [], **_THEME)
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, title: str,
               color: str = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, title=title, color=color, markers=True, **_THEME)
    fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
    return fig


def top_scorers_chart(df: pd.DataFrame, n: int = 10) -> go.Figure:
    top = df.nlargest(n, "total_runs")
    return bar_chart(top, y="full_name", x="total_runs",
                     title=f"Top {n} Run Scorers", orientation="h")


def top_wicket_chart(df: pd.DataFrame, n: int = 10) -> go.Figure:
    top = df.nlargest(n, "total_wickets")
    return bar_chart(top, y="full_name", x="total_wickets",
                     title=f"Top {n} Wicket Takers", orientation="h")


def team_wins_chart(df: pd.DataFrame) -> go.Figure:
    return bar_chart(df.sort_values("wins", ascending=False),
                     x="team_name", y="wins", title="Team Wins Comparison")
