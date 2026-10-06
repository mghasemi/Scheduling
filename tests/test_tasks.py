import pytest

from scheduling import Tasks


def test_task_records_resources_and_prerequisites():
    tasks = Tasks()
    tasks.add_task("prepare", release=2, due=8, process={"worker": 3})
    tasks.add_task("review", release=4, due=10, process={"reviewer": 2})
    tasks.add_prerequisite("prepare", "review")

    assert tasks.Tasks[0]["release"] == 2
    assert tasks.Tasks[0]["process"] == {"worker": 3}
    assert set(tasks.Resources) == {"worker", "reviewer"}
    assert tasks.Prerequisite == [(0, 1)]


def test_unavailable_task_is_complete_for_scheduler_consumers():
    tasks = Tasks()
    tasks.schedule_unavailable("worker", process=2, start=4)

    assert tasks.Tasks[0]["id"] == 0
    assert tasks.Tasks[0]["start"] == 4


def test_duplicate_task_names_are_rejected():
    tasks = Tasks()
    tasks.add_task("same")

    with pytest.raises(ValueError, match="already exists"):
        tasks.add_task("same")


def test_invalid_processing_duration_is_rejected():
    tasks = Tasks()

    with pytest.raises(ValueError, match="finite, non-negative"):
        tasks.add_task(process={"worker": float("nan")})
