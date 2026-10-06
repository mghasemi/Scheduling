from scheduling import FCFSP, Tasks

tasks = Tasks()
tasks.add_task("prepare", release=0, due=10, process={"worker-1": 3})
tasks.add_task("review", release=1, due=12, process={"worker-1": 2})

for task_id, entry in FCFSP(tasks)().items():
    print(task_id, entry)
