import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from pawpal_system import Owner, Pet, Task
from agent import run_schedule_agent, evaluate_schedule_result

load_dotenv()

# Resolve API key: Streamlit secrets (deployment) → .env / environment (local)
try:
    _api_key: str = st.secrets.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
except Exception:
    _api_key = os.environ.get("ANTHROPIC_API_KEY", "")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Plan and manage your pet's daily care tasks with AI-powered scheduling.")

_PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
_PRIORITY_LABEL = {1: "low", 2: "medium", 3: "high"}

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Per-owner storage: each owner_name gets its own Owner object and task display list
if "owners" not in st.session_state:
    st.session_state.owners = {}
if owner_name not in st.session_state.owners:
    st.session_state.owners[owner_name] = {"owner": Owner(owner_name), "tasks": []}

owner: Owner = st.session_state.owners[owner_name]["owner"]

st.subheader("Pets")
pcol1, pcol2, pcol3 = st.columns([3, 2, 2])
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with pcol3:
    gender = st.selectbox("Gender", ["male", "female", "unknown"])

if st.button("Add pet"):
    existing = next((p for p in owner.pets if p.name == pet_name), None)
    if not existing:
        new_pet = Pet(name=pet_name, type=species, gender=gender)
        owner.add_pet(new_pet)
        st.success(f"Added pet '{pet_name}'")
    else:
        st.info(f"Pet '{pet_name}' already exists")

if owner.pets:
    st.write("Pets: " + ", ".join(f"{p.name} ({p.type})" for p in owner.pets))

st.subheader("Tasks")
col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 2, 2, 2])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time_str = st.text_input("Start time (HH:MM)", value="08:00", max_chars=5)
with col3:
    am_pm = st.selectbox("AM/PM", ["AM", "PM"])
with col4:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col5:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col6:
    pet_options = [p.name for p in owner.pets]
    task_pet_name = st.selectbox("Pet", pet_options if pet_options else ["— add a pet first —"])

if st.button("Add task"):
    if not task_title.strip():
        st.error("Task title cannot be empty.")
        st.stop()
    if not owner.pets:
        st.warning("No pet added yet. Add a pet before creating tasks.")
        st.stop()
    try:
        hour, minute = map(int, task_time_str.strip().split(":"))
        if not (1 <= hour <= 12 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        st.error("Invalid time. Use HH:MM with hour 1–12 (e.g. 08:00).")
        st.stop()
    if am_pm == "AM" and hour == 12:
        hour = 0
    elif am_pm == "PM" and hour != 12:
        hour += 12
    task_time = datetime(1900, 1, 1, hour, minute)
    display_time = f"{task_time_str.strip()} {am_pm}"
    pet_obj = next((p for p in owner.pets if p.name == task_pet_name), None)
    task = Task(type=task_title, time=task_time, pet=pet_obj, priority=_PRIORITY_MAP[priority], duration_minutes=int(duration))
    owner.add_task(task)
    st.session_state.owners[owner_name]["tasks"].append(
        {"id": task.id, "title": task_title, "time": display_time, "duration_minutes": int(duration), "priority": priority, "pet": pet_obj.name if pet_obj else None}
    )
    st.success(f"Added task '{task_title}' at {display_time}")

owner_tasks = st.session_state.owners[owner_name]["tasks"]
if owner_tasks:
    st.write("Current tasks:")
    hcols = st.columns([3, 2, 2, 2, 2, 1])
    for label, col in zip(["Title", "Time", "Duration (min)", "Priority", "Pet", ""], hcols):
        col.markdown(f"**{label}**")
    to_delete = []
    for t in owner_tasks:
        row = st.columns([3, 2, 2, 2, 2, 1])
        row[0].write(t["title"])
        row[1].write(t["time"])
        row[2].write(str(t["duration_minutes"]))
        row[3].write(t["priority"])
        row[4].write(t["pet"] or "Unassigned")
        if row[5].button("🗑", key=f"del_{t['id']}"):
            to_delete.append(t["id"])
    if to_delete:
        for task_id in to_delete:
            owner.schedule.delete_task(task_id)
            owner_state = st.session_state.owners[owner_name]
            owner_state["tasks"] = [t for t in owner_state["tasks"] if t["id"] != task_id]
        st.rerun()
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

        header_cols = st.columns([3, 2, 1, 2, 2, 1])
        for label, col in zip(["Task", "Time", "Duration (min)", "Pet", "Priority", "Done"], header_cols):
            col.markdown(f"**{label}**")

        to_complete = []
        for task in sorted_tasks:
            time_display = (
                task.time.strftime("%I:%M %p").lstrip("0")
                if isinstance(task.time, datetime)
                else str(task.time)
            )
            row = st.columns([3, 2, 1, 2, 2, 1])
            row[0].write(task.type)
            row[1].write(time_display)
            row[2].write(str(task.duration_minutes))
            row[3].write(task.pet.name if task.pet else "Unassigned")
            row[4].write(_PRIORITY_LABEL.get(task.priority, str(task.priority)))
            if row[5].checkbox("", key=f"sched_done_{task.id}", label_visibility="collapsed"):
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
                pending_ids = [t.id for t in owner.schedule.get_pending_tasks()]
                result = run_schedule_agent(owner, _api_key)
                owner_state["ai_result"] = result
                owner_state["ai_eval"] = evaluate_schedule_result(result, pending_ids)
            except Exception as e:
                st.error(f"Agent error: {e}")
                owner_state.pop("ai_result", None)
                owner_state.pop("ai_eval", None)

if owner_state.get("ai_result"):
    result = owner_state["ai_result"]

    st.success(result.get("summary", ""))

    ev = owner_state.get("ai_eval")
    if ev:
        label = f"Agent evaluation: {ev['checks_passed']}/{ev['checks_total']} checks passed  |  score {int(ev['score'] * 100)}%"
        if ev["passed"]:
            st.success(label)
        else:
            st.warning(label)
            with st.expander("Evaluation issues"):
                for issue in ev["issues"]:
                    st.write(f"- {issue}")

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

