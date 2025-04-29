import streamlit as st
import sqlite3
import random
import time
from datetime import date, datetime, time as dtime

# ----------------------------------------------------------------------------
# ▶ Points Mapping (Ensure defined for selectbox)
# ----------------------------------------------------------------------------
POINTS_MAP = {"Homework":1, "Quiz":2, "Paper":3, "Project":4, "Test":4, "Mid-Term":5, "Final":10}

# ----------------------------------------------------------------------------
# ▶ Custom CSS & Dynamic Title
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #00A550;
            color: #FFFFFF;
            border: none;
            padding: 80px 10px 10px;
            max-width: 1600px;
            margin: 0 auto;
        }
        [data-testid="collapsedControl"] {
            position: fixed;
            top: 28px;
            left: 28px;
            z-index: 1100;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(145deg, #74c69d 0%, #2d6a4f 100%) !important;
            color: #FFFFFF !important;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin: 10px;
            transition: box-shadow 0.3s ease;
        }
        [data-testid="stSidebar"]:hover {
            box-shadow: 0 12px 24px rgba(0,0,0,0.3);
        }
        [data-testid="stSidebar"] .title {
            font-size: 28px !important;
            font-weight: bold;
            text-align: center;
            margin-bottom: 16px;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] button {
            width: 100% !important;
            background-color: #228B22 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 0 !important;
            margin: 8px 0 !important;
            font-size: 16px !important;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
            font-size: 200px;
            transition: font-size 0.2s ease-out;
        }
        .stats-left {
            position: fixed;
            top: 20px;
            left: 80px;
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        }
        .stats-right {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: rgba(255,255,255,0.8);
            color: #228B22;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 24px;
            font-weight: bold;
            z-index: 1000;
        }
        input, .stTextInput>div>div>input,
        .stDateInput>div>div>input,
        .stTimeInput>div>div>input,
        .stSelectbox>div>div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            border-radius: 4px !important;
        }
        form#form_add, .stForm {
            background-color: #FFFFFF !important;
            border: 0.5px solid #000000 !important;
            border-radius: 4px !important;
            padding: 16px !important;
            color: #000000 !important;
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
    <script>
        window.addEventListener('scroll', () => {
            const maxSize = 200;
            const minSize = 60;
            const scrollY = window.scrollY;
            const h1 = document.querySelector('h1');
            const newSize = Math.max(minSize, maxSize - scrollY / 3);
            if (h1) h1.style.fontSize = newSize + 'px';
        });
    </script>
    <script>
        window.addEventListener('scroll', () => {
            const maxSize = 200;
            const minSize = 60;
            const scrollY = window.scrollY;
            const h1 = document.querySelector('h1');
            const newSize = Math.max(minSize, maxSize - scrollY / 3);
            if (h1) h1.style.fontSize = newSize + 'px';
        });
    </script>
    """,
    unsafe_allow_html=True
)
st.markdown('<h1 style="font-size:120px;">🌿</h1>', unsafe_allow_html=True)

# Page Content
# Initialize navigation state
if 'page' not in st.session_state:
    st.session_state.page = 'Add'
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
