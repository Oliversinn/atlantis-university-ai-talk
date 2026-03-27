"""Tests for QuestionHandler — mocks all OpenAI calls."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.f1_ai.ai.handler import QuestionHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_openai_client(content: str) -> MagicMock:
    """Return an OpenAI client mock whose chat.completions.create returns *content*."""
    choice = MagicMock()
    choice.message.content = content

    completion = MagicMock()
    completion.choices = [choice]

    client = MagicMock()
    client.chat.completions.create.return_value = completion
    return client


# ---------------------------------------------------------------------------
# classify_question
# ---------------------------------------------------------------------------

class TestClassifyQuestion:
    @pytest.mark.parametrize(
        "model_response,expected",
        [
            ("historical", "historical"),
            ("regulations", "regulations"),
            ("race_data", "race_data"),
            ("HISTORICAL", "historical"),  # case-insensitive normalization
            ("  race_data  ", "race_data"),  # strip whitespace
        ],
    )
    def test_known_categories(self, model_response: str, expected: str) -> None:
        client = _make_openai_client(model_response)
        handler = QuestionHandler(client)
        assert handler.classify_question("some question") == expected

    def test_unknown_category_falls_back_to_historical(self) -> None:
        client = _make_openai_client("something_random")
        handler = QuestionHandler(client)
        assert handler.classify_question("?") == "historical"

    def test_openai_called_once(self) -> None:
        client = _make_openai_client("historical")
        handler = QuestionHandler(client)
        handler.classify_question("Who won in 1994?")
        client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# answer_historical_question
# ---------------------------------------------------------------------------

class TestAnswerHistoricalQuestion:
    def test_returns_model_content(self) -> None:
        expected = "Michael Schumacher won 7 championships."
        client = _make_openai_client(expected)
        handler = QuestionHandler(client)
        result = handler.answer_historical_question("Who won the most championships?")
        assert result == expected

    def test_openai_called_once(self) -> None:
        client = _make_openai_client("answer")
        handler = QuestionHandler(client)
        handler.answer_historical_question("question")
        client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# answer_regulations_question
# ---------------------------------------------------------------------------

class TestAnswerRegulationsQuestion:
    def test_returns_model_content(self) -> None:
        expected = "DRS reduces drag on straights."
        client = _make_openai_client(expected)
        handler = QuestionHandler(client)
        result = handler.answer_regulations_question("What is DRS?")
        assert result == expected

    def test_openai_called_once(self) -> None:
        client = _make_openai_client("answer")
        handler = QuestionHandler(client)
        handler.answer_regulations_question("question")
        client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# extract_race_params
# ---------------------------------------------------------------------------

class TestExtractRaceParams:
    def test_parses_full_json_response(self) -> None:
        payload = json.dumps({"year": 2023, "event": "Monaco", "session_type": "R"})
        client = _make_openai_client(payload)
        handler = QuestionHandler(client)
        params = handler.extract_race_params("Monaco 2023 race lap times")
        assert params["year"] == 2023
        assert params["event"] == "Monaco"
        assert params["session_type"] == "R"

    def test_applies_default_event_when_missing(self) -> None:
        payload = json.dumps({"year": 2023, "session_type": "Q"})
        client = _make_openai_client(payload)
        handler = QuestionHandler(client)
        params = handler.extract_race_params("qualifying 2023")
        assert params["event"] == "Monaco"

    def test_applies_default_session_type_when_missing(self) -> None:
        payload = json.dumps({"year": 2022, "event": "British"})
        client = _make_openai_client(payload)
        handler = QuestionHandler(client)
        params = handler.extract_race_params("British 2022")
        assert params["session_type"] == "R"

    def test_applies_default_year_when_missing(self) -> None:
        from src.f1_ai.config import CURRENT_YEAR

        payload = json.dumps({"event": "Italian"})
        client = _make_openai_client(payload)
        handler = QuestionHandler(client)
        params = handler.extract_race_params("Italian GP results")
        assert params["year"] == CURRENT_YEAR - 1

    def test_openai_called_once(self) -> None:
        payload = json.dumps({"year": 2023, "event": "Monaco", "session_type": "R"})
        client = _make_openai_client(payload)
        handler = QuestionHandler(client)
        handler.extract_race_params("something")
        client.chat.completions.create.assert_called_once()
