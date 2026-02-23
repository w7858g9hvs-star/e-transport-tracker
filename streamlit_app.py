import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

RPH_TARGET = 300
RPH_MAX_GREEN = 600
REVMIX_TARGET = 0.60
MAX_ITEMS = 10

st.set_page_config(layout="wide")

# -----------------------------
# Session init
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

# Ensure widget keys exist
for idx in range(1, MAX_ITEMS + 1):
    st.session_state.setdefault(f"rev_{idx}", 0.0)
    st.session_state.setdefault(f"tags_{idx}", [])

# -----------------------------
# Helpers
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

def _shift_lines_up(start_index: int):
    """Shift rev/tags from start_index+1..item_count up by one."""
    for j in range(start_index, st.session_state.item_count):
        st.session_state[f"rev_{j}"] = float(st.session_state.get(f"rev_{j+1}", 0.0) or 0.0)
        st.session_state[f"tags_{j}"] = list(st.session_state.get(f"tags_{j+1}", []) or [])

    last = st.session_state.item_count
    st.session_state[f"rev_{last}"] = 0.0
    st.session_state[f"tags_{last}"] = []

def add_line_cb():
    if st.session_state.item_count < MAX_ITEMS:
        st.session_state.item_count += 1

def remove_line_cb(i: int):
    if st.session_state.item_count <= 1 or i > st.session_state.item_count:
        return
    _shift_lines_up(i)
    st.session_state.item_count -= 1

def add_sale_cb():
    added = 0
    for i in range(1, st.session_state.item_count + 1):
        revenue = float(st.session_state.get(f"rev_{i}", 0.0) or 0.0)
        tags = st.session_state.get(f"tags_{i}", []) or []
        if revenue > 0:
            st.session_state.sales.append({"revenue": revenue, "categories": tags})
            added += 1

    # Clear inputs safely (callback context)
    for i in range(1, MAX_ITEMS + 1):
        st.session_state[f"rev_{i}"] = 0.0
        st.session_state[f"tags_{i}"] = []
    st.session_state.item_count = 1

    # Store a toast message
    st.session_state._last_added = added

# -----------------------------
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")

# -----------------------------
# Add Sale (compact progressive list)
# -----------------------------
st.header("Add Sale")

# Show message from last Add Sale
if "_last_added" in st.session_state:
    if st.session_state._last_added > 0:
        st.success(f"Added {st.session_state._last_added} item(s).")
    else:
        st.warning("Nothing added. Enter revenue > $0 for at least one item.")
    del st.session_state._last_added

# Layout widths: [X] [Revenue] [Tags]
X_COL = 0.45
REV_COL = 1.25
TAGS_COL = 3.3

for i in range(1, st.session_state.item_count + 1):
    c_x, c_rev, c_tags = st.columns([X_COL, REV_COL, TAGS_COL], vertical_alignment="center")

    with c_x:
        if i == 1:
            st.write("")  # keep alignment
        else:
            st.button(
                "❌",
                key=f"rm_btn_{i}",
                help=f"Remove line {i}",
                on_click=remove_line_cb,
                args=(i,),
            )

    with c_rev:
        st.number_input(
            "Revenue ($)",
            min_value=0.0,
            step=1.0,
            key=f"rev_{i}",
            label_visibility="collapsed",
            placeholder="Revenue",
        )

    with c_tags:
        st.multiselect(
            "Category Tags",
            ["Health/Wearables", "CarFi", "Other"],
            key=f"tags_{i}",
            label_visibility="collapsed",
            placeholder="Category tags",
        )

# Plus row: put + under Revenue column (directly beneath the input)
c_x2, c_rev2, c_tags2 = st.columns([X_COL, REV_COL, TAGS_COL], vertical_alignment="center")
with c_rev2:
    st.button(
        "➕ Add line",
        key="add_line_btn",
        help=f"Add another item (max {MAX_ITEMS})",
        on_click=add_line_cb,
        disabled=st.session_state.item_count >= MAX_ITEMS,
    )

# Add Sale button (outside any form = no session_state restrictions)
st.button("Add Sale", key="add_sale_btn", on_click=add_sale_cb)

# -----------------------------
# Metrics
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
