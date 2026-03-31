from pawpal_system import Owner, Pet, Task


def test_mark_completed_changes_status():
    t = Task(type="walk")
    assert t.completed is False
    t.mark_completed()
    assert t.completed is True


def test_adding_task_to_pet_increases_count():
    owner = Owner("Alice")
    pet = Pet(name="Buddy", type="dog", gender="male")
    owner.add_pet(pet)

    def pet_task_count(o: Owner, p: Pet) -> int:
        return sum(1 for t in o.schedule.get_pending_tasks() if t.pet is p)

    assert pet_task_count(owner, pet) == 0
    task = Task(type="feed", pet=pet)
    owner.add_task(task)
    assert pet_task_count(owner, pet) == 1