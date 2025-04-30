import streamlit as st
import sqlite3
import random
import time
from datetime import date, datetime, time as dtime

# ----------------------------------------------------------------------------
# ▶ Configuration & Constants
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="🌿 Plant-Based Assignment Tracker",
    page_icon="🌿",
    layout="wide"
)

POINTS_MAP = {
    "Homework": 1,
    "Quiz": 2,
    "Paper": 3,
    "Project": 4,
    "Test": 4,
    "Mid-Term": 5,
    "Final": 10,
}
RARITY_CATS = ["Common", "Rare", "Epic", "Legendary"]
RARITY_WEIGHTS = [0.5, 0.3, 0.15, 0.05]
ROLL_COST = 5
COLORS = {
    "Common": "#e6ffe6",
    "Rare": "#4da6ff",
    "Epic": "#b84dff",
    "Legendary": "#ffd11a",
}

PLANTS = [
    "Monstera deliciosa", "Ficus lyrata", "Golden Pothos", "Palm Tree",
    "Cactus", "Cherry Blossom", "Clover", "Red Apple", "Green Apple",
    "Rose", "Tulip", "Sunflower", "Banana", "Grape", "Strawberry",
]
EMOJIS = [
    "🌱","🌿","🍃","🌴","🌵","🌸","🍀","🍎","🍏",
    "🌹","🌷","🌻","🍌","🍇","🍓",
]
EMOJI_MAP = {PLANTS[i]: EMOJIS[i % len(EMOJIS)] for i in range(len(PLANTS))}

# ----------------------------------------------------------------------------
# ▶ Database Helper
# ----------------------------------------------------------------------------

def init_db():
    conn = sqlite3.connect('assignments.db', check_same_thread=False)
    c = conn.cursor()
    # Ensure tables and columns
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT,
            assignment TEXT,
            type TEXT,
            due_date TEXT,
            due_time TEXT,
            completed INTEGER DEFAULT 0
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            awarded_at TEXT,
            rarity TEXT,
            cost INTEGER
        )
        """
    )
    # Add missing columns if needed
    for col, spec in [("rarity", "TEXT"), ("cost", "INTEGER")]:
        try:
            c.execute(f"ALTER TABLE plants ADD COLUMN {col} {spec}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn, c

conn, c = init_db()

# ----------------------------------------------------------------------------
# ▶ Core Functions
# ----------------------------------------------------------------------------
def get_balance():
    earned = sum(POINTS_MAP.get(r[0], 0) for r in c.execute("SELECT type FROM assignments WHERE completed=1"))
    spent = sum(r[0] for r in c.execute("SELECT cost FROM plants"))
    return earned - spent, earned, spent


def load_assignments(completed=False):
    flag = 1 if completed else 0
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()


def award_free_plants():
    total = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    free_count = total // 5
    owned = {r[0] for r in c.execute("SELECT name FROM plants")}
    while len(owned) < free_count:
        choice = random.choice([p for p in PLANTS if p not in owned])
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?,?,?,0)",
            (choice, datetime.now().isoformat(), rarity)
        )
        conn.commit()
        owned.add(choice)
        st.balloons()
        st.success(f"Unlocked free plant: {EMOJI_MAP[choice]} {choice} ({rarity})")


def roll_plant():
    balance, _, _ = get_balance()
    if balance < ROLL_COST:
        st.error(f"Not enough points: need {ROLL_COST}, have {balance}")
        return
    # Deduct cost record
    c.execute(
        "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES ('RollCost', ?, '', ?)",
        (datetime.now().isoformat(), ROLL_COST)
    )
    conn.commit()
    ph = st.empty()
    for _ in range(15):
        p = random.choice(PLANTS)
        ph.markdown(f"### Rolling: {EMOJI_MAP[p]} {p}")
        time.sleep(0.05)
    pick = random.choices(PLANTS, weights=RARITY_WEIGHTS * (len(PLANTS)//4 + 1), k=1)[0]
    existing = {r[0] for r in c.execute("SELECT name FROM plants")}
    if pick in existing:
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?, ?, 'Duplicate', -1)",
            (pick, datetime.now().isoformat())
        )
        conn.commit()
        ph.markdown(f"🎲 Duplicate! Refunded 1 point. {EMOJI_MAP[pick]} {pick}")
    else:
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name, awarded_at, rarity, cost) VALUES (?,?,?,0)",
            (pick, datetime.now().isoformat(), rarity)
        )
        conn.commit()
        ph.markdown(f"🎲 You got: {EMOJI_MAP[pick]} {pick} ({rarity})")
    st.balloons()

# ----------------------------------------------------------------------------
# ▶ Styles & Layout
# ----------------------------------------------------------------------------
st.markdown("""
<style>
  .app-container { padding:1rem; background:#00A550; }
  h1 { text-align:center; font-size:4rem; margin:0.5rem 0; }
  .stats-right { position:fixed; top:20px; right:20px; background:rgba(255,255,255,0.8); color:#228B22; padding:0.5rem 1rem; border-radius:0.5rem; font-weight:bold; }
  .stSidebar { background:linear-gradient(145deg,#74c69d,#2d6a4f) !important; border-radius:1rem; padding:1rem; }
  .stSidebar button { width:100% !important; margin:0.5rem 0 !important; background:#228B22 !important; color:#fff !important; border:none !important; border-radius:0.5rem !important; padding:0.5rem 0 !important; }
  .stForm { background:#fff; color:#000; border:1px solid #000; border-radius:0.5rem; padding:1rem; }
  input, select { background:#fff !important; color:#000 !important; border:1px solid #000 !important; border-radius:0.25rem !important; }
  .card { width:8rem; height:10rem; margin:0.5rem; padding:1rem; background:#fff; border-radius:1rem; box-shadow:0 0.5rem 1rem rgba(0,0,0,0.1); text-align:center; display:inline-block; }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.title("🌿 Menu")
    page = st.radio("Navigate to", ["Add", "Upcoming", "Completed", "Catalog", "Collected"], key='page')

# Header & Points
st.header("🌿 Plant-Based Tracker")
balance, earned, spent = get_balance()
st.markdown(f"<div class='stats-right'>Points: {balance}</div>", unsafe_allow_html=True)

# Container wrapper
st.markdown("<div class='app-container'>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# ▶ Pages
# ----------------------------------------------------------------------------
if page == "Add":
    st.subheader("➕ Add Assignment")
    with st.form("form_add", clear_on_submit=True):
        course = st.text_input("Course Name")
        assign_ = st.text_input("Assignment Title")
        a_type = st.selectbox("Type", list(POINTS_MAP.keys()))
        due_d = st.date_input("Due Date", date.today())
        due_t = st.time_input("Due Time", dtime(23,59))
        if st.form_submit_button("Add Assignment"):
            if course and assign_:
                c.execute(
                    "INSERT INTO assignments(course,assignment,type,due_date,due_time) VALUES (?,?,?,?,?)",
                    (course, assign_, a_type, due_d.isoformat(), due_t.isoformat())
                )
                conn.commit()
                st.success("Assignment added!")
            else:
                st.error("Please fill in all fields.")

elif page == "Upcoming":
    st.subheader("⏳ Upcoming Assignments")
    for id_, course, assign_, a_type, d_date, d_time in load_assignments(False):
        dt = datetime.fromisoformat(f"{d_date}T{d_time}")
        st.markdown(f"**{course} - {assign_}** ({a_type})  \nDue: {dt:%Y-%m-%d %H:%M}")
        c1, c2 = st.columns([0.9, 0.1])
        if c1.button("✅ Done", key=f"done_{id_}"):
            c.execute("UPDATE assignments SET completed=1 WHERE id=?", (id_,))
            conn.commit(); award_free_plants(); st.experimental_rerun()
        if c2.button("❌", key=f"del_{id_}"):
            c.execute("DELETE FROM assignments WHERE id=?", (id_,))
            conn.commit(); st.experimental_rerun()
        st.markdown("---")

elif page == "Completed":
    st.subheader("✅ Completed Assignments")
    for id_, course, assign_, a_type, d_date, d_time in load_assignments(True):
        st.markdown(f"~~{course} - {assign_}~~ ({a_type})  \nCompleted: {d_date} {d_time}")
        if st.button("🗑️ Remove", key=f"rem_{id_}"):
            c.execute("DELETE FROM assignments WHERE id=?", (id_,))
            conn.commit(); st.experimental_rerun()

elif page == "Catalog":
    st.subheader("🌿 Plant Catalog")
    if st.button(f"🎲 Roll ({ROLL_COST} pts)"):
        roll_plant()
    for i, p in enumerate(PLANTS):
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        st.markdown(
            f"<div class='card' style='background:{COLORS[rarity]}'>"
            f"<div style='font-size:2rem'>{EMOJI_MAP[p]}</div>"
            f"<p><strong>{p}</strong></p>"
            f"<small>{rarity}</small>"
            f"</div>", unsafe_allow_html=True
        )

elif page == "Collected":
    st.subheader("🌳 Collected Plants")
    seen = set()
    for name, rarity, cost in c.execute("SELECT name,rarity,cost FROM plants"):
        if name == 'RollCost' or name in seen:
            continue
        seen.add(name)
        st.markdown(
            f"<div class='card' style='background:{COLORS.get(rarity, '#fff')}'>"
            f"<div style='font-size:2rem'>{EMOJI_MAP.get(name,'🌱')}</div>"
            f"<p><strong>{name}</strong></p>"
            f"<small>{rarity}</small>"
            f"</div>", unsafe_allow_html=True
        )

# Close container wrapper
st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# ▶ Footer
# ----------------------------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ and plants 🌿")
