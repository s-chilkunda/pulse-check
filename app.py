import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

# 1. Page Config
st.set_page_config(page_title="PulseCheck", page_icon="⚡", layout="wide")

# 2. Password & Environment Logic
PASS_PROD = "lucky"  
PASS_TEST = "testenv"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["db_choice"] = None

if not st.session_state["authenticated"]:
    st.title("⚡ PulseCheck Login")
    pwd = st.text_input("Say the magic word!", type="password")
    if st.button("Unlock"):
        if pwd == PASS_PROD:
            st.session_state["authenticated"] = True
            st.session_state["db_choice"] = "gsheets"
            st.rerun()
        elif pwd == PASS_TEST:
            st.session_state["authenticated"] = True
            st.session_state["db_choice"] = "gsheets_test"
            st.rerun()
        else:
            st.error("Invalid Access Code")
    st.stop()

# 3. Connection Setup
conn = st.connection(st.session_state["db_choice"], type=GSheetsConnection)

def get_data():
    students = conn.read(worksheet="Students", ttl=300)
    attendance = conn.read(worksheet="Attendance", ttl=300)
    return students, attendance

students_df, attendance_df = get_data()

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #1e293b !important; font-family: 'Inter', sans-serif; font-weight: 600; }
    section[data-testid="stSidebar"] { background-color: #f1f5f9; border-right: 1px solid #e2e8f0; }
    label { color: #475569 !important; font-weight: 500 !important; }
    div.stButton > button:first-child { background-color: #4f46e5; color: white; border-radius: 6px; border: none; padding: 0.5rem 1.5rem; font-weight: 500; }
    div.stButton > button:hover { background-color: #4338ca; border: none; color: white; }
    .stDataFrame, div[data-testid="stMetric"] { background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & HEADER ---
env_label = "" if st.session_state["db_choice"] == "gsheets" else "[TEST MODE]"
st.title(f"PulseCheck {env_label}")
st.markdown("##### Performance & Attendance Management")

st.sidebar.title("Management")
with st.sidebar.expander("Register New Student", expanded=False):
    with st.form("reg_form"):
        name = st.text_input("Full Name")
        if st.form_submit_button("Add to Roster"):
            if name and name not in students_df["Name"].values:
                new_row = pd.DataFrame([{
                    "Student ID": len(students_df) + 1, 
                    "Name": name, 
                    "Total Classes": 0, 
                    "Date Joined": datetime.now().strftime("%Y-%m-%d")
                }])
                conn.update(worksheet="Students", data=pd.concat([students_df, new_row], ignore_index=True))
                st.cache_data.clear()
                st.rerun()

# --- CHECK-IN ---
st.divider()
st.subheader("Class Check-in")
if not students_df.empty:
    col1, col2 = st.columns([2, 1])
    with col1:
        member = st.selectbox("Select Student", students_df["Name"].sort_values())
    with col2:
        checkin_date = st.date_input("Date", datetime.now())

    if st.button("Log Attendance", use_container_width=True):
        student_id = students_df[students_df["Name"] == member]["Student ID"].values[0]
        log = pd.DataFrame([{"Date": checkin_date.strftime("%Y-%m-%d"), "Student ID": student_id, "Name": member}])
        conn.update(worksheet="Attendance", data=pd.concat([attendance_df, log], ignore_index=True))
        students_df.loc[students_df["Name"] == member, "Total Classes"] += 1
        conn.update(worksheet="Students", data=students_df)
        st.toast(f"Logged {member}", icon="✅")
        st.cache_data.clear()
        st.rerun()

# --- ANALYTICS ---
st.divider()
st.subheader("📊 Analytics Dashboard")
t1, t2, t3 = st.tabs(["Monthly Report", "Yearly Leaderboard", "Member History"])

has_attendance = not attendance_df.empty
if has_attendance:
    attendance_df['Date'] = pd.to_datetime(attendance_df['Date'])

with t1:
    curr = datetime.now()
    st.write(f"### {curr.strftime('%B %Y')}")
    
    if has_attendance:
        m_data = attendance_df[(attendance_df['Date'].dt.month == curr.month) & (attendance_df['Date'].dt.year == curr.year)]
        daily_counts = m_data.groupby(m_data['Date'].dt.day).size().to_dict()
        cal_matrix = calendar.monthcalendar(curr.year, curr.month)
        
        # Calendar Header Labels
        cols = st.columns(7)
        days_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day_name in enumerate(days_abbr):
            cols[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#94a3b8; margin-bottom:5px;'>{day_name}</p>", unsafe_allow_html=True)

        # Calendar Grid Generation
        for week in cal_matrix:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    count = daily_counts.get(day, 0)
                    
                    # Color Logic: 0 is white, then Amber Warning ranges
                    if count == 0:
                        bg, txt, border = "#ffffff", "#94a3b8", "#e2e8f0"
                    elif count <= 3:
                        bg, txt, border = "#fffbeb", "#92400e", "#fcd34d"
                    elif count <= 7:
                        bg, txt, border = "#fde68a", "#78350f", "#fcd34d"
                    else:
                        bg, txt, border = "#d97706", "#ffffff", "#d97706"

                    cols[i].markdown(f"""
                        <div style="background-color:{bg}; color:{txt}; padding:8px; border-radius:6px; border:1px solid {border}; min-height:80px; display:flex; flex-direction:column; justify-content:space-between;">
                            <div style="font-size:0.75rem; font-weight:600; text-align:left;">{day}</div>
                            <div style="font-size:1.6rem; font-weight:800; text-align:center;">{count}</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        if not m_data.empty:
            st.write("**Student Summary**")
            summary = m_data['Name'].value_counts().reset_index(name='Check-ins').rename(columns={'index': 'Name'})
            st.dataframe(summary, hide_index=True, use_container_width=True)
        else:
            st.info("No check-ins recorded for this calendar month.")
    else:
        st.info("Log your first session to see monthly data.")

with t2:
    st.write(f"### Rankings ({datetime.now().year})")
    if has_attendance:
        y_data = attendance_df[attendance_df['Date'].dt.year == datetime.now().year]
        if not y_data.empty:
            y_summary = y_data['Name'].value_counts().reset_index(name='Total')
            st.dataframe(y_summary, hide_index=True, use_container_width=True)

with t3:
    st.write("### Member Search")
    if not students_df.empty:
        search = st.selectbox("Search Student", students_df["Name"].sort_values())
        if has_attendance:
            # Filter history for the selected student
            history = attendance_df[attendance_df['Name'] == search].sort_values('Date', ascending=False)
            
            if not history.empty:
                st.metric("Total Sessions", len(history))
                
                # Create a display copy and strip the time segment
                display_h = history[['Date']].copy()
                display_h['Date'] = display_h['Date'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_h, hide_index=True, use_container_width=True)
            else:
                st.info(f"No history found for {search}.")