⚡ PulseCheck: Attendance & Momentum Engine
PulseCheck is a lightweight, mobile-responsive web application built with Streamlit and Python. It serves as a digital front-end for a Google Sheets database, allowing instructors to bypass manual spreadsheet entry in favor of a clean, functional UI for logging student attendance and tracking performance trends.

🛠️ Tech Stack
Frontend/App Framework: Streamlit

Database: Google Sheets (via st-gsheets-connection)

Data Processing: Pandas

Deployment: Streamlit Community Cloud

🚀 Key Features
CRUD Operations: Seamlessly register new students and log timestamped attendance entries.

Dynamic Analytics: Automated monthly and yearly leaderboards generated via Pandas aggregations.

Smart Caching: Implements ttl (Time-To-Live) caching logic to stay within Google Sheets API rate limits (60 requests/min).

Defensive Programming: Graceful handling of empty data states to prevent runtime crashes during initial setup.

Minimalist UI: Custom CSS-injected theme optimized for readability and high-speed mobile interaction.

⚙️ Setup & Installation
Environment: Created using Conda/Python 3.10+.

API Configuration: Requires a Google Cloud Service Account with Google Sheets API enabled.

Local Secrets: Connection strings stored in .streamlit/secrets.toml.

Note: Ensure the Service Account email is shared with the target Google Sheet with "Editor" permissions.

Requirements:

Plaintext
streamlit
st-gsheets-connection
pandas
📂 Data Schema
The application expects a Google Workbook with two specific worksheets:

Students: Student ID, Name, Total Classes, Date Joined

Attendance: Date, Student ID, Name
