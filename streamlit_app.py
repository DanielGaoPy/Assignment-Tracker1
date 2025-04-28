import streamlit as st
import sqlite3
import random
from datetime import date, datetime, time as dtime

# ------------------------------------------------------------------------------
# ▶ Page configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Plant Tracker",
    page_icon="🌿",
    layout="wide"
)

# ------------------------------------------------------------------------------
# ▶ Custom CSS: Navigation bar and theme
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');
        [data-testid="stAppViewContainer"] {
            background-color: #2E8B57 !important;
            font-family: 'Comfortaa', sans-serif;
            color: #FFFFFF;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"], footer { visibility: hidden; }
        .nav-container { display: flex; justify-content: center; gap: 16px; margin: 20px 0; }
        .nav-button {
            background-color: #A8D5BA; color: #1B4332; padding: 8px 16px; border-radius: 8px;
            font-weight: bold; cursor: pointer; transition: background-color 0.3s;
        }
        .nav-button:hover { background-color: #C3E3C8; }
        .nav-button.active { background-color: #FFFFFF; color: #2E8B57; }
        .card {
            background-color: #FFFFFF; color: #1B4332; border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15); padding: 16px; margin-bottom: 16px;
        }
        .large-emoji { font-size: 64px; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# ▶ Database setup
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
for col, props in [
    ('type',      "TEXT NOT NULL DEFAULT 'Assignment'"),
    ('due_time',  "TEXT NOT NULL DEFAULT '23:59:00'"),
    ('completed', "INTEGER NOT NULL DEFAULT 0")
]:
    try: c.execute(f"ALTER TABLE assignments ADD COLUMN {col} {props}")
    except sqlite3.OperationalError: pass
c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course      TEXT    NOT NULL,
        assignment  TEXT    NOT NULL,
        type        TEXT    NOT NULL,
        due_date    TEXT    NOT NULL,
        due_time    TEXT    NOT NULL,
        completed   INTEGER NOT NULL
    )
"""
)
c.execute("""
    CREATE TABLE IF NOT EXISTS plants (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        image_url   TEXT    NOT NULL,
        awarded_at  TEXT    NOT NULL
    )
"""
)
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Plant catalog and emojis
# ------------------------------------------------------------------------------
PLANTS = [
    {"name": "Monstera deliciosa"},
    {"name": "Ficus lyrata"},
    {"name": "Golden Pothos"},
    {"name": "Snake Plant"},
    {"name": "Dragon Tree"},
    {"name": "ZZ Plant"},
    {"name": "Peace Lily"}
]
EMOJIS = ["🌳","🌲","🌴","🎄","🌵","🌿","🍀"]
EMOJI_MAP = {PLANTS[i]['name']: EMOJIS[i % len(EMOJIS)] for i in range(len(PLANTS))}

# ------------------------------------------------------------------------------
# ▶ Utility functions
# ------------------------------------------------------------------------------
def award_plant():
    owned = [row[0] for row in c.execute("SELECT name FROM plants").fetchall()]
    choices = [p for p in PLANTS if p['name'] not in owned]
    if not choices:
        st.info("All plants collected! 🌱")
        return
    plant = random.choice(choices)
    c.execute(
        "INSERT INTO plants (name, image_url, awarded_at) VALUES (?,?,?)",
        (plant['name'], '', datetime.now().isoformat())
    )
    conn.commit()
    st.balloons()
    st.success(f"Unlocked: {EMOJI_MAP[plant['name']]} {plant['name']}")

def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ Navigation
# ------------------------------------------------------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'Add'

# Navigation bar
nav_buttons = ''
for pg in ['Add', 'Upcoming', 'Completed', 'Plant Catalog', 'Collected Plants']:
    active = 'active' if st.session_state.page == pg else ''
    nav_buttons += f"<button class='nav-button {active}' onclick=\"window.streamlit.setComponentValue('{pg}')\">{pg}</button>"
st.markdown(f"<div class='nav-container'>{nav_buttons}</div>", unsafe_allow_html=True)
page = st.session_state.page

# ------------------------------------------------------------------------------
# ▶ Pages implementation
# ------------------------------------------------------------------------------
# ... (Add, Upcoming, Completed, Plant Catalog code remains unchanged)

# Collected Plants Tab - fixed to only emojis
if page == 'Collected Plants':
    st.header('🌳 Collected Plants')
    collected = [r[0] for r in c.execute("SELECT name FROM plants").fetchall()]
    if not collected:
        st.info('Complete assignments to earn plants!')
    else:
        # Display in rows of 4
        for i in range(0, len(collected), 4):
            cols = st.columns(4)
            for idx, name in enumerate(collected[i:i+4]):
                emoji = EMOJI_MAP.get(name, '🌱')
                cols[idx].markdown(
                    f"<div class='card'><div class='large-emoji'>{emoji}</div>"
                    f"<p style='text-align:center;color:#1B4332'>{name}</p></div>",
                    unsafe_allow_html=True
                )

# Footer
st.markdown('---')
st.caption('Made with ❤️ and plants 🌿')
