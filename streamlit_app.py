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
      .stApp {
        background-color: #F0FBF3;
      }
      button.css-1emrehy {
        background-color: #A8D5BA !important;
        color: #1B4332 !important;
        border-radius: 10px;
        padding: 5px 10px;
      }
      .stMetric {
        background-color: #D8F3DC;
        border-radius: 10px;
        padding: 5px 10px;
        color: #1B4332;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# ▶ Database setup & migration (runs once)
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()

# Ensure columns exist
for col, props in [
    ('type', "TEXT NOT NULL DEFAULT 'Assignment'"),
    ('due_time', "TEXT NOT NULL DEFAULT '23:59:00'"),
    ('completed', "INTEGER NOT NULL DEFAULT 0")
]:
    try:
        c.execute(f"ALTER TABLE assignments ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass

# Create assignments table
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
# Create plants table
c.execute(
    """
    CREATE TABLE IF NOT EXISTS plants (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        image_url  TEXT    NOT NULL,
        awarded_at TEXT    NOT NULL
    )
    """
)
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Plant catalog
# ------------------------------------------------------------------------------
PLANTS = [
    {"name": "Monstera deliciosa", "url": "https://images.unsplash.com/photo-1579370318442-73a6ff72b0a0?auto=format&fit=crop&w=400&q=80"},
    {"name": "Ficus lyrata (Fiddle Leaf Fig)", "url": "https://images.unsplash.com/photo-1534081333815-ae5019106622?auto=format&fit=crop&w=400&q=80"},
    {"name": "Golden Pothos", "url": "https://images.unsplash.com/photo-1556912167-f556f1f39d6b?auto=format&fit=crop&w=400&q=80"},
    {"name": "Snake Plant", "url": "https://images.unsplash.com/photo-1590254074496-c36d4871eaf5?auto=format&fit=crop&w=400&q=80"},
    {"name": "Dragon Tree", "url": "https://images.unsplash.com/photo-1600607689867-020a729b3d4d?auto=format&fit=crop&w=400&q=80"},
    {"name": "ZZ Plant", "url": "https://images.unsplash.com/photo-1592423492834-77e6ec2ffc3e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Peace Lily", "url": "https://images.unsplash.com/photo-1602524815465-f2b36bb874f9?auto=format&fit=crop&w=400&q=80"},
    {"name": "Zebra Haworthia", "url": "https://images.unsplash.com/photo-1560844517-08c756ab6b27?auto=format&fit=crop&w=400&q=80"},
    {"name": "Aloe vera", "url": "https://images.unsplash.com/photo-1542219550-2ab3012dff5e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Heartleaf Philodendron", "url": "https://images.unsplash.com/photo-1556886564-6a2053850d29?auto=format&fit=crop&w=400&q=80"},
    {"name": "Boston Fern", "url": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=400&q=80"},
    {"name": "String of Pearls", "url": "https://images.unsplash.com/photo-1542831371-29b0f74f9713?auto=format&fit=crop&w=400&q=80"},
    {"name": "Rubber Plant", "url": "https://images.unsplash.com/photo-1587285133999-32d66b2655de?auto=format&fit=crop&w=400&q=80"},
    {"name": "Spider Plant", "url": "https://images.unsplash.com/photo-1493927732325-8a15479f4d49?auto=format&fit=crop&w=400&q=80"}
]

# ------------------------------------------------------------------------------
# ▶ Award plant on completion
# ------------------------------------------------------------------------------
def award_plant():
    owned = [r[0] for r in c.execute("SELECT name FROM plants").fetchall()]
    choices = [p for p in PLANTS if p['name'] not in owned]
    if not choices:
        st.info("All plants collected! 🌱")
        return
    choice = random.choice(choices)
    c.execute(
        "INSERT INTO plants (name, image_url, awarded_at) VALUES (?, ?, ?)",
        (choice['name'], choice['url'], datetime.now().isoformat())
    )
    conn.commit()
    st.balloons()
    st.success(f"New plant unlocked: {choice['name']} 🌿")

# ------------------------------------------------------------------------------
# ▶ App layout
# ------------------------------------------------------------------------------
st.title("🌱 Plant-Based Assignment Tracker 🌱")

tabs = st.tabs(["Add", "Upcoming", "Completed", "Garden"])

# --- Add Tab ---
with tabs[0]:
    with st.form('form'):
        st.subheader('Add Assignment')
        course    = st.text_input('Course Name')
        title     = st.text_input('Assignment Title')
        a_type    = st.selectbox('Type', ['Quiz','Mid-Term','Final','Test','Project','Paper'])
        due_date  = st.date_input('Due Date', date.today())
        due_time  = st.time_input('Due Time', dtime(23,59))
        if st.form_submit_button('Add'):
            if course and title:
                c.execute(
                    "INSERT INTO assignments (course, assignment, type, due_date, due_time) VALUES (?,?,?,?,?)",
                    (course, title, a_type, due_date.isoformat(), due_time.isoformat())
                )
                conn.commit()
                st.success('Assignment added!')
            else:
                st.error('Please enter course and title')

# Helper to load assignments

def load(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# --- Upcoming Tab ---
with tabs[1]:
    st.subheader('Upcoming Assignments')
    rows = load(0)
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
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2,4,3,2,1])
                c1.markdown(f"**{course}**")
                c2.markdown(f"{title} ({a_type})")
                c3.markdown(f"Due: {dt.strftime('%Y-%m-%d %H:%M')}")
                c4.metric('Remaining', f"{weeks}w {days}d {hrs}h {mins}m")
                if c5.button('✅', key=f'c{id_}'):
                    c.execute("UPDATE assignments SET completed=1 WHERE id=?", (id_,))
                    conn.commit()
                    award_plant()
                    st.experimental_rerun()
                if c5.button('❌', key=f'd{id_}'):
                    c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# --- Completed Tab ---
with tabs[2]:
    st.subheader('Completed Assignments')
    rows = load(1)
    if not rows:
        st.info('No completed assignments')
    else:
        for id_, course, title, a_type, d_date, d_time in rows:
            with st.container():
                c1, c2, c3, c4 = st.columns([2,4,3,1])
                c1.markdown(f"~~{course}~~")
                c2.markdown(f"~~{title}~~ ({a_type})")
                c3.markdown(f"Completed\n{d_date} {d_time}")
                if c4.button('🗑️', key=f'del{id_}'):
                    c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# --- Garden Tab ---
with tabs[3]:
    st.subheader('Your Garden')
    plants = c.execute("SELECT name, image_url FROM plants").fetchall()
    if not plants:
        st.info('Earn plants by completing assignments!')
    else:
        cols = st.columns(3)
        for i, (name, img) in enumerate(plants):
            cols[i % 3].image(img, caption=name, use_column_width=True)

# Footer
st.markdown('---')
st.caption('Made with love and plants 🌿')
