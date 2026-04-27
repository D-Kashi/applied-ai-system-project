# PawPal+

[PawPal Demo Walkthrough](https://www.loom.com/share/f02e31984c8c404c92207acac4116f91)

GitHub Link: https://github.com/D-Kashi/applied-ai-system-project



**PawPal+** was originally designed as a rule-based pet care scheduling assistant. Its goal was to help a busy pet owner stay consistent with daily tasks by tracking those tasks against constraints like time, priority, and pet type. The system could detect scheduling conflicts, sort tasks by time or priority, and mark tasks as complete to keep the schedule current.

---

## Title and Summary

**PawPal+** is an AI-powered pet care planning assistant built with Python and Streamlit. It lets owners manage multiple pets, organize daily care tasks with time and priority, and run an AI agent (powered by Claude) that analyzes the schedule, detects conflicts, and produces an optimized plan with a written reason for each task.

It matters because juggling multiple pets and tasks manually is error-prone. PawPal+ removes the guesswork by catching conflicts automatically and letting an AI explain *why* a schedule is ordered the way it is — not just what the schedule is.

---

## Architecture Overview

The system has three layers:

- **Data layer** (`pawpal_system.py`): `Owner`, `Pet`, `Task`, and `Schedule` dataclasses. `Schedule` handles task storage, conflict detection, sorting, and completion. All scheduling logic lives here, isolated from the UI.

- **Agent layer** (`agent.py`): A Claude-powered agentic loop using four tools — `get_pending_tasks`, `detect_conflicts`, `validate_proposed_schedule`, and `finalize_schedule`. The agent follows a strict PLAN → ACT → CHECK → FINALIZE sequence, checking its own proposed schedule for conflicts before committing to a final output.

- **UI layer** (`app.py`): A Streamlit front end that manages per-owner session state, renders task forms, displays the schedule, and surfaces the AI agent's output in a readable table.

---

## Setup Instructions

**1. Clone the repository and create a virtual environment:**
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Add your Anthropic API key:**
```bash
# Copy the example file
cp .env.example .env
# Open .env and replace the placeholder with your real key:
# ANTHROPIC_API_KEY=sk-ant-...
```
Get a key at [console.anthropic.com](https://console.anthropic.com).

**4. Run the app:**
```bash
streamlit run app.py
```

**5. Run the tests:**
```bash
python -m pytest tests/test_pawpal.py
```

---

## Sample Interactions

### Example 1 — Conflict detection
**Input:** Two tasks both scheduled at 8:00 AM (Morning walk and Feeding) for the same owner.

**Output (Build Schedule):**
```
Task conflicts detected:
Warning: conflict at 08:00: Morning walk(pet=Mochi), Feeding(pet=Mochi)
```
The schedule still renders both tasks so the user can see what clashes and decide how to resolve it.

---

### Example 2 — AI Schedule with no conflicts
**Input:** Three tasks — Morning walk at 8:00 AM (20 min, high), Medication at 9:00 AM (5 min, high), Brushing at 3:00 PM (15 min, medium) — all for pet "Mochi".

**AI Output (Run AI Schedule):**

| Task | Pet | Original Time | Suggested Time | Reason |
|---|---|---|---|---|
| Morning walk | Mochi | 8:00 AM | — | High priority; scheduled first to set an active tone for the day. |
| Medication | Mochi | 9:00 AM | — | Administered after the walk so Mochi is calm; high priority ensures it is never skipped. |
| Brushing | Mochi | 3:00 PM | — | Medium priority grooming placed in the afternoon to avoid rushing the morning routine. |

**Summary:** All three tasks are conflict-free and ordered logically — exercise before medication, grooming in a low-pressure afternoon slot. No time changes were needed.

---

### Example 3 — AI resolving a conflict
**Input:** Morning walk and Feeding both at 8:00 AM.

**AI Output:**

| Task | Pet | Original Time | Suggested Time | Reason |
|---|---|---|---|---|
| Morning walk | Mochi | 8:00 AM | 8:00 AM | Walk first — exercise before eating is healthier for dogs. |
| Feeding | Mochi | 8:00 AM | 8:30 AM | Moved 30 minutes later to resolve the conflict and allow time for the walk to finish. |

**Summary:** A conflict was detected at 8:00 AM. Feeding was shifted to 8:30 AM to give space after the walk. Both tasks are now conflict-free.

---

## Design Decisions

**Separate data and UI layers:** All scheduling logic lives in `pawpal_system.py`, completely independent of Streamlit. This makes the logic testable without running the app and easy to swap the UI later.

**Agentic workflow over a single prompt:** A single prompt asking "optimize this schedule" would return a response with no way to verify its own work. The four-tool loop forces the agent to explicitly check its proposed schedule for conflicts before finalizing — a self-correction step that catches errors the model might otherwise gloss over.

**Adaptive thinking on Claude Opus 4.7:** Scheduling tasks with conflict resolution is a reasoning problem. Adaptive thinking lets the model decide how much internal reasoning to spend on simple vs. complex schedules, balancing quality and cost automatically.

**Per-owner session state:** Each owner gets their own isolated `Owner` object in `st.session_state`. Switching the owner name field immediately switches context, so multiple owners can be tested in the same session without data leaking between them.

**Trade-offs:** The app has no storage so all data is lost when the page refreshes. The AI agent suggests time changes but does not automatically apply them to the schedule; the user stays in control of what gets changed.

---

## Testing Summary

Three tests cover the core scheduling behaviors:

| Test | What it checks | Result |
|---|---|---|
| `test_mark_completed_changes_status` | Completing a task sets `completed = True` | Passed |
| `test_adding_task_to_pet_increases_count` | Adding a task to a schedule increments the pending count for that pet | Passed |
| `test_detect_conflicts_returns_warning_for_duplicate_times` | Two tasks at the same time produce exactly one conflict warning with both task names | Passed |

**What worked:** Conflict detection was straightforward to test because the logic is deterministic — same input always gives the same output. Task completion and pet-task association were also easy to isolate.

**What didn't:** Recurring task logic (daily/weekly auto-scheduling) was initially implemented but removed because it added complexity without a matching UI to support it, and it introduced a  `AttributeError` since the `frequency` field was never defined on `Task`. Removing it simplified the system.

**What was learned:** Writing tests before connecting the UI caught the `_to_time_obj` naming bug early. The functions were being called under one name but defined under another — something the UI would have silently swallowed but tests surfaced immediately.

---

## Reflection

Building PawPal+ showed that the hardest part of an AI system  is designing the data layer cleanly so that the AI can receive meaningful inputs and return output you expect. The agentic loop only works because `Task`, `Schedule`, and `Owner` are well-defined; if those were messy, the tools would return unreliable data and the agent's reasoning would degrade.

It also reinforced that AI works best as a layer on top of deterministic logic, not a replacement for it. Conflict detection is a simple loop — the AI does not need to invent it. What the AI adds is the explanation: *why* tasks are ordered the way they are, and *how* to resolve conflicts in a way that makes sense for the specific pet and context. That combination — rule-based structure plus language model reasoning — is more reliable and more useful than either one alone.
