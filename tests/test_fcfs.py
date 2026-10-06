from scheduling import FCFSP, Tasks


def test_fcfs_uses_compatible_resources_and_tracks_availability():
    tasks = Tasks()
    tasks.add_task("first", release=0, due=20, process={"worker-a": 3})
    tasks.add_task("second", release=0, due=20, process={"worker-b": 2})
    tasks.add_task("third", release=1, due=20, process={"worker-a": 4})

    result = FCFSP(tasks)()

    assert result["Message"] == "Success"
    assert result[0]["resources"] == "worker-a"
    assert result[0]["start"] == 0
    assert result[2]["start"] == 3
    assert result[1]["resources"] == "worker-b"
    assert result[1]["start"] == 0


def test_fcfs_accepts_empty_task_set():
    assert FCFSP(Tasks())() == {"Message": "Success"}


def test_core_import_does_not_load_optional_dependencies():
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            (
                "import sys; import scheduling; "
                "from scheduling import FCFSP, Tasks; "
                "assert FCFSP(Tasks())()['Message'] == 'Success'; "
                "assert 'pandas' not in sys.modules and 'pyomo' not in sys.modules"
            ),
        ],
        check=True,
    )


def test_fcfs_schedules_unavailable_period():
    tasks = Tasks()
    tasks.schedule_unavailable("worker", process=2, start=4)

    result = FCFSP(tasks)()

    assert result[0]["start"] == 4
    assert result[0]["finish"] == 6


def test_fcfs_reports_unavailable_fixed_start():
    tasks = Tasks()
    tasks.add_task("busy", release=0, due=20, process={"worker": 6})
    tasks.add_task("fixed", release=0, due=20, process={"worker": 1}, start=4)

    import pytest

    with pytest.raises(ValueError, match="not available for the fixed start"):
        FCFSP(tasks)()
