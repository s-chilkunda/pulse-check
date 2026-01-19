import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="PulseCheck", page_icon="⚡", layout="wide")

# 2. Password & Environment Logic
# Change these to whatever you like!
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

# --- DATA LOADING ---
def get_data():
    # Keep the 5-min cache to avoid the 429 errors we saw earlier
    students = conn.read(worksheet="Students", ttl=300)
    attendance = conn.read(worksheet="Attendance", ttl=300)
    return students, attendance

students_df, attendance_df = get_data()

# --- HEADER (Visual indicator of which DB you are in) ---
env_label = "" if st.session_state["db_choice"] == "gsheets" else "[TEST MODE]"
st.title(f"PulseCheck {env_label}")
st.markdown("##### Performance & Attendance Management")

st.markdown("""
    <style>
    /* Clean, light background */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Professional Slate Headers */
    h1, h2, h3 {
        color: #1e293b !important; 
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    /* Sidebar - Soft Gray */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Input Labels */
    label {
        color: #475569 !important;
        font-weight: 500 !important;
    }

    /* Buttons - Elegant Indigo */
    div.stButton > button:first-child {
        background-color: #4f46e5;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    div.stButton > button:hover {
        background-color: #4338ca;
        border: none;
        color: white;
    }

    /* Dataframes and Cards */
    .stDataFrame, div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: REGISTRATION ---
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
                # Update Google Sheets
                conn.update(worksheet="Students", data=pd.concat([students_df, new_row], ignore_index=True))
                # Clear cache so the new student appears in the dropdown immediately
                st.cache_data.clear()
                st.rerun()
            elif name:
                st.sidebar.warning("Student already registered.")

# --- MAIN INTERFACE: CHECK-IN ---
st.divider()
st.subheader("Class Check-in")

# Handle case where no students exist yet
if students_df.empty:
    st.warning("No students found in the database. Please register a student in the sidebar first!")
else:
    col1, col2 = st.columns([2, 1])

    with col1:
        member = st.selectbox("Select Student", students_df["Name"].sort_values())
    with col2:
        checkin_date = st.date_input("Date", datetime.now())

    if st.button("Log Attendance", use_container_width=True):
        # 1. Prepare Log Entry
        student_id = students_df[students_df["Name"] == member]["Student ID"].values[0]
        log = pd.DataFrame([{
            "Date": checkin_date.strftime("%Y-%m-%d"), 
            "Student ID": student_id, 
            "Name": member
        }])
        
        # 2. Update Attendance Sheet
        updated_attendance = pd.concat([attendance_df, log], ignore_index=True)
        conn.update(worksheet="Attendance", data=updated_attendance)
        
        # 3. Update Lifetime Count in Students Sheet
        students_df.loc[students_df["Name"] == member, "Total Classes"] += 1
        conn.update(worksheet="Students", data=students_df)
        
        # 4. Notify and Clear Cache
        st.toast(f"Logged {member}", icon="✅")
        st.cache_data.clear()
        st.rerun()

# --- ANALYTICS SECTION ---
st.divider()
st.subheader("📊 Analytics Dashboard")
t1, t2, t3 = st.tabs(["Monthly Report", "Yearly Leaderboard", "Member History"])

# Gatekeeper: Check if attendance data exists
has_attendance = not attendance_df.empty and len(attendance_df) > 0

if has_attendance:
    attendance_df['Date'] = pd.to_datetime(attendance_df['Date'])

with t1:
    st.write(f"### Attendance for {datetime.now().strftime('%B %Y')}")
    if has_attendance:
        curr = datetime.now()
        m_data = attendance_df[(attendance_df['Date'].dt.month == curr.month) & 
                               (attendance_df['Date'].dt.year == curr.year)]
        
        if not m_data.empty:
            summary = m_data['Name'].value_counts().reset_index()
            summary.columns = ['Name', 'Check-ins']
            st.dataframe(summary, hide_index=True, use_container_width=True)
        else:
            st.info("No check-ins recorded for this calendar month.")
    else:
        st.info("Data will appear here once the first class is logged.")

with t2:
    st.write(f"### Rankings ({datetime.now().year})")
    if has_attendance:
        y_data = attendance_df[attendance_df['Date'].dt.year == datetime.now().year]
        if not y_data.empty:
            y_summary = y_data['Name'].value_counts().reset_index()
            y_summary.columns = ['Name', 'Total Check-ins']
            st.dataframe(y_summary, hide_index=True, use_container_width=True)
        else:
            st.info("No records found for the current year.")
    else:
        st.info("Leaderboard is currently empty.")

with t3:
    st.write("### Member Search")
    if not students_df.empty:
        search = st.selectbox("Search Student", students_df["Name"].sort_values(), key="search")
        
        if has_attendance:
            history = attendance_df[attendance_df['Name'] == search].sort_values('Date', ascending=False)
            if not history.empty:
                st.metric("Total Sessions", len(history))
                display_h = history[['Date']].copy()
                display_h['Date'] = display_h['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_h, hide_index=True, use_container_width=True)
            else:
                st.warning(f"No session history found for {search}.")
        else:
            st.info("Log your first session to enable history search.")
    else:
        st.warning("Please register students to enable history lookup.")
