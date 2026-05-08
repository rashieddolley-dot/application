# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
streamlit run app.py
```

Dependencies (install via pip):
```bash
pip install streamlit pandas plotly
```

## Architecture

This is a single-file Streamlit app (`app.py`) — a personal finance dashboard called **Smart Burndown** that visualizes monthly spending as a burndown chart (planned vs. actual balance over time).

**Data flow:**

1. Mock historical transaction data is hardcoded at the top of `app.py` (December 2025 spending by category).
2. The sidebar collects user inputs: payday starting balance, emergency buffer goal, and fixed costs (with day-of-month for each).
3. Velocity is computed per spending category from the mock history, then combined with fixed costs to project a planned daily burn path.
4. An actual spending path is simulated by randomizing daily variable spend against the planned path.
5. A Plotly chart renders both paths (planned dotted gray, actual cyan) plus a safety buffer threshold line.
6. Summary metrics show suggested daily variable budget and per-category burn rates.

**State management:** Streamlit `session_state` holds the spending history and fixed costs editor data between rerenders.

All logic — config, data processing, and rendering — lives in `app.py`. There are no separate modules, tests, or build steps.
