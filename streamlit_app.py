import json
from pathlib import Path

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, date
from zoneinfo import ZoneInfo  # Python 3.9+

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

# Discord-ish palette
BG = "#0f111a"
CARD = "#151926"
TEXT = "#d7dbe6"
MUTED = "#9aa3b2"
MUTED2 = "#7f8796"
ACCENT = "#5865F2"  # discord blurple

# Eastern time
ET = ZoneInfo("America/New_York")

# Local persistence folder
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Schedule persistence
SCHEDULE_FILE = DATA_DIR / "schedule.json"

st.set_page_config(layout="wide")


# -----------------------------
# Styling
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
# Time helpers
# -----------------------------
def now_et() -> datetime:
    return datetime.now(ET)


def et_day_key() -> str:
    return now_et().date().isoformat()


# -----------------------------
# Persistence helpers (Sales)
# -----------------------------
def sales_file(day_key: str) -> Path:
    return DATA_DIR / f"sales_{day_key}.json"


def load_sales(day_key: str) -> list[dict]:
    fp = sales_file(day_key)
    if not fp.exists():
        return []
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_sales(day_key: str, sales: list[dict]) -> None:
    sales_file(day_key).write_text(json.dumps(sales, indent=2), encoding="utf-8")


# -----------------------------
# Persistence helpers (Schedule)
# -----------------------------
def default_schedule() -> dict:
    # Weekly template (Mon..Sun), each day is list of {"start":"HH:MM","end":"HH:MM"}
    return {
        "version": 1,
        "timezone": "America/New_York",
        "weekly": {
            "Mon": [],
            "Tue": [],
            "Wed": [],
            "Thu": [],
            "Fri": [],
            "Sat": [],
            "Sun": [],
        },
    }


def load_schedule() -> dict:
    if not SCHEDULE_FILE.exists():
        return default_schedule()
    try:
        data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return default_schedule()
        # Ensure keys exist
        out = default_schedule()
        out.update({k: data.get(k, out[k]) for k in out.keys()})
        if not isinstance(out.get("weekly"), dict):
            out["weekly"] = default_schedule()["weekly"]
        # Ensure all weekdays present
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            out["weekly"].setdefault(d, [])
            if not isinstance(out["weekly"][d], list):
                out["weekly"][d] = []
        return out
    except Exception:
        return default_schedule()


def save_schedule(schedule: dict) -> None:
    SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2), encoding="utf-8")


# -----------------------------
# Session State (IMPORTANT: no stat resets)
# -----------------------------
def ss_init():
    ss = st.session_state
    today = et_day_key()

    # One-time init guard so we don't reload/overwrite on every rerun
    ss.setdefault("_initialized", False)

    ss.setdefault("current_date", today)
    ss.setdefault("sales", [])
    ss.setdefault("item_count", 1)
    ss.setdefault("_last_added", None)

    # Inputs
    for i in range(1, MAX_ITEMS + 1):
        ss.setdefault(f"rev_{i}", "")
        ss.setdefault(f"desc_{i}", "")
        ss.setdefault(f"tag_{i}", DEFAULT_TAG)

    # If first load of the session: load today's sales from disk once
    if not ss._initialized:
        ss.current_date = today
        ss.sales = load_sales(today)
        ss.item_count = 1
        ss._initialized = True

    # If day changed (ET), roll to new day and load that day from disk
    if ss.current_date != today:
        ss.current_date = today
        ss.sales = load_sales(today)
        ss.item_count = 1


ss_init()

# Always update last refresh each rerun (does NOT touch sales)
st.session_state["last_refresh_et"] = now_et()


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
    if st.session_state.item_count < MAX_ITEMS:
        st.session_state.item_count += 1


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
                "ts": now_et().strftime("%H:%M:%S"),
            }
        )
        added += 1

    # Persist immediately
    save_sales(ss.current_date, ss.sales)

    clear_items()
    ss._last_added = added


def delete_sale(idx: int):
    ss = st.session_state
    if 0 <= idx < len(ss.sales):
        ss.sales.pop(idx)
        save_sales(ss.current_date, ss.sales)


# -----------------------------
# Schedule -> hours worked so far today
# -----------------------------
def parse_hhmm(hhmm: str) -> tuple[int, int]:
    hhmm = (hhmm or "").strip()
    h, m = hhmm.split(":")
    return int(h), int(m)


def weekday_key(d: date) -> str:
    return d.strftime("%a")  # Mon, Tue, ...


def scheduled_hours_so_far(schedule: dict, now: datetime) -> float:
    weekly = (schedule or {}).get("weekly", {}) or {}
    day = weekday_key(now.date())
    shifts = weekly.get(day, []) or []

    total_seconds = 0.0
    for sh in shifts:
        try:
            sh_start_h, sh_start_m = parse_hhmm(sh.get("start"))
            sh_end_h, sh_end_m = parse_hhmm(sh.get("end"))
        except Exception:
            continue

        start_dt = now.replace(hour=sh_start_h, minute=sh_start_m, second=0, microsecond=0)
        end_dt = now.replace(hour=sh_end_h, minute=sh_end_m, second=0, microsecond=0)

        # Overnight shift support (end <= start means next day)
        if end_dt <= start_dt:
            end_dt = end_dt.replace(day=end_dt.day + 1)

        # Not started yet
        if now <= start_dt:
            continue

        worked_until = min(now, end_dt)
        total_seconds += max((worked_until - start_dt).total_seconds(), 0.0)

    return total_seconds / 3600.0


# -----------------------------
# UI
# -----------------------------
st.title("E-Transport Sales Tracker")

st.caption(
    f"Date (ET): **{st.session_state.current_date}**  |  "
    f"Last refresh: **{st.session_state['last_refresh_et'].strftime('%I:%M:%S %p ET')}**"
)

# Schedule popover (📅)
schedule = load_schedule()
with st.popover("📅 Schedule"):
    st.write(
        "Upload a **schedule.json** (weekly template). It will persist until you replace or clear it.\n\n"
        "Format example:\n"
        "- weekly -> Mon..Sun -> list of shifts\n"
        "- shift: {\"start\":\"HH:MM\",\"end\":\"HH:MM\"}"
    )

    up = st.file_uploader("Upload schedule.json", type=["json"], key="schedule_uploader")
    if up is not None:
        try:
            new_schedule = json.loads(up.read().decode("utf-8"))
            # Light validation/coercion
            if not isinstance(new_schedule, dict):
                raise ValueError("Top-level JSON must be an object/dict.")
            if "weekly" not in new_schedule or not isinstance(new_schedule["weekly"], dict):
                raise ValueError("Missing or invalid 'weekly' object.")
            # Ensure weekdays exist
            for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                new_schedule["weekly"].setdefault(d, [])
                if not isinstance(new_schedule["weekly"][d], list):
                    new_schedule["weekly"][d] = []
            new_schedule.setdefault("version", 1)
            new_schedule.setdefault("timezone", "America/New_York")

            save_schedule(new_schedule)
            schedule = new_schedule
            st.success("Schedule saved ✅")
        except Exception as e:
            st.error(f"Invalid schedule JSON: {e}")

    if st.button("Clear saved schedule", type="secondary"):
        save_schedule(default_schedule())
        schedule = load_schedule()
        st.success("Schedule cleared.")

    # Quick preview
    weekly = schedule.get("weekly", {})
    today_key = weekday_key(now_et().date())
    st.write(f"**Today ({today_key}) shifts:**")
    today_shifts = weekly.get(today_key, [])
    if today_shifts:
        for sh in today_shifts:
            st.write(f"- {sh.get('start','??:??')} → {sh.get('end','??:??')}")
    else:
        st.caption("No shifts for today.")


st.header("Add Sale")

if st.session_state._last_added is not None:
    n = st.session_state._last_added
    st.session_state._last_added = None
    if n > 0:
        st.success(f"Added {n} item(s).")
    else:
        st.warning("Nothing added. Enter revenue > $0 for at least one item.")

# Compact row layout: [X][Revenue][Item][Tag]
X_COL, REV_COL, DESC_COL, TAG_COL = 0.16, 1.05, 2.85, 1.20

for i in range(1, st.session_state.item_count + 1):
    c_x, c_rev, c_desc, c_tag = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")

    with c_x:
        if i == 1:
            st.write("")
        else:
            st.button("✕", key=f"rm_{i}", type="secondary", on_click=remove_item, args=(i,))

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

_, c_add, _, _ = st.columns([X_COL, REV_COL, DESC_COL, TAG_COL], vertical_alignment="center")
with c_add:
    st.button("＋ Add item", type="secondary", on_click=add_item, disabled=st.session_state.item_count >= MAX_ITEMS)

st.button("Add Sale", type="primary", on_click=add_sale)

# -----------------------------
# Metrics (auto hours from schedule)
# -----------------------------
st.header("Today's Performance")

total_revenue = sum(s["revenue"] for s in st.session_state.sales)
category_revenue = sum(s["revenue"] for s in st.session_state.sales if s.get("tag") in ("Health/Wearables", "CarFi"))
other_revenue = total_revenue - category_revenue

now = now_et()
auto_hours = max(scheduled_hours_so_far(schedule, now), 0.0)

st.session_state.setdefault("use_manual_hours", False)
use_manual = st.toggle("Manually override hours worked", value=st.session_state.use_manual_hours)
st.session_state.use_manual_hours = use_manual

if use_manual:
    st.session_state.setdefault("manual_hours_worked", float(max(auto_hours, 1.0)))
    hours_worked = st.number_input(
        "Hours Worked Today",
        min_value=0.0,
        max_value=24.0,
        value=float(st.session_state.manual_hours_worked),
        step=0.25,
    )
    st.session_state.manual_hours_worked = float(hours_worked)
else:
    hours_worked = auto_hours
    st.caption(f"Auto hours (from schedule + current time): **{hours_worked:.2f} hrs**")

rph = (total_revenue / hours_worked) if hours_worked and hours_worked > 0 else 0.0
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
        <div><div style="color:{MUTED2}; font-size:12px;">Hours Worked</div>
             <div style="color:{TEXT}; font-size:22px; font-weight:800;">{hours_worked:.2f}</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Pie Chart
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
    # RPH target based on computed hours_worked (auto or manual)
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
        col1, col2, col3, col4, col5 = st.columns([1.0, 1.2, 3.2, 1.4, 0.8])
        with col1:
            st.write(s.get("ts", "--:--:--"))
        with col2:
            st.write(f"${s['revenue']:,.2f}")
        with col3:
            st.write(s.get("desc") or "(No description)")
        with col4:
            st.write(s.get("tag", DEFAULT_TAG))
        with col5:
            if st.button("❌", key=f"del_{i}"):
                delete_sale(i)
                st.rerun()
else:
    st.info("No sales recorded today.")
