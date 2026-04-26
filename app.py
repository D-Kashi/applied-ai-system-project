import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from pawpal_system import Owner, Pet, Task
from agent import run_schedule_agent

load_dotenv()

# Resolve API key: Streamlit secrets (deployment) → .env / environment (local)
try:
    _api_key: str = st.secrets.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
except Exception:
    _api_key = os.environ.get("ANTHROPIC_API_KEY", "")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
gender = st.selectbox("Gender", ["male", "female", "unknown"])

# Per-owner storage: each owner_name gets its own Owner object and task display list
if "owners" not in st.session_state:
    st.session_state.owners = {}
if owner_name not in st.session_state.owners:
    st.session_state.owners[owner_name] = {"owner": Owner(owner_name), "tasks": []}

owner: Owner = st.session_state.owners[owner_name]["owner"]

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 2])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time_str = st.text_input("Start time (HH:MM)", value="08:00", max_chars=5)
with col3:
    am_pm = st.selectbox("AM/PM", ["AM", "PM"])
with col4:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col5:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# Add Pet button: call Owner.add_pet
if st.button("Add pet"):
    existing = next((p for p in owner.pets if p.name == pet_name), None)
    if not existing:
        new_pet = Pet(name=pet_name, type=species, gender=gender)
        owner.add_pet(new_pet)
        st.success(f"Added pet '{pet_name}'")
    else:
        st.info(f"Pet '{pet_name}' already exists")

# Add Task button: create Task and add to Owner's schedule
if st.button("Add task"):
    try:
        hour, minute = map(int, task_time_str.strip().split(":"))
        if not (1 <= hour <= 12 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        st.error("Invalid time. Use HH:MM with hour 1–12 (e.g. 08:00).")
        st.stop()
    # convert to 24-hour for internal storage
    if am_pm == "AM" and hour == 12:
        hour = 0
    elif am_pm == "PM" and hour != 12:
        hour += 12
    task_time = datetime(1900, 1, 1, hour, minute)
    display_time = f"{task_time_str.strip()} {am_pm}"
    pet_obj = next((p for p in owner.pets if p.name == pet_name), None)
    task = Task(type=task_title, time=task_time, pet=pet_obj)
    owner.add_task(task)
    st.session_state.owners[owner_name]["tasks"].append(
        {"id": task.id, "title": task_title, "time": display_time, "duration_minutes": int(duration), "priority": priority, "pet": pet_obj.name if pet_obj else None}
    )
    st.success(f"Added task '{task_title}' at {display_time}")

owner_tasks = st.session_state.owners[owner_name]["tasks"]
if owner_tasks:
    st.write("Current tasks:")
    display = [{k: v for k, v in t.items() if k != "id"} for t in owner_tasks]
    st.table(display)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

owner_state = st.session_state.owners[owner_name]

if st.button("Generate schedule"):
    owner_state["schedule_generated"] = True

if owner_state.get("schedule_generated"):
    pending_tasks = owner.schedule.get_pending_tasks()
    if not pending_tasks:
        st.info("All tasks completed or no tasks added yet.")
    else:
        conflicts = owner.schedule.detect_conflicts()
        if conflicts:
            st.warning("Task conflicts detected:")
            for conflict in conflicts:
                st.warning(conflict)
        else:
            st.success("No conflicts detected in your schedule.")

        sorted_tasks = owner.schedule.sort_by_time()
        st.markdown("### Scheduled tasks")

        header_cols = st.columns([3, 2, 2, 1, 1])
        for label, col in zip(["Task", "Time", "Pet", "Priority", "Done"], header_cols):
            col.markdown(f"**{label}**")

        to_complete = []
        for task in sorted_tasks:
            time_display = (
                task.time.strftime("%I:%M %p").lstrip("0")
                if isinstance(task.time, datetime)
                else str(task.time)
            )
            row = st.columns([3, 2, 2, 1, 1])
            row[0].write(task.type)
            row[1].write(time_display)
            row[2].write(task.pet.name if task.pet else "Unassigned")
            row[3].write(str(task.priority))
            if row[4].checkbox("", key=f"sched_done_{task.id}", label_visibility="collapsed"):
                to_complete.append(task.id)

        if to_complete:
            for task_id in to_complete:
                owner.schedule.set_task_completed(task_id)
                owner_state["tasks"] = [
                    t for t in owner_state["tasks"] if t["id"] != task_id
                ]
            st.rerun()

st.divider()

st.subheader("AI Schedule")
st.caption(
    "Runs an AI agent that plans, detects conflicts, checks its own work, "
    "then produces an optimized schedule with a reason for each task."
)

if st.button("Run AI Schedule"):
    if not _api_key:
        st.error("ANTHROPIC_API_KEY is not set. Add it to a .env file or Streamlit secrets.")
    elif not owner.schedule.get_pending_tasks():
        st.info("No pending tasks to schedule. Add some tasks first.")
    else:
        with st.spinner("Agent is planning, checking conflicts, and optimizing…"):
            try:
                result = run_schedule_agent(owner, _api_key)
                owner_state["ai_result"] = result
            except Exception as e:
                st.error(f"Agent error: {e}")
                owner_state.pop("ai_result", None)

if owner_state.get("ai_result"):
    result = owner_state["ai_result"]

    st.success(result.get("summary", ""))

    schedule = result.get("schedule", [])
    if schedule:
        st.markdown("#### AI-optimized schedule")

        header = st.columns([3, 2, 2, 2, 3])
        for label, col in zip(["Task", "Pet", "Original time", "Suggested time", "Reason"], header):
            col.markdown(f"**{label}**")

        for entry in schedule:
            row = st.columns([3, 2, 2, 2, 3])
            row[0].write(entry.get("task_name", ""))
            row[1].write(entry.get("pet", ""))
            row[2].write(entry.get("original_time", ""))
            suggested = entry.get("suggested_time", "")
            row[3].write(f"**{suggested}**" if suggested else "—")
            row[4].write(entry.get("reason", ""))

