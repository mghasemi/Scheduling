Telus and Perimeter data
==============================
The evaluation unit data is provided by Perimeter in 30-minutes aggregate format.
Hence, determining the exact workload of each agent is not a straight forward task.
Among the information in the Perimeter dataset, total duration that agents spent on calls
``t_duration``, maximum call duration ``max_duration``,
number of completed calls ``n_complete``, and number of offered and presented calls
``n_offer``, ``n_presented`` within the 30 minutes period are present.

A very basic solution to simulate the calls for each period is to take the average duration
of calls :math:`\frac{t\_duration}{n\_complete}` as the base value for the calls and proceed
from there. The following example shows why this approach is not suitable.

Example:
    Imagine a scenario where 4 high priority calls are coming through starting at 9, 10, 11,
    and 15 minutes from the start of the 30-minutes time interval with corresponding
    durations 18, 12, 15, and 15 minutes, respectively. This adds up to 60 minutes
    workload.

    Also, 10 low priority and rather short calls (3 minutes each) are received by the
    evaluation unit, which adds up to 30 minutes. Therefore the total workload for this
    time interval is 90 minutes. The average duration of each call is about 6.42 minutes
    which can be fit within the schedule for 3 evaluators. While in fact the long calls
    are overlapping which makes it impossible to fit all the above calls in the given
    time interval. :numref:`xmpl` proposes an optimal schedule that handles all
    calls given that 4 evaluators are available.

.. figure:: ./images/example4agent.png
    :width: 50%
    :align: center
    :name: xmpl

    Sample Optimal Schedule

This suggests that using the average duration of calls for analysis is not a wise
decision. At the same time, the duration distribution of calls is unknown based on the
existing Perimeter data.

.. note::
    To resolve the above issue, lets assume that the duration of calls
    are following a normal distribution :math:`\mathcal{N}(\mu, \sigma)`. The shift
    of this distribution is :math:`\mu=\frac{t\_duration}{n\_complete}`, while the
    standard deviation :math:`\sigma` is unknown. To estimate :math:`\sigma` one can
    choose either of the following solutions:

      .. figure:: ./images/normal.png
          :width: 60%
          :align: center

          Truncation of a Normal distribution

      + Assume that there is only one call with the ``max_duration`` and :math:`N=n\_complete`.
        Then the probability of having such long calls is :math:`\frac{1}{N}`.
        Solving the following equation for :math:`\sigma` provides an estimate for
        :math:`\sigma`.

         .. math::
            \int_{max\_duration}^{\infty}e^{-\frac{1}{2}(\frac{x-\mu}{\sigma})^2}~dx=\frac{\sigma\sqrt{2\pi}}{N}

      + Assume that the minimum duration is :math:`m\ge0` and the maximum duration is
        :math:`M=max\_duration`.
        The joint cumulative distribution function for the minimum :math:`m` and
        maximum :math:`M` for a sample of :math:`N` from a Gaussian distribution
        with mean :math:`\mu` and standard deviation :math:`\sigma` is

         .. math::
            \Phi\left(\frac{M-\mu}{\sigma}\right)^N-\left[\Phi\left(\frac{M-\mu}{\sigma}\right)-\Phi\left(\frac{m-\mu}{\sigma}\right)\right]^N

        where :math:`\Phi` is the standard Gaussian CDF.
        Differentiation with respect to :math:`m` and :math:`M` gives the joint
        probability density function

         .. math::
            \begin{array}{ll}
                f(m, M; \mu, \sigma) & = \\
                    & N(N-1)\left[\Phi\left(\frac{M-\mu}{\sigma}\right)-\Phi\left(\frac{m-\mu}{\sigma}\right)\right]^{(N-2)}\\
                    & \cdot \phi\left(\frac{M-\mu}{\sigma}\right)\cdot\phi\left(\frac{m-\mu}{\sigma}\right)\cdot\frac{1}{\sigma^2}
            \end{array}

        where :math:`\phi` is the standard Gaussian PDF. Taking the log and
        dropping terms that don't contain parameters gives the log-likelihood function

         .. math::
            \begin{array}{lll}
                \ell(\mu,\sigma;m, M) & = & (N-2)\log\left[\Phi\left(\frac{M-\mu}{\sigma}\right)-\Phi\left(\frac{m-\mu}{\sigma}\right)\right]\\
                & + & \log\phi\left(\frac{M-\mu}{\sigma}\right)+\log\phi\left(\frac{m-\mu}{\sigma}\right)-2\log\sigma
            \end{array}

        This expression has to be maximized numerically to find an estimate for :math:`\sigma`.

The following process explains how all the calls transferred to a line are simulated

  1. For a row, take :math:`N=\max({\rm n\_offer, n\_presented}), m=10, M=max\_duration`, and :math:`\mu=\frac{t\_duration}{n\_complete}`

  2. Find :math:`\sigma` using the above algorithms

  3. Draw :math:`N` number from the truncated distribution :math:`\mathcal{N}_m^M(\mu,\sigma)` as duration of calls

  4. Draw :math:`N` numbers between 0 and 1800 (30 minutes in seconds), uniformly as the start time of calls

  5. Combine the above numbers which simulate a hypothetical schedule according to the existing information.

Volume of incoming calls
------------------------------
To get an approximate idea about the workload throughout the day, let us distinguish
between number of *Emergency* and *Non-Emergency* calls arriving at each 30-minutes time
slot based on two years of Perimeter data (:numref:`emrvol` and :numref:`nemrvol`).

.. figure:: ./images/emrvol.png
    :width: 70%
    :align: center
    :name: emrvol

    Volume of incoming Emergency calls

.. figure:: ./images/nemrvol.png
    :width: 70%
    :align: center
    :name: nemrvol

    Volume of incoming Non-Emergency calls

A peak at the volume of calls transferred to evaluation from 911 primary :numref:`avg911`
confirms that the perimeter data and Telus data align with each other.

.. figure:: ./images/avg911.png
    :width: 70%
    :align: center
    :name: avg911

    Average volume of transferred calls from 911

To generate the volume of both Emergency and Non-Emergency incoming calls, we are
going to assume that the distribution of incoming calls per time slot follows a
normal distribution. Then we calculate the parameters of this distribution according
to the Perimeter data, plug in those values to simulate a hypothetical day for any
given 30-minutes time slot.
The following plots (:numref:`emgdist` & :numref:`nonemgdist`) show the actual
distributions extracted from Perimeter data.

.. figure:: ./images/emgdist.png
    :width: 70%
    :align: center
    :name: emgdist

    Distribution of incoming Emergency calls

.. figure:: ./images/nonemgdist.png
    :width: 70%
    :align: center
    :name: nonemgdist

    Distribution of incoming Non-Emergency calls

These plots resembles collections of **Truncated Normal** distributions which validates
the above assumption.

Stochastic Schedule Analysis
-----------------------------------
Now, we use the above information and processes to generate random calls with different
priorities for various time slots. We also assume that each evaluator takes a 2 to 8
minutes **break** per 30 minutes time slot.

To get a more realistic idea about the workloads and performances, we generate 50
random scenarios per time slot for 3 and 4 evaluators. A typical optimal schedule looks
like :numref:`typical-schedule`.

.. figure:: ./images/15-4.png
    :width: 50%
    :align: center
    :name: typical-schedule

    An optimal schedule for 4 evaluators

Preliminary Results on Staffing
---------------------------------
The preemptive model was run over the simulated data for all 48 timeslots with different
number of evaluators in place. This simulation was repeated 50 times to measure the ASAs,
Utilization, and their corresponding 95% confidence intervals.
:numref:`min_res` shows the minimum number of evaluators required to achieve Emergency
ASA below 2 seconds, the corresponding Non-emergency ASA, their 95% upper bound, and
the average expected utilization.

.. table:: Minimum Required Resource
    :name: min_res

    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |Index|Timeslot|Minimum| ASA  |ASA Upper|Non-EM-ASA|Upper Bound|Utilization|
    +=====+========+=======+======+=========+==========+===========+===========+
    |    0|00:00   |      8|0.9807|   1.8733|    8.4709|    23.3209|      49.70|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    1|00:30   |      8|0.5154|   0.5663|    1.0950|     2.2133|      43.72|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    2|01:00   |      8|0.6467|   0.9103|    2.0294|     4.4187|      44.77|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    3|01:30   |      5|1.9684|   3.6591|   15.0067|    31.4791|      57.80|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    4|02:00   |      8|0.6461|   1.0077|    0.6163|     0.9394|      37.26|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    5|02:30   |      5|1.3391|   2.7579|    2.9601|     5.2445|      53.33|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    6|03:00   |      6|0.3831|   0.4748|    0.7258|     1.1058|      38.82|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    7|03:30   |      5|1.3210|   2.4955|    3.2139|     6.3450|      46.35|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    8|04:00   |      5|0.5732|   0.7032|    1.1280|     2.0734|      39.54|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |    9|04:30   |      5|0.7653|   1.3828|    2.0961|     4.4098|      40.38|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   10|05:00   |      4|0.7523|   1.0860|    2.3083|     4.0776|      41.63|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   11|05:30   |      4|0.8881|   1.3145|    7.3983|    16.9285|      49.96|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   12|06:00   |      4|1.9951|   4.6979|    5.1747|    11.5476|      45.52|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   13|06:30   |      4|1.1180|   2.2454|    3.0685|     5.3090|      47.89|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   14|07:00   |      5|0.5518|   0.6643|    2.5639|     4.8813|      49.89|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   15|07:30   |      5|0.5767|   0.7251|    3.0594|     5.3394|      48.16|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   16|08:00   |      9|0.4962|   0.5992|    0.4975|     0.5318|      45.14|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   17|08:30   |      8|0.5317|   0.6946|    3.6832|     6.6077|      56.70|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   18|09:00   |      9|1.1273|   2.2669|    3.8138|     8.1027|      56.02|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   19|09:30   |      9|0.5828|   0.7383|    8.1237|    15.4273|      62.23|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   20|10:00   |     10|1.3839|   2.6395|   13.8913|    30.8402|      61.99|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   21|10:30   |     10|0.5943|   0.7261|    5.8964|    13.8142|      60.86|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   22|11:00   |     12|0.5230|   0.6483|    0.4923|     0.5156|      48.56|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   23|11:30   |     10|0.5073|   0.6291|    4.1672|     6.9196|      63.48|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   24|12:00   |      9|1.5881|   3.4937|   13.9806|    25.3669|      71.08|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   25|12:30   |     12|0.5949|   0.7558|    1.7774|     3.4218|      54.70|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   26|13:00   |     12|0.4850|   0.6122|    2.1081|     4.9460|      56.79|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   27|13:30   |     13|0.6054|   0.7224|    6.3373|    14.6660|      56.09|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   28|14:00   |     12|0.9037|   1.8848|    2.9823|     6.9839|      56.71|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   29|14:30   |     12|1.3013|   2.9203|    7.3702|    17.0771|      57.41|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   30|15:00   |     13|0.5163|   0.6589|    0.6311|     0.9411|      51.74|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   31|15:30   |     12|0.8237|   1.4580|    6.8628|    13.9997|      61.35|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   32|16:00   |     14|0.8067|   1.4152|    3.5954|     7.5356|      56.08|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   33|16:30   |     13|0.8675|   1.7568|    4.4680|    11.1452|      54.03|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   34|17:00   |     12|1.7370|   4.1529|    7.8506|    18.7565|      58.15|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   35|17:30   |     11|1.4980|   3.2992|   19.5509|    42.6512|      64.28|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   36|18:00   |     12|0.9937|   1.6129|    4.0630|     8.6971|      55.11|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   37|18:30   |     11|0.4735|   0.5577|    2.1979|     4.6018|      53.69|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   38|19:00   |     11|0.5539|   0.6366|    3.3152|     9.0017|      49.84|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   39|19:30   |     10|0.5288|   0.6070|    2.8375|     5.5163|      54.01|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   40|20:00   |     11|1.7888|   4.2986|    4.9194|    12.7403|      53.02|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   41|20:30   |     10|1.3010|   2.5268|    8.5427|    20.5821|      53.12|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   42|21:00   |     10|0.5259|   0.6375|    8.4066|    19.2426|      57.51|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   43|21:30   |     10|0.7358|   1.2307|    3.2608|     6.6859|      49.57|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   44|22:00   |      9|0.5941|   0.6983|    1.6726|     3.6633|      54.61|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   45|22:30   |      7|1.3112|   2.2735|   15.5813|    29.5775|      63.09|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   46|23:00   |      8|0.8151|   1.1752|    2.5183|     4.5128|      54.50|
    +-----+--------+-------+------+---------+----------+-----------+-----------+
    |   47|23:30   |      8|1.6981|   3.0315|    7.2277|    14.3897|      54.46|
    +-----+--------+-------+------+---------+----------+-----------+-----------+

Abandoned Calls
--------------------
Next we look at the percentage of non-emergency calls that were dropped without being
answered by an evaluator.
Clearly, if the calls were answered immediately, none of them would be abandoned.
Therefore, it is reasonable to assume that non-emergency ASA has a positive impact on
the number of abandoned calls and hence proportion of abandoned calls to all presented
calls.

.. figure:: ./images/nasa_abond.png
    :width: 90%
    :align: center
    :name: abndnd

    Correlation between non-emergency ASA and proportion of abandoned calls

:numref:`abndnd` illustrates a non-linear correlation between non-emergency ASA and
proportion of abandoned calls. It is evident that if non-emergency ASA is kept below
5 minutes, then the expectation of having over 30% abandoned calls is very low.
