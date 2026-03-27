"""Tests for ChartBuilder — assert correct Plotly figure types and data."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.f1_ai.viz.charts import ChartBuilder


@pytest.fixture()
def builder() -> ChartBuilder:
    return ChartBuilder()


# ---------------------------------------------------------------------------
# plot_lap_times
# ---------------------------------------------------------------------------

class TestPlotLapTimes:
    def test_returns_figure(self, builder: ChartBuilder, sample_laps_df: pd.DataFrame) -> None:
        fig = builder.plot_lap_times(sample_laps_df)
        assert isinstance(fig, go.Figure)

    def test_title_applied(self, builder: ChartBuilder, sample_laps_df: pd.DataFrame) -> None:
        title = "Monaco 2023 Lap Times"
        fig = builder.plot_lap_times(sample_laps_df, title=title)
        assert fig.layout.title.text == title

    def test_default_title(self, builder: ChartBuilder, sample_laps_df: pd.DataFrame) -> None:
        fig = builder.plot_lap_times(sample_laps_df)
        assert fig.layout.title.text == "Lap Times"

    def test_has_traces(self, builder: ChartBuilder, sample_laps_df: pd.DataFrame) -> None:
        """Figure must have at least one trace (one per driver)."""
        fig = builder.plot_lap_times(sample_laps_df)
        assert len(fig.data) >= 1

    def test_limits_to_10_drivers(self, builder: ChartBuilder) -> None:
        """When more than 10 drivers are present, only the 10 fastest are shown."""
        drivers = [f"D{i:02d}" for i in range(15)]
        rows = []
        for i, driver in enumerate(drivers):
            for lap in range(1, 4):
                rows.append(
                    {
                        "Driver": driver,
                        "LapNumber": lap,
                        "LapTimeSeconds": 90 + i,  # each driver slightly slower
                    }
                )
        df = pd.DataFrame(rows)
        fig = builder.plot_lap_times(df)
        plotted_drivers = {trace.name for trace in fig.data}
        assert len(plotted_drivers) <= 10

    def test_dark_template(self, builder: ChartBuilder, sample_laps_df: pd.DataFrame) -> None:
        fig = builder.plot_lap_times(sample_laps_df)
        assert fig.layout.template is not None


# ---------------------------------------------------------------------------
# plot_race_results
# ---------------------------------------------------------------------------

class TestPlotRaceResults:
    def test_returns_figure(
        self, builder: ChartBuilder, sample_results_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_race_results(sample_results_df)
        assert isinstance(fig, go.Figure)

    def test_title_applied(
        self, builder: ChartBuilder, sample_results_df: pd.DataFrame
    ) -> None:
        title = "British GP Results"
        fig = builder.plot_race_results(sample_results_df, title=title)
        assert fig.layout.title.text == title

    def test_default_title(
        self, builder: ChartBuilder, sample_results_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_race_results(sample_results_df)
        assert fig.layout.title.text == "Race Results"

    def test_has_traces(
        self, builder: ChartBuilder, sample_results_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_race_results(sample_results_df)
        assert len(fig.data) >= 1

    def test_sorted_ascending_by_points(
        self, builder: ChartBuilder, sample_results_df: pd.DataFrame
    ) -> None:
        """The chart must display drivers sorted by ascending Points (horizontal bar)."""
        fig = builder.plot_race_results(sample_results_df)
        # The first trace's y-values should start with the driver with fewest points
        y_values = list(fig.data[0].y)
        assert y_values[0] == "LEC"  # 15 pts — lowest in fixture


# ---------------------------------------------------------------------------
# plot_season_standings
# ---------------------------------------------------------------------------

class TestPlotSeasonStandings:
    def test_returns_figure(
        self, builder: ChartBuilder, sample_standings_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_season_standings(sample_standings_df, 2023)
        assert isinstance(fig, go.Figure)

    def test_title_contains_year(
        self, builder: ChartBuilder, sample_standings_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_season_standings(sample_standings_df, 2023)
        assert "2023" in fig.layout.title.text

    def test_has_traces(
        self, builder: ChartBuilder, sample_standings_df: pd.DataFrame
    ) -> None:
        fig = builder.plot_season_standings(sample_standings_df, 2023)
        assert len(fig.data) >= 1

    def test_limits_to_top_10(self, builder: ChartBuilder) -> None:
        """When more than 10 drivers are present only the first 10 rows are shown."""
        data = {
            "Position": list(range(1, 16)),
            "Driver": [f"Driver{i}" for i in range(1, 16)],
            "Team": ["Team"] * 15,
            "Points": [500 - i * 10 for i in range(15)],
            "Wins": [20 - i for i in range(15)],
        }
        df = pd.DataFrame(data)
        fig = builder.plot_season_standings(df, 2023)
        # Collect all x-values across traces; should correspond to ≤10 drivers
        all_names = [
            name
            for trace in fig.data
            for name in (list(trace.x) if trace.x is not None else [])
        ]
        assert len(all_names) <= 10
