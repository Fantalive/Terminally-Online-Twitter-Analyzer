import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
from streamlit_javascript import st_javascript

# -------------------- App Setup --------------------
st.set_page_config("Twitter/X Activity Analyzer", layout="centered")
st.title("📊 Twitter/X Activity Analyzer")
st.write("Analyze your posting frequency and classify your online behavior.")

# -------------------- Load from localStorage --------------------
default_group_data = [
    {"name": "Terminally Online", "threshold": 50},
    {"name": "Active User", "threshold": 10},
    {"name": "Casual User", "threshold": 0}
]
raw_group_data = st_javascript("JSON.parse(window.localStorage.getItem('group_config') || 'null');")
group_data = raw_group_data or default_group_data

# -------------------- Reset to Defaults --------------------
if st.button("🧼 Reset to Default Groups"):
    st_javascript("window.localStorage.removeItem('group_config');")
    st.rerun()

# -------------------- Grouping Mode --------------------
st.markdown("---")
st.subheader("🔧 Group Configuration")

grouping_mode = st.selectbox("Select Grouping Mode", ["Default Grouping", "Custom Thresholds"])
custom_thresholds = {}
custom_emojis = {}

if grouping_mode == "Custom Thresholds":
    with st.expander("🛠️ Customize Your Groupings", expanded=True):
        num_groups = st.slider("Number of Groups", min_value=2, max_value=10, value=len(group_data))
        group_data = group_data[:num_groups] + [{"name": f"Group {i+1}", "threshold": 0} for i in range(len(group_data), num_groups)]
        updated_data = []

        for i in range(num_groups):
            col1, col2 = st.columns([2, 1])
            with col1:
                name = st.text_input(f"Group {i+1} Name", key=f"name_{i}", value=group_data[i]["name"])
            with col2:
                threshold = st.number_input(f"Min Posts/Day", key=f"thresh_{i}", value=float(group_data[i]["threshold"]))
            updated_data.append({"name": name, "threshold": threshold})
            custom_thresholds[name] = threshold
            custom_emojis[name] = "🚨" if i == 0 else "⚡" if i == 1 else "🌿"

        # Save updated group config
        st_javascript(f"window.localStorage.setItem('group_config', JSON.stringify({json.dumps(updated_data)}));")

# -------------------- Number Formatting --------------------
st.markdown("---")
st.subheader("🔢 Number Format")
separator = st.selectbox("Choose Thousands Separator", [",", ".", " "], index=0)

def format_number(num):
    if separator == ",":
        return f"{num:,.2f}"
    elif separator == ".":
        return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif separator == " ":
        return f"{num:,.2f}".replace(",", " ").replace(".", ",")

# -------------------- Input --------------------
st.markdown("---")
st.subheader("🧾 Input Account Data")

posts_input = st.text_input("🔢 Total Number of Posts", format_number(0), key="posts_input")
try:
    posts = int(posts_input.replace(",", "").replace(".", "").replace(" ", ""))
except:
    st.error("⚠️ Invalid number format.")
    posts = None

date_input = st.text_input("📅 Account Creation Date", help="Enter like 'October 2008', '10/2008' or '10/08'")

# -------------------- Helpers --------------------
def parse_flexible_date(date_str):
    formats = [
		"%B %Y",      # October 2008
		"%m/%Y",      # 10/2008
		"%m/%y",      # 10/08
		"%d/%m/%Y",   # 30/03/2006
		"%Y-%m-%d",   # 2006-03-30
	]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt >= datetime(2006, 3, 21):
                return dt
        except:
            continue
    return None

def classify_user(posts_per_day, thresholds_dict):
    sorted_groups = sorted(thresholds_dict.items(), key=lambda x: x[1], reverse=True)
    for group_name, threshold in sorted_groups:
        if posts_per_day >= threshold:
            return group_name
    return "Uncategorized"

# -------------------- Calculate --------------------
if st.button("🧮 Calculate") and posts:
    creation_date = parse_flexible_date(date_input)

    if not creation_date:
        st.error("⚠️ Please enter a valid date after Twitter's launch (March 2006).")
    else:
        today = datetime.now()
        days_active = max((today - creation_date).days, 1)
        years_active = days_active / 365.25

        posts_per_day = posts / days_active
        posts_per_week = posts_per_day * 7
        posts_per_month = posts_per_day * 30.44
        posts_per_year = posts_per_day * 365.25

        # Milestones
        milestones = [50_000, 100_000, 250_000, 500_000, 1_000_000]
        milestone_outputs = []
        for milestone in milestones:
            if posts >= milestone:
                days_to_milestone = milestone / posts_per_day
                date_achieved = creation_date + timedelta(days=days_to_milestone)
                milestone_outputs.append(f"✅ **{milestone:,} posts** reached around ~**{date_achieved.strftime('%b %d, %Y')}**")
            else:
                posts_needed = milestone - posts
                est_days = posts_needed / posts_per_day if posts_per_day > 0 else float('inf')
                est_date = today + timedelta(days=est_days) if est_days < float('inf') else "∞"
                milestone_outputs.append(f"📅 **{milestone:,} posts** projected for **{est_date.strftime('%b %d, %Y') if isinstance(est_date, datetime) else '∞'}**")

        # Thresholds
        if grouping_mode == "Default Grouping":
            thresholds = {item["name"]: item["threshold"] for item in default_group_data}
            emojis = {"Terminally Online": "🚨", "Active User": "⚡", "Casual User": "🌿"}
        else:
            thresholds = custom_thresholds
            emojis = custom_emojis

        user_group = classify_user(posts_per_day, thresholds)
        emoji = emojis.get(user_group, "🔍")

        # -------------------- Output --------------------
        st.markdown("---")
        st.subheader("🧠 Classification")
        st.success(f"{emoji} **{user_group}**")

        st.subheader("📊 Posting Frequency")
        col1, col2 = st.columns(2)
        col1.metric("Posts per Day", format_number(posts_per_day))
        col2.metric("Posts per Week", format_number(posts_per_week))
        col1.metric("Posts per Month", format_number(posts_per_month))
        col2.metric("Posts per Year", format_number(posts_per_year))

        st.subheader("🕰️ Account Lifetime")
        st.write(f"Account age: **{years_active:.2f} years** (~{days_active} days)")

        st.subheader("🎯 Milestone Projections")
        for msg in milestone_outputs:
            st.markdown(msg)

        st.subheader("📉 Post Frequency Chart")
        categories = ["Per Day", "Per Week", "Per Month", "Per Year"]
        values = [posts_per_day, posts_per_week, posts_per_month, posts_per_year]

        fig, ax = plt.subplots()
        ax.bar(categories, values)
        ax.set_ylabel("Posts")
        ax.set_title("Post Frequency Breakdown")
        st.pyplot(fig)
