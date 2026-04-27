# PawPal+ Reflection and Ethics

## Limitations and Biases

PawPal+ has several limitations. The AI scheduler only knows what the user manually inputs. It has no access to a pet's health history, vet recommendations, or breed-specific care needs. This means it can suggest an ordering that sounds logical in general but may not be right for a specific animal. For example, it might schedule a walk right after feeding without knowing that the pet has a condition where that is harmful.

The conflict detection is also limited to exact minute-level matches. Two tasks scheduled at 8:00 AM and 8:10 AM will not trigger a conflict warning even if the first task takes 30 minutes and they genuinely overlap. The system treats each task as a point in time, not a block of time.

There is also a bias toward high-priority tasks in the AI's output. Because priority is passed to the model, it tends to justify high-priority tasks first and treat lower-priority ones as flexible, which may not always reflect what the owner actually wants.

---

## Potential Misuse and Prevention

PawPal+ is a low-risk application — it handles pet schedules, not sensitive personal data or critical systems. That said, a few misuse scenarios exist. Someone could repeatedly click "Run AI Schedule" to rack up API usage costs, since each run makes multiple Claude API calls. The agent loop already has a 12-iteration hard cap to limit this, and the API key stays private in a `.env` file rather than being exposed in the UI.

A more subtle misuse would be entering conflicting or nonsensical tasks to test whether the AI produces confident-sounding but wrong suggestions. The validate step in the agentic loop helps here — the agent is required to verify its own proposed schedule before finalizing it — but it is not a guarantee. Users should always treat AI scheduling suggestions as a starting point, not a final decision.

---

## What Surprised Me About Testing

The most surprising thing during testing was how silently things could break. The recurring task feature, where completing a daily task would automatically create the next one, appeared to be implemented and never raised an error during normal use. It was only when looking closely at the code that the frequency field was never actually defined on the task class. The feature was completely non-functional but gave no indication of that.

Similarly, the priority field on task was always 0 in the schedule view because the UI collected "low/medium/high" as a string but never converted it to an integer before storing it on the object. The task table just silently showed 0 for every task.
---

## AI Collaboration

Claude Code was used throughout this project for debugging, implementing new features, writing tests, and refining class methods.

**Helpful suggestion:** The most valuable suggestion was implementing the agentic workflow using a four-tool loop — `get_pending_tasks`, `detect_conflicts`, `validate_proposed_schedule`, and `finalize_schedule` — instead of a single prompt. This forced the AI to check its own proposed schedule for conflicts before committing to a final output, which made the AI component genuinely more reliable and more interesting than a one-shot answer. That structure came directly from an AI recommendation and it worked well.

**Flawed suggestion:** During a code review, the AI flagged claude-opus-4-7 as an invalid model ID that would cause an API error. Acting on that suggestion would have caused a working feature to be changed unnecessarily. It was a reminder that AI-generated analysis of code can be confidently wrong, and that any suggestion touching something external needs to be verified against the actual documentation.

## AI Engineer
This project shows my growth as an AI Engineer. Compared to my knowledge at the beginning of this codepath course, I have gained much more information about AI and how to properly use and prompt it in order to help me improve upon my programming and further my understand on concepts I may not understand. 