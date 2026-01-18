import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Page Configuration & Minimalist Theme
st.set_page_config(page_title="PulseCheck", page_icon="⚡", layout="wide")

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

# 2. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DATA LOADING ---
def get_data():
    students = conn.read(worksheet="Students", ttl=0)
    attendance = conn.read(worksheet="Attendance", ttl=0)
    return students, attendance

students_df, attendance_df = get_data()

# --- HEADER ---
st.title("PulseCheck")
st.markdown("##### Performance & Attendance Management")

# --- SIDEBAR ---
st.sidebar.title("Management")
with st.sidebar.expander("Register New Student", expanded=False):
    with st.form("reg_form"):
        name = st.text_input("Full Name")
        if st.form_submit_button("Add to Roster"):
            if name and name not in students_df["Name"].values:
                new_row = pd.DataFrame([{
                    "Student ID": len(students_df) + 1, "Name": name, 
                    "Total Classes": 0, "Date Joined": datetime.now().strftime("%Y-%m-%d")
                }])
                conn.update(worksheet="Students", data=pd.concat([students_df, new_row], ignore_index=True))
                st.cache_data.clear()
                st.rerun()

# --- MAIN INTERFACE ---
st.divider()
st.subheader("Class Check-in")
col1, col2 = st.columns([2, 1])

with col1:
    member = st.selectbox("Select Student", students_df["Name"].sort_values())
with col2:
    checkin_date = st.date_input("Date", datetime.now())

if st.button("Log Attendance", use_container_width=True):
    # Log entry
    log = pd.DataFrame([{
        "Date": checkin_date.strftime("%Y-%m-%d"), 
        "Student ID": students_df[students_df["Name"] == member]["Student ID"].values[0], 
        "Name": member
    }])
    conn.update(worksheet="Attendance", data=pd.concat([attendance_df, log], ignore_index=True))
    
    # Update total
    students_df.loc[students_df["Name"] == member, "Total Classes"] += 1
    conn.update(worksheet="Students", data=students_df)
    
    st.toast(f"Logged {member}", icon="✅")
    st.cache_data.clear()
    st.rerun()

# --- ANALYTICS ---
st.divider()
t1, t2, t3 = st.tabs(["Monthly Report", "Yearly Leaderboard", "Member History"])

if not attendance_df.empty:
    attendance_df['Date'] = pd.to_datetime(attendance_df['Date'])

with t1:
    curr = datetime.now()
    m_data = attendance_df[(attendance_df['Date'].dt.month == curr.month) & (attendance_df['Date'].dt.year == curr.year)]
    if not m_data.empty:
        summary = m_data['Name'].value_counts().reset_index()
        summary.columns = ['Name', 'Check-ins']
        st.dataframe(summary, hide_index=True, use_container_width=True)
    else:
        st.info("No records for this month.")

with t2:
    st.dataframe(students_df[['Name', 'Total Classes']].sort_values('Total Classes', ascending=False), hide_index=True, use_container_width=True)

with t3:
    search = st.selectbox("Search Student", students_df["Name"].sort_values(), key="search")
    history = attendance_df[attendance_df['Name'] == search].sort_values('Date', ascending=False)
    if not history.empty:
        st.metric("Total Sessions", len(history))
        display_h = history[['Date']].copy()
        display_h['Date'] = display_h['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_h, hide_index=True, use_container_width=True)
