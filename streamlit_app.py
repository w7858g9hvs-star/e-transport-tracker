import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

# -----------------------------
# Config
# -----------------------------
RPH_TARGET = 300
RPH_MAX_GREEN = 600
REVMIX_TARGET = 0.60
MAX_ITEMS = 10

TAGS = ["Health/Wearables", "CarFi", "Other"]
DEFAULT_TAG = "Health/Wearables"
ITEM_PLACEHOLDER = "Item (ex: Apple Watch SE 3, Oura Ring, Car speakers + install)"

# Discord-ish palette (used for chart + cards)
BG = "#0f111a"
CARD = "#151926"
BORDER = (1, 1, 1, 0.08)
TEXT = "#d7dbe6"
MUTED = "#9aa3b2"
MUTED2 = "#7f8796"
ACCENT = "#5865F2"  # discord blurple

st.set_page_config(layout="wide")

# -----------------------------
# Discord-ish dark styling (softer text, muted UI)
# -----------------------------
st.markdown(
    f"""
    <style>
    :root {{
      --bg: {BG};
      --card: {CARD};
      --border: rgba(255,255,255,0.08);
      --text: {TEXT};
      --muted: {MUTED};
      --muted2: {MUTED2};
      --accent: {ACCENT};
    }}

    .stApp {{ background: var(--bg); color: var(--text); }}
    h1,h2,h3,h4,h5,h6, p, label {{ color: var(--text) !important; }}
    .stCaption, small {{ color: var(--muted) !important; }}

    div.block-container {{ padding-top: 1.5rem; max-width: 1100px; }}

    /* Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {{
      background: var(--card) !important;
      border: 1px solid var(--border) !important;
      color: var(--text) !important;
      border-radius: 12px !important;
    }}
    input, textarea {{ color: var(--text) !important; caret-color: var(--text) !important; }}
    input::placeholder, textarea::placeholder {{ color: var(--muted2) !important; }}
    div[data-baseweb="select"] span {{ color: var(--text) !important; }}

    .stTextInput, .stSelectbox {{ margin-top: -6px; }}

    /* Secondary buttons (✕ and + Add item): small, muted, no box */
    div[data-testid="stBaseButton-secondary"] > button {{
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: var(--muted) !important;

      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;

      padding: 0px 6px !important;
      min-height: 22px !important;
      height: 22px !important;
      line-height: 22px !important;

      font-size: 14px !important;
      font-weight: 700 !important;
      border-radius: 10px !important;
      width: auto !important;
    }}
    div[data-testid="stBaseButton-secondary"] > button:hover {{
      background: rgba(255,255,255,0.06) !important;
      color: var(--text) !important;
    }}
    div[data-testid="stBaseButton-secondary"] > button:focus,
    div[data-testid="stBaseButton-secondary"] > button:focus-visible {{
      outline: none !important;
      box-shadow: none !important;
      border: none !important;
    }}

    /* Primary button: blurple */
    div[data-testid="stBaseButton-primary"] > button {{
      background: var(--accent) !important;
      border: 1px solid rgba(255,255,255,0.10) !important;
      color: #fff !important;
      border-radius: 12px !important;
      padding: 0.55rem 1rem !important;
      font-weight: 700 !important;
    }}
    div[data-testid="stBaseButton-primary"] > button:hover {{
      filter: brightness(1.05);
    }}

    hr {{ border-color: var(--border) !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Session State
# -----------------------------
def ss_init():
    ss = st.session_state
    today = str(date.today())

    if "current_date" not in ss:
        ss.current_date = today
        ss.sales = []
        ss.item_count = 1

    if ss.current_date != today:
        ss.current_date = today
        ss.sales = []
        ss.item_count = 1

    for i in range(1, MAX_ITEMS + 1):
        ss.setdefault(f"rev_{i}", "")
        ss.setdefault(f"desc_{i}", "")
        ss.setdefault(f"tag_{i}", DEFAULT_TAG)

ss_init()

# -----------------------------
# Helpers
# -----------------------------
def parse_money(s: str) -> float:
    s = (s or "").strip().replace("$", "").replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

def rph_color(rph: float) -> str:
    if rph >= RPH_TARGET:
        scale = min((rph - RPH_TARGET) / (RPH_MAX_GREEN - RPH_TARGET), 1.0)
        g = int(150 + 105 * scale)
        return f"rgb(0,{g},0)"
    scale = min((RPH_TARGET - rph) / RPH_TARGET, 1.0)
    r = int(150 + 105 * scale)
    return f"rgb({r},0,0)"

def shift_up(start_idx: int):
    ss = st.session_state
    for j in range(start_idx, ss.item_count):
        ss[f"rev_{j}"] = ss.get(f"rev_{j+1}", "")
        ss[f"desc_{j}"] = ss.get(f"desc_{j+1}", "")
        ss[f"tag_{j}"] = ss.get(f"tag_{j+1}", DEFAULT_TAG)

    last = ss.item_count
    ss[f"rev_{last}"] = ""
    ss[f"desc_{last}"] = ""
    ss[f"tag_{last}"] = DEFAULT_TAG

def add_item():
    ss = st.session_state
    if ss.item_count < MAX_ITEMS:
        ss.item_count += 1

def remove_item(i: int):
    ss = st.session_state
    if ss.item_count <= 1 or i < 2 or i > ss.item_count:
        return
    shift_up(i)
    ss.item_count -= 1

def clear_items():
    ss = st.session_state
    for i in range(1, MAX_ITEMS + 1):
        ss[f"rev_{i}"] = ""
        ss[f"desc_{i}"] = ""
        ss[f"tag_{i}"] = DEFAULT_TAG
    ss.item_count = 1

def add_sale():
    ss = st.session_state
    added = 0
    for i in range(1, ss.item_count + 1):
        revenue = parse_money(ss.get(f"rev_{i}", ""))
        if revenue <= 0:
            continue
        ss.sales.append(
            {
                "revenue": revenue,
                "desc": (ss.get(f"desc_{i}", "") or "").strip(),
                "tag": ss.get(f"tag_{i}", DEFAULT_TAG),
            }
        )
        added += 1
    clear_items()
    ss._last_added = added

# -----------------------------
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")
st.header("Add Sale")

if "_last_added" in st.session_state:
    n = st.session_state._last_added
    if n > 0:
        st.success(f"Added {n} item(s).")
    else:
        st.warning("Nothing added. Enter revenue > $0 for at least one item.")
    del st.session_state._last_added

# Compact row layout: [X][Revenue][Item][Tag]
X_COL, REV_COL, DESC_COL, TAG_COL = 0.16, 1.05, 2.85, 1.20

for i in range(1, st.session_state.item_count + 1):
    c_x, c_rev, c_desc, c_tag = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")

    with c_x:
        if i == 1:
            st.write("")
        else:
            st.button("✕", key=f"rm_{i}", type="secondary", on_click=remove_item, args=(i,), help=f"Remove item {i}")

    with c_rev:
        st.text_input("Revenue", key=f"rev_{i}", label_visibility="collapsed", placeholder="Revenue")

    with c_desc:
        st.text_input("Item", key=f"desc_{i}", label_visibility="collapsed", placeholder=ITEM_PLACEHOLDER)

    with c_tag:
        st.selectbox(
            "Tag",
            TAGS,
            index=TAGS.index(st.session_state.get(f"tag_{i}", DEFAULT_TAG)),
            key=f"tag_{i}",
            label_visibility="collapsed",
        )

# Add item under Revenue column
_, c_add, _, _ = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")
with c_add:
    st.button(
        "＋ Add item",
        key="add_item_btn",
        type="secondary",
        disabled=st.session_state.item_count >= MAX_ITEMS,
        on_click=add_item,
    )

st.button("Add Sale", key="add_sale_btn", type="primary", on_click=add_sale)

# -----------------------------
# Metrics
# -----------------------------
st.header("Today's Performance")
hours_worked = st.number_input("Hours Worked Today", min_value=1.0, max_value=16.0, value=8.0, step=0.5)

total_revenue = sum(s["revenue"] for s in st.session_state.sales)
category_revenue = sum(s["revenue"] for s in st.session_state.sales if s.get("tag") in ("Health/Wearables", "CarFi"))
other_revenue = total_revenue - category_revenue

rph = total_revenue / hours_worked if hours_worked else 0.0
revmix = (category_revenue / total_revenue) if total_revenue > 0 else 0.0

st.markdown(
    f"""
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
                padding: 14px 16px; border-radius: 14px;">
      <div style="color: {MUTED}; font-weight:600; letter-spacing:0.2px;">Today</div>
      <div style="display:flex; gap:20px; flex-wrap:wrap; margin-top:8px;">
        <div><div style="color:{MUTED2}; font-size:12px;">Total Revenue</div>
             <div style="color:{TEXT}; font-size:22px; font-weight:800;">${total_revenue:,.2f}</div></div>
        <div><div style="color:{MUTED2}; font-size:12px;">RPH</div>
             <div style="color:{rph_color(rph)}; font-size:22px; font-weight:900;">${rph:,.2f}</div></div>
        <div><div style="color:{MUTED2}; font-size:12px;">Category Revenue</div>
             <div style="color:{TEXT}; font-size:22px; font-weight:800;">${category_revenue:,.2f}</div></div>
        <div><div style="color:{MUTED2}; font-size:12px;">Revmix</div>
             <div style="color:{TEXT}; font-size:22px; font-weight:800;">{revmix*100:.2f}%</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Pie Chart (dark-mode matching)
# -----------------------------
st.subheader("Revenue Breakdown")

if total_revenue > 0:
    fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=130)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    wedges, texts, autotexts = ax.pie(
        [category_revenue, other_revenue],
        labels=["Category", "Other"],
        autopct="%1.1f%%",
        textprops={"color": MUTED, "fontsize": 10},
        wedgeprops={"linewidth": 1, "edgecolor": (1, 1, 1, 0.10)},
    )

    for t in autotexts:
        t.set_color(TEXT)
        t.set_fontsize(10)
        t.set_fontweight("bold")

    ax.set_title("Category vs Other Revenue", color=TEXT, fontsize=12, fontweight="bold", pad=10)

    st.pyplot(fig, transparent=True)
else:
    st.info("No revenue yet to display.")

# -----------------------------
# Targets
# -----------------------------
st.subheader("What Do I Need to Hit Target?")

if total_revenue <= 0:
    st.info("No sales recorded today.")
else:
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
    for i, s in enumerate(st.session_state.sales):
        col1, col2, col3, col4 = st.columns([1.2, 3.2, 1.4, 0.8])
        with col1:
            st.write(f"${s['revenue']:,.2f}")
        with col2:
            st.write(s.get("desc") or "(No description)")
        with col3:
            st.write(s.get("tag", DEFAULT_TAG))
        with col4:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.sales.pop(i)
                st.rerun()
else:
    st.info("No sales recorded today.")
