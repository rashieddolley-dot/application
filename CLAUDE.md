# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A single-file Streamlit app (`app.py`) that plots a monthly spending "burndown" chart: planned vs. actual balance from payday to month end. There is no README, requirements file, tests, or lint config yet.

## Commands

- Install deps (none are pinned): `pip install streamlit pandas plotly`
- Run: `streamlit run app.py`

## Architecture (`app.py`)

Streamlit re-executes the whole script on every interaction, so the file reads top to bottom as a pipeline:

1. **Inputs** (`app.py:21-32`): sidebar number inputs (payday balance, emergency buffer) and an editable `fixed_data` table (Name / Amount / Day-of-month).
2. **History** (`app.py:12-18`): mock spending DataFrame (Date, Category, Amount) kept in `st.session_state.history`. This is placeholder data; the comment says it should come from a CSV/API.
3. **Velocity** (`calculate_velocity`, `app.py:35`): total spend per category divided by the number of days in the history span. It returns a per-category Series, and `daily_planned_burn` is its sum. An empty history returns a float (50.0) instead of a Series, so the later `.sum()` / `.map()` calls would break on it.
4. **Planned path** (`app.py:53-62`): for each day of the current month, subtract the fixed costs due that day (matched on `Day`) plus `daily_planned_burn`, floored at 0.
5. **Actual path** (`app.py:64-72`): currently **simulated** as planned burn × 1.1 up to today. It is meant to be replaced by real current-month transactions.
6. **Rendering** (`app.py:75-111`): a Plotly figure (planned dotted line, actual line, safety-buffer hline) followed by metrics. "Under/Over Budget" compares the last actual point to the planned value for today.

Note: the planned path is clamped at 0 but the actual path is not, so the two can diverge once the balance goes negative.
