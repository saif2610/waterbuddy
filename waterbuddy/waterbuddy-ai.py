import streamlit as st
import json
import os
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time

try:
    from plyer import notification
except ImportError:
    notification = None

# -------------------- File Constants -------------------- #
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
BADGES_FILE = "badges.json"

st.set_page_config(page_title="💧 WaterBuddy", page_icon="💧", layout="centered")

# -------------------- CSS (Modern Blue Theme) -------------------- #
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: #003366;
}
div.stButton > button {
    border-radius: 12px;
    background: linear-gradient(90deg, #00b4d8, #0077b6);
    color: white;
    font-weight: bold;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background: linear-gradient(90deg, #0096c7, #023e8a);
    transform: scale(1.05);
}
h1, h2, h3 {
    color: #004aad !important;
    text-shadow: 0px 0px 8px rgba(0, 162, 255, 0.4);
}
</style>
""", unsafe_allow_html=True)

# -------------------- Utility Functions -------------------- #
def atomic_save(data, filename):
    tmp = filename + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, filename)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------- Load Data -------------------- #
users = load_json(USERS_FILE)
logs = load_json(LOGS_FILE)
badges = load_json(BADGES_FILE)

# -------------------- Functions -------------------- #
def calculate_daily_goal(age, health_conditions):
    base = 2000
    if age < 18:
        base = 1800
    elif age > 60:
        base = 1700

    if health_conditions.get("Heart Issue"):
        base *= 1.1
    if health_conditions.get("Diabetes"):
        base *= 1.08
    if health_conditions.get("Kidney Issue"):
        base *= 1.15

    return int(base)

def save_user(email, name, age, profession, health_conditions):
    goal = calculate_daily_goal(age, health_conditions)
    users[email] = {
        "name": name,
        "age": age,
        "profession": profession,
        "health_conditions": health_conditions,
        "goal": goal,
        "created": datetime.now(timezone.utc).isoformat()
    }
    atomic_save(users, USERS_FILE)
    return goal

def log_intake(email, amount):
    today = datetime.now(timezone.utc).date().isoformat()
    if email not in logs:
        logs[email] = {}
    logs[email][today] = logs[email].get(today, 0) + amount
    atomic_save(logs, LOGS_FILE)

def get_badges(email):
    if email not in badges:
        badges[email] = []
    return badges[email]

def award_badge(email, badge):
    if badge not in badges[email]:
        badges[email].append(badge)
        atomic_save(badges, BADGES_FILE)

def send_notification(title, message):
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=5)
        except Exception:
            pass

# -------------------- Main App -------------------- #
st.title("💧 WaterBuddy — Smart Hydration Tracker")

if "user" not in st.session_state:
    st.session_state.user = None

# -------------------- Page 1: Profile Setup -------------------- #
if not st.session_state.user:
    st.markdown("### 👋 Let's get to know you better!")
    name = st.text_input("Your Name")
    email = st.text_input("Email ID")
    age = st.number_input("Your Age", 1, 120, 25)
    profession = st.selectbox("Profession", ["Student", "Teacher", "Office Worker", "Athlete", "Retired", "Other"])
    st.markdown("### 💊 Any health conditions?")
    health_conditions = {
        "Heart Issue": st.checkbox("❤️ Heart Issue"),
        "Diabetes": st.checkbox("🩸 Diabetes"),
        "Kidney Issue": st.checkbox("🦵 Kidney Issue")
    }

    if st.button("Continue ➡️"):
        if not name or not email:
            st.error("Please fill in all fields!")
        else:
            goal = save_user(email, name, age, profession, health_conditions)
            st.session_state.user = email
            st.success(f"Welcome {name}! Your daily water goal is {goal} ml 💧")
            st.rerun()
    st.stop()

# -------------------- Dashboard -------------------- #
email = st.session_state.user
profile = users[email]
st.sidebar.markdown(f"### 👤 {profile['name']}")
st.sidebar.write(f"**Age:** {profile['age']}")
st.sidebar.write(f"**Profession:** {profile['profession']}")
conds = ", ".join([k for k, v in profile["health_conditions"].items() if v]) or "None"
st.sidebar.write(f"**Health Issues:** {conds}")
goal = profile["goal"]

if st.sidebar.button("🔒 Log Out"):
    st.session_state.user = None
    st.rerun()

# -------------------- Main Dashboard -------------------- #
today = datetime.now(timezone.utc).date().isoformat()
total = logs.get(email, {}).get(today, 0)
progress = min(100, int((total / goal) * 100))
emoji = "😠" if progress < 50 else "🙂" if progress < 80 else "🎉"

st.markdown(f"### 💧 Today's Progress: {progress}% {emoji}")
st.progress(progress / 100)
st.write(f"**Total Intake:** {total} ml / {goal} ml")

# -------------------- Add Water Buttons -------------------- #
cols = st.columns(3)
if cols[0].button("💧 100 ml"):
    log_intake(email, 100)
    st.rerun()
if cols[1].button("💦 250 ml"):
    log_intake(email, 250)
    st.rerun()
with cols[2]:
    custom = st.number_input("Custom (ml)", 10, 5000, 300)
    if st.button("Add Custom 💧"):
        log_intake(email, int(custom))
        st.rerun()

# -------------------- Chart -------------------- #
st.markdown("### 📊 Weekly Hydration Chart")
user_logs = logs.get(email, {})
if user_logs:
    df = pd.DataFrame(list(user_logs.items()), columns=["Date", "Intake"])
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(df["Date"], df["Intake"], color="#00b4d8", edgecolor="#0077b6")
    ax.axhline(y=goal, color="red", linestyle="--", label="Goal")
    ax.set_xlabel("Date")
    ax.set_ylabel("Water Intake (ml)")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("No history yet — start logging water!")

# -------------------- Badges -------------------- #
st.markdown("### 🏅 Badges & Achievements")
if total >= goal and "Goal Achiever" not in get_badges(email):
    award_badge(email, "Goal Achiever")
    st.balloons()
    st.success("🎉 You reached your daily goal!")

for badge in get_badges(email):
    st.markdown(f"🏆 **{badge}**")

# -------------------- Reminder -------------------- #
st.markdown("### ⏰ Hydration Reminder")
remind = st.slider("Remind me every (minutes):", 15, 120, 30)
if st.button("Start Reminder"):
    st.info("💧 Reminder active! You’ll get a gentle reminder soon.")
    time.sleep(1)
    send_notification("💧 WaterBuddy Reminder", "Time to sip some water!")

