import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

RPH_TARGET = 300
RPH_MAX_GREEN = 600
REVMIX_TARGET = 0.60

st.set_page_config(layout="wide")

# -----------------------------
# Initialize Session State
# -----------------------------
if "sales" not in st.session_state:
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())

# Auto daily reset
if st.session_state.current_date != str(date.today()):
    st.session_state.sales = []
    st.session_state.current_date = str(date.today())

# -----------------------------
# RPH Color Logic
# -----------------------------
def get_rph_color(rph):
    if rph >= RPH_TARGET:
        scale = min((rph - RPH_TARGET) / (RPH_MAX_GREEN - RPH_TARGET), 1)
        green_value = int(150 + (105 * scale))
        return f"rgb(0,{green_value},0)"
    else:
        scale = min((RPH_TARGET - rph) / RPH_TARGET, 1)
        red_value = int(150 + (105 * scale))
        return f"rgb({red_value},0,0)"

# -----------------------------
# Title
# -----------------------------
st.title("E-Transport Sales Tracker")

# -----------------------------
# Add Sale Section
# -----------------------------
st.header("Add Sale")

col1, col2 = st.columns(2)

with col1:
    revenue = st.number_input("Revenue ($)", min_value=0.0, step=1.0)

with col2:
    categories = st.multiselect(
        "Category Tags (Basket Attach Supported)",
        ["Health/Wearables", "CarFi", "Other"],
        default=[]
    )

if st.button("Add Sale"):
    if revenue > 0:
        st.session_state.sales.append({
            "revenue": revenue,
            "categories": categories
        })
        st.success("Sale Added")
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
# Sales History Section
# -----------------------------
st.header("Sales History")

if st.session_state.sales:
    for i, sale in enumerate(st.session_state.sales):
        col1, col2, col3 = st.columns([4,3,1])
        with col1:
            st.write(f"${sale['revenue']:,.2f}")
        with col2:
            st.write(", ".join(sale["categories"]))
        with col3:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.sales.pop(i)
                st.rerun()
else:
    st.info("No sales recorded today.")
    
