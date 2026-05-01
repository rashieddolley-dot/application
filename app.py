import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Portfolio Dashboard", layout="wide", page_icon="📈")

# ── Seed data ──────────────────────────────────────────────────────────────────

CURRENT_ACCOUNTS = [
    {"Account": "Sanlam Provident",  "Balance": 3_727_008.00, "Type": "Retirement"},
    {"Account": "10X LA",            "Balance": 2_721_626.20, "Type": "Retirement"},
    {"Account": "RSA Retail Savings","Balance":    19_000.00, "Type": "Savings"},
    {"Account": "EasyEquities",      "Balance":    16_645.68, "Type": "Equity"},
]

MONTHLY_CONTRIBUTION = 28_761.90

# (Date, Closing Balance, Increase/Decrease, Less Contribution, Growth %)
HISTORY_ROWS = [
    ("2020-06-30", 3_818_212.00,  3_818_212.00,         None,   None),
    ("2020-07-31", 3_835_841.00,     17_629.00,         None,   0.46),
    ("2020-08-31", 3_838_971.00,      3_130.00,         None,   0.08),
    ("2020-09-30", 3_883_736.00,     44_765.00,    16_003.10,   1.17),
    ("2020-10-31", 3_899_832.00,     16_096.00,   -12_665.90,   0.41),
    ("2020-11-30", 4_071_016.00,    171_184.00,   142_422.10,   4.39),
    ("2020-12-31", 4_039_865.00,    -31_151.00,   -59_912.90,  -0.77),
    ("2021-01-31", 3_534_516.00,   -505_349.00,  -534_110.90, -12.51),
    ("2021-02-28", 3_564_385.00,     29_869.00,     1_107.10,   0.85),
    ("2021-03-31", 3_724_528.00,    160_143.00,   131_381.10,   4.49),
    ("2021-04-30", 3_719_429.00,     -5_099.00,   -33_860.90,  -0.14),
    ("2021-05-31", 3_763_781.00,     44_352.00,    15_590.10,   1.19),
    ("2021-06-30", 3_793_027.00,     29_246.00,       484.10,   0.78),
    ("2021-07-31", 4_591_657.00,    798_630.00,   769_868.10,  21.06),
    ("2021-08-31", 4_667_735.00,     76_078.00,    47_316.10,   1.66),
    ("2021-09-30", 4_654_015.00,    -13_720.00,   -42_481.90,  -0.29),
    ("2021-10-31", 4_721_543.00,     67_528.00,    38_766.10,   1.45),
    ("2021-11-30", 4_759_449.00,     37_906.00,     9_144.10,   0.80),
    ("2021-12-31", 4_844_250.00,     84_801.00,    56_039.10,   1.78),
    ("2022-01-31", 4_690_421.00,   -153_829.00,  -182_590.90,  -3.18),
    ("2022-02-28", 4_706_567.00,     16_146.00,   -12_615.90,   0.34),
    ("2022-03-31", 4_754_115.00,     47_548.00,    18_786.10,   1.01),
    ("2022-04-30", 4_828_101.86,     73_986.86,    45_224.96,   1.56),
    ("2022-05-31", 4_703_247.75,   -124_854.11,  -153_616.01,  -2.59),
    ("2022-06-30", 4_526_497.10,   -176_750.65,  -205_512.55,  -3.76),
    ("2022-07-31", 4_661_481.83,    134_984.73,   106_222.83,   2.98),
    ("2022-08-31", 4_751_267.13,     89_785.30,    61_023.40,   1.93),
    ("2022-09-30", 4_611_805.73,   -139_461.40,  -168_223.30,  -2.94),
    ("2022-10-31", 4_781_786.72,    169_980.99,   141_219.09,   3.69),
    ("2022-11-30", 4_851_324.00,     69_537.28,    40_775.38,   1.45),
    ("2022-12-31", 4_827_938.00,    -23_386.00,   -52_147.90,  -0.48),
    ("2023-01-31", 5_080_186.00,    252_248.00,   223_486.10,   5.22),
    ("2023-02-28", 5_153_402.00,     73_216.00,    44_454.10,   1.44),
    ("2023-03-31", 5_099_549.00,    -53_853.00,   -82_614.90,  -1.04),
    ("2023-04-30", 5_224_460.00,    124_911.00,    96_149.10,   2.45),
    ("2023-05-31", 5_351_030.00,    126_570.00,    97_808.10,   2.42),
    ("2023-06-30", 5_313_083.00,    -37_947.00,   -66_708.90,  -0.71),
    ("2023-07-31", 5_278_969.00,    -34_114.00,   -62_875.90,  -0.64),
    ("2023-08-31", 5_301_455.00,     22_486.00,    -6_275.90,   0.43),
    ("2023-09-30", 5_078_117.00,   -223_338.00,  -252_099.90,  -4.21),
    ("2023-10-31", 4_959_762.00,   -118_355.00,  -147_116.90,  -2.33),
    ("2023-11-30", 4_738_647.00,   -221_115.00,  -249_876.90,  -4.46),
    ("2023-12-31", 4_904_371.00,    165_724.00,   136_962.10,   3.50),
    ("2024-01-31", 4_939_347.00,     34_976.00,     6_214.10,   0.71),
    ("2024-02-29", 5_029_770.00,     90_423.00,    61_661.10,   1.83),
    ("2024-03-31", 5_145_722.00,    115_952.00,    87_190.10,   2.31),
    ("2024-04-30", 5_126_171.00,    -19_551.00,   -48_312.90,  -0.38),
    ("2024-05-31", 5_248_599.00,    122_428.00,    93_666.10,   2.39),
    ("2024-06-30", 5_263_071.00,     14_472.00,   -14_289.90,   0.28),
    ("2024-07-31", 5_383_795.00,    120_724.00,    91_962.10,   2.29),
    ("2024-08-31", 5_406_059.00,     22_264.00,    -6_497.90,   0.41),
    ("2024-09-30", 5_422_435.00,     16_376.00,   -12_385.90,   0.30),
    ("2024-10-31", 5_514_101.00,     91_666.00,    62_904.10,   1.69),
    ("2024-11-30", 5_488_765.00,    -25_336.00,   -54_097.90,  -0.46),
    ("2024-12-31", 5_513_186.00,     24_421.00,    -4_340.90,   0.44),
    ("2025-01-31", 5_601_384.92,     88_198.92,    59_437.02,   1.60),
    ("2025-02-28", 5_634_034.34,     32_649.42,     3_887.52,   0.58),
    ("2025-03-31", 5_616_633.49,    -17_400.85,   -46_162.75,  -0.31),
    ("2025-04-30", 5_696_175.97,     79_542.47,    50_780.57,   1.42),
    ("2025-05-31", 5_789_561.72,     93_385.76,    64_623.86,   1.64),
    ("2025-06-30", 5_906_080.63,    116_518.90,    87_757.00,   2.01),
    ("2025-07-31", 6_082_213.81,    176_133.19,   147_371.29,   2.98),
    ("2025-08-31", 6_102_307.50,     20_093.69,    -8_668.21,   0.33),
    ("2025-09-30", 6_193_888.17,     91_580.67,    62_818.77,   1.50),
    ("2025-10-31", 6_343_737.50,    149_849.33,   121_087.43,   2.42),
    ("2025-11-30", 6_337_469.10,     -6_268.40,   -35_030.30,  -0.10),
    ("2025-12-31", 6_386_747.94,     49_278.85,    20_516.95,   0.78),
    ("2026-01-31", 6_486_427.21,     99_679.27,    70_917.37,   1.56),
    ("2026-02-28", 6_535_735.08,     49_307.87,    20_545.97,   0.76),
    ("2026-03-31", 6_484_279.88,    -51_455.20,   -80_217.10,  -0.79),
]

DEFAULT_EXPENSES = [
    {"Category": "Home Loan",               "Monthly": 11_959.19},
    {"Category": "Healthcare",              "Monthly":  8_500.00},
    {"Category": "Food",                    "Monthly": 10_000.00},
    {"Category": "RCP (Standard Bank)",     "Monthly":  8_075.00},
    {"Category": "Credit Card ABSA",        "Monthly":  6_799.59},
    {"Category": "Credit Card Standard Bank","Monthly": 5_000.00},
    {"Category": "Rates, Water & Sewage",   "Monthly":  3_159.00},
    {"Category": "Short Term Insurance",    "Monthly":  3_500.00},
    {"Category": "Cellphone",               "Monthly":  1_500.00},
    {"Category": "Transport & Fuel",        "Monthly":  1_500.00},
    {"Category": "Pet Food",                "Monthly":  1_000.00},
    {"Category": "Internet (Fibre)",        "Monthly":    929.00},
    {"Category": "Life Insurance",          "Monthly":    750.00},
    {"Category": "Armed Response",          "Monthly":    350.00},
    {"Category": "Bin2Bin",                 "Monthly":    165.00},
    {"Category": "Donation",               "Monthly":    100.00},
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def zar(v):
    sign = "-" if v < 0 else ""
    return f"{sign}R{abs(v):,.2f}"


def calc_lump_sum_tax(withdrawal, previous=0):
    """SARS retirement lump sum tax table."""
    brackets = [
        (550_000,      0.00, 550_000,      0),
        (770_000,      0.18, 550_000,      0),
        (1_155_000,    0.27, 770_000,  39_600),
        (float("inf"), 0.36, 1_155_000, 143_550),
    ]

    def tax_on(amount):
        for ceiling, rate, base, base_tax in brackets:
            if amount <= ceiling:
                return base_tax + rate * max(0, amount - base)
        return 0

    return max(0, tax_on(withdrawal + previous) - tax_on(previous))


def home_loan_repayment(balance, annual_rate=0.0888, periods=180):
    if balance <= 0:
        return 0.0
    r = annual_rate / 12
    return balance * r * (1 + r) ** periods / ((1 + r) ** periods - 1)


# ── Session state ──────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        HISTORY_ROWS,
        columns=["Date", "Closing Balance", "Increase/Decrease", "Less Contribution", "Growth %"],
    )
    st.session_state.history["Date"] = pd.to_datetime(st.session_state.history["Date"])

if "accounts" not in st.session_state:
    st.session_state.accounts = pd.DataFrame(CURRENT_ACCOUNTS)

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=["Date", "Description", "Amount", "Category"]
    )

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(DEFAULT_EXPENSES)

# ── Layout ─────────────────────────────────────────────────────────────────────

st.title("📈 Portfolio Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Dashboard", "Performance History", "Import CSV", "Expenses", "Retirement Planner"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    df_acc = st.session_state.accounts
    total = df_acc["Balance"].sum()

    hist = st.session_state.history
    prev_bal = hist.iloc[-2]["Closing Balance"] if len(hist) > 1 else total
    mom_change = total - prev_bal
    mom_pct = mom_change / prev_bal * 100 if prev_bal else 0
    latest_growth = hist.iloc[-1]["Growth %"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Portfolio",      zar(total))
    c2.metric("Month-on-Month",       zar(mom_change),         f"{mom_pct:+.2f}%")
    c3.metric("Latest Month Growth",  f"{latest_growth:+.2f}%" if pd.notna(latest_growth) else "—")
    c4.metric("Accounts",             len(df_acc))

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Accounts")
        display = df_acc.copy()
        display["Share"] = (df_acc["Balance"] / total * 100).map(lambda x: f"{x:.1f}%")
        display["Balance"] = df_acc["Balance"].map(zar)
        st.dataframe(display, use_container_width=True, hide_index=True)

        with st.expander("Update balances"):
            edited_acc = st.data_editor(st.session_state.accounts, use_container_width=True, hide_index=True)
            if st.button("Save balances"):
                st.session_state.accounts = edited_acc
                st.rerun()

    with col_r:
        st.subheader("Allocation")
        fig_pie = px.pie(
            df_acc, values="Balance", names="Account", hole=0.5,
            color_discrete_sequence=["#00ebc7", "#4169E1", "#FFD700", "#FF6B6B"],
        )
        fig_pie.update_layout(
            template="plotly_dark", height=300,
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", y=-0.15),
        )
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PERFORMANCE HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    hist = st.session_state.history.copy()

    bar_colors = hist["Increase/Decrease"].map(
        lambda v: "#00ebc7" if pd.notna(v) and v >= 0 else "#ff4d4d"
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Closing Balance"],
        name="Net Worth", line=dict(color="#00ebc7", width=3),
        fill="tozeroy", fillcolor="rgba(0,235,199,0.07)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Balance: R%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=hist["Date"], y=hist["Increase/Decrease"],
        name="Monthly Change", marker_color=bar_colors,
        yaxis="y2", opacity=0.55,
        hovertemplate="<b>%{x|%b %Y}</b><br>Change: R%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark", height=440,
        yaxis=dict(title="Balance (R)", tickformat=",.0f"),
        yaxis2=dict(title="Monthly Change (R)", overlaying="y", side="right", tickformat=",.0f"),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05),
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    growth_data = hist.dropna(subset=["Growth %"])
    fig_g = go.Figure(go.Bar(
        x=growth_data["Date"], y=growth_data["Growth %"],
        marker_color=growth_data["Growth %"].map(lambda v: "#00ebc7" if v >= 0 else "#ff4d4d"),
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig_g.update_layout(
        template="plotly_dark", height=200,
        yaxis=dict(title="Growth %"), margin=dict(t=5, b=5), showlegend=False,
    )
    st.plotly_chart(fig_g, use_container_width=True)

    with st.expander("View / edit history table"):
        editable = hist.copy()
        editable["Date"] = editable["Date"].dt.strftime("%Y-%m-%d")
        edited_hist = st.data_editor(editable, use_container_width=True, hide_index=True, num_rows="dynamic")
        if st.button("Save history"):
            edited_hist["Date"] = pd.to_datetime(edited_hist["Date"])
            st.session_state.history = edited_hist
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — IMPORT CSV
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Import CSV Statement")
    st.caption("Supports any bank or investment export. Map the date, description, and amount columns after upload.")

    uploaded = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded:
        try:
            raw = pd.read_csv(uploaded)
            st.write("**Preview (first 10 rows)**")
            st.dataframe(raw.head(10), use_container_width=True)

            cols = list(raw.columns)
            ca, cb, cc = st.columns(3)
            date_col   = ca.selectbox("Date column",        cols, key="imp_date")
            desc_col   = cb.selectbox("Description column", cols, key="imp_desc")
            amount_col = cc.selectbox("Amount column",      cols, key="imp_amt")

            if st.button("Import"):
                imported = raw[[date_col, desc_col, amount_col]].copy()
                imported.columns = ["Date", "Description", "Amount"]
                imported["Date"] = pd.to_datetime(imported["Date"], dayfirst=True, errors="coerce")
                imported["Amount"] = (
                    imported["Amount"]
                    .astype(str)
                    .str.replace(r"[R,\s]", "", regex=True)
                    .pipe(pd.to_numeric, errors="coerce")
                )
                imported["Category"] = "Uncategorised"
                imported = imported.dropna(subset=["Date", "Amount"])
                st.session_state.transactions = pd.concat(
                    [st.session_state.transactions, imported], ignore_index=True
                )
                st.success(f"Imported {len(imported)} transactions.")
        except Exception as exc:
            st.error(f"Could not parse file: {exc}")

    if not st.session_state.transactions.empty:
        st.divider()
        txn = st.session_state.transactions.copy()

        total_in  = txn.loc[txn["Amount"] > 0, "Amount"].sum()
        total_out = txn.loc[txn["Amount"] < 0, "Amount"].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total In",  zar(total_in))
        m2.metric("Total Out", zar(abs(total_out)))
        m3.metric("Net",       zar(total_in + total_out))

        date_col_str = txn["Date"].dt.strftime("%Y-%m-%d") if pd.api.types.is_datetime64_any_dtype(txn["Date"]) else txn["Date"]
        edited_txn = st.data_editor(
            txn.assign(Date=date_col_str),
            use_container_width=True, hide_index=True,
        )
        col_btn1, col_btn2, _ = st.columns([1, 1, 4])
        if col_btn1.button("Save edits"):
            edited_txn["Date"] = pd.to_datetime(edited_txn["Date"], errors="coerce")
            st.session_state.transactions = edited_txn
            st.rerun()
        if col_btn2.button("Clear all"):
            st.session_state.transactions = pd.DataFrame(
                columns=["Date", "Description", "Amount", "Category"]
            )
            st.rerun()

        cat_sum = txn.groupby("Category")["Amount"].sum().reset_index()
        fig_cat = px.bar(
            cat_sum.sort_values("Amount"), x="Amount", y="Category", orientation="h",
            color="Amount", color_continuous_scale=["#ff4d4d", "#555", "#00ebc7"],
            title="Net spend by category",
        )
        fig_cat.update_layout(template="plotly_dark", height=280, showlegend=False,
                              coloraxis_showscale=False, margin=dict(t=40))
        st.plotly_chart(fig_cat, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXPENSES
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Monthly Expense Budget")

    col_l, col_r = st.columns(2)

    with col_l:
        edited_exp = st.data_editor(
            st.session_state.expenses, use_container_width=True,
            hide_index=True, num_rows="dynamic",
        )
        if st.button("Save expenses"):
            st.session_state.expenses = edited_exp
            st.rerun()
        st.metric("Total Fixed Expenses", zar(edited_exp["Monthly"].sum()))

    with col_r:
        fig_exp = px.bar(
            edited_exp.sort_values("Monthly"),
            x="Monthly", y="Category", orientation="h",
            color="Monthly",
            color_continuous_scale=["#00ebc7", "#FFD700", "#ff4d4d"],
        )
        fig_exp.update_layout(
            template="plotly_dark", height=460,
            showlegend=False, coloraxis_showscale=False,
            margin=dict(t=10),
        )
        st.plotly_chart(fig_exp, use_container_width=True)

    st.divider()
    st.subheader("Daily Work Expense Calculator")
    st.caption("Estimates remaining daily budget based on your canteen and coffee choice.")

    ca, cb, cc = st.columns(3)
    work_budget    = ca.number_input("Monthly work budget (R)", value=1_313.0, min_value=0.0)
    total_days     = cb.number_input("Total work days in month", value=22, min_value=1)
    days_remaining = cc.number_input("Work days remaining",      value=11, min_value=0)

    days_elapsed = total_days - days_remaining
    budget_per_day = work_budget / total_days
    spent_baseline = days_elapsed * budget_per_day

    coffee = 32.0
    options = {"Urban Flav": 26, "Main Meal": 38, "Chef": 50}

    rows = []
    for name, price in options.items():
        daily_total = coffee + price
        projected_spend = spent_baseline + days_remaining * daily_total
        remaining = work_budget - projected_spend
        rows.append({
            "Canteen": name,
            "Lunch": f"R{price}",
            "Coffee": f"R{int(coffee)}",
            "Daily Total": f"R{daily_total:.0f}",
            "Budget Remaining": zar(remaining),
        })
    st.table(pd.DataFrame(rows))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RETIREMENT PLANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Retirement Scenario Planner")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Capital & Income**")
        sanlam_cap    = st.number_input("Sanlam Provident (R)",        value=3_727_008.00, step=1_000.0)
        tenx_cap      = st.number_input("10X LA (R)",                  value=2_720_311.89, step=1_000.0)
        rsa_monthly   = st.number_input("RSA Retail monthly income (R)",value=145.00,      step=10.0)
        sanlam_rate   = st.slider("Sanlam drawdown rate (%)", 2.0, 25.0, 17.0, 0.5) / 100
        tenx_rate     = st.slider("10X drawdown rate (%)",    2.0, 25.0, 17.0, 0.5) / 100

    with col2:
        st.markdown("**Cash Withdrawal**")
        prev_withdrawals = st.number_input("Previous withdrawals (R)", value=500_000.00, step=1_000.0)
        cash_withdrawal  = st.number_input("New withdrawal (R)",       value=50_000.00,  step=1_000.0)

        st.markdown("**Debt Settlement at Retirement**")
        settle_rcp   = st.checkbox("Settle Standard Bank RCP (R280,508.52)",  value=False)
        settle_absa  = st.checkbox("Settle ABSA Credit Card (R226,652.84)",   value=False)
        bond_payment = st.number_input("Once-off Home Loan payment (R)", value=50_000.00, step=1_000.0)

    # ── Calculations ──────────────────────────────────────────────────────────
    tax       = calc_lump_sum_tax(cash_withdrawal, prev_withdrawals)
    net_cash  = cash_withdrawal - tax

    rcp_settle_amt  = 280_508.52 if settle_rcp  else 0
    absa_settle_amt = 226_652.84 if settle_absa else 0
    sanlam_remaining = sanlam_cap - cash_withdrawal - rcp_settle_amt - absa_settle_amt

    sanlam_income = sanlam_remaining * sanlam_rate / 12
    tenx_income   = tenx_cap * tenx_rate / 12
    gross_income  = sanlam_income + tenx_income + rsa_monthly

    annual_gross = gross_income * 12
    if annual_gross <= 550_000:
        annual_tax = 0
    elif annual_gross <= 770_000:
        annual_tax = 0.18 * (annual_gross - 550_000)
    elif annual_gross <= 1_155_000:
        annual_tax = 39_600 + 0.27 * (annual_gross - 770_000)
    else:
        annual_tax = 143_550 + 0.36 * (annual_gross - 1_155_000)

    income_after_tax = gross_income - annual_tax / 12

    home_loan_bal     = max(0, 1_230_588.96 - bond_payment)
    home_loan_payment = home_loan_repayment(home_loan_bal)
    rcp_payment       = 0.0 if settle_rcp  else 8_075.00
    absa_payment      = 0.0 if settle_absa else 6_799.59

    exp_df = st.session_state.expenses
    variable_exp = exp_df[
        ~exp_df["Category"].isin(["Home Loan", "RCP (Standard Bank)", "Credit Card ABSA"])
    ]["Monthly"].sum()
    total_expenses  = home_loan_payment + rcp_payment + absa_payment + variable_exp
    discretionary   = income_after_tax - total_expenses

    # ── Results ───────────────────────────────────────────────────────────────
    st.divider()
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Lump Sum Tax",      zar(tax),             help="SARS retirement fund lump sum table")
    r2.metric("Net Cash in Hand",  zar(net_cash))
    r3.metric("Gross Monthly",     zar(gross_income))
    r4.metric("After-Tax Monthly", zar(income_after_tax))

    st.divider()
    left, right = st.columns(2)

    with left:
        st.markdown("**Income sources**")
        inc_df = pd.DataFrame([
            {"Source": "Sanlam annuity", "Monthly": sanlam_income},
            {"Source": "10X annuity",    "Monthly": tenx_income},
            {"Source": "RSA Retail",     "Monthly": rsa_monthly},
        ])
        st.dataframe(
            inc_df.assign(Monthly=inc_df["Monthly"].map(zar)),
            hide_index=True, use_container_width=True,
        )
        fig_inc = px.pie(
            inc_df, values="Monthly", names="Source", hole=0.45,
            color_discrete_sequence=["#00ebc7", "#4169E1", "#FFD700"],
        )
        fig_inc.update_layout(
            template="plotly_dark", height=220,
            margin=dict(t=0, b=0), legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_inc, use_container_width=True)

    with right:
        st.markdown("**Monthly cash flow**")
        cf_df = pd.DataFrame([
            {"Item": "After-tax income",   "Amount": income_after_tax},
            {"Item": "Home Loan",          "Amount": -home_loan_payment},
            {"Item": "RCP",                "Amount": -rcp_payment},
            {"Item": "Credit Card ABSA",   "Amount": -absa_payment},
            {"Item": "Other expenses",     "Amount": -variable_exp},
            {"Item": "Discretionary",      "Amount": discretionary},
        ])
        st.dataframe(
            cf_df.assign(Amount=cf_df["Amount"].map(zar)),
            hide_index=True, use_container_width=True,
        )
        st.metric(
            "Discretionary Spend",
            zar(discretionary),
            delta="surplus" if discretionary >= 0 else "shortfall",
            delta_color="normal" if discretionary >= 0 else "inverse",
        )

    st.divider()
    st.caption(
        "SARS lump sum tax: R1–R550k @ 0% | R550k–R770k @ 18% | "
        "R770k–R1.155M @ 27% | Above R1.155M @ 36%"
    )
