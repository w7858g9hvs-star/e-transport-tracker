import json
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, date
from zoneinfo import ZoneInfo

# -----------------------------
# Config
# -----------------------------
RPH_TARGET = 300
REVMIX_TARGET = 0.60
SAFE_MIX = 0.70
MAX_ITEMS = 10

TAGS = ["Health/Wearables", "CarFi", "Other"]
DEFAULT_TAG = "Health/Wearables"

ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(layout="wide")

# -----------------------------
# Time
# -----------------------------
def now_et():
    return datetime.now(ET)

st.session_state["last_refresh_et"] = now_et()

# -----------------------------
# Persistence
# -----------------------------
def et_day_key():
    return now_et().date().isoformat()

def sales_file(day_key):
    return DATA_DIR / f"sales_{day_key}.json"

def load_sales(day_key):
    fp = sales_file(day_key)
    if not fp.exists():
        return []
    return json.loads(fp.read_text())

def save_sales(day_key, sales):
    sales_file(day_key).write_text(json.dumps(sales, indent=2))

# -----------------------------
# Session Init
# -----------------------------
def ss_init():
    today = et_day_key()
    ss = st.session_state

    ss.setdefault("current_date", today)
    ss.setdefault("sales", load_sales(today))
    ss.setdefault("item_count", 1)
    ss.setdefault("_last_added", None)

    for i in range(1, MAX_ITEMS + 1):
        ss.setdefault(f"rev_{i}", "")
        ss.setdefault(f"desc_{i}", "")
        ss.setdefault(f"tag_{i}", DEFAULT_TAG)

ss_init()

# -----------------------------
# Helpers
# -----------------------------
def parse_money(s):
    s = (s or "").replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def add_item():
    if st.session_state.item_count < MAX_ITEMS:
        st.session_state.item_count += 1

def clear_items():
    for i in range(1, MAX_ITEMS + 1):
        st.session_state[f"rev_{i}"] = ""
        st.session_state[f"desc_{i}"] = ""
        st.session_state[f"tag_{i}"] = DEFAULT_TAG
    st.session_state.item_count = 1

def add_sale():
    added = 0
    for i in range(1, st.session_state.item_count + 1):
        revenue = parse_money(st.session_state.get(f"rev_{i}", ""))
        if revenue <= 0:
            continue

        st.session_state.sales.append({
            "revenue": revenue,
            "desc": st.session_state.get(f"desc_{i}", ""),
            "tag": st.session_state.get(f"tag_{i}", DEFAULT_TAG),
            "ts": now_et().strftime("%H:%M:%S")
        })
        added += 1

    save_sales(st.session_state.current_date, st.session_state.sales)
    clear_items()
    st.session_state._last_added = added

def delete_sale(idx):
    st.session_state.sales.pop(idx)
    save_sales(st.session_state.current_date, st.session_state.sales)

# -----------------------------
# UI Header
# -----------------------------
st.title("E-Transport Sales Tracker")

col_l, col_r = st.columns([0.85, 0.15])
with col_l:
    st.caption(
        f"Date (ET): **{st.session_state.current_date}** | "
        f"Last refresh: **{st.session_state['last_refresh_et'].strftime('%I:%M:%S %p ET')}**"
    )
with col_r:
    if st.button("↻", help="Refresh"):
        st.rerun()

# -----------------------------
# Add Sale
# -----------------------------
st.header("Add Sale")

for i in range(1, st.session_state.item_count + 1):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.text_input("Revenue", key=f"rev_{i}", label_visibility="collapsed", placeholder="Revenue")
    with c2:
        st.text_input("Item", key=f"desc_{i}", label_visibility="collapsed", placeholder="Description")
    with c3:
        st.selectbox("Tag", TAGS, key=f"tag_{i}", label_visibility="collapsed")

st.button("＋ Add item", on_click=add_item)
st.button("Add Sale", on_click=add_sale)

# -----------------------------
# Metrics
# -----------------------------
st.header("Today's Performance")

hours_worked = st.number_input("Hours Worked Today", 0.0, 24.0, 8.0, 0.25)

total_revenue = sum(s["revenue"] for s in st.session_state.sales)
category_revenue = sum(s["revenue"] for s in st.session_state.sales if s["tag"] in ("Health/Wearables", "CarFi"))
other_revenue = total_revenue - category_revenue

rph = total_revenue / hours_worked if hours_worked else 0
revmix = category_revenue / total_revenue if total_revenue else 0

st.metric("Total Revenue", f"${total_revenue:,.2f}")
st.metric("RPH", f"${rph:,.2f}")
st.metric("Category Revenue", f"${category_revenue:,.2f}")
st.metric("Revmix", f"{revmix*100:.2f}%")

# -----------------------------
# Targets + 70% Headroom
# -----------------------------
st.subheader("What Do I Need to Hit Target?")

if total_revenue > 0:

    # RPH target
    required_total = RPH_TARGET * hours_worked
    additional_needed = max(required_total - total_revenue, 0)

    if additional_needed > 0:
        st.write(f"You need **${additional_needed:,.2f} more total revenue** to hit $300 RPH.")
    else:
        st.success("RPH Target Hit ✅")

    # 60% mix
    required_category = REVMIX_TARGET * total_revenue
    category_shortfall = max(required_category - category_revenue, 0)

    if category_shortfall > 0:
        st.write(f"You need **${category_shortfall:,.2f} more Category** to reach 60% mix.")
    else:
        st.success("60% Mix Target Hit ✅")

    st.divider()

    # 70% safe mix headroom
    max_total_at_safe = category_revenue / SAFE_MIX
    other_headroom_70 = max(max_total_at_safe - total_revenue, 0)

    required_category_safe_now = SAFE_MIX * total_revenue
    safe_shortfall = max(required_category_safe_now - category_revenue, 0)

    st.markdown("### 🔥 70% Safe Mix Mode")

    if safe_shortfall > 0:
        st.warning(
            f"You're below 70%. Add **${safe_shortfall:,.2f} Category** (no Other) to get back to safe zone."
        )
    else:
        st.success(
            f"You can sell **${other_headroom_70:,.2f} more in Other** and still stay ≥70%."
        )

    st.caption(
        f"Max total at 70% mix: **${max_total_at_safe:,.2f}**"
    )

else:
    st.info("No sales recorded yet.")

# -----------------------------
# Sales History
# -----------------------------
st.header("Sales History")

for i, s in enumerate(st.session_state.sales):
    c1, c2, c3, c4 = st.columns([1, 1, 3, 1])
    c1.write(s["ts"])
    c2.write(f"${s['revenue']:,.2f}")
    c3.write(s["desc"])
    c4.write(s["tag"])
    if st.button("❌", key=f"del_{i}"):
        delete_sale(i)
        st.rerun()
