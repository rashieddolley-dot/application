import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# --- APP CONFIG ---
st.set_page_config(page_title="Smart Burndown", layout="wide")

# --- MOCK HISTORICAL DATA ---
# In a real app, this would come from your uploaded CSV/API
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame([
        {"Date": "2025-12-01", "Category": "Groceries", "Amount": 60},
        {"Date": "2025-12-05", "Category": "Dining", "Amount": 40},
        {"Date": "2025-12-10", "Category": "Transport", "Amount": 20},
        {"Date": "2025-12-15", "Category": "Groceries", "Amount": 55},
    ])

# --- UI: SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    payday_val = st.number_input("Payday Balance", min_value=0.0, value=4500.0)
    safety_net = st.number_input("Emergency Buffer (Goal)", min_value=0.0, value=500.0)
    
    st.divider()
    st.subheader("Fixed Costs (Rent, Bills)")
    fixed_data = st.data_editor(pd.DataFrame([
        {"Name": "Rent/Mortgage", "Amount": 1200.0, "Day": 1},
        {"Name": "Utilities", "Amount": 150.0, "Day": 10},
        {"Name": "Internet", "Amount": 70.0, "Day": 15},
    ]))

# --- LOGIC: CATEGORIZED VELOCITY ---
def calculate_velocity(df):
    # Simplistic version: Total spent in history / number of days in history
    if df.empty: return 50.0 # Default fallback
    total_days = (pd.to_datetime(df['Date']).max() - pd.to_datetime(df['Date']).min()).days + 1
    if total_days <= 0: total_days = 30
    
    # Group by category to show the user their habits
    cat_spend = df.groupby('Category')['Amount'].sum() / total_days
    return cat_spend

category_velocities = calculate_velocity(st.session_state.history)
daily_planned_burn = category_velocities.sum()

# --- DATA GENERATION ---
today = datetime.now()
last_day = calendar.monthrange(today.year, today.month)[1]
days = list(range(1, last_day + 1))

# 1. Planned Burndown Calculation
planned_path = []
current_bal = payday_val
for d in days:
    # Subtract fixed costs
    today_fixed = fixed_data[fixed_data['Day'] == d]['Amount'].sum()
    current_bal -= today_fixed
    # Subtract variable categorized burn
    current_bal -= daily_planned_burn
    planned_path.append(max(current_bal, 0))

# 2. Actual Spending (Mocked for current month)
# This would normally pull from a 'Current_Month_Transactions' table
actual_path = []
temp_actual = payday_val
for d in range(1, today.day + 1):
    # Logic: simulate actual spend slightly higher than planned
    today_fixed = fixed_data[fixed_data['Day'] == d]['Amount'].sum()
    temp_actual -= (today_fixed + (daily_planned_burn * 1.1)) 
    actual_path.append(temp_actual)

# --- VISUALIZATION ---
st.title("📊 Monthly Spending Burndown")

fig = go.Figure()

# Planned Line (The Budget)
fig.add_trace(go.Scatter(x=days, y=planned_path, name="Planned Budget", 
                         line=dict(color='gray', width=2, dash='dot')))

# Actual Line (The Reality)
fig.add_trace(go.Scatter(x=list(range(1, today.day + 1)), y=actual_path, 
                         name="Actual Balance", line=dict(color='#00ebc7', width=4)))

# Safety Net
fig.add_hline(y=safety_net, line_color="orange", annotation_text="Safety Buffer")

fig.update_layout(hovermode="x unified", template="plotly_dark", height=500,
                  xaxis=dict(title="Day of Month"), yaxis=dict(title="Balance ($)"))

st.plotly_chart(fig, use_container_width=True)

# --- CATEGORY BREAKDOWN & METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Suggested Daily Variable Budget", f"${daily_planned_burn:.2f}")
    st.caption("Based on historical averages per category.")

with col2:
    status = "Under Budget" if actual_path[-1] > planned_path[today.day-1] else "Over Budget"
    st.metric("Current Status", status, f"{actual_path[-1] - planned_path[today.day-1]:.2f}")

with col3:
    st.subheader("Burn Rate by Category")
    st.write(category_velocities.map(lambda x: f"${x:.2f}/day"))

st.divider()
st.info("💡 **Pro-Tip:** Your Rent and Utilities cause 'cliffs' in your chart. The daily slope represents your variable spending like food and transport.")