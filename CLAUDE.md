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

## expense-tracker.html

A separate, fully offline single-file app (no Streamlit, no network; a CSP blocks all requests). Vanilla JS in one `<script>`, state persisted to `localStorage` (key `spendtruth.v1`) plus optional linked file / JSON backup. Open it directly in a browser; add `?today=YYYY-MM-DD` to fake the date when testing.

Flow: CSV import → `classify()` (user rules → learned merchant key → naive Bayes on user-confirmed txns → built-in keyword seeds) → `analyse()` builds pay-cycle (payday-to-payday) history, bills, planned vs actual vs forecast balance, and the "safe to spend" verdict → views render from that single analysis object (`getA()`; call `touch()` after any state change).

### PDF statement import (expense-tracker.html)

`readPdfFile()` uses a self-written PDF reader (parses objects, inflates streams with `DecompressionStream`, interprets text operators incl. form XObjects) – no libraries, WinAnsi/simple fonts only, no password-protected PDFs. It produces positioned text lines; `convertPages()` picks a conversion profile in `RULES` (`sb-cheque`, `sb-card`, `generic`), and each profile proves its result against the statement's own running/closing balance. To support another bank layout, add a `parseXxx(pages)` function plus a `RULES` entry (its `how` text is shown to the user). Never commit real statements or their extracted data.
