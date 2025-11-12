import streamlit as st
import json
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import random

# Optional desktop notifications
try:
    from plyer import notification
except Exception:
    notification = None

# ---------------- FILES ----------------
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
BADGES_FILE = "badges.json"

st.set_page_config(page_title="💧 Water Buddy - Hydration Tracker", page_icon="💦", layout="centered")

# ---------------- BEAUTIFUL CSS ----------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] > section:first-child {
  height: 100%;
  background: linear-gradient(135deg, #6dd5ed, #2193b0);
  background-size: 300% 300%;
  animation: gradientMove 10s ease infinite;
}
@keyframes gradientMove {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
div.stButton > button {
  border-radius: 12px;
  padding: 12px 25px;
  font-weight: 600;
  background: linear-gradient(90deg, #0072ff, #00c6ff);
  color: white;
  border: none;
  transition: 0.3s;
}
div.stButton > button:hover {
  transform: scale(1.05);
  filter: brightness(115%);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #00c6ff 0%, #0072ff 100%);
  color: white;
}
h1, h2, h3 {
  color: #004aad !important;
  text-shadow: 0px 0px 8px rgba(0, 162, 255, 0.4);
}
hr {
  border: 1px solid rgba(255,255,255,0.3);
}
</style>
""", unsafe_allow_html=True)

# ---------------- UTILITIES ----------------
def atomic_save(filename, data):
    s = json.dumps(data, indent=4)
    dirn = os.path.dirname(os.path.abspath(filename)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirn, prefix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(s)
        os.replace(tmp_path, filename)
    except Exception:
        with open(filename, "w") as f:
            f.write(s)

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_data(filename, data):
    atomic_save(filename, data)

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_health_adjustment(conditions):
    multiplier = 1.0
    if conditions.get("Heart Issue", False): multiplier += 0.12
    if conditions.get("Diabetes", False): multiplier += 0.10
    if conditions.get("Kidney Issue", False): multiplier += 0.15
    return multiplier

def calculate_daily_goal(age, conditions):
    base = 2000
    if age < 18: base = 1800
    elif age > 60: base = 1700
    return int(base * calculate_health_adjustment(conditions))

def sign_up(name, email, password, age, profession, health_conditions):
    users = load_data(USERS_FILE)
    if email in users:
        st.error("😕 Email already registered.")
        return False
    goal = calculate_daily_goal(age, health_conditions)
    users[email] = {
        "name": name,
        "profession": profession,
        "password": hash_password(password),
        "age": age,
        "health_conditions": health_conditions,
        "daily_goal": goal,
        "created_at": datetime.now(timezone.utc).isoformat()
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
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logs.setdefault(email, {}).setdefault(today, 0)
    logs[email][today] += int(amount_ml)
    save_data(LOGS_FILE, logs)

def get_today_log(email):
    logs = load_data(LOGS_FILE)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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

def send_reminder():
    st.toast("💧 Time to drink water!", icon="💧")
    if notification:
        try:
            notification.notify(title="💧 Water Buddy Reminder", message="Time to hydrate yourself!", timeout=5)
        except Exception:
            pass

# ---------------- QUOTES ----------------
MOTIVATION_QUOTES = [
    "💪 Keep going! Every sip counts!",
    "🌿 Hydration = Happiness!",
    "🚀 You're fueling your body for greatness!",
    "💙 Drink water, shine brighter!",
    "🌞 Healthy habits start with hydration!",
    "✨ Stay cool, stay hydrated!",
    "🏅 Consistency makes champions!"
]

def get_quote():
    return random.choice(MOTIVATION_QUOTES)

# ---------------- PLOT ----------------
def plot_progress_chart(email):
    logs = get_logs(email)
    today = datetime.now(timezone.utc).date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [d.strftime("%b %d") for d in dates]
    values = [logs.get(d.strftime("%Y-%m-%d"), 0) for d in dates]
    user = get_user_profile(email)
    goal = user.get("daily_goal", 2000)

    plt.figure(figsize=(8, 4))
    bars = plt.bar(labels, values, color="#0072ff", alpha=0.85)
    plt.axhline(goal, color="#00c6ff", linestyle="--", label=f"Goal: {goal} ml")
    plt.title("💧 Weekly Hydration Progress")
    plt.ylabel("Water Intake (ml)")
    plt.legend()
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, val + 50, f"{val}", ha="center", fontsize=9)
    st.pyplot(plt)

# ---------------- MAIN ----------------
def main():
    st.markdown("<h1 style='text-align:center;'>💧 Water Buddy — Hydration Tracker</h1>", unsafe_allow_html=True)
    if "user" not in st.session_state:
        st.session_state.user = None

    # ----------- LOGIN / SIGN UP -----------
    if not st.session_state.user:
        st.markdown("### Stay hydrated and healthy every day 💙")
        option = st.selectbox("Choose an option:", ["Sign In", "Sign Up"])
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")

        if option == "Sign Up":
            name = st.text_input("👤 Full Name")
            age = st.number_input("🎂 Age", 1, 120, 25)
            profession = st.text_input("💼 Profession")
            st.markdown("### 🩺 Select any health conditions:")
            health_conditions = {
                "Heart Issue": st.checkbox("❤️ Heart Issue"),
                "Diabetes": st.checkbox("🩸 Diabetes"),
                "Kidney Issue": st.checkbox("🦵 Kidney Issue")
            }
            if st.button("Sign Up 💧", use_container_width=True):
                if not (name and email and password and profession):
                    st.error("Please fill in all fields.")
                elif sign_up(name, email, password, age, profession, health_conditions):
                    st.success("✅ Sign-up successful! Please sign in now.")
        else:
            if st.button("Sign In 💦", use_container_width=True):
                if email and password and sign_in(email, password):
                    st.success(f"Welcome back, {get_user_profile(email)['name']}!")
                    st.rerun()
        return

    # ----------- DASHBOARD -----------
    email = st.session_state.user
    profile = get_user_profile(email)
    if not profile:
        st.error("⚠️ Profile not found. Please sign in again.")
        st.session_state.user = None
        return

    st.sidebar.title("👋 Welcome")
    st.sidebar.markdown(f"**Name:** {profile['name']}")
    st.sidebar.markdown(f"**Age:** {profile['age']}")
    st.sidebar.markdown(f"**Profession:** {profile['profession']}")
    conds = ", ".join([k for k, v in profile["health_conditions"].items() if v]) or "None"
    st.sidebar.markdown(f"**Health Conditions:** {conds}")
    if st.sidebar.button("🚪 Sign Out"):
        st.session_state.user = None
        st.rerun()

    st.markdown("---")

    daily_goal = profile["daily_goal"]
    today_total = get_today_log(email)
    progress = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0

    st.markdown(f"### 💧 Today's Hydration: **{today_total} ml / {daily_goal} ml** ({progress}%)")
    st.progress(min(progress, 100))

    st.info(get_quote())

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("100 ml 💧"):
            log_water(email, 100)
            st.balloons()
            st.success(get_quote())
            st.rerun()
    with c2:
        if st.button("200 ml 💦"):
            log_water(email, 200)
            st.balloons()
            st.success(get_quote())
            st.rerun()
    with c3:
        custom = st.number_input("Custom (ml)", 10, 5000, 250)
        if st.button("Add Custom 🚰"):
            log_water(email, custom)
            st.balloons()
            st.success(get_quote())
            st.rerun()

    st.markdown("---")
    plot_progress_chart(email)

    # Badges
    if progress >= 100:
        award_badge(email, "🏅 Hydration Hero")
        st.success("🎉 You earned the Hydration Hero Badge!")
    badges = get_badges(email)
    if badges:
        st.markdown("### 🏅 Your Badges:")
        for b in badges:
            st.markdown(f"- {b}")

    # Reminder
    st.markdown("---")
    st.markdown("### ⏰ Smart Reminders")
    enable = st.checkbox("Enable Reminders", value=False)
    interval = st.slider("Reminder Frequency (minutes)", 15, 120, 30)
    if enable:
        if "next_reminder" not in st.session_state:
            st.session_state.next_reminder = datetime.now(timezone.utc) + timedelta(minutes=interval)
        if datetime.now(timezone.utc) >= st.session_state.next_reminder:
            send_reminder()
            st.session_state.next_reminder = datetime.now(timezone.utc) + timedelta(minutes=interval)
        st.info(f"💧 Reminder active! Every {interval} minutes.")
    else:
        st.warning("Reminders are off. Enable to stay hydrated!")

    # Daily Summary
    st.markdown("---")
    if progress >= 100:
        st.success("💙 Excellent! You've achieved your hydration goal today!")
    elif progress >= 75:
        st.info("🌿 Almost there! Just a few more sips!")
    elif progress >= 50:
        st.warning("💧 Halfway there! Keep it up!")
    else:
        st.error("🥵 Less than 50%. Time to hydrate, champ!")

if __name__ == "__main__":
    main()
