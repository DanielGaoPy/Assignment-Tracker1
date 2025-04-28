import streamlit as st
import sqlite3
from datetime import date, datetime

# ------------------------------------------------------------------------------
# ▶ Database setup (runs once)
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
# Create table with new fields: type, completed
c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course      TEXT NOT NULL,
        assignment  TEXT NOT NULL,
        type        TEXT NOT NULL,
        due_date    TEXT NOT NULL,
        completed   INTEGER DEFAULT 0
    )
""")
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Page layout & config
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Assignment Tracker", page_icon="📚", layout="wide")
st.title("📚 Assignment Tracker")

# ------------------------------------------------------------------------------
# ▶ Tabs for navigation
# ------------------------------------------------------------------------------
tabs = st.tabs(["➕ Add", "⏳ Upcoming", "✅ Completed"])

# ------------------------------------------------------------------------------
# ▶ Tab 1: Add Assignment
# ------------------------------------------------------------------------------
with tabs[0]:
    with st.form("add_form", clear_on_submit=True):
        st.subheader("➕ Add a New Assignment")
        course = st.text_input("Course Name")
        assignment = st.text_input("Assignment Title")
        a_type = st.selectbox("Assignment Type", ["Quiz", "Mid-Term", "Final", "Test", "Project", "Paper"])
        due_date = st.date_input("Due Date", value=date.today())
        submitted = st.form_submit_button("Add Assignment")
        if submitted:
            if course and assignment:
                c.execute(
                    "INSERT INTO assignments (course, assignment, type, due_date) VALUES (?, ?, ?, ?)",
                    (course, assignment, a_type, due_date.isoformat())
                )
                conn.commit()
                st.success(f"Added **{assignment}** ({a_type}) for **{course}**, due {due_date}")
            else:
                st.error("Please fill in Course Name and Assignment Title.")

# ------------------------------------------------------------------------------
# ▶ Helper: load assignments
# ------------------------------------------------------------------------------
def load_assignments(completed_flag):
    rows = c.execute(
        "SELECT id, course, assignment, type, due_date FROM assignments WHERE completed = ? ORDER BY due_date",
        (completed_flag,)
    ).fetchall()
    return rows

# ------------------------------------------------------------------------------
# ▶ Tab 2: Upcoming Assignments
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("⏳ Upcoming Assignments")
    upcoming = load_assignments(0)
    if not upcoming:
        st.info("No upcoming assignments! 🎉")
    else:
        for id, course, assignment, a_type, due in upcoming:
            due_dt = datetime.fromisoformat(due).date()
            days_left = (due_dt - date.today()).days
            cols = st.columns([2, 4, 2, 1, 1])
            cols[0].markdown(f"**{course}**")
            cols[1].markdown(f"**{assignment}** ({a_type})")
            cols[2].markdown(f"Due: {due_dt} ({days_left} days)")
            if cols[3].button("✅ Done", key=f"done_{id}"):
                c.execute("UPDATE assignments SET completed = 1 WHERE id = ?", (id,))
                conn.commit()
                st.experimental_rerun()
            if cols[4].button("❌", key=f"del_up_{id}"):
                c.execute("DELETE FROM assignments WHERE id = ?", (id,))
                conn.commit()
                st.experimental_rerun()

# ------------------------------------------------------------------------------
# ▶ Tab 3: Completed Assignments
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("✅ Completed Assignments")
    completed = load_assignments(1)
    if not completed:
        st.info("No assignments marked as completed.")
    else:
        for id, course, assignment, a_type, due in completed:
            cols = st.columns([2, 4, 2, 1])
            cols[0].markdown(f"~~{course}~~")
            cols[1].markdown(f"~~{assignment}~~ ({a_type})")
            cols[2].markdown(f"Due: {due}")
            if cols[3].button("🗑️", key=f"del_comp_{id}"):
                c.execute("DELETE FROM assignments WHERE id = ?", (id,))
                conn.commit()
                st.experimental_rerun()

# ------------------------------------------------------------------------------
# ▶ Footer
# ------------------------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit")
