# 🏎️ Apex GPT: Your AI Race Engineer

[https://apex-gpt.streamlit.app/](https://streamlit.io)

**Apex GPT** transforms raw Formula 1 telemetry and historical data into actionable insights through natural language. Built for the **Atlantis University AI Talk**, it demonstrates how GitHub Copilot can take an app from "Junior Draft" to "Pro-Grade" in record time.

> [\!TIP]
> **The Vision:** Stop digging through PDFs and CSVs. Just ask: *"Compare Max and Lewis’s high-speed cornering at Copse during the 2024 British GP."*

-----

## 📽️ The Demo

*Real-time telemetry analysis and historical lookups powered by GPT-4o-mini.*

-----

## ⚡ Core Capabilities

  * **🎙️ Natural Language Telemetry:** Query lap times, gear shifts, and throttle data using [FastF1](https://theoehrly.github.io/Fast-F1/).
  * **📚 The F1 Encyclopedia:** Instant answers on sporting regulations, championship history, and technical "gray areas."
  * **📊 Dynamic Visualization:** Automated [Plotly](https://plotly.com/python/) charts that render based on the context of your question.
  * **⏱️ Live Standings:** Real-time access to the current season's driver and constructor battles.

-----


## Features

- 💬 **Ask anything** about Formula 1 in plain English
- 📚 **Historical knowledge** — championships, records, drivers, teams
- 📋 **Regulation answers** — DRS, ERS, budget cap, sporting code
- 📊 **Live race data** — lap times, race results, season standings via [FastF1](https://theoehrly.github.io/Fast-F1/)
- 📈 **Interactive visualisations** — Plotly charts that update with your question
- 💡 **Example questions** — one-click example prompts in the sidebar

---

## 🛠️ Tech Stack

| Layer | Technology | Why? |
| :--- | :--- | :--- |
| **Frontend** | [Streamlit](https://streamlit.io) | Zero-boilerplate UI for rapid AI prototyping. |
| **Brain** | [OpenAI GPT-4o-mini](https://openai.com) | Low latency, high reasoning for data extraction. |
| **Engine** | [FastF1](https://theoehrly.github.io/Fast-F1/) | The gold standard for F1 telemetry and timing data. |
| **Tooling** | [Poetry](https://python-poetry.org/) | Deterministic dependency management. |

-----

## 🚀 Quick Start

### 1\. Clone & Install

Ensure you have Python 3.11+ and [Poetry](https://python-poetry.org/docs/#installation) installed.

```bash
git clone https://github.com/your-username/apex-gpt.git
cd apex-gpt
poetry install
```

### 2\. Configure Environment

```bash
cp .env.example .env
# Open .env and add your OPENAI_API_KEY
```

If you leave `OPENAI_API_KEY` unset in a public deployment, the app will prompt each visitor to enter their own key in the UI.

### 3\. Ignite

```bash
poetry run streamlit run app.py
```

-----

## 📈 The Copilot Journey (Roadmap)

This repo is the output of my talk at the Atlantis University about **AI in Real Workflows**. Where the goal was to show students with a fun example how we leverege **Coding Agents** in production level settings.

This repo is a living case study in **AI-Accelerated Development**. We are refactoring this app in stages to show the power of **GitHub Copilot**:

| Milestone | Status | Key Focus |
| :--- | :--- | :--- |
| **v1.0: The Junior** | ✅ | Functional "Script-style" code. |
| **v2.0: The Engineer** | 🏗️ | Refactoring to OOP and Singleton patterns. |
| **v3.0: The Pro** | 📋 | Unit testing with `pytest` & Mocking APIs. |
| **v4.0: The Master** | 🛡️ | Strict Type Checking (Mypy) and Linting (Ruff). |

-----

## 📂 Data & Caching

To keep things fast (and avoid hammering the F1 servers), **Apex GPT** uses a local `cache/` directory for session data. The first time you ask about a race, it downloads the data; every time after, it's instant.

-----

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](https://www.google.com/search?q=LICENSE) for details.

-----

**Built with 🏎️ by [Your Name/Handle]**
*Join the conversation at Atlantis University.*