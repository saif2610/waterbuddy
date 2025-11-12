import streamlit as st
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import threading
import time

# Optional desktop notifications
try:
    from plyer import notification
except Exception:
    notification = None

# ---------- CONFIG ----------
st.set_page_config(page_title="💧 Water Buddy", page_icon="💧", layout="centered")

USERS_FILE = "users.json"
LOGS_FILE = "logs.json"

# ---------- UTILITIES ----------
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
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=4)
        except Exception:
            pass

# ---------- INITIALIZE ----------
users = load_data(USERS_FILE)
logs = load_data(LOGS_FILE)
if "page" not in st.session_state:
    st.session_state.page = "intro"
if "last_reminder" not in st.session_state:
    st.session_state.last_reminder = time.time()

# ---------- INTRO PAGE ----------
if st.session_state.page == "intro":
    st.markdown(
        """
        <h1 style="color:#0072ff;text-align:center;">💧 Water Buddy</h1>
        <h3 style="text-align:center;">Your Smart Hydration Partner 🌿</h3>
        """,
        unsafe_allow_html=True,
    )

    st.write("Let's personalize your hydration journey 💙")

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

    st.markdown("---")
    st.markdown("### 🩵 Health & Hydration Tips:")
    tips = [
        "Drink a glass of water first thing in the morning 🌞",
        "Keep a reusable bottle nearby 💧",
        "Take small sips regularly 💦",
        "Avoid dehydration by tracking your intake ⏱️",
        "Add lemon or mint for natural flavor 🍋",
    ]
    for tip in tips:
        st.write(f"- {tip}")

    st.markdown("---")
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
    st.markdown(
        """
        <h1 style="color:#0072ff;text-align:center;">💧 Water Intake Tracker</h1>
        <h4 style="text-align:center;color:#555;">Stay hydrated, stay healthy 🌿</h4>
        """,
        unsafe_allow_html=True,
    )

    # Profile summary
    if "profile" in users:
        prof = users["profile"]
        st.markdown(
            f"<p style='text-align:center;font-size:16px;'>👤 <b>Age:</b> {prof['age']} &nbsp;&nbsp; 💼 <b>Profession:</b> {prof['profession']} &nbsp;&nbsp; ⚕️ <b>Health:</b> {', '.join(prof['diseases']) if prof['diseases'] else 'None'}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---------- DAILY TRACK ----------
    daily_goal = 2500  # ml/day
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in logs:
        logs[today] = {"intake": 0, "timestamps": []}
        save_data(LOGS_FILE, logs)

    intake = logs[today]["intake"]
    percent = round((intake / daily_goal) * 100, 1)

    # Display metrics
    st.metric(
        label="💧 Total Intake Today",
        value=f"{intake} ml",
        delta=f"{max(0, daily_goal - intake)} ml left",
    )
    st.progress(min(intake / daily_goal, 1.0))

    # Add water
    add_ml = st.number_input("Add water (ml):", min_value=50, max_value=1000, step=50)
    if st.button("✅ Log Water"):
        logs[today]["intake"] += add_ml
        logs[today]["timestamps"].append(datetime.now().strftime("%H:%M:%S"))
        save_data(LOGS_FILE, logs)
        notify_user("Water Buddy", f"You drank {add_ml} ml of water 💦")
        st.balloons()
        st.success("Water added successfully! Keep going 💧")
        time.sleep(0.6)
        st.rerun()

    # ---------- REMINDER SYSTEM ----------
    st.markdown("---")
    st.markdown("### ⏰ Hydration Reminder")

    interval = st.slider("Set reminder interval (minutes)", 15, 120, 60)
    current_time = time.time()

    if current_time - st.session_state.last_reminder >= interval * 60:
        notify_user("💧 Time to drink water!", "Keep yourself hydrated 💙")
        st.session_state.last_reminder = current_time
        st.info("🔔 Reminder sent!")

    st.caption("Reminders appear as desktop notifications every few minutes.")

    # ---------- WEEKLY HYDRATION PROGRESS ----------
    st.markdown("---")
    st.markdown("### 📈 Weekly Hydration Progress")

    today_date = datetime.now().date()
    last7 = [(today_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    intake_vals = [logs.get(d, {}).get("intake", 0) for d in last7]

    df_plot = pd.DataFrame({
        "Date": [datetime.strptime(d, "%Y-%m-%d").strftime("%a %d %b") for d in last7],
        "Intake": intake_vals
    })

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar(df_plot["Date"], df_plot["Intake"], color="#4FC3F7", edgecolor="#0277BD")
    ax.axhline(y=daily_goal, color="#FF5252", linestyle="--", linewidth=1.3, label=f"Goal ({daily_goal} ml)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Water (ml)")
    ax.set_title("Hydration Over Time")
    ax.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()
    st.pyplot(fig)

    # ---------- SUMMARY ----------
    st.markdown("---")
    st.markdown("### 📊 Today's Hydration Summary")
    st.write(f"**You’ve completed {percent}% of your daily goal!**")

    if percent < 50:
        st.warning("🟥 Below 50% — You need more water! Stay hydrated 💧")
    elif percent < 90:
        st.info("🟨 Doing great! A bit more to reach your target 💪")
    elif percent < 100:
        st.success("🟩 Great work! Almost there 💦")
    else:
        st.balloons()
        st.success("🎉 Excellent! You’ve achieved your daily hydration goal 🏆")

    st.markdown("---")
    st.info("💡 Tip: Set reminders to sip every hour for optimal hydration.")

    if st.button("🔁 Go Back"):
        st.session_state.page = "intro"
        st.rerun()
