# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a single-file Streamlit application (`app.py`) that visualizes a monthly spending burndown chart. It compares a planned budget path against actual spending, derived from historical transaction data and user-configured fixed costs.

## Running the App

Install dependencies first (no requirements.txt exists yet — install manually):

```bash
pip install streamlit pandas plotly
```

Run the app:

```bash
streamlit run app.py
```

There are no tests, linting configs, or build steps currently defined.

## Architecture

The entire application lives in `app.py` and follows a top-to-bottom Streamlit execution model — the file is re-executed on every user interaction.

**Data flow:**

1. **Session state** (`st.session_state.history`) holds mock historical transactions as a DataFrame. In a production version this would come from a CSV upload or API.
2. **Sidebar inputs** collect `payday_val`, `safety_net`, and a `fixed_data` DataFrame of recurring fixed costs (name, amount, day-of-month).
3. **`calculate_velocity(df)`** computes per-category daily spending rate from historical data. The sum becomes `daily_planned_burn`.
4. **Planned burndown** iterates over each day of the current month, deducting fixed costs on their scheduled day and `daily_planned_burn` daily.
5. **Actual burndown** does the same but multiplies variable burn by 1.1 (currently a hardcoded simulation — a real implementation would use actual transaction data).
6. **Plotly figure** renders both lines plus an orange safety-net threshold line.
7. **Metrics row** shows daily variable budget, over/under budget status, and per-category burn rates.

## Key Conventions

- All state that must persist across reruns must go into `st.session_state`.
- Fixed costs use day-of-month matching (`fixed_data[fixed_data['Day'] == d]`) — entries with no matching day are simply not deducted.
- The actual spending path is only computed up to `today.day`, while planned covers the full month.
- `calculate_velocity` returns a Series (per-category), not a scalar — callers use `.sum()` to get total daily burn.
