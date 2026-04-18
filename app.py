"""Formula 1 AI Assistant

A Streamlit app that lets users ask natural language questions about Formula 1.
Supports historical questions, regulation queries, and live race data via FastF1.
"""

import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from src.f1_ai.ai.handler import QuestionHandler
from src.f1_ai.config import CURRENT_YEAR, EXAMPLE_QUESTIONS
from src.f1_ai.data.fetcher import F1DataFetcher
from src.f1_ai.viz.charts import ChartBuilder

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()


def resolve_openai_api_key(env_api_key: str | None, session_api_key: str | None) -> str | None:
    """Return the first usable OpenAI API key from the environment or session state."""
    if env_api_key and env_api_key.strip():
        return env_api_key.strip()
    if session_api_key and session_api_key.strip():
        return session_api_key.strip()
    return None


def get_openai_client(api_key: str | None) -> OpenAI | None:
    """Create and return an OpenAI client when a usable API key is available."""
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def render_openai_key_prompt() -> None:
    """Show the UI used when the deployment does not provide a shared API key."""
    st.warning(
        "⚠️ No OpenAI API key is configured for this deployment. Enter your own key to enable AI-powered answers."
    )

    st.subheader("🔑 Bring your own key")
    st.markdown(
        "Get a key from the [OpenAI API keys page](https://platform.openai.com/api-keys) "
        "or follow the [OpenAI API quickstart](https://platform.openai.com/docs/quickstart)."
    )
    st.text_input(
        "OpenAI API key",
        type="password",
        key="openai_api_key",
        placeholder="sk-...",
        help="Stored only in this browser session.",
    )
    st.info("Once you enter a key and refresh the page, the app will unlock for the current session.")


# ---------------------------------------------------------------------------
# Race-data question handler (uses all three classes)
# ---------------------------------------------------------------------------


def handle_race_data_question(
    handler: QuestionHandler,
    fetcher: F1DataFetcher,
    charts: ChartBuilder,
    question: str,
) -> None:
    """Route a race_data question to the right data fetch and visualisation."""
    params = handler.extract_race_params(question)
    year = int(params.get("year", CURRENT_YEAR - 1))
    event = params.get("event", "Monaco")
    session_type = params.get("session_type", "R")

    st.info(f"📊 Fetching data for the **{year} {event} Grand Prix** (session: {session_type})…")

    question_lower = question.lower()

    # --- lap times / sector analysis ---
    if any(w in question_lower for w in ("lap time", "fastest lap", "sector", "pace")):
        laps = fetcher.get_lap_times(year, event, session_type)
        fig = charts.plot_lap_times(laps, f"Lap Times – {year} {event} Grand Prix")
        st.plotly_chart(fig, use_container_width=True)

        fastest = laps.groupby("Driver")["LapTimeSeconds"].min().sort_values().head(10).reset_index()
        fastest.columns = ["Driver", "Fastest Lap (s)"]
        fastest["Fastest Lap"] = fastest["Fastest Lap (s)"].apply(lambda x: f"{int(x // 60)}:{x % 60:06.3f}")
        st.dataframe(fastest[["Driver", "Fastest Lap"]], use_container_width=True)

    # --- season standings ---
    elif any(w in question_lower for w in ("standing", "championship", "season points")):
        standings = fetcher.get_season_standings(year)
        if standings.empty:
            st.warning(f"No standings data found for {year}.")
        else:
            fig = charts.plot_season_standings(standings, year)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(standings, use_container_width=True)

    # --- race results (default for race_data) ---
    else:
        results = fetcher.get_race_results(year, event)
        fig = charts.plot_race_results(results, f"Race Results – {year} {event} Grand Prix")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(results, use_container_width=True)


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="F1 AI Assistant 🏎️",
        page_icon="🏎️",
        layout="wide",
    )

    # --- Header ---
    st.title("🏎️ Formula 1 AI Assistant")
    st.markdown(
        "Ask me anything about Formula 1 — from championship history and regulations to real race data and lap times."
    )

    # --- Sidebar: example questions ---
    with st.sidebar:
        st.header("💡 Example Questions")
        st.caption("Click any question to load it instantly:")
        st.divider()
        for question in EXAMPLE_QUESTIONS:
            if st.button(question, key=f"example_{hash(question)}", use_container_width=True):
                st.session_state["question_input"] = question
                st.session_state["auto_submit"] = True

    # --- API key gate ---
    env_api_key = os.getenv("OPENAI_API_KEY")
    session_api_key = st.session_state.get("openai_api_key")
    if not isinstance(session_api_key, str):
        session_api_key = None

    api_key = resolve_openai_api_key(env_api_key, session_api_key)
    if api_key is None:
        render_openai_key_prompt()
        return

    openai_client = get_openai_client(api_key)
    if openai_client is None:
        st.error("Could not initialize the OpenAI client.")
        return

    # Instantiate the helpers
    handler = QuestionHandler(openai_client)
    fetcher = F1DataFetcher()
    charts = ChartBuilder()

    # --- Question input ---
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_question = st.text_input(
            "Ask a question about Formula 1:",
            placeholder="e.g., Who has the most Formula 1 championships?",
            key="question_input",
            label_visibility="collapsed",
        )
    with col_btn:
        ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

    if ask_button and not user_question:
        st.warning("Please enter or select a question first!")
        return

    auto_submit = st.session_state.pop("auto_submit", False)
    if (ask_button or auto_submit) and user_question:
        st.divider()

        with st.spinner("🧠 Analyzing your question…"):
            try:
                category = handler.classify_question(user_question)
            except Exception as exc:
                st.error(f"Could not classify question: {exc}")
                return

        if category == "historical":
            st.subheader("📚 F1 History")
            with st.spinner("Looking up F1 history…"):
                try:
                    answer = handler.answer_historical_question(user_question)
                    st.markdown(answer)
                except Exception as exc:
                    st.error(f"Error fetching answer: {exc}")

        elif category == "regulations":
            st.subheader("📋 F1 Regulations")
            with st.spinner("Checking F1 regulations…"):
                try:
                    answer = handler.answer_regulations_question(user_question)
                    st.markdown(answer)
                except Exception as exc:
                    st.error(f"Error fetching answer: {exc}")

        elif category == "race_data":
            st.subheader("📊 Race Data")
            try:
                handle_race_data_question(handler, fetcher, charts, user_question)
            except Exception as exc:
                st.error(f"Could not fetch race data: {exc}")
                st.info("💡 Tip: Try asking about a specific race, e.g. *'Show me the 2023 Monaco GP results'*")

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
