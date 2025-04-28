import streamlit as st
import sqlite3
import random
import time
from datetime import date, datetime, time as dtime

# ------------------------------------------------------------------------------
# ▶ Page configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Plant-Based Assignment Tracker",
    page_icon="🌿",
    layout="wide"
)

# ------------------------------------------------------------------------------
# ▶ Custom CSS: forest green background, white accents, app border
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #228B22 !important;
            color: #FFFFFF;
            border: 4px solid #FFFFFF;
            padding: 10px;
        }
        h1 {
            font-size: 80px;
            text-align: center;
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
        .card {
            background-color: #FFFFFF;
            color: #1B4332;
            border: 2px solid #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            padding: 16px;
            margin-bottom: 16px;
        }
        hr {
            border-top: 2px solid #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# ▶ Database setup & migration
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
# Add missing columns if not exist
for col, props in [('rarity', "TEXT NOT NULL DEFAULT ''"), ('cost', "INTEGER NOT NULL DEFAULT 0")]:
    try:
        c.execute(f"ALTER TABLE plants ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
# Create tables
c.execute(
    """
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        assignment TEXT NOT NULL,
        type TEXT NOT NULL,
        due_date TEXT NOT NULL,
        due_time TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0
    )
    """
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        awarded_at TEXT NOT NULL,
        rarity TEXT NOT NULL DEFAULT '',
        cost INTEGER NOT NULL DEFAULT 0
    )
    """
)
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Points and rarity config
# ------------------------------------------------------------------------------
POINTS_MAP = {"Homework":1, "Quiz":2, "Paper":3, "Project":4, "Test":4, "Mid-Term":5, "Final":10}
RARITY_CATS = ["Common","Rare","Epic","Legendary"]
RARITY_COSTS = {"Common":1,"Rare":3,"Epic":5,"Legendary":10}
RARITY_WEIGHTS = [0.5,0.3,0.15,0.05]

# ------------------------------------------------------------------------------
# ▶ Helpers
# ------------------------------------------------------------------------------
def get_balance():
    earned = sum(POINTS_MAP.get(r[0],0) for r in c.execute("SELECT type FROM assignments WHERE completed=1").fetchall())
    spent = sum(r[0] for r in c.execute("SELECT cost FROM plants").fetchall())
    return earned-spent, earned, spent

def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ Plant catalog data
# ------------------------------------------------------------------------------
PLANT_BREEDS = ["Monstera deliciosa","Ficus lyrata","Golden Pothos","Snake Plant",
                 "Dragon Tree","ZZ Plant","Peace Lily","Red Apple","Green Apple",
                 "Rose","Tulip","Sunflower","Daisy","Cherry Blossom","Banana",
                 "Grapes","Strawberry","Cactus","Four Leaf Clover","Herb","Maple Leaf"]
EMOJIS = ["🌱","🌿","🍃","🌴","🌵","🌼","🍀","🍎","🍏",
          "🌹","🌷","🌻","🌼","🌸","🍌","🍇","🍓","🌵","🍀","🍁"]
EMOJI_MAP = {breed: EMOJIS[i % len(EMOJIS)] for i, breed in enumerate(PLANT_BREEDS)}

# ------------------------------------------------------------------------------
# ▶ Award plant every 5 completions
# ------------------------------------------------------------------------------
def award_plant():
    total = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    due = total // 5
    owned = [r[0] for r in c.execute("SELECT name FROM plants").fetchall()]
    while len(owned) < due:
        choice = random.choice([b for b in PLANT_BREEDS if b not in owned])
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        cost = RARITY_COSTS[rarity]
        c.execute("INSERT INTO plants (name,awarded_at,rarity,cost) VALUES (?,?,?,?)",
                  (choice, datetime.now().isoformat(), rarity, cost))
        conn.commit(); owned.append(choice)
        st.balloons()
        st.success(f"Unlocked: {EMOJI_MAP[choice]} {choice} ({rarity}, Cost {cost} pts)")

# ------------------------------------------------------------------------------
# ▶ Roll for plant feature
# ------------------------------------------------------------------------------
def roll_plant():
    bal,_,_ = get_balance()
    if bal < 5:
        st.error(f"Not enough points (need 5, have {bal})")
        return
    # Deduct roll cost
    c.execute("INSERT INTO plants (name,awarded_at,rarity,cost) VALUES (?,?,?,?)",
              ("Roll Cost", datetime.now().isoformat(), "","5"))
    conn.commit()
    # Animation
    placeholder = st.empty()
    for _ in range(20):
        temp = random.choice(PLANT_BREEDS)
        placeholder.markdown(f"### Rolling: {EMOJI_MAP[temp]} {temp}")
        time.sleep(0.05)
    # Final pick
    pick = random.choices(PLANT_BREEDS, weights=RARITY_WEIGHTS, k=1)[0]
    if pick in [r[0] for r in c.execute("SELECT name FROM plants")] :
        # duplicate refund 1 pt
        c.execute("INSERT INTO plants (name,awarded_at,rarity,cost) VALUES (?,?,?,?)",
                  (pick, datetime.now().isoformat(), "Duplicate", -1))
        conn.commit()
        placeholder.markdown(f"🎲 Duplicate! Refunded 1 point. {EMOJI_MAP[pick]} {pick}")
    else:
        rarity = random.choices(RARITY_CATS, weights=RARITY_WEIGHTS, k=1)[0]
        c.execute("INSERT INTO plants (name,awarded_at,rarity,cost) VALUES (?,?,?,?)",
                  (pick, datetime.now().isoformat(), rarity, 0))
        conn.commit()
        placeholder.markdown(f"🎲 You got: {EMOJI_MAP[pick]} {pick} ({rarity})")
    st.balloons()

# ------------------------------------------------------------------------------
# ▶ UI Header & Points
# ------------------------------------------------------------------------------
balance, earned, spent = get_balance()
st.metric("Points Balance", f"{balance}", delta=f"Earned: {earned}, Spent: {spent}")
st.markdown('<h1>🌱 Plant-Based Assignment Tracker 🌱</h1>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ▶ Tabs
# ------------------------------------------------------------------------------
tabs = st.tabs(["Add","Upcoming","Completed","Plant Catalog","Collected Plants"])

# Add
with tabs[0]:
    st.subheader("➕ Add a New Assignment")
    with st.form("add_form", clear_on_submit=True):
        course = st.text_input("Course Name")
        assignment = st.text_input("Assignment Title")
        a_type = st.selectbox("Assignment Type", list(POINTS_MAP.keys()))
        due_date = st.date_input("Due Date", date.today())
        due_time = st.time_input("Due Time", dtime(23,59))
        if st.form_submit_button("Add Assignment"):
            if course and assignment:
                c.execute("INSERT INTO assignments(course,assignment,type,due_date,due_time,completed) VALUES (?,?,?,?,?,0)",
                          (course,assignment,a_type,due_date.isoformat(),due_time.isoformat()))
                conn.commit(); st.success("Assignment added!")
            else: st.error("Please fill in both Course Name and Assignment Title.")

# Upcoming
with tabs[1]:
    st.subheader("⏳ Upcoming Assignments")
    rows = load_assignments(0)
    if not rows: st.info("No upcoming assignments!")
    for id_, course, assign, a_type, d_date, d_time in rows:
        dt = datetime.fromisoformat(f"{d_date}T{d_time}")
        diff = dt - datetime.now()
        parts=[]
        if diff.days//7: parts.append(f"{diff.days//7}w")
        if diff.days%7: parts.append(f"{diff.days%7}d")
        h=diff.seconds//3600; m=(diff.seconds%3600)//60
        if h: parts.append(f"{h}h");
        if m: parts.append(f"{m}m")
        rem=' '.join(parts) or 'Now'
        st.markdown(f"**{course} - {assign} ({a_type})**  ")
        st.markdown(f"Due: {dt:%Y-%m-%d %H:%M} | Remaining: {rem}")
        c1,c2 = st.columns([5,1])
        if c1.button("✅ Done",key=f"done_{id_}"):
            c.execute("UPDATE assignments SET completed=1 WHERE id=?",(id_,)); conn.commit(); award_plant(); st.experimental_rerun()
        if c2.button("❌",key=f"del_{id_}"):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()
        st.markdown("---")

# Completed
with tabs[2]:
    st.subheader("✅ Completed Assignments")
    rows = load_assignments(1)
    if not rows: st.info("No completed assignments.")
    for id_, course, assign, a_type, d_date, d_time in rows:
        st.markdown(f"~~{course} - {assign}~~ ({a_type})   Completed: {d_date} {d_time}")
        if st.button("🗑️ Remove",key=f"rem_{id_}"):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

# Plant Catalog
with tabs[3]:
    st.subheader("🌿 Plant Catalog")
    cols = st.columns(7)
    for i,breed in enumerate(PLANT_BREEDS):
        with cols[i%7]:
            st.markdown(f"### {EMOJI_MAP[breed]} {breed}")
    st.markdown("---")
    st.write("Roll for a random plant! Costs 5 points.")
    if st.button("🎲 Roll for a Plant (5 points)"):
        roll_plant()

# Collected Plants
with tabs[4]:
    st.subheader("🌳 Collected Plants")
    data = c.execute("SELECT name,rarity,cost FROM plants").fetchall()
    if not data: st.info("Complete assignments to earn plants!")
    for name, rarity, cost in data:
        st.markdown(f"### {EMOJI_MAP.get(name,'🌱')} {name} — {rarity} (Cost {cost} pts)")

# Footer
st.markdown("---")
st.caption("Made with ❤️ and plants 🌿")
