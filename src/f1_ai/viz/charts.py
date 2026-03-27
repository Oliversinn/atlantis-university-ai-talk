"""ChartBuilder — contains all Plotly visualisation methods."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class ChartBuilder:
    """Builds Plotly charts for Formula 1 data."""

    def plot_lap_times(self, laps_df: pd.DataFrame, title: str = "Lap Times") -> go.Figure:
        """Build a Plotly line chart of lap times per driver.

        Limits to the 10 drivers with the lowest median lap time.
        """
        top_drivers = (
            laps_df.groupby("Driver")["LapTimeSeconds"]
            .median()
            .nsmallest(10)
            .index.tolist()
        )
        filtered = laps_df[laps_df["Driver"].isin(top_drivers)]
        fig = px.line(
            filtered,
            x="LapNumber",
            y="LapTimeSeconds",
            color="Driver",
            title=title,
            labels={"LapTimeSeconds": "Lap Time (s)", "LapNumber": "Lap"},
            template="plotly_dark",
        )
        return fig

    def plot_race_results(self, results_df: pd.DataFrame, title: str = "Race Results") -> go.Figure:
        """Build a Plotly horizontal bar chart of points scored per driver."""
        fig = px.bar(
            results_df.sort_values("Points", ascending=True),
            x="Points",
            y="BroadcastName",
            orientation="h",
            color="TeamName",
            title=title,
            labels={"BroadcastName": "Driver", "Points": "Points Scored"},
            template="plotly_dark",
        )
        return fig

    def plot_season_standings(self, standings_df: pd.DataFrame, year: int) -> go.Figure:
        """Build a Plotly bar chart of the season driver standings."""
        fig = px.bar(
            standings_df.head(10),
            x="Driver",
            y="Points",
            color="Team",
            title=f"{year} Driver Championship Standings",
            labels={"Driver": "Driver", "Points": "Championship Points"},
            template="plotly_dark",
        )
        fig.update_xaxes(tickangle=30)
        return fig
