"""F1DataFetcher — wraps all FastF1 and Ergast API calls."""

import os
from typing import Any, cast

import fastf1
import pandas as pd
import requests

from src.f1_ai.config import CACHE_DIR

# Enable FastF1 cache once when this module is first imported.
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


class F1DataFetcher:
    """Fetches Formula 1 data from FastF1 and the Ergast API."""

    def get_lap_times(self, year: int, event: str, session_type: str = "R") -> pd.DataFrame:
        """Fetch lap times for a session using FastF1.

        Returns a DataFrame with columns: Driver, LapNumber, LapTimeSeconds,
        Sector1Time, Sector2Time, Sector3Time.
        """
        session = fastf1.get_session(year, event, session_type)
        session.load(telemetry=False, weather=False, messages=False)
        laps = cast(
            pd.DataFrame,
            session.laps[["Driver", "LapNumber", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]].copy(),
        )
        laps = laps.dropna(subset=["LapTime"])
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
        return laps

    def get_race_results(self, year: int, event: str) -> pd.DataFrame:
        """Fetch race results for a session using FastF1.

        Returns the top-10 finishers with columns:
        DriverNumber, BroadcastName, TeamName, Position, Points, Time.
        """
        session = fastf1.get_session(year, event, "R")
        session.load(telemetry=False, weather=False, messages=False)
        results = cast(
            pd.DataFrame,
            session.results[["DriverNumber", "BroadcastName", "TeamName", "Position", "Points", "Time"]].copy(),
        )
        return results.head(10)

    def get_season_standings(self, year: int) -> pd.DataFrame:
        """Fetch season driver standings from the Ergast API.

        Returns a DataFrame with columns: Position, Driver, Team, Points, Wins.
        """
        url = f"https://ergast.com/api/f1/{year}/driverStandings.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = cast(dict[str, Any], response.json())
        standings_list = cast(
            list[dict[str, Any]],
            data["MRData"]["StandingsTable"]["StandingsLists"],
        )
        if not standings_list:
            return pd.DataFrame()
        standings = cast(list[dict[str, Any]], standings_list[0]["DriverStandings"])
        rows = [
            {
                "Position": int(s["position"]),
                "Driver": f"{s['Driver']['givenName']} {s['Driver']['familyName']}",
                "Team": s["Constructors"][0]["name"],
                "Points": float(s["points"]),
                "Wins": int(s["wins"]),
            }
            for s in standings
        ]
        return pd.DataFrame(rows)
