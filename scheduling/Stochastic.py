import numpy as np
from scipy.stats import t, sem

from .MultiMachine import MultiMachineMILP, FCFSP, Preemptive
from .Task import Tasks


def find_asas(res):
    """
    Returns the average speed of response to each category of tasks based on their weight category

    :param res: the suggested schedule
    :return: the average speed of response for each weight
    """
    w8s = list(set([res[_]['weight'] for _ in res if _ != 'Message']))
    w8s.sort()
    delays = [0 for _ in w8s]
    counts = [0 for _ in w8s]
    for key in res:
        if key != 'Message':
            idx = w8s.index(res[key]['weight'])
            counts[idx] += 1
            delays[idx] += (res[key]['start'] - res[key]['release'])
    asas = dict()
    for _ in range(len(w8s)):
        asas[w8s[_]] = delays[_] / max(1, counts[_])
    return asas


def utilizations(res):
    """
    Finds the utilization of each resource based on the suggested schedule

    :param res: the schedule
    :return: a dictionary of utilization amounts for each resource
    """
    resources = list(set([res[_]['resources'] for _ in res if _ != 'Message']))
    resources.sort()
    busy = {_: 0 for _ in resources}
    for key in res:
        if key != 'Message':
            agent = res[key]['resources']
            busy[agent] += res[key]['actual_process'] if 'actual_process' in res[key] else (
                    res[key]['finish'] - res[key]['start'])
    return busy


def conf_int(data, ci=.95):
    """
    Finds the confidence intervals given the confidence level `ci`

    :param data: The array of numbers
    :param ci: confidence level
    :return: a triplet consisting of mean, lower limit and upper limit of the confidence interval.
    """
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), sem(a)
    h = se * t.ppf((1 + ci) / 2., n - 1)
    return m, m - h, m + h


class Evaluate(object):
    pass


class GenerateSchedule(object):
    def __init__(self, num_res, priorities, n_calls, durations, release, due=3600):
        self.num_res = num_res
        self.priorities = priorities
        self.priorities.sort()
        self.due = due
        calls_keys = list(n_calls.keys())
        calls_keys.sort()
        durations_keys = list(durations.keys())
        durations_keys.sort()
        release_keys = list(release.keys())
        release_keys.sort()
        if self.priorities != calls_keys:
            raise Exception("'n_calls' keys do not match priorities")
        if self.priorities != durations_keys:
            raise Exception("'durations' keys do not match priorities")
        if self.priorities != release_keys:
            raise Exception("'release' keys do not match priorities")
        self.n_calls = n_calls
        self.durations = durations
        self.release = release

    def __call__(self, *args, **kwargs):
        J = Tasks()
        for lvl in self.priorities:
            n_calls = self.n_calls[lvl]()
            for cnt in range(n_calls):
                duration = self.durations[lvl]()
                release = self.release[lvl]()
                J.add_task(task_name='P%d-%d' % (lvl, cnt),
                           release=release,
                           due=self.due,
                           weight=lvl,
                           process={'A%d' % _: duration for _ in range(self.num_res)}
                           )
        return J


def generate_run_eval(schdl, model):
    J = schdl()
    if model == 'lp':
        A = MultiMachineMILP(J, **{'solver': 'cplex', 'respect_due': False, 'priority': True,
                                   'executable': "/opt/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux/cplex"})
    elif model == 'fcfsp':
        A = FCFSP(J)
    elif model == 'preemptive':
        A = Preemptive(J)
    res = A()
    asa = find_asas(res)
    util = utilizations(res)
    return asa, util


class Stochastic(object):
    def __init__(self, model='fcfsp', schdl=None, n_iter=50, n_jobs=6, ci=.95):
        self.n_iter = n_iter
        self.n_jobs = n_jobs
        self.model = model
        self.schedule = schdl
        self.priorities = schdl.priorities
        self.ci = ci

    def __call__(self, *args, **kwargs):
        from joblib import Parallel, delayed
        perfs = {_: [] for _ in self.priorities}
        utils = []
        res = Parallel(n_jobs=self.n_jobs)(
            delayed(generate_run_eval)(schdl=self.schedule, model=self.model) for _ in range(self.n_iter))
        for pair in res:
            utils.append(sum(pair[1].values()) / len(pair[1]))
            for pr in pair[0]:
                perfs[pr].append(pair[0][pr])
        return {_: conf_int(perfs[_], ci=self.ci) for _ in perfs}, conf_int(utils, ci=self.ci)
