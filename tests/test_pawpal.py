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


def test_detect_conflicts_returns_warning_for_duplicate_times():
    owner = Owner("Alice")
    pet1 = Pet(name="Buddy", type="dog", gender="male")
    pet2 = Pet(name="Mittens", type="cat", gender="female")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    t1 = Task(type="Feed", time="09:00", pet=pet1)
    t2 = Task(type="Brush", time="09:00", pet=pet2)
    owner.add_task(t1)
    owner.add_task(t2)

    warnings = owner.schedule.detect_conflicts()
    assert len(warnings) == 1
    assert "Warning: conflict at 09:00" in warnings[0]
    assert "Feed(pet=Buddy)" in warnings[0]
    assert "Brush(pet=Mittens)" in warnings[0]