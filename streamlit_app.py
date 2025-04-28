import streamlit as st
import sqlite3
import random
import time
from datetime import date, datetime, time as dtime

# ----------------------------------------------------------------------------
# ▶ Page configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Plant-Based Assignment Tracker",
    page_icon="🌿",
    layout="wide"
)

# ----------------------------------------------------------------------------
# ▶ Custom CSS
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #228B22;
            color: #FFFFFF;
            border: 4px solid #FFFFFF;
            padding: 10px;
        }
        h1 {
            font-size: 80px;
            text-align: center;
            margin-bottom: 20px;
        }
        .stats-left {
            position: fixed;
            top: 20px;
            left: 30px;
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        }
        .card {
            padding: 16px;
            border: 2px solid #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            text-align: center;
            margin-bottom: 16px;
        }
        .roll-btn-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        hr {
            border-top: 2px solid #FFFFFF;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------------------------------------
# ▶ Database setup
# ----------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
# Migrate columns
for col, props in [('rarity', "TEXT NOT NULL DEFAULT ''"), ('cost', "INTEGER NOT NULL DEFAULT 0")]:
    try:
        c.execute(f"ALTER TABLE plants ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT NOT NULL,
    assignment TEXT NOT NULL,
    type TEXT NOT NULL,
    due_date TEXT NOT NULL,
    due_time TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    awarded_at TEXT NOT NULL,
    rarity TEXT NOT NULL DEFAULT '',
    cost INTEGER NOT NULL DEFAULT 0
)
""")
conn.commit()

# ----------------------------------------------------------------------------
# ▶ Configuration
# ----------------------------------------------------------------------------
POINTS_MAP = {"Homework":1, "Quiz":2, "Paper":3, "Project":4, "Test":4, "Mid-Term":5, "Final":10}
RARITY_CATS = ["Common","Rare","Epic","Legendary"]
RARITY_WEIGHTS = [0.5,0.3,0.15,0.05]
ROLL_COST = 5
COLORS = {"Common":"#FFFFFF","Rare":"#ADD8E6","Epic":"#D8BFD8","Legendary":"#FFFFE0"}

# ----------------------------------------------------------------------------
# ▶ Helper functions
# ----------------------------------------------------------------------------
def get_balance():
    return sum(POINTS_MAP.get(r[0], 0) for r in c.execute("SELECT type FROM assignments WHERE completed=1"))

def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# Fixed catalog data
PLANTS = [
    "Monstera deliciosa", "Ficus lyrata", "Golden Pothos", "Snake Plant",
    "Dragon Tree", "ZZ Plant", "Peace Lily", "Red Apple", "Green Apple",
    "Rose", "Tulip", "Sunflower", "Daisy", "Cherry Blossom", "Banana",
    "Grapes", "Strawberry", "Cactus", "Four Leaf Clover", "Herb", "Maple Leaf"
]
EMOJIS = [
    "🌱","🌿","🍃","🌴","🌵","🌼","🍀","🍎","🍏",
    "🌹","🌷","🌻","🌸","🍌","🍇","🍓","🌵","🍀","🍁"
]
EMOJI_MAP = {PLANTS[i]: EMOJIS[i % len(EMOJIS)] for i in range(len(PLANTS))}
CATALOG_RARITY = {p: random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0] for p in PLANTS}

# ----------------------------------------------------------------------------
# ▶ Award free plants (every 5 completions)
# ----------------------------------------------------------------------------
def award_plant():
    total = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    due = total // 5
    owned = [r[0] for r in c.execute("SELECT name FROM plants")]
    while len(owned) < due:
        choice = random.choice([p for p in PLANTS if p not in owned])
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?, ?, ?, ?)",
            (choice, datetime.now().isoformat(), rarity, 0)
        )
        conn.commit()
        owned.append(choice)
        st.balloons()
        st.success(f"Unlocked: {EMOJI_MAP[choice]} {choice} ({rarity})")

# ----------------------------------------------------------------------------
# ▶ Roll for a random plant
# ----------------------------------------------------------------------------
def roll_plant():
    bal = get_balance()
    if bal < ROLL_COST:
        st.error(f"Not enough points (need {ROLL_COST}, have {bal})")
        return
    # Deduct cost
    c.execute(
        "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?, ?, ?, ?)",
        ("RollCost", datetime.now().isoformat(), "", ROLL_COST)
    )
    conn.commit()
    placeholder = st.empty()
    for _ in range(20):
        temp = random.choice(PLANTS)
        placeholder.markdown(f"### Rolling: {EMOJI_MAP[temp]} {temp}")
        time.sleep(0.05)
    pick = random.choices(
        PLANTS,
        weights=[RARITY_WEIGHTS[RARITY_CATS.index(CATALOG_RARITY[p])] for p in PLANTS],
        k=1
    )[0]
    existing = [r[0] for r in c.execute("SELECT name FROM plants")]
    if pick in existing:
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?, ?, ?, ?)",
            (pick, datetime.now().isoformat(), "Duplicate", -1)
        )
        conn.commit()
        placeholder.markdown(f"🎲 Duplicate! Refunded 1 point. {EMOJI_MAP[pick]} {pick}")
    else:
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?, ?, ?, ?)",
            (pick, datetime.now().isoformat(), rarity, 0)
        )
        conn.commit()
        placeholder.markdown(f"🎲 You got: {EMOJI_MAP[pick]} {pick} ({rarity})")
    st.balloons()

# ----------------------------------------------------------------------------
# ▶ UI Rendering
# ----------------------------------------------------------------------------
st.markdown(f"<div class='stats-left'>Points: {get_balance()}</div>", unsafe_allow_html=True)
st.markdown('<h1>🌱 Plant-Based Assignment Tracker 🌱</h1>', unsafe_allow_html=True)

tab_add, tab_upc, tab_cmp, tab_cat, tab_col = st.tabs([
    "Add", "Upcoming", "Completed", "Plant Catalog", "Collected Plants"
])

# --- Add Tab ---
with tab_add:
    st.subheader("➕ Add Assignment")
    with st.form("form_add", clear_on_submit=True):
        course = st.text_input("Course Name")
        assign = st.text_input("Assignment Title")
        a_type = st.selectbox("Assignment Type", list(POINTS_MAP.keys()))
        due_d = st.date_input("Due Date", date.today())
        due_t = st.time_input("Due Time", dtime(23,59))
        if st.form_submit_button("Add"):
            if course and assign:
                c.execute(
                    "INSERT INTO assignments(course, assignment, type, due_date, due_time) VALUES (?, ?, ?, ?, ?)",
                    (course, assign, a_type, due_d.isoformat(), due_t.isoformat())
                )
                conn.commit()
                st.success("Assignment added!")
            else:
                st.error("Please provide both course and assignment title.")

# --- Upcoming Tab ---
with tab_upc:
    st.subheader("⏳ Upcoming Assignments")
    rows = load_assignments(0)
    if not rows:
        st.info("No upcoming assignments.")
    for id_, course, assign, a_type, d_date, d_time in rows:
        dt = datetime.fromisoformat(f"{d_date}T{d_time}")
        st.markdown(f"**{course} - {assign} ({a_type})**  ")
        st.markdown(f"Due: {dt:%Y-%m-%d %H:%M}")

# --- Completed Tab ---
with tab_cmp:
    st.subheader("✅ Completed Assignments")
    rows = load_assignments(1)
    if not rows:
        st.info("No completed assignments.")
    for id_, course, assign, a_type, d_date, d_time in rows:
        st.markdown(f"~~{course} - {assign}~~ ({a_type})")

# --- Plant Catalog Tab ---
with tab_cat:
    st.subheader("🌿 Plant Catalog")
    # Centered roll button
    st.markdown('<div class="roll-btn-container">', unsafe_allow_html=True)
    if st.button(f"🎲 Roll for a Plant ({ROLL_COST} pts)"):
        roll_plant()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('---')
    cols = st.columns(4)
    for i, plant in enumerate(PLANTS):
        rarity = CATALOG_RARITY[plant]
        color = COLORS[rarity]
        with cols[i % 4]:
            st.markdown(
                f"<div class='card' style='background-color:{color}'>"
                f"<p style='font-size:12px;color:#1B4332'>{rarity}</p>"
                f"<div style='font-size:48px'>{EMOJI_MAP[plant]}</div>"
                f"<p>{plant}</p>"
                f"</div>",
                unsafe_allow_html=True
            )

# --- Collected Plants Tab ---
with tab_col:
    st.subheader("🌳 Collected Plants")
    data = c.execute("SELECT name, rarity, cost FROM plants").fetchall()
    if not data:
        st.info("No collected plants yet.")
    for name, rarity, cost in data:
        color = COLORS.get(rarity, COLORS['Common'])
        st.markdown(
            f"<div class='card' style='background-color:{color}'>"
            f"<p style='font-size:12px;color:#1B4332'>{rarity}</p>"
            f"<div style='font-size:48px'>{EMOJI_MAP.get(name,'🌱')}</div>"
            f"<p>{name}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

# Footer
st.markdown("---")
st.caption("Made with ❤️ and plants 🌿")
