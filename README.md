# Scheduling Toolkit

A Python library for modeling tasks, assigning work to resources, and comparing
scheduling strategies. PCB workload analysis is provided separately as an
optional use case; it is not part of the core workflow.

## Requirements

- Python 3.10 or newer.
- The built-in `Tasks` model and `FCFSP` heuristic have no third-party
  runtime dependencies.
- Optimization models require the `optimization` extra and a separately
  installed solver executable.

## Install

```bash
python -m pip install scheduling-toolkit
```

Install only the optional capabilities you need:

```bash
python -m pip install "scheduling-toolkit[optimization]"  # Pyomo models
python -m pip install "scheduling-toolkit[simulation]"    # stochastic evaluation
python -m pip install "scheduling-toolkit[visualization]" # Gantt charts
python -m pip install "scheduling-toolkit[data]"          # synthetic data tools
```

For the PCB workload case study, install the additional use-case dependencies:

```bash
python -m pip install "scheduling-toolkit[pcb]"
```

Pyomo does not bundle a solver. Install one separately (such as GLPK, HiGHS,
or CPLEX), then select it by name and optionally pass its executable path to
`MultiMachineMILP`.

## Quick start

```python
from scheduling import FCFSP, Tasks

tasks = Tasks()
tasks.add_task("prepare", release=0, due=10, process={"worker-1": 3})
tasks.add_task("review", release=1, due=12, process={"worker-1": 2})

schedule = FCFSP(tasks)()
for task_id, entry in schedule.items():
    print(task_id, entry)
```

`FCFSP` is a lightweight heuristic; it does not enforce due dates or
prerequisites. For optimization and prerequisite constraints, use a solver-backed
model, for example:

```python
from scheduling import MultiMachineMILP, Tasks

tasks = Tasks()
tasks.add_task("prepare", release=0, due=10, process={"worker-1": 3})
tasks.add_task("review", release=0, due=12, process={"worker-1": 2})
tasks.add_prerequisite("prepare", "review")

result = MultiMachineMILP(tasks, solver="glpk", respect_due=True)()
```

Solver-based schedules include a `"Message"` status entry. Configure additional
solver arguments with `solver_options={...}`. See the
[general documentation](doc/index.rst) for task modeling, solver setup,
visualization, and stochastic evaluation.

## PCB workload analysis: optional use case

The repository also includes an example application that uses aggregate
workload data to generate synthetic calls and evaluate schedules. It requires
the optional `pcb` extra and a user-supplied dataset. No operational, personal,
or research datasets are distributed here.

```bash
python examples/pcb_workload.py path/to/perimeter-export.csv --slot 18
```

The input must follow the columns consumed by `scheduling.use_cases.pcb.Perimeter`.
See the [PCB use-case guide](doc/use_cases/pcb/index.rst) for assumptions,
limitations, data shape, and the historical analysis. New code should import
from `scheduling.use_cases.pcb`; `scheduling.pcb` remains as a compatibility
path.

## Development

```bash
python -m pip install -e ".[dev,pcb]"
python -m pytest
ruff check scheduling tests
python -m build
sphinx-build -W --keep-going -b html doc doc/_build/html
```

Stochastic evaluation accepts `random_state` to make runs reproducible when
callbacks use Python's `random` module or NumPy's legacy global random
functions.

## Project status

This package is being modernized from a research codebase. The general-purpose
API is documented independently from the PCB case study; solver-dependent and
dataset-dependent features remain optional.
