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
        /* Hide default header and footer */
        [data-testid="stHeader"], [data-testid="stToolbar"], footer {visibility: hidden;}
        /* Navigation bar */
        .nav-container {
            display: flex; justify-content: center; gap: 16px;
            margin: 20px 0;
        }
        .nav-button {
            background-color: #A8D5BA; color: #1B4332;
            padding: 8px 16px; border: none; border-radius: 8px;
            font-weight: bold; cursor: pointer;
            transition: background-color 0.3s;
        }
        .nav-button:hover {
            background-color: #C3E3C8;
        }
        .nav-button.active {
            background-color: #FFFFFF; color: #2E8B57;
        }
        .card {
            background-color: #FFFFFF; color: #1B4332;
            border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            padding: 16px; margin-bottom: 16px;
        }
        .large-emoji {font-size:64px; text-align:center;}
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
    try: c.execute(f"ALTER TABLE assignments ADD COLUMN {col} {props}")
    except sqlite3.OperationalError: pass
c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        assignment TEXT NOT NULL,
        type TEXT NOT NULL,
        due_date TEXT NOT NULL,
        due_time TEXT NOT NULL,
        completed INTEGER NOT NULL
    )
"""
)
c.execute("""
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
# ▶ Plant catalog and emojis
# ------------------------------------------------------------------------------
PLANTS = [
    {"name":"Monstera deliciosa","url":"https://images.unsplash.com/photo-1579370318442-73a6ff72b0a0"},
    {"name":"Ficus lyrata","url":"https://images.unsplash.com/photo-1534081333815-ae5019106622"},
    {"name":"Golden Pothos","url":"https://images.unsplash.com/photo-1556912167-f556f1f39d6b"},
    {"name":"Snake Plant","url":"https://images.unsplash.com/photo-1590254074496-c36d4871eaf5"},
    {"name":"Dragon Tree","url":"https://images.unsplash.com/photo-1600607689867-020a729b3d4d"},
    {"name":"ZZ Plant","url":"https://images.unsplash.com/photo-1592423492834-77e6ec2ffc3e"},
    {"name":"Peace Lily","url":"https://images.unsplash.com/photo-1602524815465-f2b36bb874f9"}
]
EMOJIS=["🌳","🌲","🌴","🎄","🌵","🌿","🍀"]
EMOJI_MAP={p['name']:EMOJIS[i%len(EMOJIS)] for i,p in enumerate(PLANTS)}

# ------------------------------------------------------------------------------
# ▶ Utility functions
# ------------------------------------------------------------------------------
def award_plant():
    owned=[r[0] for r in c.execute("SELECT name FROM plants").fetchall()]
    choices=[p for p in PLANTS if p['name'] not in owned]
    if not choices:
        st.info("All plants collected! 🌱"); return
    plant=random.choice(choices)
    c.execute("INSERT INTO plants (name,image_url,awarded_at) VALUES (?,?,?)",
        (plant['name'],plant['url'],datetime.now().isoformat()))
    conn.commit(); st.balloons(); st.success(f"Unlocked: {EMOJI_MAP[plant['name']]} {plant['name']}")

def load_assignments(flag):
    return c.execute(
        "SELECT id,course,assignment,type,due_date,due_time FROM assignments WHERE completed=? ORDER BY due_date,due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ Navigation state
# ------------------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page='Add'

# ------------------------------------------------------------------------------
# ▶ Render navigation bar
# ------------------------------------------------------------------------------
st.markdown(
    '<div class="nav-container">' + ''.join([
        f'<button class="nav-button {"active" if st.session_state.page==pg else ""}" '
        f'onclick="window.streamlit.setComponentValue(\"{pg}\")">{pg}</button>'
        for pg in ['Add','Upcoming','Completed','Plant Catalog','Collected Plants']
    ]) + '</div>', unsafe_allow_html=True
)

def on_nav_click():
    st.session_state.page=st.experimental_get_query_params().get('value',['Add'])[0]

# ------------------------------------------------------------------------------
# ▶ Pages
# ------------------------------------------------------------------------------
page=st.session_state.page
if page=='Add':
    st.header('➕ Add Assignment')
    with st.form('add'): 
        course=st.text_input('Course Name'); title=st.text_input('Assignment Title')
        a_type=st.selectbox('Type',['Quiz','Mid-Term','Final','Test','Project','Paper'])
        d_date=st.date_input('Due Date',date.today()); d_time=st.time_input('Due Time',dtime(23,59))
        if st.form_submit_button('Add'):
            if course and title:
                c.execute("INSERT INTO assignments(course,assignment,type,due_date,due_time,completed) VALUES(?,?,?,?,?,0)",
                    (course,title,a_type,d_date.isoformat(),d_time.isoformat()))
                conn.commit(); st.success('Assignment added!')
            else: st.error('Enter both course and title')

elif page=='Upcoming':
    st.header('⏳ Upcoming Assignments')
    rows=load_assignments(0)
    if not rows: st.info('No upcoming assignments')
    for id_,course,title,a_type,d_date,d_time in rows:
        dt=datetime.fromisoformat(f"{d_date}T{d_time}"); diff=dt-datetime.now()
        parts=[f"{diff.days//7}w"] if diff.days//7 else []
        if diff.days%7: parts.append(f"{diff.days%7}d")
        hrs=diff.seconds//3600; mins=(diff.seconds%3600)//60
        if hrs: parts.append(f"{hrs}h");
        if mins: parts.append(f"{mins}m")
        rem=' '.join(parts) or 'Now'
        st.markdown(f"<div class='card'><h4>{course} - {title} ({a_type})</h4>"
                    f"<p><strong>Due:</strong> {dt.strftime('%Y-%m-%d %H:%M')}</p>"
                    f"<p><strong>Remaining:</strong> {rem}</p></div>",unsafe_allow_html=True)
        c1,c2=st.columns([9,1]);
        if c2.button('✅',key=f'done_{id_}'):
            c.execute("UPDATE assignments SET completed=1 WHERE id=?",(id_,)); conn.commit(); award_plant(); st.experimental_rerun()
        if c2.button('❌',key=f'del_{id_}'):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

elif page=='Completed':
    st.header('✅ Completed Assignments')
    rows=load_assignments(1)
    if not rows: st.info('No completed assignments')
    for id_,course,title,a_type,d_date,d_time in rows:
        st.markdown(f"<div class='card'><h4><s>{course} - {title}</s> ({a_type})</h4>"
                    f"<p>Completed: {d_date} {d_time}</p></div>",unsafe_allow_html=True)
        if st.button('🗑️',key=f'delc_{id_}'):
            c.execute("DELETE FROM assignments WHERE id=?",(id_,)); conn.commit(); st.experimental_rerun()

elif page=='Plant Catalog':
    st.header('🌿 Plant Catalog')
    cols=st.columns(3)
    for i,p in enumerate(PLANTS): cols[i%3].image(p['url'],caption=p['name'],use_column_width=True)

elif page=='Collected Plants':
    st.header('🌳 Collected Plants')
    collected=[r[0] for r in c.execute("SELECT name FROM plants")] 
    if not collected: st.info('Complete assignments to earn plants!')
    else:
        cols=st.columns(4)
        for i,name in enumerate(collected):
            emoji=EMOJI_MAP.get(name,'🌱')
            cols[i%4].markdown(f"<div class='card'><div class='large-emoji'>{emoji}</div>"
                              f"<p style='text-align:center'>{name}</p></div>",unsafe_allow_html=True)

# Footer
st.markdown('---')
st.caption('Made with ❤️ and plants 🌿')
