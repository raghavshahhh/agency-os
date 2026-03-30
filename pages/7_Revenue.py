"""
RAGSPRO Revenue Tracking — Track income, expenses, and financial goals
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="RAGSPRO - Revenue", page_icon="💰", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
REVENUE_FILE = DATA_DIR / "revenue.json"

# ─── Custom CSS ───
st.markdown("""
<style>
    .revenue-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.25rem;
        border-radius: 12px;
        text-align: center;
    }
    .revenue-card .value {
        font-size: 2rem;
        font-weight: 700;
    }
    .revenue-card .label {
        font-size: 0.8rem;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .income-card {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .expense-card {
        background: linear-gradient(135deg, #eb3349, #f45c43);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def load_revenue():
    if REVENUE_FILE.exists():
        try:
            with open(REVENUE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"entries": [], "goals": {"monthly": 100000}}
    return {"entries": [], "goals": {"monthly": 100000}}


def save_revenue(data):
    REVENUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVENUE_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def format_inr(amount):
    if amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    return f"₹{int(amount)}"


# ─── Main ─────────────────────────────────────────────────────────────────────

st.title("💰 Revenue Tracking")

revenue_data = load_revenue()
entries = revenue_data.get("entries", [])
monthly_goal = revenue_data.get("goals", {}).get("monthly", 100000)

# Current month calculations
now = datetime.now()
current_month = now.strftime("%Y-%m")

month_entries = [e for e in entries if e.get("date", "").startswith(current_month)]
month_income = sum(e["amount"] for e in month_entries if e.get("type") == "income")
month_expenses = sum(e["amount"] for e in month_entries if e.get("type") == "expense")
month_profit = month_income - month_expenses
total_income = sum(e["amount"] for e in entries if e.get("type") == "income")
total_expenses = sum(e["amount"] for e in entries if e.get("type") == "expense")

# ─── KPI Cards ────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='revenue-card'>
        <div class='label'>This Month Revenue</div>
        <div class='value'>{format_inr(month_income)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='income-card'>
        <div class='label'>Profit</div>
        <div class='value' style='font-size:1.5rem;font-weight:700;'>{format_inr(month_profit)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='expense-card'>
        <div class='label'>Expenses</div>
        <div class='value' style='font-size:1.5rem;font-weight:700;'>{format_inr(month_expenses)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    progress = min((month_income / monthly_goal * 100) if monthly_goal > 0 else 0, 100)
    st.markdown(f"""
    <div style='background:#f8f9fa;border:1px solid #e5e5e5;border-radius:10px;padding:1rem;text-align:center;'>
        <div style='font-size:0.8rem;color:#666;text-transform:uppercase;'>Monthly Goal</div>
        <div style='font-size:1.5rem;font-weight:700;color:#333;'>{progress:.0f}%</div>
        <div style='font-size:0.75rem;color:#888;'>{format_inr(month_income)} / {format_inr(monthly_goal)}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Add Entry ────────────────────────────────────────────────────────────────

col_form, col_chart = st.columns([1, 2])

with col_form:
    st.subheader("Add Entry")

    with st.form("add_revenue"):
        entry_type = st.selectbox("Type", ["income", "expense"])
        amount = st.number_input("Amount (₹)", min_value=0, step=500, value=0)
        category = st.selectbox("Category",
            ["Freelance Project", "Retainer", "SaaS Revenue", "Consultation",
             "Tool Subscription", "Hosting", "Marketing", "Other"]
            if entry_type == "income" else
            ["Tool Subscription", "Hosting", "Marketing", "Software", "Freelancer Pay", "Other"]
        )
        client_name = st.text_input("Client / Source", placeholder="e.g. XYZ Corp")
        description = st.text_input("Description", placeholder="Brief note...")
        entry_date = st.date_input("Date", value=datetime.now())
        submitted = st.form_submit_button("Add Entry", use_container_width=True)

        if submitted and amount > 0:
            new_entry = {
                "id": f"rev_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": entry_type,
                "amount": amount,
                "category": category,
                "client": client_name,
                "description": description,
                "date": entry_date.strftime("%Y-%m-%d"),
                "created_at": datetime.now().isoformat()
            }
            entries.append(new_entry)
            revenue_data["entries"] = entries
            save_revenue(revenue_data)
            st.success(f"{'💰 Income' if entry_type == 'income' else '💸 Expense'} of ₹{amount:,} added!")
            st.rerun()

    # Monthly goal setting
    st.divider()
    st.subheader("🎯 Set Monthly Goal")
    new_goal = st.number_input("Monthly Goal (₹)", min_value=0, step=10000, value=monthly_goal)
    if new_goal != monthly_goal:
        revenue_data["goals"]["monthly"] = new_goal
        save_revenue(revenue_data)
        st.success("Goal updated!")
        st.rerun()

with col_chart:
    st.subheader("📈 Monthly Trend")

    if entries:
        # Group by month
        monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
        for entry in entries:
            month = entry.get("date", "")[:7]
            if month:
                monthly_data[month][entry.get("type", "income")] += entry.get("amount", 0)

        if monthly_data:
            months = sorted(monthly_data.keys())[-6:]  # Last 6 months
            chart_data = pd.DataFrame({
                "Month": months,
                "Income": [monthly_data[m]["income"] for m in months],
                "Expenses": [monthly_data[m]["expense"] for m in months]
            })
            chart_data = chart_data.set_index("Month")
            st.bar_chart(chart_data)

        # Category breakdown
        st.subheader("📊 Income by Category")
        income_by_cat = defaultdict(int)
        for e in month_entries:
            if e.get("type") == "income":
                income_by_cat[e.get("category", "Other")] += e.get("amount", 0)

        if income_by_cat:
            cat_df = pd.DataFrame(
                [(k, v) for k, v in income_by_cat.items()],
                columns=["Category", "Amount"]
            )
            st.bar_chart(cat_df.set_index("Category"))
        else:
            st.info("No income entries this month yet")
    else:
        st.info("No revenue data yet. Add your first entry!")

# ─── All Entries ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("📋 All Entries")

# Filter
filter_type = st.selectbox("Filter", ["All", "Income", "Expenses"], key="filter_entries")
filtered = entries
if filter_type == "Income":
    filtered = [e for e in entries if e.get("type") == "income"]
elif filter_type == "Expenses":
    filtered = [e for e in entries if e.get("type") == "expense"]

# Sort by date descending
filtered = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

if filtered:
    for entry in filtered[:20]:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])
        with col1:
            icon = "💰" if entry.get("type") == "income" else "💸"
            st.markdown(f"{icon} **{entry.get('client', 'Unknown')}** — {entry.get('description', '')}")
            st.caption(f"{entry.get('category', '')} | {entry.get('date', '')}")
        with col2:
            color = "#11998e" if entry.get("type") == "income" else "#eb3349"
            st.markdown(f"<span style='color:{color};font-weight:600;'>₹{entry.get('amount',0):,}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"`{entry.get('type','').upper()}`")
        with col4:
            st.caption(entry.get("date", ""))
        with col5:
            if st.button("🗑", key=f"del_{entry['id']}"):
                entries = [e for e in entries if e["id"] != entry["id"]]
                revenue_data["entries"] = entries
                save_revenue(revenue_data)
                st.rerun()
        st.markdown("---")
else:
    st.info("No entries found")

# ─── Summary ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📊 All Time Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"₹{total_income:,}")
col2.metric("Total Expenses", f"₹{total_expenses:,}")
col3.metric("Net Profit", f"₹{total_income - total_expenses:,}")
