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

# Initialize item inputs
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
def add_sale_items():
    added = 0
    for i in range(1, st.session_state.item_count + 1):
        revenue = float(st.session_state.get(f"rev_{i}", 0.0) or 0.0)
        tags = st.session_state.get(f"tags_{i}", []) or []
        if revenue > 0:
            st.session_state.sales.append({"revenue": revenue, "categories": tags})
            added += 1
    return added

def clear_item_inputs():
    for i in range(1, MAX_ITEMS + 1):
        st.session_state[f"rev_{i}"] = 0.0
        st.session_state[f"tags_{i}"] = []
    st.session_state.item_count = 1

def remove_line(line_index: int):
    """
    Remove a line item 1..item_count by shifting later lines up.
    """
    if st.session_state.item_count <= 1:
        return

    # Shift values up from line_index -> item_count-1
    for j in range(line_index, st.session_state.item_count):
        st.session_state[f"rev_{j}"] = float(st.session_state.get(f"rev_{j+1}", 0.0) or 0.0)
        st.session_state[f"tags_{j}"] = list(st.session_state.get(f"tags_{j+1}", []) or [])

    # Clear last line
    last = st.session_state.item_count
    st.session_state[f"rev_{last}"] = 0.0
    st.session_state[f"tags_{last}"] = []
    st.session_state.item_count -= 1

# -----------------------------
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")

# -----------------------------
# Add Sale (compact, progressive)
# -----------------------------
st.header("Add Sale")

# Use a form so the layout stays tight and inputs feel like a single “basket”
with st.form("add_sale_form", clear_on_submit=False):

    # Render line items compactly
    for i in range(1, st.session_state.item_count + 1):
        # Revenue | Tags | Remove (for lines > 1)
        c1, c2, c3 = st.columns([1.2, 3.2, 0.35], vertical_alignment="center")

        with c1:
            st.number_input(
                "Revenue ($)",
                min_value=0.0,
                step=1.0,
                key=f"rev_{i}",
                label_visibility="collapsed",
                placeholder="Revenue",
            )

        with c2:
            st.multiselect(
                "Tags",
                ["Health/Wearables", "CarFi", "Other"],
                key=f"tags_{i}",
                label_visibility="collapsed",
                placeholder="Category tags",
            )

        with c3:
            if i == 1:
                st.write("")  # keep alignment
            else:
                # minus button for this line
                if st.form_submit_button("−", help=f"Remove item {i}"):
                    remove_line(i)
                    st.rerun()

    # Add-line button goes at the bottom under the last row
    bottom_left, bottom_mid, bottom_right = st.columns([1.2, 3.2, 0.35], vertical_alignment="center")
    with bottom_right:
        if st.form_submit_button("＋", help="Add another item"):
            if st.session_state.item_count < MAX_ITEMS:
                st.session_state.item_count += 1
            st.rerun()

    # Main submit button
    submitted = st.form_submit_button("Add Sale")

    if submitted:
        count = add_sale_items()
        if count > 0:
            st.success(f"Added {count} item(s).")
            clear_item_inputs()
            st.rerun()
        else:
            st.warning("Nothing added. Enter revenue > $0 for at least one item.")

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
