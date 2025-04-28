import streamlit as st
import sqlite3
import random
from datetime import date, datetime, time as dtime

# ------------------------------------------------------------------------------
# ▶ Page configuration (must be first Streamlit command)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Plant-Based Assignment Tracker",
    page_icon="🌿",
    layout="wide"
)

# ------------------------------------------------------------------------------
# ▶ Custom CSS for plant-based theme
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #2E8B57 !important;
            color: #FFFFFF;
        }
        h1 {
            font-size: 64px;
            text-align: center;
            margin-bottom: 20px;
        }
        button {
            background-color: #A8D5BA !important;
            color: #1B4332 !important;
            border-radius: 10px !important;
            padding: 8px 16px !important;
            font-weight: bold;
        }
        [role="tab"] {
            color: #FFFFFF !important;
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
for col, props in [
    ('type', "TEXT NOT NULL DEFAULT 'Assignment'"),
    ('due_time', "TEXT NOT NULL DEFAULT '23:59:00'"),
    ('completed', "INTEGER NOT NULL DEFAULT 0")
]:
    try:
        c.execute(f"ALTER TABLE assignments ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
c.execute(
    """
    CREATE TABLE IF NOT EXISTS assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course      TEXT    NOT NULL,
        assignment  TEXT    NOT NULL,
        type        TEXT    NOT NULL,
        due_date    TEXT    NOT NULL,
        due_time    TEXT    NOT NULL DEFAULT '23:59:00',
        completed   INTEGER NOT NULL DEFAULT 0
    )
    """
)
c.execute(
    """
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
# ▶ Plant catalog (real images)
# ------------------------------------------------------------------------------
PLANTS = [
    {"name": "Monstera deliciosa", "url": "https://images.unsplash.com/photo-1579370318442-73a6ff72b0a0?auto=format&fit=crop&w=400&q=80"},
    {"name": "Ficus lyrata",        "url": "https://images.unsplash.com/photo-1534081333815-ae5019106622?auto=format&fit=crop&w=400&q=80"},
    {"name": "Golden Pothos",       "url": "https://images.unsplash.com/photo-1556912167-f556f1f39d6b?auto=format&fit=crop&w=400&q=80"},
    {"name": "Snake Plant",         "url": "https://images.unsplash.com/photo-1590254074496-c36d4871eaf5?auto=format&fit=crop&w=400&q=80"},
    {"name": "Dragon Tree",         "url": "https://images.unsplash.com/photo-1600607689867-020a729b3d4d?auto=format&fit=crop&w=400&q=80"},
    {"name": "ZZ Plant",            "url": "https://images.unsplash.com/photo-1592423492834-77e6ec2ffc3e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Peace Lily",          "url": "https://images.unsplash.com/photo-1602524815465-f2b36bb874f9?auto=format&fit=crop&w=400&q=80"},
]

# Tree emojis for collected plants (transparent emojis)
EMOJIS = ["🌳", "🌲", "🌴", "🎄", "🌵", "🌿", "🍀", "🌾"]
EMOJI_MAP = {PLANTS[i]['name']: EMOJIS[i % len(EMOJIS)] for i in range(len(PLANTS))}

# ------------------------------------------------------------------------------
# ▶ Award plant on completion
# ------------------------------------------------------------------------------
def award_plant():
    owned = [row[0] for row in c.execute("SELECT name FROM plants").fetchall()]
    choices = [p for p in PLANTS if p['name'] not in owned]
    if not choices:
        st.info("All plants collected! 🌱")
        return
    plant = random.choice(choices)
    c.execute(
        "INSERT INTO plants (name, image_url, awarded_at) VALUES (?, ?, ?)",
        (plant['name'], plant['url'], datetime.now().isoformat())
    )
    conn.commit()
    st.balloons()
    st.success(f"New plant unlocked: {EMOJI_MAP.get(plant['name'], '🌱')} {plant['name']}")

# ------------------------------------------------------------------------------
# ▶ Helper to load assignments
# ------------------------------------------------------------------------------
def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ App header & tabs
# ------------------------------------------------------------------------------
st.markdown('<h1>🌱 Plant-Based Assignment Tracker 🌱</h1>', unsafe_allow_html=True)

tabs = st.tabs(["Add", "Upcoming", "Completed", "Plant Catalog", "Collected Plants"])

# --- Add Tab ---
with tabs[0]:
    with st.form('add_form', clear_on_submit=True):
        st.subheader('Add Assignment')
        course     = st.text_input('Course Name')
        title      = st.text_input('Assignment Title')
        a_type     = st.selectbox('Type', ['Quiz','Mid-Term','Final','Test','Project','Paper'])
        due_date   = st.date_input('Due Date', date.today())
        due_time   = st.time_input('Due Time', dtime(23,59))
        if st.form_submit_button('Add'):
            if course and title:
                c.execute(
                    "INSERT INTO assignments (course, assignment, type, due_date, due_time) VALUES (?,?,?,?,?)",
                    (course, title, a_type, due_date.isoformat(), due_time.isoformat())
                )
                conn.commit()
                st.success('Assignment added!')
            else:
                st.error('Please enter both course and title.')

# --- Upcoming Tab ---
with tabs[1]:
    st.subheader('Upcoming Assignments')
    rows = load_assignments(0)
    if not rows:
        st.info('No upcoming assignments')
    else:
        for id_, course, title, a_type, d_date, d_time in rows:
            dt = datetime.fromisoformat(f"{d_date}T{d_time}")
            diff = dt - datetime.now()
            weeks = diff.days // 7
            days  = diff.days % 7
            hrs   = diff.seconds // 3600
            mins  = (diff.seconds % 3600) // 60
            parts = []
            if weeks > 0:
                parts.append(f"{weeks}w")
            if days > 0:
                parts.append(f"{days}d")
            if hrs > 0:
                parts.append(f"{hrs}h")
            if mins > 0:
                parts.append(f"{mins}m")
            remaining = ' '.join(parts) if parts else "Now"
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2,4,3,2,1])
                c1.markdown(f"**{course}**", unsafe_allow_html=True)
                c2.markdown(f"{title} ({a_type})", unsafe_allow_html=True)
                c3.markdown(f"Due: {dt.strftime('%Y-%m-%d %H:%M')}", unsafe_allow_html=True)
                c4.metric('Remaining', remaining)
                if c5.button('✅', key=f'done_{id_}'):
                    c.execute("UPDATE assignments SET completed=1 WHERE id=?", (id_,))
                    conn.commit()
                    award_plant()
                    st.experimental_rerun()
                if c5.button('❌', key=f'del_{id_}'):
                    c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# --- Completed Tab ---
with tabs[2]:
    st.subheader('Completed Assignments')
    rows = load_assignments(1)
    if not rows:
        st.info('No completed assignments')
    else:
        for id_, course, title, a_type, d_date, d_time in rows:
            with st.container():
                c1, c2, c3, c4 = st.columns([2,4,3,1])
                c1.markdown(f"~~{course}~~", unsafe_allow_html=True)
                c2.markdown(f"~~{title}~~ ({a_type})", unsafe_allow_html=True)
                c3.markdown(f"Completed: {d_date} {d_time}", unsafe_allow_html=True)
                if c4.button('🗑️', key=f'delc_{id_}'):
                    c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# --- Plant Catalog Tab ---
with tabs[3]:
    st.subheader('Plant Catalog')
    cols = st.columns(3)
    for i, plant in enumerate(PLANTS):
        cols[i % 3].image(plant['url'], caption=plant['name'], use_column_width=True)

# --- Collected Plants Tab ---
with tabs[4]:
    st.subheader('Collected Plants')
    collected = c.execute("SELECT name FROM plants").fetchall()
    if not collected:
        st.info('Complete assignments to earn plants!')
    else:
        cols = st.columns(4)
        for i, (name,) in enumerate(collected):
            emoji = EMOJI_MAP.get(name, "🌱")
            cols[i % 4].markdown(f"<div style='font-size:48px;text-align:center'>{emoji}</div><div style='text-align:center'>{name}</div>", unsafe_allow_html=True)

# Footer
st.markdown('---')
st.caption('Made with love and plants 🌿')
