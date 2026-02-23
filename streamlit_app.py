import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

RPH_TARGET = 300
RPH_MAX_GREEN = 600
REVMIX_TARGET = 0.60
MAX_ITEMS = 10

st.set_page_config(layout="wide")

# -----------------------------
# CSS: make secondary buttons look like plain grey icons (no box)
# -----------------------------
st.markdown(
    """
    <style>
    /* Remove button chrome on SECONDARY buttons (we use secondary for ✕ and + Add line) */
    div[data-testid="stBaseButton-secondary"] > button {
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        padding: 0px 6px !important;
        min-height: 22px !important;
        height: 22px !important;
        line-height: 22px !important;
        color: #9aa0a6 !important;  /* grey */
        font-size: 14px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        width: auto !important;
    }
    div[data-testid="stBaseButton-secondary"] > button:hover {
        background: rgba(255,255,255,0.06) !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stBaseButton-secondary"] > button:focus,
    div[data-testid="stBaseButton-secondary"] > button:focus-visible {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* Tighten vertical spacing a bit */
    div.block-container { padding-top: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Session init
# -----------------------------
if "sales" not in st.session_state:
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())

if "item_count" not in st.session_state:
    st.session_state.item_count = 1

if "mobile_layout" not in st.session_state:
    st.session_state.mobile_layout = False

# Auto daily reset
if st.session_state.current_date != str(date.today()):
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())
    st.session_state.item_count = 1

# Ensure widget keys exist (blank by default)
for idx in range(1, MAX_ITEMS + 1):
    st.session_state.setdefault(f"rev_{idx}", "")          # blank revenue
    st.session_state.setdefault(f"desc_{idx}", "")         # blank description
    st.session_state.setdefault(f"tag_{idx}", "Other")     # single tag

TAGS = ["Health/Wearables", "CarFi", "Other"]

# -----------------------------
# Helpers
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

def parse_money(s: str) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if not s:
        return 0.0
    s = s.replace("$", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0

def _shift_lines_up(start_index: int):
    for j in range(start_index, st.session_state.item_count):
        st.session_state[f"rev_{j}"] = st.session_state.get(f"rev_{j+1}", "")
        st.session_state[f"desc_{j}"] = st.session_state.get(f"desc_{j+1}", "")
        st.session_state[f"tag_{j}"] = st.session_state.get(f"tag_{j+1}", "Other")

    last = st.session_state.item_count
    st.session_state[f"rev_{last}"] = ""
    st.session_state[f"desc_{last}"] = ""
    st.session_state[f"tag_{last}"] = "Other"

def add_line_cb():
    if st.session_state.item_count < MAX_ITEMS:
        st.session_state.item_count += 1

def remove_line_cb(i: int):
    # only lines 2+ removable
    if st.session_state.item_count <= 1 or i < 2 or i > st.session_state.item_count:
        return
    _shift_lines_up(i)
    st.session_state.item_count -= 1

def add_sale_cb():
    added = 0
    for i in range(1, st.session_state.item_count + 1):
        revenue = parse_money(st.session_state.get(f"rev_{i}", ""))
        desc = (st.session_state.get(f"desc_{i}", "") or "").strip()
        tag = st.session_state.get(f"tag_{i}", "Other")

        if revenue > 0:
            st.session_state.sales.append({"revenue": revenue, "desc": desc, "tag": tag})
            added += 1

    # Clear inputs safely (callback context)
    for i in range(1, MAX_ITEMS + 1):
        st.session_state[f"rev_{i}"] = ""
        st.session_state[f"desc_{i}"] = ""
        st.session_state[f"tag_{i}"] = "Other"
    st.session_state.item_count = 1
    st.session_state._last_added = added

# -----------------------------
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")

# Mobile toggle (top, easy to reach on phone)
st.session_state.mobile_layout = st.toggle(
    "Mobile layout (recommended on phone)",
    value=st.session_state.mobile_layout
)

st.header("Add Sale")

if "_last_added" in st.session_state:
    if st.session_state._last_added > 0:
        st.success(f"Added {st.session_state._last_added} item(s).")
    else:
        st.warning("Nothing added. Enter revenue > $0 for at least one item.")
    del st.session_state._last_added

# -----------------------------
# Add Sale Inputs (two layouts)
# -----------------------------
ITEM_PLACEHOLDER = "Item (ex: Apple Watch SE 3, Oura Ring, Car speakers + install)"

if not st.session_state.mobile_layout:
    # Desktop / wide layout: X | Revenue | Item | Tag
    X_COL, REV_COL, DESC_COL, TAG_COL = 0.16, 1.05, 2.85, 1.20

    for i in range(1, st.session_state.item_count + 1):
        c_x, c_rev, c_desc, c_tag = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")

        with c_x:
            if i == 1:
                st.write("")
            else:
                st.button(
                    "✕",
                    key=f"rm_{i}",
                    type="secondary",
                    help=f"Remove line {i}",
                    on_click=remove_line_cb,
                    args=(i,),
                )

        with c_rev:
            st.text_input("Revenue", key=f"rev_{i}", label_visibility="collapsed", placeholder="Revenue")

        with c_desc:
            st.text_input("Item", key=f"desc_{i}", label_visibility="collapsed", placeholder=ITEM_PLACEHOLDER)

        with c_tag:
            st.selectbox(
                "Tag",
                TAGS,
                index=TAGS.index(st.session_state.get(f"tag_{i}", "Other")),
                key=f"tag_{i}",
                label_visibility="collapsed",
            )

    # Add line under Revenue column
    c_x2, c_rev2, c_desc2, c_tag2 = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")
    with c_rev2:
        st.button(
            "＋ Add line",
            key="add_line_btn",
            type="secondary",
            disabled=st.session_state.item_count >= MAX_ITEMS,
            on_click=add_line_cb,
        )

else:
    # Mobile layout: keep X with Revenue so it doesn't float above (Streamlit stacks columns on narrow screens)
    for i in range(1, st.session_state.item_count + 1):
        st.markdown("---") if i > 1 else None

        # Row 1: (optional X) + Revenue
        c_left, c_right = st.columns([0.18, 0.82], vertical_alignment="center")
        with c_left:
            if i == 1:
                st.write("")
            else:
                st.button(
                    "✕",
                    key=f"rm_m_{i}",
                    type="secondary",
                    help=f"Remove line {i}",
                    on_click=remove_line_cb,
                    args=(i,),
                )
        with c_right:
            st.text_input("Revenue", key=f"rev_{i}", label_visibility="collapsed", placeholder="Revenue")

        # Row 2: Item
        st.text_input("Item", key=f"desc_{i}", label_visibility="collapsed", placeholder=ITEM_PLACEHOLDER)

        # Row 3: Tag
        st.selectbox(
            "Tag",
            TAGS,
            index=TAGS.index(st.session_state.get(f"tag_{i}", "Other")),
            key=f"tag_{i}",
            label_visibility="collapsed",
        )

    # Add line button (full width on mobile)
    st.button(
        "＋ Add line",
        key="add_line_btn_mobile",
        type="secondary",
        disabled=st.session_state.item_count >= MAX_ITEMS,
        on_click=add_line_cb,
    )

# Add Sale button
st.button("Add Sale", key="add_sale_btn", type="primary", on_click=add_sale_cb)

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
category_revenue = sum(s["revenue"] for s in st.session_state.sales if s.get("tag") in ["Health/Wearables", "CarFi"])
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
        col1, col2, col3, col4 = st.columns([1.2, 3.2, 1.4, 0.8])
        with col1:
            st.write(f"${sale['revenue']:,.2f}")
        with col2:
            st.write(sale.get("desc", "") or "(No description)")
        with col3:
            st.write(sale.get("tag", "Other"))
        with col4:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.sales.pop(i)
                st.rerun()
else:
    st.info("No sales recorded today.")
