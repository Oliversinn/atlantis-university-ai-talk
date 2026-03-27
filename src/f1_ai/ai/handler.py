"""QuestionHandler — wraps OpenAI calls for classification and text answers."""

import json

from openai import OpenAI

from src.f1_ai.config import CURRENT_YEAR, OPENAI_MODEL


class QuestionHandler:
    """Handles question classification and AI-generated text answers via OpenAI."""

    def __init__(self, client: OpenAI) -> None:
        self.client = client

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
        category = response.choices[0].message.content.strip().lower()
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
        return response.choices[0].message.content

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
        return response.choices[0].message.content

    def extract_race_params(self, question: str) -> dict:
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
        params = json.loads(response.choices[0].message.content)
        # Provide sensible defaults
        params.setdefault("year", CURRENT_YEAR - 1)
        params.setdefault("event", "Monaco")
        params.setdefault("session_type", "R")
        return params
