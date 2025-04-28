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
        .app-container {
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
        .roll-btn {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
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
# Columns migration
for col, props in [('rarity', "TEXT NOT NULL DEFAULT ''"), ('cost', "INTEGER NOT NULL DEFAULT 0")]:
    try:
        c.execute(f"ALTER TABLE plants ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
# Tables creation
c.execute("""
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    course TEXT,
    assignment TEXT,
    type TEXT,
    due_date TEXT,
    due_time TEXT,
    completed INTEGER DEFAULT 0
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY,
    name TEXT,
    awarded_at TEXT,
    rarity TEXT DEFAULT '',
    cost INTEGER DEFAULT 0
)
""")
conn.commit()

# ----------------------------------------------------------------------------
# ▶ Config
# ----------------------------------------------------------------------------
POINTS_MAP = {"Homework":1,"Quiz":2,"Paper":3,"Project":4,"Test":4,"Mid-Term":5,"Final":10}
RARITY_CATS = ["Common","Rare","Epic","Legendary"]
RARITY_WEIGHTS = [0.5,0.3,0.15,0.05]
ROLL_COST = 5
COLORS = {"Common":"#FFFFFF","Rare":"#ADD8E6","Epic":"#D8BFD8","Legendary":"#FFFFE0"}

# ----------------------------------------------------------------------------
# ▶ Helpers
# ----------------------------------------------------------------------------
def get_balance():
    earned = sum(POINTS_MAP.get(r[0],0) for r in c.execute("SELECT type FROM assignments WHERE completed=1"))
    return earned

def load_assignments(flag):
    return c.execute(
        "SELECT id,course,assignment,type,due_date,due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time", (flag,)
    ).fetchall()

# Fixed catalog rarity
PLANTS = ["Monstera deliciosa","Ficus lyrata","Golden Pothos","Snake Plant","Dragon Tree","ZZ Plant","Peace Lily","Red Apple","Green Apple","Rose","Tulip","Sunflower","Daisy","Cherry Blossom","Banana","Grapes","Strawberry","Cactus","Four Leaf Clover","Herb","Maple Leaf"]
EMOJIS = ["🌱","🌿","🍃","🌴","🌵","🌼","🍀","🍎","🍏","🌹","🌷","🌻","🌸","🍌","🍇","🍓","🌵","🍀","🍁"]
EMOJI_MAP = {PLANTS[i]:EMOJIS[i%len(EMOJIS)] for i in range(len(PLANTS))}
CATALOG_RARITY = {p:random.choices(RARITY_CATS,weights=RARITY_WEIGHTS,k=1)[0] for p in PLANTS}

# Award free every 5
def award_plant():
    total = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    due = total//5
    owned = [r[0] for r in c.execute("SELECT name FROM plants")]
    while len(owned)<due:
        choice = random.choice([p for p in PLANTS if p not in owned])
        rarity = random.choices(RARITY_CATS,weights=RARITY_WEIGHTS,k=1)[0]
        c.execute("INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",(choice,datetime.now().isoformat(),rarity,0))
        conn.commit(); owned.append(choice)
        st.balloons(); st.success(f"Unlocked: {EMOJI_MAP[choice]} {choice} ({rarity})")

# Roll
def roll_plant():
    bal = get_balance()
    if bal<ROLL_COST:
        st.error(f"Need {ROLL_COST}, have {bal}")
        return
    c.execute("INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",("RollCost",datetime.now().isoformat(),"",ROLL_COST))
    conn.commit()
    ph=st.empty()
    for _ in range(20):
        temp=random.choice(PLANTS)
        ph.markdown(f"### Rolling: {EMOJI_MAP[temp]} {temp}")
        time.sleep(0.05)
    pick=random.choices(PLANTS,weights=[RARITY_WEIGHTS[RARITY_CATS.index(CATALOG_RARITY[p])] for p in PLANTS],k=1)[0]
    existing=[r[0] for r in c.execute("SELECT name FROM plants")]
    if pick in existing:
        c.execute("INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",(pick,datetime.now().isoformat(),"Duplicate",-1))
        conn.commit(); ph.markdown(f"🎲 Duplicate! Refund 1 {EMOJI_MAP[pick]}")
    else:
        rarity=random.choices(RARITY_CATS,weights=RARITY_WEIGHTS,k=1)[0]
        c.execute("INSERT INTO plants(name,awarded_at,rarity,cost) VALUES(?,?,?,?)",(pick,datetime.now().isoformat(),rarity,0))
        conn.commit(); ph.markdown(f"🎲 You got: {EMOJI_MAP[pick]} {pick} ({rarity})")
    st.balloons()

# ----------------------------------------------------------------------------
# ▶ UI
# ----------------------------------------------------------------------------
st.markdown(f"<div class='stats-left'>Points: {get_balance()}</div>",unsafe_allow_html=True)
st.markdown('<h1>🌱 Plant-Based Assignment Tracker 🌱</h1>',unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["Add","Upcoming","Completed","Catalog","Collected"])

with tab1:
    st.subheader("Add Assignment")
    with st.form("f1"):
        c1=st.text_input("Course")
        a1=st.text_input("Title")
        t1=st.selectbox("Type",list(POINTS_MAP.keys()))
        d1=st.date_input("Due Date",date.today())
        tm1=st.time_input("Due Time",dtime(23,59))
        if st.form_submit_button("Add"):
            if c1 and a1:
                c.execute("INSERT INTO assignments(course,assignment,type,due_date,due_time) VALUES(?,?,?,?,?)",(c1,a1,t1,d1.isoformat(),tm1.isoformat()))
                conn.commit(); st.success("Added")
            else: st.error("Fill both")

with tab2:
    st.subheader("Upcoming")
    for *row, in load_assignments(0):
        st.write(row)

with tab3:
    st.subheader("Completed")
    for *row, in load_assignments(1):
        st.write(row)

with tab4:
    with st.container():
        st.subheader("Catalog")
        if st.button("Roll for Plant",key="rb"): roll_plant()
        cols=st.columns(4)
        for i,p in enumerate(PLANTS):
            rarity=CATALOG_RARITY[p]
            cols[i%4].markdown(f"<div style='background:{COLORS[rarity]};padding:10px;border-radius:8px;'>"
                               f"<p style='font-size:12px'>{rarity}</p>"
                               f"<div style='font-size:48px'>{EMOJI_MAP[p]}</div>" 
                               f"<p>{p}</p></div>",unsafe_allow_html=True)

with tab5:
    st.subheader("Collected")
    for n,r,cost in c.execute("SELECT name,rarity,cost FROM plants"):
        st.write(f"{EMOJI_MAP.get(n,'🌱')} {n} ({r}) Cost:{cost}")

st.markdown("---")
st.caption("Made with ❤️")
