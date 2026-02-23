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
        green_value = int(150 + (105 * scale))
        return f"rgb(0,{green_value},0)"
    else:
        scale = min((RPH_TARGET - rph) / RPH_TARGET, 1.0)
        red_value = int(150 + (105 * scale))
        return f"rgb({red_value},0,0)"

# -----------------------------
# Helpers
# -----------------------------
def sale_row(row_num: int):
    c1, c2 = st.columns([2, 3])
    with c1:
        st.number_input(
            f"Revenue ($) — Item {row_num}",
            min_value=0.0,
            step=1.0,
            key=f"rev_{row_num}",
        )
    with c2:
        st.multiselect(
            f"Category Tags — Item {row_num}",
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
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")

# -----------------------------
# Add Sale (progressive items)
# -----------------------------
st.header("Add Sale")

# Controls row: + and - buttons
ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 6])
with ctrl1:
    if st.button("➕", help="Add another item (max 3)") and st.session_state.item_count < MAX_ITEMS:
        st.session_state.item_count += 1
        st.rerun()
with ctrl2:
    if st.button("➖", help="Remove last item") and st.session_state.item_count > 1:
        # clear last row inputs when removing it
        last = st.session_state.item_count
        st.session_state[f"rev_{last}"] = 0.0
        st.session_state[f"tags_{last}"] = []
        st.session_state.item_count -= 1
        st.rerun()

# Render only the number of rows needed
for row in range(1, st.session_state.item_count + 1):
    sale_row(row)

btn1, btn2 = st.columns([2, 2])
with btn1:
    if st.button("Add Sale"):
        count = add_basket()
        if count > 0:
            st.success(f"Added {count} item(s).")
            clear_inputs()
            st.rerun()
        else:
            st.warning("Nothing added. Enter revenue > $0 for at least one item.")
with btn2:
    if st.button("Clear"):
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

# -----------------------------
# Display Metrics
# -----------------------------
color = get_rph_color(rph)

st.markdown(f"""
<h2>Total Revenue: ${total_revenue:,.2f}</h2>
<h2 style='color:{color}'>RPH: ${rph:,.2f}</h2>
<h2>Category Revenue: ${category_revenue:,.2f}</h2>
<h2>Revmix: {revmix*100:.2f}%</h2>
""", unsafe_allow_html=True)

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
# What Do I Need Section
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
