"""
===============================
PCB Specific Module
===============================
"""
import gc
import os
import signal
import time
from pprint import pprint

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm, t, sem


def find_std(mx, size, mu=None, mn=10):
    """
    Finds the standard deviation of a normal distribution when minimum, maximum, size of data, and the average are known

    :param mx: known maximum of data points
    :param size: number of data points
    :param mu: average of the data
    :param mn: known minimum of data points
    :return: standard deviation of the assumed Normal distribution
    """
    if size <= 1:
        return 0
    if mx == mn:
        return 0
    if mu is not None:
        g = lambda s, m=mn, M=mx, mu=mu, n=size: -(
                (n - 2) * np.log(norm().cdf((M - mu) / s) - norm().cdf((m - mu) / s)) + np.log(
            norm().pdf((M - mu) / s)) + np.log(norm().pdf((m - mu) / s)) - 2 * np.log(s))
    else:
        g = lambda s, m=mn, M=mx, n=size: -(
                (n - 2) * np.log(1 - 2 * norm().cdf(-(M - m) / (2 * s))) - (M - m) ** 2 / (4 * s ** 2) - 2 * np.log(
            s))
    x0 = (mx - mn) / 2.
    # res = minimize(g, x0, method='BFGS')
    # return res['x'][0]+0
    res = minimize(g, x0, method='COBYLA')
    return res['x'] + 0.


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


def kill_cplex():
    """
    Kills a running instance of ``CPLEX``

    :return: `pid` of the CPLEX instance
    """
    import subprocess
    subprocess = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    output, error = subprocess.communicate()

    target_process = "cplex"
    for line in output.splitlines():
        if target_process in str(line):
            pid = int(line.split(None, 1)[0])
            print(pid)
            os.kill(pid, 9)


def handler(signum, frame):
    """
    Raises an exception when a timeout signal is triggered

    :param signum: signal number
    :param frame: scope of signal
    :return: `None`
    """
    print("Forever is over!")
    kill_cplex()
    raise Exception("end of time")


class Perimeter(object):
    """
    Takes a Perimeter excel file for pre processing and scheduling
    """

    def __init__(self, skiprows=1, fname=None, div=1, calc_std=True, start_date=None, end_date=None):
        self.div = div
        self.weights = dict(emergency=17, nonemergency=3, breaks=1)
        self.emergency = [7809443700, 7809443750]
        self.nonemergency = [7809443675]  # , 7804081618, 7804084264, 7809443600, 7809443698, 7809443699, 7809443759]
        self.columns = ['date', 'start_time', 'idx', 'dn_xref', 'priority', 't_duration', 'max_duration', 'n_complete',
                        't_delay', 'max_delay', 'n_offer', 'n_answer', 'n_presented',  # 'sigma_delay',
                        'sigma_duration']
        fname_eval = "./data/DN_perimeter_export.xls"
        if fname is not None:
            fname_eval = fname
        if fname.endswith('.xsl'):
            df_eval = pd.read_excel(fname_eval, skiprows=skiprows)
            df_eval['idx'] = df_eval.apply(lambda x: int(2 * x['start_time'].hour + x['start_time'].minute / 30),
                                           axis=1)
        else:
            df_eval = pd.read_csv(fname_eval, parse_dates=['date'])
        if start_date is not None:
            df_eval = df_eval[df_eval['date'] >= start_date]
        if end_date is not None:
            df_eval = df_eval[df_eval['date'] < end_date]
        # df_eval['sigma_delay'] = df_eval.apply(
        #    lambda x: find_std(x['max_delay'], x['n_offer'], mu=(x['t_delay'] / max(1, x['n_offer'])), mn=1), axis=1)
        if calc_std:
            df_eval['sigma_duration'] = df_eval.apply(
                lambda x: find_std(x['max_duration'], x['n_complete'], mu=(x['t_duration'] / max(1, x['n_complete'])),
                                   mn=10), axis=1)
        df_eval = df_eval[df_eval['dn_xref'].isin(self.emergency + self.nonemergency)]
        df_eval['priority'] = df_eval.apply(lambda x, nemg=self.nonemergency: 1 if x['dn_xref'] in nemg else 0, axis=1)
        self.df = df_eval[self.columns]
        clmns = ['date', 'idx', 'n_complete', 'n_offer', 'n_answer', 'n_presented']
        df0 = self.df[self.df['priority'] == 0][clmns]
        df1 = self.df[self.df['priority'] == 1][clmns]
        mx_calls = lambda x: max(x['n_complete'], x['n_offer'], x['n_answer'])
        mx_calls2 = lambda x: max(x['n_offer'], x['n_presented'])
        df0['mx'] = df0.apply(mx_calls, axis=1)
        df1['mx'] = df1.apply(mx_calls, axis=1)
        df0['mx2'] = df0.apply(mx_calls2, axis=1)
        df1['mx2'] = df1.apply(mx_calls2, axis=1)
        self.df0_means = df0.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').mean()['mx']
        self.df1_means = df1.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').mean()['mx']
        self.df0_stds = df0.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').std()['mx']
        self.df1_stds = df1.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').std()['mx']
        self.df0_means2 = df0.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').mean()['mx2']
        self.df1_means2 = df1.groupby(['date', 'idx']).sum().reset_index(level=1).groupby('idx').mean()['mx2']

    def generate_synth(self):
        """
        Generates a DataFrame with synthetic calls information, including arrival time, duration, and their dn.

        :return: a DataFrame including all generated synthetic data
        """
        from scipy.stats import truncnorm, uniform
        synth_df = pd.DataFrame()
        for _, row in self.df.iterrows():
            clip_a = 10
            clip_b = max(float(row['max_duration']), clip_a + 1)
            scale = float(row['sigma_duration'])
            n_calls = max(int(row['n_complete']), int(row['n_offer']))
            if scale == 0 or int(row['n_complete']) == 0:
                continue
            mean = float(row['t_duration']) / int(row['n_complete'])
            try:
                X = truncnorm(a=(clip_a - mean) / scale, b=(clip_b - mean) / scale, loc=mean, scale=scale).rvs(
                    size=int(n_calls / self.div))
                X = X.round().astype(int)
                idx = [row['idx']] * int(n_calls / self.div)
                Y = uniform.rvs(loc=0, scale=1750, size=int(n_calls / self.div))
                Y = Y.round().astype(int)
                dn_xref = [row['dn_xref']] * int(n_calls / self.div)
                priority = [row['priority']] * int(n_calls / self.div)
                synth_df = pd.concat(
                    [synth_df,
                     pd.DataFrame({'idx': idx, 'duration': X, 'time': Y, 'priority': priority, 'dn_xref': dn_xref})],
                    ignore_index=True)
            except ValueError:
                print(clip_a, clip_b, mean, scale, n_calls)

        return synth_df

    def generate_call_counts(self, idx):
        """
        Randomly produces number of emergency and non-emergency calls for a given time slot

        :param idx: the index of 30-minutes time slot
        :return: tuple (number of emergency calls, number of non-emergency calls)
        """
        m0 = self.df0_means[idx]
        m1 = self.df1_means[idx]
        s0 = self.df0_stds[idx]
        s1 = self.df1_stds[idx]
        x1 = max(norm(m0, s0).rvs(size=1).round().astype(int)[0], 0)
        x2 = max(norm(m1, s1).rvs(size=1).round().astype(int)[0], 0)
        return x1, x2

    def sample(self, idx):
        """
        Randomly samples the synthetic dataset for the given time slot

        :param idx: the index of the time slot
        :return: DataFrame
        """
        try:
            call_df = pd.read_csv('./data/sim_calls.csv')
        except FileNotFoundError:
            call_df = self.generate_synth()
            call_df.to_csv("./data/sim_calls.csv", index=False)
        n0, n1 = self.generate_call_counts(idx)
        print(n0, n1)
        smpl0 = call_df[(call_df['priority'] == 0) & (call_df['idx'] == idx)].sample(n0)
        smpl1 = call_df[(call_df['priority'] == 1) & (call_df['idx'] == idx)].sample(n1)
        return pd.concat([smpl0, smpl1])

    def evaluation_schedule(self, time_slot, num_res=4, sto=5, priority=False, model='lp', visuals=False):
        """
        Finds the performance measures for a automatically generated optimal schedule

        :param time_slot: the index of the time slot
        :param num_res: number of available evaluators
        :param sto: scheduled time off, default 5 minutes
        :param priority: `boolean` determines whether the priority of calls has to be considered for
            schedule optimization or not
        :return: a dictionary of performance measures
        """
        from .MultiMachine import MultiMachineMILP, FCFSP, Preemptive
        from .Task import Tasks
        from .Visuals import Visuals
        from random import randint

        gc.enable()
        gc.collect()

        t_df = self.sample(time_slot)
        J = Tasks()
        V = None
        call_no = 0
        for idx, row in t_df.iterrows():
            if priority:
                if row['priority'] == 1:
                    J.add_task(task_name='C%d' % call_no, release=float(row['time']), due=1800,
                               weight=self.weights['nonemergency'],
                               process={'A%d' % _: max(60., float(row['duration'])) for _ in range(num_res)})
                else:
                    J.add_task(task_name='C%d' % call_no, release=float(row['time']), due=1800,
                               weight=self.weights['emergency'],
                               process={'A%d' % _: max(60., float(row['duration'])) for _ in range(num_res)})
            else:
                J.add_task(task_name='C%d' % call_no, release=float(row['time']), due=1800,
                           process={'A%d' % _: max(60., float(row['duration'])) for _ in range(num_res)})
            call_no += 1
        for idx in range(num_res):
            J.add_task(task_name='NA%d' % idx, release=randint(0, 1800), due=2000, weight=self.weights['breaks'],
                       process={'A%d' % idx: randint(max(0, sto - 3), sto + 3) * 60})
            # J[hr].schedule_unavailable(resource='A%d'%idx, process=10*60, release=hr*3600, start=None, due=None)
        if model == 'lp':
            A = MultiMachineMILP(J, **{'solver': 'cplex', 'respect_due': False, 'priority': True,
                                       'executable': "/opt/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux/cplex"})
        elif model == 'fcfsp':
            A = FCFSP(J)
        elif model == 'preemptive':
            A = Preemptive(J)
        # A = MultiMachineMILP(J[hr], **{'solver': 'scip', 'respect_due': False, 'priority':priority})
        # pprint(J[hr].Tasks)
        res = A()
        # pprint(res)
        asa = find_asas(res)
        util = utilizations(res)
        pprint(asa)
        pprint(util)
        params = {'Title': "Schedule for slot %d" % time_slot, 'Subtitle': 'Agents Schedule', 'ylabel': "Calls",
                  'Resource': "Agent"}
        plt = None
        if visuals:
            V = Visuals(A)
            plt = V.gantt(**params)
            plt.show()
        del J
        del A
        del res
        del V
        gc.collect()
        return asa, util, plt

    def stochastic(self, time_slot, num_res=4, iter=10, timeout=300, ci=.95, model='lp', visuals=False):
        """
        Runs the schedule evaluation procedure stochastically

        :param time_slot: the index of the time slot
        :param num_res: number of evaluators
        :param iter: number of iterations
        :param timeout: time limit to execute the optimization
        :param ci: confidence level (default 95%)
        :param model:
        :param visuals:
        :return: dictionary of performance measures with confidence intervals
        """
        gc.enable()
        gc.collect()
        idx = 0
        asas_em = []
        asas_nem = []
        util = []
        while idx < iter:
            if model == 'lp':
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(timeout)
            #try:
            if True:
                gc.collect()
                print("Iteration %d" % idx)
                A, B, _ = self.evaluation_schedule(time_slot, num_res=num_res, priority=True, model=model,
                                                   visuals=visuals)
                idx += 1
                if self.weights['emergency'] in A:
                    asas_em.append(A[self.weights['emergency']])
                if self.weights['nonemergency'] in A:
                    asas_nem.append(A[self.weights['nonemergency']])
                util.append(sum(B.values()) / len(B))
                print("---" * 20)
            #except:
            #    pass
            if model == 'lp':
                signal.alarm(0)
            time.sleep(1)
        return {'EM': conf_int(asas_em, ci=ci), "NEM": conf_int(asas_nem, ci=ci),
                "Util": conf_int(util, ci=ci)}, asas_em, asas_nem, util
