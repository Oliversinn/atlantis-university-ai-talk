"""QuestionHandler — wraps OpenAI calls for classification and text answers."""

import json
import re
from typing import Any, TypedDict

from openai import OpenAI

from src.f1_ai.config import CURRENT_YEAR, OPENAI_MODEL


class RaceParams(TypedDict):
    """Structured race parameters extracted from a user question."""

    year: int
    event: str
    session_type: str


class QuestionHandler:
    """Handles question classification and AI-generated text answers via OpenAI."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client

    @staticmethod
    def _extract_text_content(response: Any) -> str:
        """Safely extract text content from an OpenAI completion response."""
        content = response.choices[0].message.content
        if isinstance(content, str):
            return content
        return ""

    @staticmethod
    def _extract_year_from_question(question: str) -> int | None:
        """Return an explicitly mentioned year (e.g. 2023) if present."""
        match = re.search(r"\b(19\d{2}|20\d{2})\b", question)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _question_requests_latest_event(question: str) -> bool:
        """Return True when the question asks for the latest/most recent race."""
        question_lower = question.lower()
        keywords = ("latest", "most recent", "last race", "newest")
        return any(keyword in question_lower for keyword in keywords)

    @staticmethod
    def _infer_session_type_from_question(question: str) -> str | None:
        """Infer a FastF1 session code from common natural language terms."""
        question_lower = question.lower()
        if "qualifying" in question_lower or re.search(r"\bq\b", question_lower):
            return "Q"
        if "fp1" in question_lower or "practice 1" in question_lower or "free practice 1" in question_lower:
            return "FP1"
        if "fp2" in question_lower or "practice 2" in question_lower or "free practice 2" in question_lower:
            return "FP2"
        if "fp3" in question_lower or "practice 3" in question_lower or "free practice 3" in question_lower:
            return "FP3"
        if "race" in question_lower or "results" in question_lower or "lap" in question_lower:
            return "R"
        return None

    def classify_question(self, question: str) -> str:
        """Classify a question into: historical, regulations, or race_data.

        Returns one of the three string labels. Falls back to 'historical'
        if the model returns an unexpected value.
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
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
        category = self._extract_text_content(response).strip().lower()
        if category not in ("historical", "regulations", "race_data"):
            return "historical"
        return category

    def answer_historical_question(self, question: str) -> str:
        """Use OpenAI to answer a historical F1 question."""
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
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
        return self._extract_text_content(response)

    def answer_regulations_question(self, question: str) -> str:
        """Use OpenAI to answer an F1 regulations question."""
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
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
        return self._extract_text_content(response)

    def extract_race_params(self, question: str) -> RaceParams:
        """Extract race parameters (year, event, session_type) from a natural-language question.

        Returns a dict with keys:
            year (int), event (str), session_type (str)
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
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
        raw_params = json.loads(self._extract_text_content(response))
        if not isinstance(raw_params, dict):
            raw_params = {}

        explicit_year = self._extract_year_from_question(question)
        latest_requested = self._question_requests_latest_event(question)
        inferred_session_type = self._infer_session_type_from_question(question)

        year = raw_params.get("year", CURRENT_YEAR - 1)
        if explicit_year is not None:
            year = explicit_year
        elif latest_requested and "year" not in raw_params:
            year = CURRENT_YEAR

        event = raw_params.get("event", "Monaco")
        if latest_requested:
            event = "latest"

        session_type = raw_params.get("session_type", "R")
        if inferred_session_type is not None:
            session_type = inferred_session_type

        return {
            "year": int(year),
            "event": str(event),
            "session_type": str(session_type).upper(),
        }
