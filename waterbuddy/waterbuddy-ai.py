import streamlit as st
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from plyer import notification
import os
import time

# ---------- CONFIG ----------
st.set_page_config(page_title="💧 Water Buddy", page_icon="💧", layout="centered")

USERS_FILE = "users.json"
LOGS_FILE = "logs.json"

# ---------- UTIL FUNCTIONS ----------
def load_data(file):
    if not os.path.exists(file):
        return {}
    try:
        with open(file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def notify_user(title, message):
    try:
        notification.notify(title=title, message=message, timeout=3)
    except Exception:
        pass

# ---------- INIT DATA ----------
users = load_data(USERS_FILE)
logs = load_data(LOGS_FILE)

# ---------- PAGE SELECTION ----------
if "page" not in st.session_state:
    st.session_state.page = "intro"

# ---------- INTRO PAGE ----------
if st.session_state.page == "intro":
    st.title("💧 Welcome to **Water Buddy**")
    st.subheader("Your Personal Hydration Coach 💙")

    st.write("Before we begin, please share a few quick details:")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("👶 Age", min_value=5, max_value=100, step=1)
        profession = st.selectbox(
            "💼 Profession", ["Student", "Teacher", "Athlete", "Office Worker", "Other"]
        )
    with col2:
        diseases = st.multiselect(
            "⚕️ Any health conditions?",
            ["None", "Diabetes", "Kidney issues", "High BP", "Heart disease", "Other"],
        )

    st.divider()

    st.markdown("### 🩵 Health & Hydration Tips:")
    tips = [
        "Drink a glass of water first thing in the morning 🌞",
        "Keep a reusable bottle with you everywhere 💧",
        "Take small sips regularly instead of gulping 💦",
        "Avoid dehydration by tracking your intake ⏱️",
        "Add lemon or mint to your water for taste 🍋",
    ]
    st.write("• " + "\n• ".join(tips))

    if st.button("✨ Start Tracking"):
        users["profile"] = {
            "age": age,
            "profession": profession,
            "diseases": diseases,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_data(USERS_FILE, users)
        st.session_state.page = "tracker"
        st.rerun()

# ---------- TRACKER PAGE ----------
elif st.session_state.page == "tracker":
    st.title("💧 Water Intake Tracker")
    st.caption("Stay hydrated, stay healthy 🌿")

    # Profile summary
    if "profile" in users:
        prof = users["profile"]
        st.markdown(
            f"**👤 Age:** {prof['age']} &nbsp;&nbsp; "
            f"**💼 Profession:** {prof['profession']} &nbsp;&nbsp; "
            f"**⚕️ Diseases:** {', '.join(prof['diseases']) if prof['diseases'] else 'None'}"
        )
        st.divider()

    # Input for water intake
    today = datetime.now().strftime("%Y-%m-%d")
    water_goal = 2500  # ml
    if today not in logs:
        logs[today] = {"intake": 0, "timestamps": []}

    intake = logs[today]["intake"]
    percent = round((intake / water_goal) * 100, 1) if water_goal > 0 else 0

    st.metric(
        label="💧 Total Intake Today",
        value=f"{intake} ml",
        delta=f"{water_goal - intake} ml left",
    )

    st.progress(min(intake / water_goal, 1.0))

    add_ml = st.number_input("Add water (ml):", min_value=50, max_value=1000, step=50)
    if st.button("✅ Log Water"):
        logs[today]["intake"] += add_ml
        logs[today]["timestamps"].append(datetime.now().strftime("%H:%M:%S"))
        save_data(LOGS_FILE, logs)
        notify_user("Water Buddy", f"You drank {add_ml} ml of water 💦")
        st.balloons()  # 🎈 Balloons fly after each log
        st.success("Water added successfully!")
        time.sleep(0.8)
        st.rerun()

    st.divider()

    # Chart
    st.markdown("### 📈 Your Weekly Hydration Progress")
    df = pd.DataFrame({
        "Date": list(logs.keys()),
        "Intake": [logs[day]["intake"] for day in logs]
    })
    df["Goal"] = water_goal
    df = df.tail(7)

    fig, ax = plt.subplots()
    ax.bar(df["Date"], df["Intake"], color="#4FC3F7", label="Water Intake")
    ax.axhline(y=water_goal, color="red", linestyle="--", label="Goal")
    ax.set_xlabel("Date")
    ax.set_ylabel("Water (ml)")
    ax.set_title("Last 7 Days Hydration")
    ax.legend()
    plt.xticks(rotation=30)
    st.pyplot(fig)

    st.divider()

    # 💧 Percentage & Daily Summary
    st.markdown("### 📊 Today's Hydration Summary")
    st.write(f"**You’ve completed {percent}% of your daily goal!**")

    if percent < 50:
        st.warning("🟥 You’re below 50%. Keep drinking water throughout the day! 💧")
    elif percent < 90:
        st.info("🟨 You’re doing well! Just a bit more to reach your target 💪")
    elif percent < 100:
        st.success("🟩 Great work! You’re almost there 💦")
    else:
        st.balloons()
        st.success("🎉 Excellent! You’ve completed your hydration goal for today! 🏆")

    st.divider()

    # Reminder & motivational message
    st.info("💡 Tip: Set hourly reminders on your phone or smartwatch to sip water.")

    st.button("🔁 Go Back", on_click=lambda: st.session_state.update(page="intro"))
