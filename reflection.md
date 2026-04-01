# PawPal+ Project Reflection

## 1. System Design
    Users should be able to add a pet(more than one), add tasks, see what tasks they have that are completed or have to be completed(schedule)
**a. Initial design**

- Briefly describe your initial UML design.
An owner has 0 to many pets. They have one schedule with many tasks on it. One pet can have 0 to many tasks

- What classes did you include, and what responsibilities did you assign to each?

    The owner should be able to input their name and be able to add a pet, add tasks, and view the tasks they have that are completed or have yet to be completed. They should be able to change the status. Pet should have a name, type of pet it is, gender. Task class should have type of task (walk, appointment, feed, etc) and time the task should take place. Tasks should have a status of completed or incompleted (base status is incompleted until owner changes it) Schedule should store tasks. Tasks that are completed should be removed. 
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
One change that was made was adding an ID to tasks for them to be tracked easier. Completed tasks are also changed to be archived instead of deleted unless the owner specficially deletes the completed task

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
Constraints that my scheduler considers is time. Time mostly matters as if it passes the time in order to do a task, especially if its something important like an appointment, then that would be troublesome for the user.  
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
The schedule uses a simple minute-level conflict check instead of full overlap or duration-based scheduling. It only flags tasks that share the same clock time, not tasks that partially overlap. This is reasonable here because the app is meant as a lightweight pet task tracker. It keeps the logic easy to understand and maintain while still catching the most common scheduling issue: two activities booked for the same moment.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI for debugging and refining my classes and their methods, implementing new methods and drafting tests. The questions asking for
test plans were most helpful and provided the most useful results/

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
I did not accept an AI suggestion as-is when it proposed handling recurrence by mutating the same task object. I checked the implementation and verified that the design should instead archive the completed task and create a new pending instance. I also had to change what was called in the main.py for pet as it did not take the gender and type string parameters inputted. 
I validated suggestions by reading the code, comparing them to the intended behavior, and thinking  how the schedule should behave.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
I tested sorting tasks by time and recurrence logic so completing a daily task creates a new task for the next day. I also test conflict detection, with duplicate task times producing a warning. These tests were important to ensure functionality of the program. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
I am decently confident that the scheduler works correctly and if I had more time, I would test more edge cases such as pets with no tasks or repeated tasks with the same time with multiple pets. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
Im satisifed that the testing portion went well. There were no errors when I ran my tests, which makes me confident about my methods fucntioning properly.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would possibly add more constraints to scheduling tasks to cover more ground in order to improve its function. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I learned that designing systems can be really tedious and require a lot of testing and tweaking to ensure its functioning as intended. AI helps alot with expediting these processes
