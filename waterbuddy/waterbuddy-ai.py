import streamlit as st
import json
import os
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import time

# Optional: Desktop notification
try:
    from plyer import notification
except ImportError:
    notification = None

# ========= FILES =========
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
BADGES_FILE = "badges.json"

st.set_page_config(page_title="💧 WaterBuddy", page_icon="💧", layout="wide")

# ========= GLOBAL STYLES =========
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #e0f7fa 0%, #e3f2fd 100%);
}
div[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #d7f3ff 0%, #f2fcff 100%);
}
h1, h2, h3 {
    color: #0077b6 !important;
    font-family: 'Poppins', sans-serif;
}
button, .stButton button {
    background: linear-gradient(90deg, #0077b6, #00b4d8);
    color: white !important;
    border-radius: 12px !important;
    padding: 0.6em 1em !important;
    border: none;
    transition: 0.3s;
}
button:hover {
    background: linear-gradient(90deg, #00b4d8, #0096c7);
    transform: scale(1.03);
}
</style>
""", unsafe_allow_html=True)

# ========= SAFE FILE HANDLING =========
def atomic_save(data, filename):
    tmp = filename + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, filename)

def load_json(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

users = load_json(USERS_FILE)
logs = load_json(LOGS_FILE)
badges = load_json(BADGES_FILE)

# ========= FUNCTIONS =========
def save_user(username, goal):
    users[username] = {"goal": goal, "created": datetime.now(timezone.utc).isoformat()}
    atomic_save(users, USERS_FILE)

def log_intake(username, amount):
    today = datetime.now(timezone.utc).date().isoformat()
    if username not in logs:
        logs[username] = {}
    logs[username][today] = logs[username].get(today, 0) + amount
    atomic_save(logs, LOGS_FILE)

def get_badges(username):
    if username not in badges:
        badges[username] = []
    return badges[username]

def award_badge(username, badge):
    user_badges = get_badges(username)
    if badge not in user_badges:
        user_badges.append(badge)
        badges[username] = user_badges
        atomic_save(badges, BADGES_FILE)

def send_notification(title, message):
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=5)
        except Exception:
            pass

# ========= APP UI =========
st.title("💧 WaterBuddy – Smart Hydration Tracker")

username = st.text_input("👤 Enter your name:")
if username:
    # 💧 Allow customizing goal anytime
    current_goal = users.get(username, {}).get("goal", 2000)
    goal = st.number_input("🎯 Set or update your daily goal (ml):", 100, 10000, current_goal)
    
    if st.button("💾 Save / Update Goal"):
        save_user(username, goal)
        st.success(f"Goal set to {goal}ml successfully! 💙")

    if username in users:
        st.subheader(f"Welcome back, {username}! 👋")
        amount = st.number_input("💦 Enter water intake (ml):", 100, 2000, 250)
        if st.button("➕ Add Intake"):
            log_intake(username, amount)
            st.success(f"{amount}ml logged successfully! ✅")

            today = datetime.now(timezone.utc).date().isoformat()
            total = logs.get(username, {}).get(today, 0)
            if total >= users[username]["goal"]:
                award_badge(username, "🏅 Goal Achiever")
                st.balloons()
                st.success("🎉 You reached your goal today! Awesome work!")
                send_notification("Hydration Goal Achieved!", "You’ve reached your daily water goal! 💧")

        # ===== PROGRESS SECTION =====
        st.subheader("📈 Today's Progress")

        today = datetime.now(timezone.utc).date().isoformat()
        total = logs.get(username, {}).get(today, 0)
        goal_value = users[username]["goal"]
        percent = max(0, min(100, int((total / goal_value) * 100)))

        # Circular Progress
        circle_html = f"""
        <div style="width:140px; height:140px; border-radius:50%;
            background: conic-gradient(#0077b6 {percent*3.6}deg, #e0f7fa 0deg);
            display:flex; align-items:center; justify-content:center; color:#0077b6;
            font-size:26px; font-weight:700; box-shadow: 0px 0px 10px rgba(0,0,0,0.2);">
            {percent}%
        </div>
        """
        st.markdown(circle_html, unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:#0096c7;'>💧 {total}ml / {goal_value}ml</h4>", unsafe_allow_html=True)

        # ===== HYDRATION HISTORY =====
        st.subheader("📊 Hydration History")

        user_logs = logs.get(username, {})
        if user_logs:
            df = pd.DataFrame(list(user_logs.items()), columns=["Date", "Intake (ml)"])
            df["Date"] = pd.to_datetime(df["Date"])
            df.sort_values("Date", inplace=True)

            fig, ax = plt.subplots(figsize=(7, 3.5))
            cmap = plt.cm.Blues
            norm = mcolors.Normalize(vmin=min(df["Intake (ml)"]), vmax=max(df["Intake (ml)"]))
            colors = cmap(norm(df["Intake (ml)"].values))

            bars = ax.bar(df["Date"], df["Intake (ml)"], color=colors, edgecolor="#005f73")
            ax.axhline(y=goal_value, color="#ff595e", linestyle="--", linewidth=1.5, label="Goal")
            ax.set_title("💦 Your Daily Water Intake", fontsize=13, color="#023e8a", weight="bold")
            ax.set_xlabel("Date", fontsize=11)
            ax.set_ylabel("Water Intake (ml)", fontsize=11)
            ax.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No data yet — start logging your water intake to see progress! 💧")

        # ===== BADGES SECTION =====
        st.subheader("🏆 Achievements")
        user_badges = get_badges(username)
        if user_badges:
            cols = st.columns(4)
            for i, badge in enumerate(user_badges):
                with cols[i % 4]:
                    st.markdown(f"<div style='font-size:45px; text-align:center;'>{badge}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#555;'>No badges yet. Stay hydrated and earn some! 🌊</p>", unsafe_allow_html=True)

        # ===== REMINDER =====
        st.subheader("🔔 Hydration Reminder")
        remind = st.slider("Remind me every (minutes):", 15, 180, 60)
        if st.button("🚰 Start Reminder"):
            st.info("Reminder active! You’ll get notifications periodically (simulated).")
            for i in range(3):  # simulate limited reminders
                time.sleep(remind * 0.1)
                send_notification("💧 Time to Drink Water!", "Hydrate yourself and stay fresh!")
            st.success("Reminder test completed ✅")

else:
    st.info("Please enter your name to begin 💧")
