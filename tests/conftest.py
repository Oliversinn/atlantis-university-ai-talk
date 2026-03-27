"""Shared pytest fixtures for the F1 AI test suite."""

import pandas as pd
import pytest


@pytest.fixture()
def sample_laps_df() -> pd.DataFrame:
    """Return a minimal lap-times DataFrame that mirrors F1DataFetcher.get_lap_times output."""
    data = {
        "Driver": ["HAM", "HAM", "VER", "VER", "LEC"],
        "LapNumber": [1, 2, 1, 2, 1],
        "LapTimeSeconds": [90.1, 89.5, 88.9, 89.0, 91.2],
        "Sector1Time": [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
        "Sector2Time": [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
        "Sector3Time": [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
    }
    return pd.DataFrame(data)


@pytest.fixture()
def sample_results_df() -> pd.DataFrame:
    """Return a minimal race-results DataFrame that mirrors F1DataFetcher.get_race_results output."""
    data = {
        "DriverNumber": ["44", "1", "16"],
        "BroadcastName": ["HAM", "VER", "LEC"],
        "TeamName": ["Mercedes", "Red Bull", "Ferrari"],
        "Position": [1, 2, 3],
        "Points": [25.0, 18.0, 15.0],
        "Time": [pd.NaT, pd.NaT, pd.NaT],
    }
    return pd.DataFrame(data)


@pytest.fixture()
def sample_standings_df() -> pd.DataFrame:
    """Return a minimal standings DataFrame that mirrors F1DataFetcher.get_season_standings output."""
    data = {
        "Position": [1, 2, 3],
        "Driver": ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc"],
        "Team": ["Red Bull", "Mercedes", "Ferrari"],
        "Points": [575.0, 234.0, 206.0],
        "Wins": [19, 2, 1],
    }
    return pd.DataFrame(data)


@pytest.fixture()
def ergast_response() -> dict:
    """Return a minimal Ergast API JSON payload for driver standings."""
    return {
        "MRData": {
            "StandingsTable": {
                "StandingsLists": [
                    {
                        "DriverStandings": [
                            {
                                "position": "1",
                                "points": "575",
                                "wins": "19",
                                "Driver": {
                                    "givenName": "Max",
                                    "familyName": "Verstappen",
                                },
                                "Constructors": [{"name": "Red Bull"}],
                            },
                            {
                                "position": "2",
                                "points": "234",
                                "wins": "2",
                                "Driver": {
                                    "givenName": "Lewis",
                                    "familyName": "Hamilton",
                                },
                                "Constructors": [{"name": "Mercedes"}],
                            },
                        ]
                    }
                ]
            }
        }
    }
