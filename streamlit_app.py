import streamlit as st
import pandas as pd
import os
from datetime import date
import matplotlib.pyplot as plt

FILE_NAME = "sales_data.csv"
RPH_TARGET = 300
REVMIX_TARGET = 0.60

# -----------------------------
# Initialize Data
# -----------------------------
def load_data():
    today = str(date.today())

    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)

        # Auto daily reset
        if df.empty or df.iloc[0]["date"] != today:
            df = pd.DataFrame(columns=["date", "category", "revenue"])
            df.to_csv(FILE_NAME, index=False)
    else:
        df = pd.DataFrame(columns=["date", "category", "revenue"])
        df.to_csv(FILE_NAME, index=False)

    return df


def save_sale(category, revenue):
    df = pd.read_csv(FILE_NAME)
    new_row = {
        "date": str(date.today()),
        "category": category,
        "revenue": revenue,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("E-Transport Sales Tracker")

df = load_data()

st.header("Add Sale")

col1, col2 = st.columns(2)

with col1:
    revenue = st.number_input("Revenue ($)", min_value=0.0, step=1.0)

with col2:
    category = st.selectbox(
        "Category",
        ["Category (Health/Wearables + CarFi)", "Other"]
    )

if st.button("Add Sale"):
    if revenue > 0:
        cat_value = "Category" if "Category" in category else "Other"
        save_sale(cat_value, revenue)
        st.success("Sale Added")
        st.rerun()

# -----------------------------
# Metrics Section
# -----------------------------
st.header("Today's Performance")

hours_worked = st.number_input("Hours Worked Today", min_value=0.1, step=0.5)

if not df.empty:
    total_revenue = df["revenue"].sum()
    category_revenue = df[df["category"] == "Category"]["revenue"].sum()

    rph = total_revenue / hours_worked
    revmix = category_revenue / total_revenue if total_revenue > 0 else 0

    st.subheader("Key Metrics")
    st.write(f"Total Revenue: ${total_revenue:,.2f}")
    st.write(f"Category Revenue: ${category_revenue:,.2f}")
    st.write(f"Revenue Per Hour: ${rph:,.2f}")
    st.write(f"Category Revmix: {revmix*100:.2f}%")

    # Progress Bars
    st.subheader("Progress")

    st.write("RPH Progress")
    st.progress(min(rph / RPH_TARGET, 1.0))

    st.write("Revmix Progress")
    st.progress(min(revmix / REVMIX_TARGET, 1.0))

    # -----------------------------
    # Pie Chart
    # -----------------------------
    st.subheader("Revenue Breakdown")

    if total_revenue > 0:
        fig = plt.figure()
        plt.pie(
            [category_revenue, total_revenue - category_revenue],
            labels=["Category", "Other"],
            autopct="%1.1f%%"
        )
        plt.title("Revenue Mix")
        st.pyplot(fig)

    # -----------------------------
    # What Do I Need?
    # -----------------------------
    st.subheader("What Do I Need to Hit Target?")

    # RPH shortfall
    required_total = RPH_TARGET * hours_worked
    additional_needed = max(required_total - total_revenue, 0)

    if additional_needed > 0:
        st.write(f"You need **${additional_needed:,.2f} more total revenue** to hit $300 RPH.")
    else:
        st.success("RPH Target Hit ✅")

    # Revmix shortfall (category revenue needed)
    if total_revenue > 0:
        required_category = REVMIX_TARGET * (total_revenue + additional_needed)
        category_shortfall = max(required_category - category_revenue, 0)

        if category_shortfall > 0:
            st.write(f"You need **${category_shortfall:,.2f} more in Category sales** to reach 60% revmix.")
        else:
            st.success("Revmix Target Hit ✅")

else:
    st.info("No sales recorded yet today.")
