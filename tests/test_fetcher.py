"""Tests for F1DataFetcher — mocks FastF1 and Ergast API calls."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Patch fastf1.Cache.enable_cache and os.makedirs before importing the module
# so the cache is never touched during tests.
with patch("os.makedirs"), patch("fastf1.Cache.enable_cache"):
    from src.f1_ai.data.fetcher import F1DataFetcher


@pytest.fixture()
def fetcher() -> F1DataFetcher:
    return F1DataFetcher()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_session(laps_df: pd.DataFrame, results_df: pd.DataFrame) -> MagicMock:
    """Build a minimal FastF1 session mock."""
    session = MagicMock()
    session.laps = laps_df
    session.results = results_df
    return session


# ---------------------------------------------------------------------------
# get_lap_times
# ---------------------------------------------------------------------------

class TestGetLapTimes:
    def test_returns_dataframe(self, fetcher: F1DataFetcher) -> None:
        """get_lap_times should return a DataFrame with LapTimeSeconds column."""
        import datetime

        laps_data = pd.DataFrame(
            {
                "Driver": ["HAM", "VER"],
                "LapNumber": [1, 1],
                "LapTime": [
                    pd.Timedelta(seconds=90),
                    pd.Timedelta(seconds=89),
                ],
                "Sector1Time": [pd.NaT, pd.NaT],
                "Sector2Time": [pd.NaT, pd.NaT],
                "Sector3Time": [pd.NaT, pd.NaT],
            }
        )
        mock_session = _make_mock_session(laps_data, pd.DataFrame())

        with patch("src.f1_ai.data.fetcher.fastf1.get_session", return_value=mock_session):
            result = fetcher.get_lap_times(2023, "Monaco", "R")

        assert isinstance(result, pd.DataFrame)
        assert "LapTimeSeconds" in result.columns
        assert len(result) == 2

    def test_drops_rows_with_missing_lap_time(self, fetcher: F1DataFetcher) -> None:
        """Rows with NaT LapTime should be dropped."""
        laps_data = pd.DataFrame(
            {
                "Driver": ["HAM", "VER"],
                "LapNumber": [1, 1],
                "LapTime": [pd.Timedelta(seconds=90), pd.NaT],
                "Sector1Time": [pd.NaT, pd.NaT],
                "Sector2Time": [pd.NaT, pd.NaT],
                "Sector3Time": [pd.NaT, pd.NaT],
            }
        )
        mock_session = _make_mock_session(laps_data, pd.DataFrame())

        with patch("src.f1_ai.data.fetcher.fastf1.get_session", return_value=mock_session):
            result = fetcher.get_lap_times(2023, "Monaco")

        assert len(result) == 1
        assert result.iloc[0]["Driver"] == "HAM"

    def test_lap_time_seconds_conversion(self, fetcher: F1DataFetcher) -> None:
        """LapTimeSeconds should equal the total seconds of the Timedelta."""
        laps_data = pd.DataFrame(
            {
                "Driver": ["HAM"],
                "LapNumber": [1],
                "LapTime": [pd.Timedelta(seconds=95.5)],
                "Sector1Time": [pd.NaT],
                "Sector2Time": [pd.NaT],
                "Sector3Time": [pd.NaT],
            }
        )
        mock_session = _make_mock_session(laps_data, pd.DataFrame())

        with patch("src.f1_ai.data.fetcher.fastf1.get_session", return_value=mock_session):
            result = fetcher.get_lap_times(2023, "Monaco")

        assert result.iloc[0]["LapTimeSeconds"] == pytest.approx(95.5)


# ---------------------------------------------------------------------------
# get_race_results
# ---------------------------------------------------------------------------

class TestGetRaceResults:
    def test_returns_top_10(self, fetcher: F1DataFetcher) -> None:
        """get_race_results should return at most 10 rows."""
        results_data = pd.DataFrame(
            {
                "DriverNumber": [str(i) for i in range(1, 16)],
                "BroadcastName": [f"DRV{i}" for i in range(1, 16)],
                "TeamName": ["Team"] * 15,
                "Position": list(range(1, 16)),
                "Points": [25.0 - i for i in range(15)],
                "Time": [pd.NaT] * 15,
            }
        )
        mock_session = _make_mock_session(pd.DataFrame(), results_data)

        with patch("src.f1_ai.data.fetcher.fastf1.get_session", return_value=mock_session):
            result = fetcher.get_race_results(2023, "Monaco")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10

    def test_expected_columns_present(self, fetcher: F1DataFetcher) -> None:
        """get_race_results should include the required columns."""
        results_data = pd.DataFrame(
            {
                "DriverNumber": ["44"],
                "BroadcastName": ["HAM"],
                "TeamName": ["Mercedes"],
                "Position": [1],
                "Points": [25.0],
                "Time": [pd.NaT],
            }
        )
        mock_session = _make_mock_session(pd.DataFrame(), results_data)

        with patch("src.f1_ai.data.fetcher.fastf1.get_session", return_value=mock_session):
            result = fetcher.get_race_results(2023, "Monaco")

        for col in ("DriverNumber", "BroadcastName", "TeamName", "Position", "Points"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# get_season_standings
# ---------------------------------------------------------------------------

class TestGetSeasonStandings:
    def test_returns_correct_rows(
        self, fetcher: F1DataFetcher, ergast_response: dict
    ) -> None:
        """get_season_standings should parse the Ergast JSON into a DataFrame."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = ergast_response
        mock_resp.raise_for_status = MagicMock()

        with patch("src.f1_ai.data.fetcher.requests.get", return_value=mock_resp):
            result = fetcher.get_season_standings(2023)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["Driver"] == "Max Verstappen"
        assert result.iloc[0]["Points"] == 575.0
        assert result.iloc[0]["Wins"] == 19

    def test_returns_empty_df_for_empty_standings(self, fetcher: F1DataFetcher) -> None:
        """get_season_standings should return an empty DataFrame when no standings data."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "MRData": {"StandingsTable": {"StandingsLists": []}}
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("src.f1_ai.data.fetcher.requests.get", return_value=mock_resp):
            result = fetcher.get_season_standings(1950)

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_raises_on_http_error(self, fetcher: F1DataFetcher) -> None:
        """get_season_standings should propagate HTTP errors."""
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.HTTPError("404 Not Found")

        with patch("src.f1_ai.data.fetcher.requests.get", return_value=mock_resp):
            with pytest.raises(req_lib.HTTPError):
                fetcher.get_season_standings(9999)
