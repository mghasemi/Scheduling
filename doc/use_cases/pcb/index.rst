PCB call-center workload planning
=================================

This is a historical case study applying the scheduling toolkit to aggregated
call-center workload data. It is provided as an example of domain adaptation,
not as a default package workflow or production staffing recommendation.

The study models emergency and non-emergency calls, generates synthetic
30-minute workloads from aggregated observations, and compares simple
first-come-first-served, preemptive, and optimization-based schedules. Results
depend on assumptions about call durations and arrivals; review the method and
limitations before adapting it.

Install the optional dependencies
---------------------------------

.. code-block:: console

   python -m pip install "scheduling-toolkit[pcb]"

The package does not include the underlying Perimeter or 911 call records.
Supply a compatible export yourself and ensure you have permission to use it.
The script at ``examples/pcb_workload.py`` demonstrates the data flow.

.. toctree::
   :maxdepth: 2

   overview
   data_and_method
   duration_assumptions
   preemptive_results
   fcfs_results
   optimization_results
   api
