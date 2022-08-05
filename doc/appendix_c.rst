========================================
Appendix C: Absolute Optimal
========================================
The preliminary analysis shows that with 3 evaluators at work the emergency ASA could go
as high as 6.3 seconds (with 95% confidence interval :math:`[0, 15,5]`).
The maximum utilization of evaluators on average is 77.8%
(95% confidence interval :math:`[64.9, 90.8]`).

With 4 evaluators, the maximum emergency ASA is 2.75 seconds (95% confidence
interval :math:`[0, 6.9]`). The maximum utilization is 65.3% (with 95% confidence
interval :math:`[51.9, 78.7]`).

.. note::
    Due to limitation on the processing, we
    only consider time intervals with low volume of calls (5:00 am to 8:00 am).
    Moreover, we run the schedule optimization for at most 5 minutes.

The Average Speed of Answering the calls for both emergency and non-emergency are
illustrated below with 3 and 4 evaluators and 95% confidence intervals
(:numref:`evals3` & :numref:`evals4`):


.. figure:: ./images/evals3.png
    :width: 70%
    :align: center
    :name: evals3

    ASA for emergency and non-emergency with 3 evaluators

.. figure:: ./images/evals4.png
    :width: 70%
    :align: center
    :name: evals4

    ASA for emergency and non-emergency with 4 evaluators

The amount of time each agent spent on calls on average is :numref:`utilization`
illustrated below with lines indicating 95% confidence intervals.

.. figure:: ./images/utilization.png
    :width: 70%
    :align: center
    :name: utilization

    Utilization of Evaluators

.. note::
    The model was **only** executed for hours between 5:00 am to 8:00 am, where the
    call volume is minimal, so the a machine with low resources can handle the
    computational complexity of the model within a reasonable time.
    Also, the parameters for the call duration distribution is set in a way that usually
    generates samples that on average are longer than what is being suggested by data.
    Therefore, the workload is slightly higher than what we may see in the actual
    Perimeter data.

.. note::
    The model is written in *Python 3.7* following *PEP8* standards.
    The optimization engine used for this analysis is *IBM's CPLEX*, running
    on *UBUNTU 20.04 LTS* equipped with 24 GB memory and
    Intel® Core™ i5-6300U CPU @ 2.40GHz × 4.

