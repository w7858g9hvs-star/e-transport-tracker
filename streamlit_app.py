import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

RPH_TARGET = 300
RPH_MAX_GREEN = 600
REVMIX_TARGET = 0.60
MAX_ITEMS = 3

st.set_page_config(layout="wide")

# -----------------------------
# Initialize Session State
# -----------------------------
if "sales" not in st.session_state:
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())

if "item_count" not in st.session_state:
    st.session_state.item_count = 1

# Auto daily reset
if st.session_state.current_date != str(date.today()):
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())
    st.session_state.item_count = 1

# Initialize item inputs so we can clear them reliably
for idx in range(1, MAX_ITEMS + 1):
    st.session_state.setdefault(f"rev_{idx}", 0.0)
    st.session_state.setdefault(f"tags_{idx}", [])

# -----------------------------
# RPH Color Logic
# -----------------------------
def get_rph_color(rph: float) -> str:
    if rph >= RPH_TARGET:
        scale = min((rph - RPH_TARGET) / (RPH_MAX_GREEN - RPH_TARGET), 1.0)
        green_value = int(150 + (105 * scale))  # 150 -> 255
        return f"rgb(0,{green_value},0)"
    else:
        scale = min((RPH_TARGET - rph) / RPH_TARGET, 1.0)
        red_value = int(150 + (105 * scale))  # 150 -> 255
        return f"rgb({red_value},0,0)"

# -----------------------------
# Helpers
# -----------------------------
def sale_row(row_num: int):
    c1, c2 = st.columns([2, 3])
    with c1:
        st.number_input(
            "Revenue ($)",
            min_value=0.0,
            step=1.0,
            key=f"rev_{row_num}",
        )
    with c2:
        st.multiselect(
            "Category Tags",
            ["Health/Wearables", "CarFi", "Other"],
            key=f"tags_{row_num}",
        )

def clear_inputs():
    for i in range(1, MAX_ITEMS + 1):
        st.session_state[f"rev_{i}"] = 0.0
        st.session_state[f"tags_{i}"] = []
    st.session_state.item_count = 1

def add_basket():
    added = 0
    for i in range(1, st.session_state.item_count + 1):
        revenue = float(st.session_state.get(f"rev_{i}", 0.0) or 0.0)
        tags = st.session_state.get(f"tags_{i}", []) or []
        if revenue > 0:
            st.session_state.sales.append({"revenue": revenue, "categories": tags})
            added += 1
    return added

# -----------------------------
# Title
# -----------------------------
st.title("E-Transport Sales Tracker")

# -----------------------------
# Add Sale (progressive items + small plus under item 1)
# -----------------------------
st.header("Add Sale")

# CSS to make the plus button smaller (targets this button via key-based CSS selector)
st.markdown(
    """
    <style>
    /* Make ONLY the plus button smaller */
    div[data-testid="stButton"] button[kind="secondary"]{
        font-size: 14px !important;
        padding: 2px 10px !important;
        height: 30px !important;
        width: 46px !important;
        line-height: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Item 1
sale_row(1)

# Small plus button under item 1
col_plus, _ = st.columns([1, 7])
with col_plus:
    if st.button("＋", key="plus_btn", help="Add another item (max 3)"):
        if st.session_state.item_count < MAX_ITEMS:
            st.session_state.item_count += 1
            st.rerun()

# Additional items appear only if needed
if st.session_state.item_count >= 2:
    st.divider()
    sale_row(2)

if st.session_state.item_count >= 3:
    st.divider()
    sale_row(3)

btn1, btn2 = st.columns([2, 2])
with btn1:
    if st.button("Add Sale", key="add_sale_btn"):
        count = add_basket()
        if count > 0:
            st.success(f"Added {count} item(s).")
            clear_inputs()
            st.rerun()
        else:
            st.warning("Nothing added. Enter revenue > $0 for at least one item.")
with btn2:
    if st.button("Clear", key="clear_btn"):
        clear_inputs()
        st.rerun()

# -----------------------------
# Metrics Section
# -----------------------------
st.header("Today's Performance")

hours_worked = st.number_input(
    "Hours Worked Today",
    min_value=1.0,
    max_value=16.0,
    value=8.0,
    step=0.5
)

total_revenue = sum(s["revenue"] for s in st.session_state.sales)

category_revenue = sum(
    s["revenue"]
    for s in st.session_state.sales
    if any(cat in ["Health/Wearables", "CarFi"] for cat in s["categories"])
)

other_revenue = total_revenue - category_revenue

rph = total_revenue / hours_worked if hours_worked else 0
revmix = category_revenue / total_revenue if total_revenue > 0 else 0

# Display Metrics
color = get_rph_color(rph)

st.markdown(
    f"""
    <h2>Total Revenue: ${total_revenue:,.2f}</h2>
    <h2 style='color:{color}'>RPH: ${rph:,.2f}</h2>
    <h2>Category Revenue: ${category_revenue:,.2f}</h2>
    <h2>Revmix: {revmix*100:.2f}%</h2>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Pie Chart
# -----------------------------
st.subheader("Revenue Breakdown")

if total_revenue > 0:
    fig = plt.figure()
    plt.pie(
        [category_revenue, other_revenue],
        labels=["Category", "Other"],
        autopct="%1.1f%%"
    )
    plt.title("Category vs Other Revenue")
    st.pyplot(fig)
else:
    st.info("No revenue yet to display.")

# -----------------------------
# What Do I Need
# -----------------------------
st.subheader("What Do I Need to Hit Target?")

required_total = RPH_TARGET * hours_worked
additional_needed = max(required_total - total_revenue, 0)

if additional_needed > 0:
    st.write(f"You need **${additional_needed:,.2f} more total revenue** to hit $300 RPH.")
else:
    st.success("RPH Target Hit ✅")

required_category = REVMIX_TARGET * total_revenue
category_shortfall = max(required_category - category_revenue, 0)

if category_shortfall > 0:
    st.write(f"You need **${category_shortfall:,.2f} more in Category sales** to reach 60% revmix.")
else:
    st.success("Revmix Target Hit ✅")

# -----------------------------
# Sales History
# -----------------------------
st.header("Sales History")

if st.session_state.sales:
    for i, sale in enumerate(st.session_state.sales):
        col1, col2, col3 = st.columns([4, 3, 1])
        with col1:
            st.write(f"${sale['revenue']:,.2f}")
        with col2:
            st.write(", ".join(sale["categories"]) if sale["categories"] else "(No tags)")
        with col3:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.sales.pop(i)
                st.rerun()
else:
    st.info("No sales recorded today.")
