# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Personal financial portfolio dashboard for a South African user. Tracks investment accounts, net worth history (Jun 2020 → present), monthly expenses, and models retirement scenarios. Key feature: import any bank/investment CSV and present it in a clean, consumable UI.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

No build step, no test suite, no linting config currently defined.

## Architecture

The entire application is a single file (`app.py`) divided into five Streamlit tabs. Streamlit re-executes the file top-to-bottom on every user interaction, so all mutable state lives in `st.session_state`.

**Execution order within `app.py`:**
1. **Seed data constants** — `CURRENT_ACCOUNTS`, `HISTORY_ROWS`, `DEFAULT_EXPENSES` define the starting dataset (actual figures from the owner's statements).
2. **Helper functions** — `zar()` (ZAR formatting), `calc_lump_sum_tax()` (SARS lump sum table), `home_loan_repayment()` (amortisation formula).
3. **Session state initialisation** — run once per browser session; converts seed data into editable DataFrames stored in `st.session_state`.
4. **Five tabs** rendered in order: Dashboard → Performance History → Import CSV → Expenses → Retirement Planner.

**State keys and their types:**

| Key | Type | Description |
|---|---|---|
| `accounts` | DataFrame | Current balances: Account, Balance, Type |
| `history` | DataFrame | Monthly net worth rows: Date, Closing Balance, Increase/Decrease, Less Contribution, Growth % |
| `transactions` | DataFrame | CSV-imported rows: Date, Description, Amount, Category |
| `expenses` | DataFrame | Fixed monthly costs: Category, Monthly |

**Data relationships:**
- `history` rows reflect the *combined* portfolio (all accounts summed). The `Closing Balance` of the last row should equal `accounts["Balance"].sum()` — these are kept in sync by editing them independently.
- `Less Contribution` = `Increase/Decrease` minus the monthly contribution (R28,761.90). This isolates pure investment return from new money added.
- The Retirement Planner reads `expenses` to calculate discretionary spend; debt repayments (Home Loan, RCP, ABSA CC) are computed dynamically based on user inputs and excluded from the expense editor total to avoid double-counting.

## Key Conventions

- All monetary amounts are South African Rand (ZAR). Use `zar(value)` for display — it handles negative values with a leading minus before `R`.
- Dates in the history table are end-of-month. The CSV importer passes `dayfirst=True` to `pd.to_datetime` to handle South African DD/MM/YYYY formats.
- CSV amounts are cleaned with `str.replace(r"[R,\s]", "", regex=True)` before numeric conversion to handle formatted bank exports.
- The SARS lump sum tax function takes `(withdrawal, previous_withdrawals)` — it computes marginal tax by differencing cumulative tax, not by taxing the withdrawal amount in isolation.
- Home loan repayment uses a standard amortisation formula at 8.88% p.a. over 180 months (15 years). The outstanding balance in seed data is R1,230,588.96.
- The Retirement Planner tab never mutates `st.session_state` — all output is computed inline from widget inputs.

## Accounts in Seed Data

| Account | Type | Balance (31-Mar-26) |
|---|---|---|
| Sanlam Provident | Retirement | R3,727,008.00 |
| 10X LA | Retirement | R2,721,626.20 |
| RSA Retail Savings | Savings | R19,000.00 |
| EasyEquities | Equity | R16,645.68 |
