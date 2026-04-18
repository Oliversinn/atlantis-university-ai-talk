"""Tests for the Streamlit app helpers."""

from unittest.mock import MagicMock

import app


class TestResolveOpenAiApiKey:
    def test_prefers_environment_key(self) -> None:
        assert app.resolve_openai_api_key("env-key", "session-key") == "env-key"

    def test_uses_session_key_when_environment_is_missing(self) -> None:
        assert app.resolve_openai_api_key(None, "session-key") == "session-key"

    def test_returns_none_when_no_key_is_available(self) -> None:
        assert app.resolve_openai_api_key(None, None) is None


class TestGetOpenAiClient:
    def test_returns_none_without_a_key(self) -> None:
        assert app.get_openai_client(None) is None

    def test_builds_client_with_a_key(self, monkeypatch) -> None:
        mock_client = MagicMock(name="OpenAIClient")
        openai_ctor = MagicMock(return_value=mock_client)
        monkeypatch.setattr(app, "OpenAI", openai_ctor)

        result = app.get_openai_client("sk-test")

        assert result is mock_client
        openai_ctor.assert_called_once_with(api_key="sk-test")
