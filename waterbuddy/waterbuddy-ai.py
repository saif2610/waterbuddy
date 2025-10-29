import streamlit as st
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from plyer import notification  # For desktop notifications
import time

USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
BADGES_FILE = "badges.json"

st.set_page_config(page_title="Water Buddy 💧 Personalized Dashboard", page_icon="💧", layout="centered")

# ---------------- CSS (Water Flow Theme) ---------------- #
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] > section:first-child {
  height: 100%;
  background: linear-gradient(135deg, #00c6ff, #0072ff, #00c6ff, #0072ff);
  background-size: 400% 400%;
  animation: waterflow 12s ease infinite;
  backdrop-filter: blur(20px);
}

div.stButton > button {
  border-radius: 14px;
  padding: 14px 28px;
  font-weight: 600;
  color: white;
  background: linear-gradient(90deg, #00aaff, #0072ff, #00aaff);
  background-size: 200% 200%;
  border: none;
  transition: all 0.3s ease;
  animation: waterflow 8s linear infinite;
}
div.stButton > button:hover {
  filter: brightness(115%);
  transform: scale(1.03);
}

@keyframes waterflow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0072ff 0%, #00c6ff 100%);
  color: white;
  animation: waterflow 15s ease infinite;
}

h1, h2, h3, h4 {
  color: #004aad !important;
  text-shadow: 0px 0px 8px rgba(0, 162, 255, 0.5);
}

hr {
  border: 1px solid rgba(0, 102, 255, 0.3);
}
</style>
""", unsafe_allow_html=True)

# ---------------- Utility Functions ---------------- #
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_health_adjustment(conditions):
    multiplier = 1.0
    if conditions.get("Heart Issue", False):
        multiplier += 0.12
    if conditions.get("Diabetes", False):
        multiplier += 0.10
    if conditions.get("Kidney Issue", False):
        multiplier += 0.15
    return multiplier

def calculate_daily_goal(age, conditions):
    base_goal = 2000
    if age < 18:
        base_goal = 1800
    elif age > 60:
        base_goal = 1700
    return int(base_goal * calculate_health_adjustment(conditions))

def sign_up(name, email, password, age, health_conditions):
    users = load_data(USERS_FILE)
    if email in users:
        st.error("😕 Email already registered.")
        return False
    goal = calculate_daily_goal(age, health_conditions)
    users[email] = {
        "name": name,
        "password": hash_password(password),
        "age": age,
        "health_conditions": health_conditions,
        "daily_goal": goal,
        "created_at": datetime.utcnow().isoformat()
    }
    save_data(USERS_FILE, users)
    return True

def sign_in(email, password):
    users = load_data(USERS_FILE)
    if email not in users:
        st.error("😕 Email not registered.")
        return False
    if users[email]["password"] != hash_password(password):
        st.error("😕 Incorrect password.")
        return False
    st.session_state.user = email
    return True

def get_user_profile(email):
    return load_data(USERS_FILE).get(email)

def log_water(email, amount_ml):
    logs = load_data(LOGS_FILE)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    logs.setdefault(email, {}).setdefault(today, 0)
    logs[email][today] += amount_ml
    save_data(LOGS_FILE, logs)

def get_today_log(email):
    logs = load_data(LOGS_FILE)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return logs.get(email, {}).get(today, 0)

def get_logs(email):
    return load_data(LOGS_FILE).get(email, {})

def award_badge(email, badge_name):
    badges = load_data(BADGES_FILE)
    badges.setdefault(email, [])
    if badge_name not in badges[email]:
        badges[email].append(badge_name)
    save_data(BADGES_FILE, badges)

def get_badges(email):
    return load_data(BADGES_FILE).get(email, [])

def show_emoji(progress_percent):
    if progress_percent >= 100:
        return "🎉🥳"
    elif progress_percent >= 75:
        return "🙂"
    elif progress_percent >= 50:
        return "😴"
    else:
        return "😠"

def plot_progress_chart(email):
    logs = get_logs(email)
    if not logs:
        st.info("No hydration data yet.")
        return
    df = pd.DataFrame([{"date": d, "totalMl": v} for d, v in logs.items()])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(7)
    plt.figure(figsize=(9, 4))
    plt.bar(df["date"].dt.strftime("%a %b %d"), df["totalMl"], color="#0072ff", edgecolor="black", alpha=0.8)
    goal = get_user_profile(email).get("daily_goal", 2000)
    plt.axhline(y=goal, color="#00c6ff", linestyle="--", linewidth=2, label="Goal")
    plt.xticks(rotation=45, fontsize=11)
    plt.ylabel("Water Intake (ml)", fontsize=12)
    plt.title("Water Intake - Last 7 Days", fontsize=15, weight="bold", color="#004aad")
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)

def progress_circle(progress):
    col1, col2, col3 = st.columns([1,6,1])
    with col2:
        circle = f"""
        <svg viewBox="0 0 36 36" width="140" height="140" role="img">
          <path fill="none" stroke="#e5e7eb" stroke-width="4" d="M18 2.0845
            a 15.9155 15.9155 0 0 1 0 31.831
            a 15.9155 15.9155 0 0 1 0 -31.831"/>
          <path fill="none" stroke="#00aaff" stroke-width="4"
            stroke-dasharray="{progress}, 100" d="M18 2.0845
            a 15.9155 15.9155 0 0 1 0 31.831
            a 15.9155 15.9155 0 0 1 0 -31.831"/>
          <text x="18" y="20.35" fill="#004aad" font-size="8" font-weight="bold" text-anchor="middle">{progress}%</text>
        </svg>
        """
        st.markdown(circle, unsafe_allow_html=True)

# ---------------- Reminder Function ---------------- #
def send_reminder():
    """Send a desktop + in-app reminder."""
    st.toast("💧 Time to drink water!", icon="💧")
    try:
        notification.notify(
            title="Water Buddy Reminder 💧",
            message="Time to take a sip of water and stay hydrated!",
            timeout=5
        )
    except:
        pass

# ---------------- MAIN ---------------- #
def main():
    st.markdown("<h1 style='color:#004aad; font-weight:bold;'>Water Buddy 💧 Personalized Dashboard</h1>", unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.session_state.user = None

    # --- Login / Signup --- #
    if not st.session_state.user:
        st.markdown("### Stay hydrated and healthy with your personalized water tracking companion.")
        action = st.selectbox("", ["Sign In", "Sign Up"], label_visibility="collapsed")
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")

        if action == "Sign Up":
            name = st.text_input("👤 Name")
            age = st.number_input("🧓 Age", 1, 120, 30)
            st.markdown("### Please select your health conditions affecting hydration:")
            health_conditions = {
                "Heart Issue": st.checkbox("❤️ Heart Issue"),
                "Diabetes": st.checkbox("🩸 Diabetes"),
                "Kidney Issue": st.checkbox("🦵 Kidney Issue")
            }
            if st.button("Sign Up", use_container_width=True):
                if not name or not email or not password:
                    st.error("Please fill all fields.")
                elif sign_up(name, email, password, age, health_conditions):
                    st.success("Sign up successful! Please sign in.")
        else:
            if st.button("Sign In", use_container_width=True):
                if email and password and sign_in(email, password):
                    st.success(f"Welcome back, {get_user_profile(email)['name']}!")
                    st.rerun()
                else:
                    st.error("Fill in valid credentials.")
        return

    # --- Dashboard --- #
    email = st.session_state.user
    profile = get_user_profile(email)
    st.sidebar.markdown(f"### Hello, <span style='color:white;'>{profile['name']}</span> 👋", unsafe_allow_html=True)
    st.sidebar.markdown(f"**Age:** {profile['age']}")
    conds = ", ".join([k for k,v in profile["health_conditions"].items() if v]) or "None"
    st.sidebar.markdown(f"**Health Conditions:** {conds}")
    daily_goal = profile["daily_goal"]

    if st.sidebar.button("Sign Out"):
        st.session_state.user = None
        st.rerun()

    today_total = get_today_log(email)
    progress_percent = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0
    emoji_face = show_emoji(progress_percent)

    st.markdown(f"<h3 style='color:#004aad;'>Today's Progress: {progress_percent}% {emoji_face}</h3>", unsafe_allow_html=True)
    progress_circle(min(progress_percent, 100))
    st.markdown(f"<h4 style='color:#004aad;'>Total water logged today: <strong>{today_total} ml</strong> / {daily_goal} ml</h4>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Water Logging Buttons --- #
    cols = st.columns(3)
    with cols[0]:
        if st.button("100 ml 💧", key="btn100"):
            log_water(email, 100)
            st.rerun()
    with cols[1]:
        if st.button("200 ml 💧", key="btn200"):
            log_water(email, 200)
            st.rerun()
    with cols[2]:
        custom_amount = st.number_input("Custom ml", 10, 5000, 250, step=10, key="custom_input")
        if st.button("Add Custom 💦", key="btncustom"):
            log_water(email, int(custom_amount))
            st.rerun()

    # --- Chart --- #
    st.markdown("---")
    st.markdown("<h3 style='color:#004aad;'>Track Your Progress 📊</h3>", unsafe_allow_html=True)
    plot_progress_chart(email)

    # --- Badges --- #
    st.markdown("---")
    st.markdown("<h3 style='color:#004aad;'>Badges & History 🏅</h3>", unsafe_allow_html=True)
    badges = get_badges(email)
    if progress_percent >= 100 and "Hydration Hero Badge 🏅" not in badges:
        award_badge(email, "Hydration Hero Badge 🏅")
        st.balloons()
        st.success("You earned the Hydration Hero Badge 🏅 — keep up the streak!")
        badges.append("Hydration Hero Badge 🏅")

    if badges:
        cols = st.columns(len(badges))
        for col, badge in zip(cols, badges):
            col.markdown(f"<div style='background:#00aaff; color:white; border-radius:12px; padding:10px 15px; text-align:center; font-weight:bold;'>{badge}</div>", unsafe_allow_html=True)
    else:
        st.write("No badges yet. Keep going!")

    # --- Reminders (Working) --- #
    st.markdown("---")
    st.markdown("<h3 style='color:#004aad;'>Reminders ⏰</h3>", unsafe_allow_html=True)
    enable = st.checkbox("Enable Reminders", value=False)
    interval = st.slider("Reminder Frequency (minutes)", 5, 120, 30)

    if enable:
        if "next_reminder" not in st.session_state:
            st.session_state.next_reminder = datetime.now() + timedelta(minutes=interval)

        if datetime.now() >= st.session_state.next_reminder:
            send_reminder()
            st.session_state.next_reminder = datetime.now() + timedelta(minutes=interval)

        st.info(f"💧 Reminder active! You'll be reminded every {interval} minutes.")
    else:
        st.warning("Reminders are off. Enable to get hydration alerts.")

if __name__ == "__main__":
    main()
