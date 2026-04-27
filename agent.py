from __future__ import annotations

import json
from collections import defaultdict
from typing import Optional

import anthropic

from pawpal_system import Owner


def evaluate_schedule_result(result: dict, expected_task_ids: list) -> dict:
    """Score the agent's output against a checklist of quality criteria.

    Returns a dict with: passed (bool), score (0.0-1.0), checks_passed,
    checks_total, and issues (list of failure messages).
    """
    issues = []
    total = 0
    passed = 0

    def check(condition: bool, message: str) -> None:
        nonlocal total, passed
        total += 1
        if condition:
            passed += 1
        else:
            issues.append(message)

    # Top-level structure
    check("schedule" in result, "Result is missing 'schedule' key")
    check("summary" in result, "Result is missing 'summary' key")
    check(bool(result.get("summary", "").strip()), "Summary is empty")

    schedule = result.get("schedule", [])
    check(len(schedule) > 0, "Schedule contains no entries")

    # All expected tasks appear in the output
    returned_ids = {e.get("task_id", "") for e in schedule}
    missing = set(expected_task_ids) - returned_ids
    check(not missing, f"Tasks missing from schedule: {', '.join(missing)}")

    # Per-entry field checks
    required_fields = ["task_id", "task_name", "original_time", "pet", "reason"]
    for i, entry in enumerate(schedule):
        for field in required_fields:
            val = entry.get(field, "")
            check(
                isinstance(val, str) and bool(val.strip()),
                f"Entry {i + 1} has empty or missing '{field}'",
            )

    score = round(passed / total, 2) if total > 0 else 0.0
    return {
        "passed": len(issues) == 0,
        "score": score,
        "checks_passed": passed,
        "checks_total": total,
        "issues": issues,
    }


def _serialize_tasks(tasks) -> list:
    result = []
    for t in tasks:
        time_str = (
            t.time.strftime("%I:%M %p").lstrip("0")
            if hasattr(t.time, "strftime")
            else str(t.time)
        )
        result.append({
            "id": t.id,
            "name": t.type,
            "time": time_str,
            "duration_minutes": t.duration_minutes,
            "pet": t.pet.name if t.pet else "Unassigned",
            "priority": t.priority,
        })
    return result


def _check_proposed_conflicts(proposed_tasks: list) -> list[str]:
    groups: dict[str, list[str]] = defaultdict(list)
    for item in proposed_tasks:
        groups[item.get("time", "unknown")].append(item.get("task_name", "?"))
    return [
        f"Conflict at {t}: {', '.join(names)}"
        for t, names in groups.items()
        if len(names) > 1
    ]


TOOLS = [
    {
        "name": "get_pending_tasks",
        "description": "Returns all pending (incomplete) tasks as a list with id, name, time, pet, and priority.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "detect_conflicts",
        "description": "Checks the current schedule for tasks that share the same start time. Returns conflict warnings.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "validate_proposed_schedule",
        "description": (
            "Verify your proposed schedule for time conflicts before finalizing. "
            "Pass the full list of tasks with their intended times. "
            "Returns a list of conflicts, or confirms the schedule is clean."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "proposed_tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_name": {"type": "string"},
                            "time": {
                                "type": "string",
                                "description": "Intended time, e.g. '8:00 AM'",
                            },
                        },
                        "required": ["task_name", "time"],
                    },
                }
            },
            "required": ["proposed_tasks"],
        },
    },
    {
        "name": "finalize_schedule",
        "description": (
            "Submit the final optimized schedule once validate_proposed_schedule confirms it is conflict-free."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "task_name": {"type": "string"},
                            "original_time": {"type": "string"},
                            "pet": {"type": "string"},
                            "suggested_time": {
                                "type": "string",
                                "description": "Only include if recommending a different time to resolve a conflict.",
                            },
                            "reason": {
                                "type": "string",
                                "description": "One sentence explaining this task's placement.",
                            },
                        },
                        "required": ["task_id", "task_name", "original_time", "pet", "reason"],
                    },
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence overview of the scheduling decisions made.",
                },
            },
            "required": ["schedule", "summary"],
        },
    },
]

# Cached once — stable across all loop iterations
_SYSTEM = [
    {
        "type": "text",
        "text": """\
You are PawPal+, an intelligent pet care scheduling assistant.

Your job: analyze a pet owner's pending tasks and produce an optimized daily care schedule.

Follow this four-step process exactly:
1. PLAN   — Call get_pending_tasks. Review each task: type, time, pet, priority.
2. ACT    — Call detect_conflicts to find any time clashes in the current schedule.
3. CHECK  — Decide how to resolve conflicts and whether the ordering is logical \
(e.g. feed before walk, medications spaced out). \
Call validate_proposed_schedule with your full proposed task list to confirm it is conflict-free \
before committing. If conflicts remain, revise and validate again.
4. FINALIZE — Call finalize_schedule with the conflict-free schedule. \
One-sentence reason per task; include suggested_time only when recommending a change. \
End with a 2-3 sentence summary.\
""",
        "cache_control": {"type": "ephemeral"},
    }
]


def run_schedule_agent(owner: Owner, api_key: str) -> dict:
    """Run the agentic scheduling loop and return the finalize_schedule payload."""
    client = anthropic.Anthropic(api_key=api_key)
    messages = [
        {"role": "user", "content": "Please analyze and optimize the pet care schedule."}
    ]

    final_result: Optional[dict] = None

    for _ in range(12):
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=_SYSTEM,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "get_pending_tasks":
                payload = _serialize_tasks(owner.schedule.get_pending_tasks())
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(payload),
                })

            elif block.name == "detect_conflicts":
                conflicts = owner.schedule.detect_conflicts()
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(conflicts or ["No conflicts detected."]),
                })

            elif block.name == "validate_proposed_schedule":
                conflicts = _check_proposed_conflicts(block.input.get("proposed_tasks", []))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(conflicts or ["Proposed schedule is conflict-free."]),
                })

            elif block.name == "finalize_schedule":
                final_result = block.input
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Schedule finalized.",
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if final_result is not None:
            break

    if final_result is None:
        raise RuntimeError("Agent did not finalize a schedule after 12 iterations. Try again or reduce the number of tasks.")
    return final_result
