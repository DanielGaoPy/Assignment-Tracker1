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
            background-color: #00A550;
            color: #FFFFFF;
            border: none;
            padding: 10px;
            max-width: 1600px;
            margin: 0 auto;
        }
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        .stats-left {
            position: fixed;
            top: 20px;
            left: 20px;
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        }
        input, .stTextInput>div>div>input,
        .stDateInput>div>div>input,
        .stTimeInput>div>div>input,
        .stSelectbox>div>div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #000000 !important;
            border-radius: 2px !important;
        }
        .card {
            width: 160px;
            height: 200px;
            padding: 16px;
            border: 2px solid #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin: 8px;
        }
        .roll-btn-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        button {
            background-color: #FFFFFF !important;
            color: #228B22 !important;
            border: 2px solid #FFFFFF !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: bold;
            margin: 5px;
        }
        hr {
            border-top: 2px solid #FFFFFF;
            margin: 20px 0;
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
for col, props in [('rarity', "TEXT NOT NULL DEFAULT ''"), ('cost', "INTEGER NOT NULL DEFAULT 0")]:
    try:
        c.execute(f"ALTER TABLE plants ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
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
COLORS = {
    "Common":"#e6ffe6",
    "Rare":"#4da6ff",
    "Epic":"#b84dff",
    "Legendary":"#ffd11a"
}

# ----------------------------------------------------------------------------
# ▶ Helper functions
# ----------------------------------------------------------------------------
def get_balance():
    return sum(POINTS_MAP.get(r[0],0) for r in c.execute("SELECT type FROM assignments WHERE completed=1"))

def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# Catalog data
PLANTS = [
    "Monstera deliciosa","Ficus lyrata","Golden Pothos","Palm Tree",
    "Cactus","Cherry Blossom","Clover","Red Apple","Green Apple",
    "Rose","Tulip","Sunflower","Banana","Grape","Strawberry",
    "Lemon","Orange","Watermelon","Pineapple","Cherry","Peach",
    "Mango","Avocado","Bamboo","Fern","Herb","Four Leaf Clover",
    "Maple Leaf","Mushroom","Sheaf","Evergreen","Blossom",
    "Hibiscus","Daisy","Pine Tree","Tree","Bush"
]
EMOJIS = [
    "🌱","🌿","🍃","🌴","🌵","🌸","🍀","🍎","🍏",
    "🌹","🌷","🌻","🍌","🍇","🍓","🍋","🍊","🍉",
    "🍍","🍒","🍑","🥭","🥑","🎋","🌲","🌾","🍁",
    "🍄","🎄","🎍","💐","🌼","🌺","🥀","🌳","🌴"
]
EMOJI_MAP = {PLANTS[i]: EMOJIS[i] for i in range(len(PLANTS))}
CATALOG_RARITY = {p: random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0] for p in PLANTS}

# ----------------------------------------------------------------------------
# ▶ Award free plant
# ----------------------------------------------------------------------------
def award_plant():
    total = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    due = total // 5
    owned = [r[0] for r in c.execute("SELECT name FROM plants")]
    while len(owned) < due:
        choice = random.choice([p for p in PLANTS if p not in owned])
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",
            (choice, datetime.now().isoformat(), rarity, 0)
        )
        conn.commit()
        owned.append(choice)
        st.balloons()
        st.success(f"Unlocked: {EMOJI_MAP[choice]} {choice} ({rarity})")

# ----------------------------------------------------------------------------
# ▶ Roll for a plant
# ----------------------------------------------------------------------------
def roll_plant():
    bal = get_balance()
    if bal < ROLL_COST:
        st.error(f"Not enough points (need {ROLL_COST}, have {bal})")
        return
    c.execute(
        "INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",
        ("RollCost", datetime.now().isoformat(), "", ROLL_COST)
    )
    conn.commit()
    ph = st.empty()
    for _ in range(20):
        temp = random.choice(PLANTS)
        ph.markdown(f"### Rolling: {EMOJI_MAP[temp]} {temp}")
        time.sleep(0.05)
    pick = random.choices(
        PLANTS,
        weights=[RARITY_WEIGHTS[RARITY_CATS.index(CATALOG_RARITY[p])] for p in PLANTS],
        k=1
    )[0]
    existing = [r[0] for r in c.execute("SELECT name FROM plants")]
    if pick in existing:
        c.execute(
            "INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",
            (pick, datetime.now().isoformat(), "Duplicate", -1)
        )
        conn.commit()
        ph.markdown(f"🎲 Duplicate! Refunded 1 point. {EMOJI_MAP[pick]} {pick}")
    else:
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute(
            "INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",
            (pick, datetime.now().isoformat(), rarity, 0)
        )
        conn.commit()
        ph.markdown(f"🎲 You got: {EMOJI_MAP[pick]} {pick} ({rarity})")
    st.balloons()

# ----------------------------------------------------------------------------
# ▶ Sidebar Navigation
# ----------------------------------------------------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'Add'
with st.sidebar:
    st.title("📋 Navigate")
    if st.button("➕ Add Assignment"): st.session_state.page='Add'
    if st.button("⏳ Upcoming"):       st.session_state.page='Upcoming'
    if st.button("✅ Completed"):      st.session_state.page='Completed'
    if st.button("🌿 Plant Catalog"):  st.session_state.page='Plant Catalog'
    if st.button("🌳 Collected Plants"):st.session_state.page='Collected Plants'

# Header
# Display collected assignment points in top-left
points = get_balance()
st.markdown(f"<div class='stats-left'>Points: {points}</div>", unsafe_allow_html=True)
st.markdown('<h1 style="font-size:120px;">🌿</h1>', unsafe_allow_html=True)

# Page Content
page = st.session_state.page

if page == 'Add':
    st.subheader("➕ Add Assignment")
    with st.form("form_add", clear_on_submit=True):
        course = st.text_input("Course Name")
        assign = st.text_input("Assignment Title")
        a_type = st.selectbox("Assignment Type", list(POINTS_MAP.keys()))
        due_d = st.date_input("Due Date", date.today())
        due_t = st.time_input("Due Time", dtime(23,59))
        if st.form_submit_button("Add Assignment"):
            if course and assign:
                c.execute("INSERT INTO assignments(course,assignment,type,duu_date,due_time)VALUES(?,?,?,?,?)",(course,assign,a_type,due_d.isoformat(),due_t.isoformat()))
                conn.commit(); st.success("Assignment added!")
            else: st.error("Fill in both fields.")

elif page == 'Upcoming':
    st.subheader("⏳ Upcoming Assignments")
    rows = load_assignments(0)
    if not rows: st.info("No upcoming assignments.")
    for id_,course,assign,a_type,d_date,d_time in rows:
        dt = datetime.fromisoformat(f"{d_date}T{d_time}")
        st.markdown(f"**{course} - {assign} ({a_type})**")
        st.markdown(f"Due: {dt:%Y-%m-%d %H:%M}")
        c1,c2 = st.columns([5,1])
        if c1.button("✅ Done",key=f"done_{id_}"): c.execute("UPDATE assignments SET completed=1 WHERE id=?",(id_,)); conn.commit(); award_plant(); st.experimental_rerun()
        if c2.button("❌ Delete",key=f"del_{id_}"): c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()
        st.markdown("---")

elif page == 'Completed':
    st.subheader("✅ Completed Assignments")
    rows = load_assignments(1)
    if not rows: st.info("No completed assignments.")
    for id_,course,assign,a_type,d_date,d_time in rows:
        st.markdown(f"~~{course} - {assign}~~ ({a_type})")
        if st.button("🗑️ Remove",key=f"rem_{id_}"): c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

elif page == 'Plant Catalog':
    st.subheader("🌿 Plant Catalog")
    st.markdown('<div class="roll-btn-container">', unsafe_allow_html=True)
    if st.button(f"🎲 Roll for a Plant ({ROLL_COST} pts)"): roll_plant()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('---')
    cols = st.columns(4)
    for i,p in enumerate(PLANTS):
        rarity = CATALOG_RARITY[p]
        color = COLORS[rarity]
        with cols[i % 4]:
            st.markdown(
                f"<div class='card' style='background-color:{color}'>"
                f"<p style='font-size:12px;color:#1B4332'>{rarity}</p>"
                f"<div style='font-size:48px'>{EMOJI_MAP[p]}</div>"
                f"<h4 style='color:#1B4332; text-align:center'>{p}</h4>"
                f"</div>",
                unsafe_allow_html=True
            )

elif page == 'Collected Plants':
    st.subheader("🌳 Collected Plants")
    # Gather unique collected plants (exclude roll costs)
    rows = c.execute("SELECT name,rarity,cost FROM plants").fetchall()
    seen = set()
    filtered = []
    for name, rarity, cost in rows:
        if name == 'RollCost':
            continue
        if name in seen:
            continue
        seen.add(name)
        filtered.append((name, rarity, cost))
    if not filtered:
        st.info("No collected plants yet.")
    else:
        # Render in grid matching Plant Catalog style
        cols = st.columns(4)
        for i, (name, rarity, cost) in enumerate(filtered):
            color = COLORS.get(rarity, COLORS['Common'])
            col = cols[i % 4]
            with col:
                st.markdown(
                    f"<div class='card' style='background-color:{color}'>"
                    f"<p style='font-size:12px;color:#1B4332'>{rarity}</p>"
                    f"<div style='font-size:48px'>{EMOJI_MAP.get(name,'🌱')}</div>"
                    f"<h4 style='color:#1B4332;text-align:center'>{name}</h4>"
                    f"</div>",
                    unsafe_allow_html=True
                )
# Footer
st.markdown("---")
st.caption("Made with ❤️ and plants 🌿")
