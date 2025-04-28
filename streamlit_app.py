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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# ▶ Custom CSS theme and layout
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
    [data-testid="stHeader"], [data-testid="stToolbar"], footer {
        visibility: hidden;
    }
    .sidebar .sidebar-content {
        background-color: #245E46;
        color: #FFFFFF;
    }
    .sidebar .sidebar-content h2, .sidebar .sidebar-content h4 {
        color: #FFFFFF;
    }
    .card {
        background-color: #FFFFFF;
        color: #1B4332;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        padding: 16px;
        margin-bottom: 16px;
    }
    .large-emoji {
        font-size: 64px;
        text-align: center;
    }
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        assignment TEXT NOT NULL,
        type TEXT NOT NULL,
        due_date TEXT NOT NULL,
        due_time TEXT NOT NULL DEFAULT '23:59:00',
        completed INTEGER NOT NULL DEFAULT 0
    )
    """
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_url TEXT NOT NULL,
        awarded_at TEXT NOT NULL
    )
    """
)
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Plant catalog
# ------------------------------------------------------------------------------
PLANTS = [
    {"name": "Monstera deliciosa", "url": "https://images.unsplash.com/photo-1579370318442-73a6ff72b0a0?auto=format&fit=crop&w=400&q=80"},
    {"name": "Ficus lyrata", "url": "https://images.unsplash.com/photo-1534081333815-ae5019106622?auto=format&fit=crop&w=400&q=80"},
    {"name": "Golden Pothos", "url": "https://images.unsplash.com/photo-1556912167-f556f1f39d6b?auto=format&fit=crop&w=400&q=80"},
    {"name": "Snake Plant", "url": "https://images.unsplash.com/photo-1590254074496-c36d4871eaf5?auto=format&fit=crop&w=400&q=80"},
    {"name": "Dragon Tree", "url": "https://images.unsplash.com/photo-1600607689867-020a729b3d4d?auto=format&fit=crop&w=400&q=80"},
    {"name": "ZZ Plant", "url": "https://images.unsplash.com/photo-1592423492834-77e6ec2ffc3e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Peace Lily", "url": "https://images.unsplash.com/photo-1602524815465-f2b36bb874f9?auto=format&fit=crop&w=400&q=80"},
]

# Tree emoji mapping
EMOJIS = ["🌳","🌲","🌴","🎄","🌵","🌿","🍀","🌾"]
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
        (plant['name'], plant['url'], datetime.now().isoformat())
    )
    conn.commit()
    st.balloons()
    st.success(f"Unlocked: {EMOJI_MAP[plant['name']]} {plant['name']}")

# Load assignments by completion flag

def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ Sidebar navigation
# ------------------------------------------------------------------------------
st.sidebar.title("Navigation 🌿")
page = st.sidebar.radio("", ["Add","Upcoming","Completed","Plant Catalog","Collected Plants"])

# ------------------------------------------------------------------------------
# ▶ Add Page
# ------------------------------------------------------------------------------
if page == "Add":
    st.header("➕ Add Assignment")
    with st.form('add', clear_on_submit=True):
        course = st.text_input('Course Name')
        title = st.text_input('Assignment Title')
        a_type = st.selectbox('Type',['Quiz','Mid-Term','Final','Test','Project','Paper'])
        due_date = st.date_input('Due Date', date.today())
        due_time = st.time_input('Due Time', dtime(23,59))
        if st.form_submit_button('Add'):
            if course and title:
                c.execute(
                    "INSERT INTO assignments (course,assignment,type,due_date,due_time) VALUES (?,?,?,?,?)",
                    (course,title,a_type,due_date.isoformat(),due_time.isoformat())
                )
                conn.commit()
                st.success('Assignment added!')
            else:
                st.error('Please enter both course and title')

# ------------------------------------------------------------------------------
# ▶ Upcoming Page
# ------------------------------------------------------------------------------
elif page == "Upcoming":
    st.header("⏳ Upcoming Assignments")
    rows = load_assignments(0)
    if not rows:
        st.info('No upcoming assignments!')
    for id_,course,title,a_type,d_date,d_time in rows:
        dt = datetime.fromisoformat(f"{d_date}T{d_time}")
        diff = dt - datetime.now()
        parts=[]
        if diff.days//7>0: parts.append(f"{diff.days//7}w")
        if diff.days%7>0: parts.append(f"{diff.days%7}d")
        hrs=diff.seconds//3600
        if hrs>0: parts.append(f"{hrs}h")
        mins=(diff.seconds%3600)//60
        if mins>0: parts.append(f"{mins}m")
        remaining=' '.join(parts) or 'Now'
        html=f"""
        <div class='card'>
          <h4>{course} - {title} ({a_type})</h4>
          <p>Due: {dt.strftime('%Y-%m-%d %H:%M')}</p>
          <p><strong>Remaining:</strong> {remaining}</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        cols=st.columns([8,1,1])
        if cols[1].button('✅', key=f'done_{id_}'):
            c.execute("UPDATE assignments SET completed=1 WHERE id=?",(id_,))
            conn.commit(); award_plant(); st.experimental_rerun()
        if cols[2].button('❌', key=f'del_{id_}'):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

# ------------------------------------------------------------------------------
# ▶ Completed Page
# ------------------------------------------------------------------------------
elif page == "Completed":
    st.header("✅ Completed Assignments")
    rows = load_assignments(1)
    if not rows:
        st.info('No completed assignments')
    for id_,course,title,a_type,d_date,d_time in rows:
        html=f"""
        <div class='card'>
          <h4><s>{course} - {title}</s> ({a_type})</h4>
          <p>Completed: {d_date} {d_time}</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        if st.button('🗑️', key=f'delc_{id_}'):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

# ------------------------------------------------------------------------------
# ▶ Plant Catalog Page
# ------------------------------------------------------------------------------
elif page == "Plant Catalog":
    st.header("🌿 Plant Catalog")
    cols=st.columns(3)
    for i,plant in enumerate(PLANTS):
        with cols[i%3]:
            st.image(plant['url'], caption=plant['name'], use_column_width=True)

# ------------------------------------------------------------------------------
# ▶ Collected Plants Page
# ------------------------------------------------------------------------------
elif page == "Collected Plants":
    st.header("🌳 Collected Plants")
    collected=[r[0] for r in c.execute("SELECT name FROM plants")] 
    if not collected:
        st.info('Complete assignments to earn plants!')
    else:
        cols=st.columns(4)
        for i,name in enumerate(collected):
            emoji=EMOJI_MAP.get(name,'🌱')
            html=f"""
            <div class='card'>
              <div class='large-emoji'>{emoji}</div>
              <p style='text-align:center'>{name}</p>
            </div>
            """
            cols[i%4].markdown(html,unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ▶ Footer
# ------------------------------------------------------------------------------
st.markdown('---')
st.caption('Made with ❤️ and plants 🌿')
