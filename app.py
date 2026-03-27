"""Formula 1 AI Assistant - First Draft

A Streamlit app that lets users ask natural language questions about Formula 1.
Supports historical questions, regulation queries, and live race data via FastF1.

First draft written in a junior developer style — logic lives mostly in top-level
functions inside a single file. Subsequent PRs will refactor this into classes,
add tests, and introduce proper linting/type checking.
"""

import json
import os
from datetime import datetime

import fastf1
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

fastf1.Cache.enable_cache("cache")

EXAMPLE_QUESTIONS = [
    "Who has the most Formula 1 World Championships?",
    "What is DRS and how does it work?",
    "Show me the lap times from the 2023 Monaco Grand Prix",
    "Who won the most races in 2023?",
    "What are the 2024 F1 technical regulations about the cost cap?",
    "Show me the race results for the 2023 British Grand Prix",
    "Which team scored the most points in 2023?",
    "Who holds the record for most pole positions?",
    "Explain the tire compound strategy used in modern F1",
    "Show me the 2023 driver championship standings",
]

CURRENT_YEAR = datetime.now().year


# ---------------------------------------------------------------------------
# OpenAI helpers
# ---------------------------------------------------------------------------

def get_openai_client():
    """Create and return an OpenAI client using the API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def classify_question(client, question):
    """Classify a question into: historical, regulations, or race_data.

    Returns one of the three string labels. Falls back to 'historical'
    if the model returns an unexpected value.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Formula 1 expert. Classify the user's question into exactly "
                    "one of three categories:\n"
                    "- historical: questions about F1 history, records, championships, drivers, teams\n"
                    "- regulations: questions about F1 rules, technical regulations, sporting code, "
                    "car specifications, DRS, ERS, budget caps\n"
                    "- race_data: questions that require specific race data such as lap times, "
                    "race results, sector times, or season standings for a particular year or event\n\n"
                    "Respond with ONLY the category name: historical, regulations, or race_data"
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=20,
    )
    category = response.choices[0].message.content.strip().lower()
    if category not in ("historical", "regulations", "race_data"):
        return "historical"
    return category


def answer_historical_question(client, question):
    """Use OpenAI to answer a historical F1 question."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Formula 1 history expert with comprehensive knowledge of F1 "
                    "from 1950 to the present. Answer questions about F1 history, drivers, "
                    "constructors, circuits, records, and championships. Be concise but "
                    "informative. Use bullet points or bold text to highlight key facts."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=600,
    )
    return response.choices[0].message.content


def answer_regulations_question(client, question):
    """Use OpenAI to answer an F1 regulations question."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Formula 1 technical and sporting regulations expert with "
                    "knowledge up to 2024. Answer questions about F1 rules, technical "
                    "regulations, sporting code, DRS, ERS, budget caps, and car specifications. "
                    "Be clear and precise. Use headings or bullet points where appropriate."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=600,
    )
    return response.choices[0].message.content


def extract_race_params(client, question):
    """Extract race parameters (year, event, session_type) from a natural-language question.

    Returns a dict with keys:
        year (int), event (str), session_type (str)
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract Formula 1 race information from the question. "
                    "Return a JSON object with these keys:\n"
                    "  - year: integer year of the race (default to the previous calendar year if not mentioned)\n"
                    "  - event: string event name like 'Monaco', 'British', 'Italian', 'Bahrain'\n"
                    "  - session_type: string, one of 'R' (Race), 'Q' (Qualifying), "
                    "'FP1', 'FP2', 'FP3' (default to 'R')\n\n"
                    "Return ONLY valid JSON, no other text."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=150,
        response_format={"type": "json_object"},
    )
    params = json.loads(response.choices[0].message.content)
    # Provide sensible defaults
    params.setdefault("year", CURRENT_YEAR - 1)
    params.setdefault("event", "Monaco")
    params.setdefault("session_type", "R")
    return params


# ---------------------------------------------------------------------------
# FastF1 data fetchers
# ---------------------------------------------------------------------------

def get_lap_times(year, event, session_type="R"):
    """Fetch lap times for a session using FastF1.

    Returns a DataFrame with columns: Driver, LapNumber, LapTimeSeconds,
    Sector1Time, Sector2Time, Sector3Time.
    """
    session = fastf1.get_session(year, event, session_type)
    session.load(telemetry=False, weather=False, messages=False)
    laps = session.laps[
        ["Driver", "LapNumber", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]
    ].copy()
    laps = laps.dropna(subset=["LapTime"])
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    return laps


def get_race_results(year, event):
    """Fetch race results for a session using FastF1.

    Returns the top-10 finishers with columns:
    DriverNumber, BroadcastName, TeamName, Position, Points, Time.
    """
    session = fastf1.get_session(year, event, "R")
    session.load(telemetry=False, weather=False, messages=False)
    results = session.results[
        ["DriverNumber", "BroadcastName", "TeamName", "Position", "Points", "Time"]
    ].copy()
    return results.head(10)


def get_season_standings(year):
    """Fetch season driver standings from the Ergast API.

    Returns a DataFrame with columns: Position, Driver, Team, Points, Wins.
    """
    url = f"https://ergast.com/api/f1/{year}/driverStandings.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    standings_list = data["MRData"]["StandingsTable"]["StandingsLists"]
    if not standings_list:
        return pd.DataFrame()
    standings = standings_list[0]["DriverStandings"]
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


# ---------------------------------------------------------------------------
# Visualization builders
# ---------------------------------------------------------------------------

def plot_lap_times(laps_df, title="Lap Times"):
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


def plot_race_results(results_df, title="Race Results"):
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


def plot_season_standings(standings_df, year):
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


# ---------------------------------------------------------------------------
# Question handlers
# ---------------------------------------------------------------------------

def handle_race_data_question(client, question):
    """Route a race_data question to the right data fetch and visualisation."""
    params = extract_race_params(client, question)
    year = int(params.get("year", CURRENT_YEAR - 1))
    event = params.get("event", "Monaco")
    session_type = params.get("session_type", "R")

    st.info(f"📊 Fetching data for the **{year} {event} Grand Prix** (session: {session_type})…")

    question_lower = question.lower()

    # --- lap times / sector analysis ---
    if any(w in question_lower for w in ("lap time", "fastest lap", "sector", "pace")):
        laps = get_lap_times(year, event, session_type)
        fig = plot_lap_times(laps, f"Lap Times – {year} {event} Grand Prix")
        st.plotly_chart(fig, use_container_width=True)

        fastest = (
            laps.groupby("Driver")["LapTimeSeconds"]
            .min()
            .sort_values()
            .head(10)
            .reset_index()
        )
        fastest.columns = ["Driver", "Fastest Lap (s)"]
        fastest["Fastest Lap"] = fastest["Fastest Lap (s)"].apply(
            lambda x: f"{int(x // 60)}:{x % 60:06.3f}"
        )
        st.dataframe(fastest[["Driver", "Fastest Lap"]], use_container_width=True)

    # --- season standings ---
    elif any(w in question_lower for w in ("standing", "championship", "season points")):
        standings = get_season_standings(year)
        if standings.empty:
            st.warning(f"No standings data found for {year}.")
        else:
            fig = plot_season_standings(standings, year)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(standings, use_container_width=True)

    # --- race results (default for race_data) ---
    else:
        results = get_race_results(year, event)
        fig = plot_race_results(results, f"Race Results – {year} {event} Grand Prix")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(results, use_container_width=True)


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="F1 AI Assistant 🏎️",
        page_icon="🏎️",
        layout="wide",
    )

    # --- Header ---
    st.title("🏎️ Formula 1 AI Assistant")
    st.markdown(
        "Ask me anything about Formula 1 — from championship history and regulations "
        "to real race data and lap times."
    )

    # --- Sidebar: example questions ---
    with st.sidebar:
        st.header("💡 Example Questions")
        st.caption("Click any question to load it instantly:")
        st.divider()
        for question in EXAMPLE_QUESTIONS:
            if st.button(question, key=f"example_{hash(question)}", use_container_width=True):
                st.session_state["current_question"] = question

    # --- API key gate ---
    openai_client = get_openai_client()
    if openai_client is None:
        st.warning(
            "⚠️ **OPENAI_API_KEY** is not set. "
            "Please provide it to enable AI-powered answers."
        )
        with st.expander("🔧 Setup instructions"):
            st.markdown("**Option 1 – environment variable:**")
            st.code("export OPENAI_API_KEY='sk-...'", language="bash")
            st.markdown("**Option 2 – `.env` file in the project root:**")
            st.code("OPENAI_API_KEY=sk-...", language="bash")
        return

    # --- Question input ---
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_question = st.text_input(
            "Ask a question about Formula 1:",
            value=st.session_state.get("current_question", ""),
            placeholder="e.g., Who has the most Formula 1 championships?",
            key="question_input",
            label_visibility="collapsed",
        )
    with col_btn:
        ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

    if ask_button and not user_question:
        st.warning("Please enter or select a question first!")
        return

    if ask_button and user_question:
        st.session_state["current_question"] = user_question
        st.divider()

        with st.spinner("🧠 Analyzing your question…"):
            try:
                category = classify_question(openai_client, user_question)
            except Exception as exc:
                st.error(f"Could not classify question: {exc}")
                return

        if category == "historical":
            st.subheader("📚 F1 History")
            with st.spinner("Looking up F1 history…"):
                try:
                    answer = answer_historical_question(openai_client, user_question)
                    st.markdown(answer)
                except Exception as exc:
                    st.error(f"Error fetching answer: {exc}")

        elif category == "regulations":
            st.subheader("📋 F1 Regulations")
            with st.spinner("Checking F1 regulations…"):
                try:
                    answer = answer_regulations_question(openai_client, user_question)
                    st.markdown(answer)
                except Exception as exc:
                    st.error(f"Error fetching answer: {exc}")

        elif category == "race_data":
            st.subheader("📊 Race Data")
            try:
                handle_race_data_question(openai_client, user_question)
            except Exception as exc:
                st.error(f"Could not fetch race data: {exc}")
                st.info(
                    "💡 Tip: Try asking about a specific race, "
                    "e.g. *'Show me the 2023 Monaco GP results'*"
                )

    # --- Footer ---
    st.divider()
    st.caption(
        "Built with ❤️ using "
        "[Streamlit](https://streamlit.io), "
        "[FastF1](https://theoehrly.github.io/Fast-F1/), "
        "and [OpenAI](https://openai.com). "
        "Race data provided by FastF1 & Ergast API."
    )


if __name__ == "__main__":
    main()
