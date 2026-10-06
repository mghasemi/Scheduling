PCB workload-planning case study
================================

This section documents a historical application of the general scheduling
library. It is an illustrative use case, not a description of the package's
default purpose or operational guidance. The study used domain-specific
assumptions and data supplied by its authors.

The Police Communication Branch (PCB) handled emergency and police
non-emergency calls. The study considered the workload transferred to police
evaluation staff after an initial assessment by 911 operators.

The workflow considered three stages:

  1. 911 primary call center
  2. Evaluation unit
  3. Dispatch unit

The 911 primary operators take all the incoming calls and after an initial assessment
transfer the calls to the appropriate unit for further response. These units include
Police Evaluation, EMS, Fire Department, and others.

The evaluation unit processes emergency and non-emergency calls. This case
study asked how staffing levels and break schedules might affect the workload
of evaluators at different times of day.

The original analysis used historical aggregate data to estimate staffing
requirements for 30-minute intervals. The estimates are specific to that
dataset and its assumptions.

Objective
-----------------
**Estimate evaluator staffing levels that can handle the modeled workload across
the day.**

The model considered scheduled breaks as well as workload, using 30-minute
time intervals.

.. note::

    Average speed of answer (ASA) and resource utilization can conflict: adding
    staff may reduce modeled waiting time while lowering utilization. The
    analysis therefore considered both measures rather than treating either as
    an unconditional objective.

Limitations of Modeling
-----------------------------
It is worth emphasizing that modeling processes that involve a lot of different parameters
is a highly complex task, let alone the processes that involve human-based decision making
along the way. As `George Box <https://en.wikipedia.org/wiki/All_models_are_wrong>`_
once said *"All models are wrong, but some are useful"*.
Once this is clarified and expectations are adjusted, modelers can relax and begin to
approximate the phenomenon they are given for investigation.

There are standard models that are proven to work very well for certain problems, again
it must be clear that since we are always trying to increase the *accuracy* of models,
there is no unique solution model for a given problem. Moreover, looking at a problem
from various angles is always a good practice and when different approaches approximately
confirm each other, one could trust either as a reliable model based on their needs.
Also, different approaches may reveal different aspects of the problem that were hidden
from the scope of the other existing solutions.

Scheduling fundamentals
-----------------------
In a scheduling problem we have to fulfill a set of tasks using a number of resources
under certain constraints such as restrictions on the task completion times,
priorities between task (one task cannot start until another one is finished), etc.
The goal is to optimize some criterion, e.g, to minimize the total processing time,
which is the completion time of the last task or to maximize the number of processed tasks.

Scheduling approaches
---------------------
There are various ways to come up with a scheduling method that affects the overall
performance of the evaluation unit. Each method assumes certain routines on the evaluation
side in terms of handling the calls. In what follows, we describe a few methods and later
on we investigate the implication of each one on the average speed of answering (emergency)
calls.

======================================
First Come, First Serve with priority
======================================
Next, we consider a more primitive method for scheduling calls known as
**First Come, First Serve with priority**.
In this method, agents try to handle all calls in the order they are presented. The only
assumption is for when an agent becomes available, the emergency calls in the queue are
given higher priority and offered prior to the non-emergency ones. Calls are not
interrupted while the agent is busy by one (either emergency or non-emergency).
It must be clear that this method will result in an increase in ASA for emergency calls
but a possible decrease in ASA for non-emergency ones.

=================================
Preemptive Scheduling Model
=================================
In this scheduling model, calls will be answered as they come in based on the
availability of resources with preemption. Meaning that if a call with higher priority
is presented, then one of the evaluators who is busy with a lower priority call will
put the current call on hold, answers the high priority one and then resumes the call
on hold. When a call with high priority presented but all evaluators are busy, the model
waits for a certain time (2 seconds by default) and then performs preemption, if no one
is available by then. The model considers evaluators who don't have another call on hold
already. There is no limit on the number of possible priority levels, the model is
capable of handling multiple different priority levels as well.

There are various algorithms handling this particular type of scheduling model including
one based on the Mixed Integer Linear Programming, one based on Evolutionary Optimization
Algorithms, and Agent Based models. The current implementation follows the *Agent Base*
modeling technique.

=================================
Absolute Optimal (Deterministic)
=================================
Let us formulate a very general scheduling problem which subsumes as special cases a great
deal of problems studied in the literature.
We are given :math:`k` tasks :math:`T=\{T_1, \dots, T_k\}` to be processed via :math:`l`
resources :math:`R=\{R_1, \dots, R_l\}`.
Consider the following parameters and variables:

  - :math:`p_{jm}` denotes the processing time of the task :math:`T_j` by the resource :math:`R_m`.
  - :math:`r_j` and :math:`d_j` are the release date/time and due date/time of the task :math:`j`, respectively.
  - :math:`x_{jm}` (binary) determines if the task :math:`j` is assigned to the resource :math:`m`: :math:`x_{jm}=1` if yes, and :math:`x_{jm}=0` otherwise.
  - :math:`y_{ij}` (binary), sequencing variables: :math:`y_{ij}=1` if the tasks :math:`i` and :math:`j` are assigned to the same resource and the task :math:`i` precedes the task :math:`j`, with :math:`y_{ij}=0` otherwise.
  - :math:`s_j` and :math:`e_j` denote the start and end times of task :math:`T_j`.

.. math::
  \left\lbrace\begin{array}{lllr}
    \min & \sum_j (e_j-d_j) & & \\
    \textrm{subject to} & & & \\
     & \sum_m x_{jm} =1 & j=1,\dots,k & \dagger\\
     & \sum_j p_{jm} x_{jm}\leq\max_j d_j - \min_j r_j & m=1,\dots, l & \ddagger\\
     & s_j + \sum_m p_{jm}x_{jm} - e_j = 0 & j=1,\dots,k & \clubsuit\\
     & e_i - s_j + Uy_{ij} \leq U & i\neq j\in\{1,\dots,k\} & \bigstar\\
     & r_j\leq s_j & j=1,\dots,k & \heartsuit\\
     & e_j \leq d_j & j=1,\dots,k & \spadesuit\\
     & y_{ij} + y_{ji}\leq 1 & i<j\in\{1,\dots,k\} & \Diamond_1\\
     & x_{im} + x_{jm} - y_{ij} - y_{ji}\leq1 & i<j\in\{1,\dots,k\}, m=1,\dots,l & \Diamond_2\\
     & x_{in} + x_{jm} + y_{ij} + y_{ji} \leq 2 & m\neq n, i<j & \Diamond_3
  \end{array}\right.

Here :math:`U` is a big value to insure the task :math:`j` will be processed,
e.g. :math:`U\ge\max_j d_j - \min_j r_j` , for :math:`m=1, \dots,l`.
It is clear that we can induce customary gaps of block certain time windows by
introducing appropriate constraints to the above program.

Associating appropriate weight to different call categories, we can replace the
objective function with

.. math::
    \sum_{j, m}w_{jm}(s_j-r_j).

This will give priority to calls with heavier weights and lower priority to other calls.

Here is a brief description of roles of each set constraints:
  + :math:`\dagger`: insures that each job is allocated to exactly one machine
  + :math:`\ddagger`: the processing time of each task on all machines does not exceed a threshold
  + :math:`\clubsuit`: the start time and end time associated to a task on a certain machine matches the assumed
    duration of the task
  + :math:`\bigstar`: insures each machine finishes its jobs within a desired time interval
  + :math:`\heartsuit` no job begins before it becomes available
  + :math:`\spadesuit`: jobs are done before their due
  + :math:`\Diamond_1`: tracks the order of tasks
  + :math:`\Diamond_2`: guarantees tasks on the same machine do not overlap
  + :math:`\Diamond_3`: ordered pair of jobs are not allocated to multiple machines at the same time
