Getting started
===============

Install the core library with:

.. code-block:: console

   python -m pip install scheduling-toolkit

The core task model and FCFS heuristic need no third-party runtime dependencies:

.. code-block:: python

   from scheduling import FCFSP, Tasks

   tasks = Tasks()
   tasks.add_task("prepare", release=0, due=10, process={"worker": 3})
   tasks.add_task("review", release=1, due=12, process={"worker": 2})
   schedule = FCFSP(tasks)()

``FCFSP`` is a heuristic and does not enforce due dates or prerequisites. Use
``MultiMachineMILP`` or ``MultiMachineQP`` when optimization or prerequisite
constraints are required. Those models need the ``optimization`` extra and a
separately installed solver executable:

.. code-block:: console

   python -m pip install "scheduling-toolkit[optimization]"

.. code-block:: python

   from scheduling import MultiMachineMILP

   result = MultiMachineMILP(tasks, solver="glpk", respect_due=True)()

Pass solver-specific settings with ``solver_options={...}``; pass
``executable="/path/to/solver"`` when the solver is not discoverable on
``PATH``. The result dictionary contains a ``"Message"`` status entry.

Optional capabilities
---------------------

* ``simulation`` adds NumPy, SciPy, and joblib for stochastic evaluation.
* ``visualization`` adds Matplotlib for Gantt charts.
* ``data`` adds NumPy, SciPy, and pandas for synthetic data tools.

Each feature can be installed independently, or combine extras as needed.
Domain-specific examples are documented separately under :doc:`use_cases/index`.
