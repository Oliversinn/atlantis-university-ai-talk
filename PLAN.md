# Formula 1 AI Assistant — Improvement Plan

This document tracks the planned pull requests for iteratively improving the project,
following software engineering best practices and showcasing how GitHub Copilot can
accelerate each step.

---

## PR 1 — First Draft (✅ current)

**Goal:** Get a working app on screen as quickly as possible, written in a
_junior developer_ style.

**What was done:**
- Created a single `app.py` with all logic living in top-level functions.
- Set up Poetry for dependency management (`pyproject.toml`, `python >= 3.11`).
- Integrated FastF1 for real race data (lap times, race results).
- Integrated Ergast API for season standings.
- Integrated OpenAI GPT-4o-mini for question classification and text answers.
- Added Plotly visualisations (lap-time line charts, results bar charts, standings bar charts).
- Added example clickable questions in the sidebar.

**Known limitations in this draft:**
- All logic in one file — hard to test or reuse.
- No unit tests.
- No type annotations.
- No linting configuration.
- Visualisation and data-fetching concerns are mixed into the same functions.

---

## PR 2 — Refactor: Functions → Classes

**Goal:** Improve code structure and separation of concerns by introducing classes.

**Changes planned:**
- Create `src/f1_ai/data/fetcher.py` — `F1DataFetcher` class  
  Wraps all FastF1 and Ergast API calls.
- Create `src/f1_ai/ai/handler.py` — `QuestionHandler` class  
  Wraps OpenAI calls for classification and text answers.
- Create `src/f1_ai/viz/charts.py` — `ChartBuilder` class  
  Contains all Plotly/Matplotlib visualisation methods.
- Update `app.py` to instantiate and use the new classes.
- Move configuration constants to `src/f1_ai/config.py`.
- Move the `src/` package under a proper `__init__.py` hierarchy.

**Benefits:**
- Easier to unit test each class in isolation.
- Clear single-responsibility separation.
- Copilot can suggest method completions more accurately when code is structured.

---

## PR 3 — Unit Tests with pytest

**Goal:** Add a comprehensive test suite to catch regressions.

**Changes planned:**
- Add `pytest` and `pytest-cov` to the `[project.optional-dependencies]` `dev` group.
- Create `tests/` directory with:
  - `tests/test_fetcher.py` — tests for `F1DataFetcher`  
    (mock FastF1 and Ergast API responses with `unittest.mock`).
  - `tests/test_handler.py` — tests for `QuestionHandler`  
    (mock OpenAI calls).
  - `tests/test_charts.py` — tests for `ChartBuilder`  
    (assert correct Plotly figure types and data structure).
  - `tests/conftest.py` — shared fixtures (sample DataFrames, mocked sessions).
- Configure test coverage reporting in `pyproject.toml`.
- Add a `Makefile` target: `make test` → `poetry run pytest --cov`.

**Minimum coverage target:** 80 % of business-logic code.

**Benefits:**
- Automated regression guard for future changes.
- Great demonstration of Copilot's test-generation capability.

---

## PR 4 — Linting and Type Checking (ruff + mypy)

**Goal:** Enforce consistent code style and type safety across the codebase.

**Changes planned:**
- **ruff** (linter + formatter):
  - Add `ruff` configuration in `pyproject.toml` under `[tool.ruff]`.
  - Enable rule sets: `E`, `W`, `F`, `I` (isort), `N` (pep8-naming), `UP` (pyupgrade).
  - Add a `Makefile` target: `make lint` → `poetry run ruff check . && poetry run ruff format --check .`.
- **mypy** (static type checker):
  - Add type annotations to all functions and class methods introduced in PR 2.
  - Configure mypy in `pyproject.toml` under `[tool.mypy]` (`strict = true`).
  - Add a `Makefile` target: `make typecheck` → `poetry run mypy src/`.
- **CI workflow** (optional bonus):
  - Add `.github/workflows/ci.yml` that runs lint + typecheck + tests on every push.

**Benefits:**
- Prevents common bugs caught at "compile time".
- Keeps code style consistent as the team grows.
- Showcases Copilot's ability to add type annotations intelligently.

---

## Summary Table

| PR | Title | Status |
|----|-------|--------|
| 1  | First draft app with Poetry | ✅ Done |
| 2  | Refactor: functions → classes | ⏳ Planned |
| 3  | Unit tests with pytest | ⏳ Planned |
| 4  | Linting with ruff + mypy | ⏳ Planned |
