"""
RAGSPRO Revenue Tracking — Full Analytics with Charts, MRR Growth, Client Funnel
Uses Plotly for interactive charts
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="RAGSPRO - Revenue Analytics", page_icon="💰", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
REVENUE_FILE = DATA_DIR / "revenue.json"
LEADS_FILE = DATA_DIR / "leads.json"
CLIENTS_FILE = DATA_DIR / "clients.json"

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.main { font-family: 'Inter', sans-serif; background: #f8fafc; }

.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
}

.kpi-card .value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.kpi-card .label {
    font-size: 0.85rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

.kpi-card .delta {
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.5rem;
}

.delta-positive { color: #10b981; }
.delta-negative { color: #ef4444; }

.funnel-stage {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 0.5rem;
}

.funnel-stage .count { font-size: 1.8rem; font-weight: 700; }
.funnel-stage .label { font-size: 0.8rem; opacity: 0.9; }

.churn-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1rem;
    border-radius: 12px;
}

.mrr-card {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
}

.mrr-card .value { font-size: 2.5rem; font-weight: 800; }
.mrr-card .label { font-size: 0.9rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_revenue():
    if REVENUE_FILE.exists():
        try:
            with open(REVENUE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"entries": [], "goals": {"monthly": 50000}}
    return {"entries": [], "goals": {"monthly": 50000}}

def load_leads():
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def load_clients():
    if CLIENTS_FILE.exists():
        try:
            with open(CLIENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

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

def format_inr_full(amount):
    return f"₹{int(amount):,}"

# ─── Main Dashboard ───────────────────────────────────────────────────────────

st.title("💰 Revenue Analytics & Growth Tracking")

revenue_data = load_revenue()
entries = revenue_data.get("entries", [])
monthly_goal = revenue_data.get("goals", {}).get("monthly", 50000)
leads = load_leads()
clients = load_clients()

# Calculate metrics
now = datetime.now()
current_month = now.strftime("%Y-%m")
prev_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

month_entries = [e for e in entries if e.get("date", "").startswith(current_month)]
prev_month_entries = [e for e in entries if e.get("date", "").startswith(prev_month)]

month_income = sum(e["amount"] for e in month_entries if e.get("type") == "income")
month_expenses = sum(e["amount"] for e in month_entries if e.get("type") == "expense")
prev_income = sum(e["amount"] for e in prev_month_entries if e.get("type") == "income")

# MRR Calculations
recurring_entries = [e for e in entries if e.get("recurring", False) and e.get("type") == "income"]
mrr = sum(e["amount"] for e in recurring_entries)
total_income = sum(e["amount"] for e in entries if e.get("type") == "income")
total_expenses = sum(e["amount"] for e in entries if e.get("type") == "expense")

# ARR (Annual Recurring Revenue)
arr = mrr * 12

# ─── KPI Cards Row ────────────────────────────────────────────────────────────

st.subheader("📊 Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

# MRR Card
with col1:
    mrr_delta = 0
    if prev_income > 0:
        mrr_delta = ((month_income - prev_income) / prev_income) * 100
    delta_class = "delta-positive" if mrr_delta >= 0 else "delta-negative"
    delta_symbol = "↑" if mrr_delta >= 0 else "↓"

    st.markdown(f"""
    <div class='kpi-card'>
        <div class='label'>This Month</div>
        <div class='value'>{format_inr(month_income)}</div>
        <div class='delta {delta_class}'>{delta_symbol} {abs(mrr_delta):.1f}% vs last month</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='label'>MRR (Recurring)</div>
        <div class='value' style='color: #10b981;'>{format_inr(mrr)}</div>
        <div class='delta' style='color: #6b7280;'>{format_inr(arr)} ARR</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    progress = min((month_income / monthly_goal * 100) if monthly_goal > 0 else 0, 100)
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='label'>Goal Progress</div>
        <div class='value' style='color: #8b5cf6;'>{progress:.0f}%</div>
        <div class='delta' style='color: #6b7280;'>{format_inr(month_income)} / {format_inr(monthly_goal)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    profit = total_income - total_expenses
    profit_margin = (profit / total_income * 100) if total_income > 0 else 0
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='label'>Net Profit</div>
        <div class='value' style='color: #f59e0b;'>{format_inr(profit)}</div>
        <div class='delta' style='color: #6b7280;'>{profit_margin:.1f}% margin</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    # Calculate LTV (Lifetime Value) - avg revenue per client
    active_clients = len([c for c in clients if c.get("status") == "active"])
    avg_ltv = total_income / active_clients if active_clients > 0 else 0
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='label'>Active Clients</div>
        <div class='value' style='color: #ec4899;'>{active_clients}</div>
        <div class='delta' style='color: #6b7280;'>{format_inr(avg_ltv)} avg LTV</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Charts Section ───────────────────────────────────────────────────────────

chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 Revenue Trend (Last 12 Months)")

    # Prepare monthly data for last 12 months
    monthly_data = defaultdict(lambda: {"income": 0, "expense": 0, "mrr": 0})

    for entry in entries:
        month = entry.get("date", "")[:7]
        if month:
            monthly_data[month][entry.get("type", "income")] += entry.get("amount", 0)
            if entry.get("recurring") and entry.get("type") == "income":
                monthly_data[month]["mrr"] += entry.get("amount", 0)

    # Get last 12 months
    months = []
    for i in range(11, -1, -1):
        d = now.replace(day=1) - timedelta(days=i*30)
        months.append(d.strftime("%Y-%m"))

    chart_data = pd.DataFrame({
        "Month": [m[5:] for m in months],  # Just MM format
        "Income": [monthly_data.get(m, {}).get("income", 0) for m in months],
        "Expenses": [monthly_data.get(m, {}).get("expense", 0) for m in months],
        "MRR": [monthly_data.get(m, {}).get("mrr", 0) for m in months],
    })

    st.line_chart(chart_data.set_index("Month"), use_container_width=True)

    # Revenue breakdown by category
    st.subheader("📊 Revenue by Category (This Month)")
    income_by_cat = defaultdict(int)
    for e in month_entries:
        if e.get("type") == "income":
            income_by_cat[e.get("category", "Other")] += e.get("amount", 0)

    if income_by_cat:
        cat_df = pd.DataFrame([(k, v) for k, v in income_by_cat.items()],
                              columns=["Category", "Amount"])
        cat_df = cat_df.sort_values("Amount", ascending=False)
        st.bar_chart(cat_df.set_index("Category"), use_container_width=True, color="#667eea")
    else:
        st.info("No income data this month")

with chart_col2:
    st.subheader("🎯 Client Acquisition Funnel")

    # Calculate funnel metrics
    total_leads = len(leads)
    contacted = len([l for l in leads if l.get("status") in ["CONTACTED", "RESPONDED", "MEETING", "CLOSED"]])
    responded = len([l for l in leads if l.get("status") in ["RESPONDED", "MEETING", "CLOSED"]])
    meetings = len([l for l in leads if l.get("status") in ["MEETING", "CLOSED"]])
    closed = len([l for l in leads if l.get("status") == "CLOSED"])

    # Conversion rates
    contact_rate = (contacted / total_leads * 100) if total_leads > 0 else 0
    response_rate = (responded / contacted * 100) if contacted > 0 else 0
    meeting_rate = (meetings / responded * 100) if responded > 0 else 0
    close_rate = (closed / meetings * 100) if meetings > 0 else 0

    st.markdown(f"""
    <div class='funnel-stage'>
        <div class='count'>{total_leads}</div>
        <div class='label'>Total Leads</div>
    </div>
    <div style='text-align: center; color: #6b7280; font-size: 0.75rem; margin: -0.25rem 0 0.25rem;'>
        ↓ {contact_rate:.1f}% contacted
    </div>

    <div class='funnel-stage' style='background: linear-gradient(135deg, #764ba2, #8b5cf6); width: 90%; margin-left: 5%;'>
        <div class='count'>{contacted}</div>
        <div class='label'>Contacted</div>
    </div>
    <div style='text-align: center; color: #6b7280; font-size: 0.75rem; margin: -0.25rem 0 0.25rem;'>
        ↓ {response_rate:.1f}% responded
    </div>

    <div class='funnel-stage' style='background: linear-gradient(135deg, #8b5cf6, #a78bfa); width: 80%; margin-left: 10%;'>
        <div class='count'>{responded}</div>
        <div class='label'>Responded</div>
    </div>
    <div style='text-align: center; color: #6b7280; font-size: 0.75rem; margin: -0.25rem 0 0.25rem;'>
        ↓ {meeting_rate:.1f}% meetings booked
    </div>

    <div class='funnel-stage' style='background: linear-gradient(135deg, #a78bfa, #c4b5fd); width: 70%; margin-left: 15%;'>
        <div class='count'>{meetings}</div>
        <div class='label'>Meetings</div>
    </div>
    <div style='text-align: center; color: #6b7280; font-size: 0.75rem; margin: -0.25rem 0 0.25rem;'>
        ↓ {close_rate:.1f}% closed
    </div>

    <div class='funnel-stage' style='background: linear-gradient(135deg, #10b981, #34d399); width: 60%; margin-left: 20%;'>
        <div class='count'>{closed}</div>
        <div class='label'>Closed Won</div>
    </div>
    """, unsafe_allow_html=True)

    # CAC (Customer Acquisition Cost) estimate
    st.divider()
    st.subheader("💡 Conversion Insights")

    total_acquisition_spend = sum(e.get("amount", 0) for e in entries
                                   if e.get("type") == "expense" and
                                   e.get("category") in ["Marketing", "Ads", "Outreach"])
    cac = total_acquisition_spend / closed if closed > 0 else 0

    st.metric("Customer Acquisition Cost", format_inr(cac))

    # LTV/CAC ratio
    ltv_cac_ratio = avg_ltv / cac if cac > 0 else 0
    st.metric("LTV/CAC Ratio", f"{ltv_cac_ratio:.1f}x",
              help="Healthy ratio is 3x or higher")

st.divider()

# ─── Add Revenue Entry ─────────────────────────────────────────────────────────

st.subheader("➕ Add Revenue Entry")

with st.form("add_revenue", clear_on_submit=True):
    entry_col1, entry_col2, entry_col3 = st.columns(3)

    with entry_col1:
        entry_type = st.selectbox("Type", ["income", "expense"])
        amount = st.number_input("Amount (₹)", min_value=0, step=1000, value=0)

    with entry_col2:
        if entry_type == "income":
            category = st.selectbox("Category", [
                "Freelance Project", "Retainer", "SaaS Revenue", "Consultation",
                "AI Agent Service", "Content Creation", "Other"
            ])
        else:
            category = st.selectbox("Category", [
                "Tool Subscription", "Hosting", "Marketing", "Ads",
                "Software", "Freelancer Pay", "Other"
            ])

        client_name = st.text_input("Client / Source", placeholder="e.g. XYZ Corp")

    with entry_col3:
        entry_date = st.date_input("Date", value=datetime.now())
        recurring = st.checkbox("Recurring (MRR)", value=False)

    description = st.text_input("Description", placeholder="Brief note about this transaction...")

    submitted = st.form_submit_button("💾 Add Entry", use_container_width=True, type="primary")

    if submitted and amount > 0:
        new_entry = {
            "id": f"rev_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": entry_type,
            "amount": amount,
            "category": category,
            "client": client_name,
            "description": description,
            "date": entry_date.strftime("%Y-%m-%d"),
            "recurring": recurring,
            "created_at": datetime.now().isoformat()
        }
        entries.append(new_entry)
        revenue_data["entries"] = entries
        save_revenue(revenue_data)
        st.success(f"✅ {'💰 Income' if entry_type == 'income' else '💸 Expense'} of ₹{amount:,} added!")
        st.rerun()

st.divider()

# ─── Goal Setting & Recent Entries ────────────────────────────────────────────

goal_col, entries_col = st.columns([1, 2])

with goal_col:
    st.subheader("🎯 Monthly Goal")
    new_goal = st.number_input("Target Monthly Revenue (₹)",
                                min_value=0, step=10000, value=monthly_goal)
    if new_goal != monthly_goal:
        revenue_data["goals"]["monthly"] = new_goal
        save_revenue(revenue_data)
        st.success("✅ Goal updated!")
        st.rerun()

    st.divider()

    # Quick stats
    st.subheader("📈 Quick Stats")
    st.metric("Total Revenue (All Time)", format_inr_full(total_income))
    st.metric("Total Expenses", format_inr_full(total_expenses))
    st.metric("Net Profit", format_inr_full(total_income - total_expenses))

with entries_col:
    st.subheader("📋 Recent Transactions")

    # Filter
    filter_tabs = st.tabs(["All", "Income", "Expenses", "Recurring"])

    filtered = entries

    with filter_tabs[0]:  # All
        filtered = entries
    with filter_tabs[1]:  # Income
        filtered = [e for e in entries if e.get("type") == "income"]
    with filter_tabs[2]:  # Expenses
        filtered = [e for e in entries if e.get("type") == "expense"]
    with filter_tabs[3]:  # Recurring
        filtered = [e for e in entries if e.get("recurring", False)]

    # Sort by date descending
    filtered = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    if filtered:
        df = pd.DataFrame(filtered[:20])
        if not df.empty:
            df["Amount"] = df.apply(lambda x: f"₹{x['amount']:,}", axis=1)
            df["Type"] = df["type"].str.upper()
            df["Recurring"] = df["recurring"].apply(lambda x: "🔄" if x else "")

            display_df = df[["date", "client", "category", "Amount", "Type", "Recurring", "description"]].copy()
            display_df.columns = ["Date", "Client", "Category", "Amount", "Type", "", "Description"]

            st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions found")

    # Delete entry
    if filtered:
        st.divider()
        entry_to_delete = st.selectbox("Delete Entry",
                                       options=[""] + [f"{e.get('date')} - {e.get('client')} - ₹{e.get('amount',0):,}"
                                                      for e in filtered[:10]],
                                       key="delete_select")
        if entry_to_delete and st.button("🗑️ Delete Selected", type="secondary"):
            # Find and delete
            for e in filtered[:10]:
                expected = f"{e.get('date')} - {e.get('client')} - ₹{e.get('amount',0):,}"
                if expected == entry_to_delete:
                    entries = [entry for entry in entries if entry["id"] != e["id"]]
                    revenue_data["entries"] = entries
                    save_revenue(revenue_data)
                    st.success("✅ Entry deleted!")
                    st.rerun()

st.divider()

# ─── Export Section ───────────────────────────────────────────────────────────

st.subheader("📤 Export Data")
export_col1, export_col2 = st.columns(2)

with export_col1:
    if st.button("📊 Export Revenue Report (CSV)", use_container_width=True):
        df_export = pd.DataFrame(entries)
        if not df_export.empty:
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"revenue_report_{now.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

with export_col2:
    if st.button("📈 Export Analytics Summary", use_container_width=True):
        summary = {
            "generated_at": now.isoformat(),
            "total_revenue": total_income,
            "total_expenses": total_expenses,
            "net_profit": total_income - total_expenses,
            "mrr": mrr,
            "arr": arr,
            "monthly_goal": monthly_goal,
            "goal_progress": progress,
            "active_clients": active_clients,
            "total_leads": total_leads,
            "conversion_rate": close_rate
        }
        st.download_button(
            label="Download JSON",
            data=json.dumps(summary, indent=2),
            file_name=f"analytics_summary_{now.strftime('%Y%m%d')}.json",
            mime="application/json"
        )
