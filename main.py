from datetime import datetime
from pawpal_system import Owner, Pet, Task

# /c:/Users/dusha/Pawpal/main.py
# No additional import handling required; imports above are sufficient.

def create_task_flexible(title, time_str, **kwargs):
    # Try common Task constructors
    for ctor_args in (
        (title, time_str),
        (title, datetime.strptime(time_str, "%H:%M").time()),
        (title,),
    ):
        try:
            return Task(*ctor_args, **kwargs)
        except Exception:
            continue
    # Last resort: try keyword names
    try:
        return Task(name=title, time=time_str, **kwargs)
    except Exception as e:
        raise

def add_task_to_pet(pet, task):
    if hasattr(pet, "add_task"):
        pet.add_task(task)
    elif hasattr(pet, "tasks") and isinstance(pet.tasks, list):
        pet.tasks.append(task)
    else:
        # try common attribute names
        if hasattr(pet, "tasks_list") and isinstance(pet.tasks_list, list):
            pet.tasks_list.append(task)
        else:
            # attach a tasks list dynamically
            setattr(pet, "tasks", [task])

def get_pet_tasks(pet):
    for attr in ("tasks", "tasks_list", "schedule"):
        if hasattr(pet, attr):
            val = getattr(pet, attr)
            if isinstance(val, list):
                return val
    return []

def task_time_key(task):
    for attr in ("time", "when", "time_str"):
        if hasattr(task, attr):
            val = getattr(task, attr)
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%H:%M").time()
                except Exception:
                    pass
            if isinstance(val, datetime):
                return val.time()
            return val
    # fallback: try parsing str(task)
    s = str(task)
    try:
        return datetime.strptime(s, "%H:%M").time()
    except Exception:
        return datetime.max.time()

def task_title(task):
    for attr in ("name", "title", "description"):
        if hasattr(task, attr):
            return getattr(task, attr)
    return str(task)

def pet_name(pet):
    for attr in ("name", "nickname"):
        if hasattr(pet, attr):
            return getattr(pet, attr)
    return "Unnamed Pet"

if __name__ == "__main__":
    # Create owner
    owner = Owner("Dusha")

    # Create at least two pets
    pet1 = Pet("Fido", type="Dog", gender="male") if "type" in Pet.__init__.__code__.co_varnames else Pet("Fido")
    pet2 = Pet("Mittens", type="Cat", gender="female") if "type" in Pet.__init__.__code__.co_varnames else Pet("Mittens")

    # Attach pets to owner
    if hasattr(owner, "add_pet"):
        owner.add_pet(pet1)
        owner.add_pet(pet2)
    elif hasattr(owner, "pets") and isinstance(owner.pets, list):
        owner.pets.append(pet1)
        owner.pets.append(pet2)
    else:
        setattr(owner, "pets", [pet1, pet2])

    # Add at least three tasks with different times
    t1 = create_task_flexible("Morning Walk", "08:00")
    t2 = create_task_flexible("Afternoon Meal", "12:30")
    t3 = create_task_flexible("Evening Play", "18:15")

    add_task_to_pet(pet1, t1)
    add_task_to_pet(pet1, t2)
    add_task_to_pet(pet2, t3)

    # Collect tasks from owner's pets
    all_tasks = []
    pets = getattr(owner, "pets", [pet1, pet2])
    for p in pets:
        for t in get_pet_tasks(p):
            all_tasks.append((task_time_key(t), pet_name(p), task_title(t)))

    # Sort by time
    all_tasks.sort(key=lambda x: x[0])

    # Print Today's Schedule
    print("Today's Schedule")
    for time_obj, pname, ttitle in all_tasks:
        time_str = time_obj.strftime("%H:%M") if hasattr(time_obj, "strftime") else str(time_obj)
        print(f"{time_str} - {pname} - {ttitle}")