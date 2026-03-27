# 🏎️ Formula 1 AI Assistant

An interactive web app that lets you ask natural-language questions about Formula 1 —
from championship history and technical regulations to real race data and visualisations.

Built as part of an **Atlantis University AI Talk** to showcase how
[GitHub Copilot](https://github.com/features/copilot) can accelerate every stage of
software development.

---

## Features

- 💬 **Ask anything** about Formula 1 in plain English
- 📚 **Historical knowledge** — championships, records, drivers, teams
- 📋 **Regulation answers** — DRS, ERS, budget cap, sporting code
- 📊 **Live race data** — lap times, race results, season standings via [FastF1](https://theoehrly.github.io/Fast-F1/)
- 📈 **Interactive visualisations** — Plotly charts that update with your question
- 💡 **Example questions** — one-click example prompts in the sidebar

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | [Streamlit](https://streamlit.io) |
| AI / NLP | [OpenAI GPT-4o-mini](https://openai.com) |
| Race Data | [FastF1](https://theoehrly.github.io/Fast-F1/) + [Ergast API](https://ergast.com/mrd/) |
| Visualisations | [Plotly](https://plotly.com/python/) |
| Dependency management | [Poetry](https://python-poetry.org/) |
| Python | >= 3.11 |

---

## Getting Started

### 1. Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure your API key

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

### 4. Run the app

```bash
poetry run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Project Roadmap

See [PLAN.md](PLAN.md) for the full multi-PR improvement plan:

| PR | Title |
|----|-------|
| **1** (current) | First draft — junior developer style |
| 2 | Refactor: top-level functions → classes |
| 3 | Unit tests with pytest |
| 4 | Linting + type checking with ruff & mypy |

---

## FastF1 Cache

FastF1 caches session data locally in a `cache/` directory (auto-created at startup).
This is excluded from git via `.gitignore` — the first request for a session will
download it from the F1 servers; subsequent requests are served from cache.

---

## License

[MIT](LICENSE)
