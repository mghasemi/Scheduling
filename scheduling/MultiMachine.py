"""
=========================
Scheduling Models
=========================
"""
import gc

THRESHOLD = 1.e3
TOLORENCE = 1.e-3


class MultiMachineMILP(object):
    """
    This is the class implementing the classical MILP version of Machine-Task scheduling.
    The class takes advantage from Pyomo which allows python code to call most well-known optimizers like
    CPLES, Gurobi, Knitro, etc.

    :param tasks: a loaded `Tasks` instance
    :param kwargs: a dictionary with the following optional values:

        + ``solver``: the optimizer engine. Default is set to the open source ``glpk``
        + ``executable``: The path to the engines executable, if not available under `PATH`
        + ``respect_due``: Boolean, default is False. If True, forces model to find an optimal schedule respecting all due dates
        + ``cost``: Boolean, default is False. If True, the objective is set to minimize cost
        + ``priority``: Boolean, default is False. If True, the objective is set to minimize weighted delay
    """

    def __init__(self, tasks=None, **kwargs):
        from math import ceil
        if tasks is None:
            from scheduling.Task import Tasks
            tasks = Tasks()
        self.tasks = tasks
        if self.tasks.Tasks != {}:
            self.r_min = ceil(
                min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx)
            )
            self.d_max = 1 + int(max(self.tasks.Tasks[_]["due"] for _ in self.tasks.TaskIdx))
        else:
            self.r_min = 0
            self.d_max = 0
        self.r_min = 0
        self.T = range(self.r_min, self.d_max)
        self.model = None
        self.respect_due = kwargs.get('respect_due', False)
        self.cost_objective = kwargs.get('cost', False)
        self.priority_objective = kwargs.get('priority', False)
        self.timetable = {}
        self.solver = kwargs.get('solver', 'glpk')
        self.executable = kwargs.get('executable', None)
        self.validate = kwargs.get('validate', False)

    def __call__(self, *args, **kwargs):
        """
        Forms the scheduling problem through `pyomo` and solves the corresponding problem.

        :return: A schedule which is a dictionary of the form `{Task:{'start': s, 'finish': e}, ...}`
        """
        from pyomo.environ import (
            ConcreteModel,
            Set,
            Var,
            Binary,
            Param,
            NonNegativeReals,
            Objective,
            minimize,
            Constraint,
            SolverFactory
        )
        # from pyomo.kernel import Binary, NonNegativeReals
        from pyomo.opt import SolverStatus

        gc.enable()

        solver = kwargs.get('solver', self.solver)

        self.model = ConcreteModel()
        # Parameters
        self.model.J = Set(initialize=self.tasks.TaskIdx)
        self.model.S = Set(initialize=self.tasks.Resources)
        self.model.JSPairs = Set(
            initialize=self.model.J * self.model.S,
            dimen=2,
            filter=lambda mdl, j, s: True,  # m in self.tasks.Tasks[j]["process"],
        )
        self.model.ExJS = Set(
            initialize=self.model.J * self.model.S,
            dimen=2,
            filter=lambda mdl, j, s: not (s in self.tasks.Tasks[j]["process"]),
        )
        self.model.IneqPairs = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 != j1,
        )
        self.model.LeqPairs = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 < j1,
        )
        self.model.SIneqPairs = Set(
            initialize=self.model.S * self.model.S,
            dimen=2,
            filter=lambda mdl, s0, s1: s0 != s1,
        )
        self.model.Prerequisite = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, i, j: (i, j) in self.tasks.Prerequisite,
        )
        self.model.StrictStart = Set(
            initialize=self.model.J,
            dimen=1,
            filter=lambda mdl, j: "start" in self.tasks.Tasks[j],
        )
        # C = {k: self.tasks.Tasks[k[0]]["weight"] for k in self.model.JSPairs}
        C = {k: self.tasks.Tasks[k]["weight"] for k in self.model.J}
        R = {k: self.tasks.Tasks[k]["release"] for k in self.model.J}
        D = {k: self.tasks.Tasks[k]["due"] for k in self.model.J}
        P = {
            k: self.tasks.Tasks[k[0]]["process"][k[1]]
            if k[1] in self.tasks.Tasks[k[0]]["process"]
            else THRESHOLD  # 0  # Does this need to be very LARGE?
            for k in self.model.JSPairs
        }
        U = self.d_max - self.r_min
        # self.model.c = Param(self.model.JSPairs, initialize=C, default=1)
        self.model.c = Param(self.model.J, initialize=C, default=1)
        self.model.r = Param(self.model.J, initialize=R, default=1)
        self.model.d = Param(self.model.J, initialize=D, default=1)
        self.model.p = Param(self.model.JSPairs, initialize=P)
        # Variables
        self.model.x = Var(self.model.JSPairs, domain=Binary)
        self.model.y = Var(self.model.IneqPairs, domain=Binary)
        self.model.s = Var(self.model.J, domain=NonNegativeReals, bounds=(0, self.d_max))
        self.model.e = Var(
            self.model.J, domain=NonNegativeReals, bounds=(0, 2 * self.d_max)
        )
        # Objective
        if self.cost_objective:
            self.model.obj = Objective(
                expr=sum(
                    self.model.c[j, s] * self.model.x[j, s] for j, s in self.model.JSPairs
                ),
                sense=minimize,
            )
        elif self.priority_objective:
            # for j in self.model.J:
            #    print(j, self.tasks.Tasks[j]["weight"], self.model.c[j], self.tasks.Tasks[j]["release"],
            #          self.model.r[j])
            # expr = sum(
            #    self.model.c[j, s] * (self.model.s[j] - self.tasks.Tasks[j]["release"]) for j, s in
            #    self.model.JSPairs
            # )
            expr = sum(
                self.model.c[j] * (self.model.s[j] - self.tasks.Tasks[j]["release"]) for j in
                self.model.J
            )
            # print(expr)
            self.model.obj = Objective(
                expr=sum(
                    self.model.c[j] * (self.model.s[j] - self.model.r[j]) for j in
                    self.model.J
                ),
                sense=minimize,
            )
        else:
            self.model.obj = Objective(
                expr=sum(
                    self.model.e[j] - self.model.d[j] for j in self.model.J
                ),
                sense=minimize,
            )
        # Constraints
        self.model.Cns0 = Constraint(
            self.model.ExJS, rule=lambda mdl, j, s: self.model.x[j, s] == 0
        )
        self.model.Cns1 = Constraint(
            self.model.J,
            rule=lambda mdl, j: sum(mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 1,
        )
        self.model.Cns2 = Constraint(
            self.model.S,
            rule=lambda mdl, s: (
                                        0
                                        <= sum(
                                    mdl.p[j, s] * mdl.x[j, s] for j in mdl.J if (j, s) in mdl.JSPairs
                                )
                                )
                                <= self.d_max - self.r_min,
        )
        self.model.Cns3 = Constraint(
            self.model.J,
            rule=lambda mdl, j: mdl.s[j]
                                - mdl.e[j]
                                + sum(mdl.p[j, s] * mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 0,
        )  # CBM
        self.model.Cns4 = Constraint(
            # self.model.J, rule=lambda mdl, j: self.tasks.Tasks[j]["release"] <= mdl.s[j]
            self.model.J, rule=lambda mdl, j: self.model.r[j] <= mdl.s[j]
        )
        # Force find a schedule within due dates
        if self.respect_due:
            self.model.Cns5 = Constraint(
                self.model.J,
                rule=lambda mdl, j: (0.0 <= mdl.e[j]) <= self.model.d[j],
            )
        # Prerequisite
        self.model.Cns6 = Constraint(
            self.model.IneqPairs,
            rule=lambda mdl, i, j: mdl.e[i] - mdl.s[j] + U * mdl.y[i, j] <= U,
        )
        self.model.Cns7 = Constraint(
            self.model.LeqPairs, rule=lambda mdl, i, j: mdl.y[i, j] + mdl.y[j, i] <= 1
        )
        self.model.Cns8 = Constraint(
            self.model.LeqPairs * self.model.S,
            rule=lambda mdl, i, j, s: mdl.x[i, s]
                                      + mdl.x[j, s]
                                      - mdl.y[i, j]
                                      - mdl.y[j, i]
                                      <= 1,
        )
        self.model.Cns9 = Constraint(
            self.model.LeqPairs * self.model.SIneqPairs,
            rule=lambda mdl, i, j, l, s: mdl.x[i, l]
                                         + mdl.x[j, s]
                                         + mdl.y[i, j]
                                         + mdl.y[j, i]
                                         <= 2,
        )
        self.model.Cns10 = Constraint(
            self.model.Prerequisite, rule=lambda mdl, i, j: mdl.y[i, j] == 1
        )
        self.model.Cns11 = Constraint(
            self.model.StrictStart,
            rule=lambda mdl, j: mdl.s[j] == self.tasks.Tasks[j]["start"],
        )
        if self.executable is None:
            solver_instance = SolverFactory(solver)
            if solver == 'scip':
                solver_instance.options['parallel/minthreads'] = 3
            results = solver_instance.solve(self.model)
        else:
            solver_instance = SolverFactory(solver, executable=self.executable, validate=self.validate)
            if solver == 'knitroampl':
                solver_instance.options['par_numthreads'] = 4
            results = solver_instance.solve(self.model)
        if results.solver.status == SolverStatus.ok:
            # print(self.model.obj())
            for j in self.model.J:
                self.timetable[j] = {
                    "start": self.model.s[j](),
                    "finish": self.model.e[j](),
                    "release": self.tasks.Tasks[j]["release"],
                    "resources": [s for s in self.model.S if self.model.x[j, s]()][0],
                    # "weight": [self.model.c[j, s] for s in self.model.S if self.model.x[j, s]][0]
                    "weight": [self.model.c[j] for s in self.model.S if self.model.x[j, s]][0]
                }
            self.timetable["Message"] = "Success"
        else:
            self.timetable["Message"] = "No feasible schedule was found."
        gc.collect()
        del self.model
        return self.timetable


class MultiMachineQP(object):
    def __init__(self, tasks=None, **kwargs):
        from math import ceil
        if tasks is None:
            from scheduling.Task import Tasks
            tasks = Tasks()
        self.tasks = tasks
        if self.tasks.Tasks != {}:
            self.r_min = ceil(
                min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx)
            )
            self.d_max = 1 + int(max(self.tasks.Tasks[_]["due"] for _ in self.tasks.TaskIdx))
        else:
            self.r_min = 0
            self.d_max = 0
        self.T = range(self.r_min, self.d_max)
        self.model = None
        self.respect_due = kwargs.get('respect_due', False)
        self.cost_objective = kwargs.get('cost', False)
        self.timetable = {}
        self.solver = kwargs.get('solver', 'glpk')
        self.executable = kwargs.get('executable', None)

    def __call__(self, *args, **kwargs):
        """
        Forms the scheduling problem through `pyomo` and solves the corresponding problem.
        :return: A schedule which is a dictionary of the form `{Task:{'start': s, 'finish': e}, ...}`
        """
        from pyomo.environ import (
            ConcreteModel,
            Set,
            Var,
            Param,
            NonNegativeReals,
            Objective,
            minimize,
            Constraint,
            SolverFactory,
        )
        # from pyomo.kernel import Binary, NonNegativeReals
        from pyomo.opt import SolverStatus

        solver = kwargs.get('solver', self.solver)

        self.model = ConcreteModel()
        # Parameters
        self.model.J = Set(initialize=self.tasks.TaskIdx)
        self.model.S = Set(initialize=self.tasks.Resources)
        self.model.JSPairs = Set(
            initialize=self.model.J * self.model.S,
            dimen=2,
            filter=lambda mdl, j, s: True,  # m in self.tasks.Tasks[j]["process"],
        )
        self.model.ExJS = Set(
            initialize=self.model.J * self.model.S,
            dimen=2,
            filter=lambda mdl, j, s: not (s in self.tasks.Tasks[j]["process"]),
        )
        self.model.IneqPairs = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 != j1,
        )
        self.model.LeqPairs = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 < j1,
        )
        self.model.SIneqPairs = Set(
            initialize=self.model.S * self.model.S,
            dimen=2,
            filter=lambda mdl, s0, s1: s0 != s1,
        )
        self.model.Prerequisite = Set(
            initialize=self.model.J * self.model.J,
            dimen=2,
            filter=lambda mdl, i, j: (i, j) in self.tasks.Prerequisite,
        )
        self.model.StrictStart = Set(
            initialize=self.model.J,
            dimen=1,
            filter=lambda mdl, j: "start" in self.tasks.Tasks[j],
        )
        C = {k: self.tasks.Tasks[k[0]]["weight"] for k in self.model.JSPairs}
        P = {
            k: self.tasks.Tasks[k[0]]["process"][k[1]]
            if k[1] in self.tasks.Tasks[k[0]]["process"]
            else THRESHOLD  # 0  # Does this need to be very LARGE?
            for k in self.model.JSPairs
        }
        U = self.d_max - self.r_min
        self.model.c = Param(self.model.JSPairs, initialize=C, default=1)
        self.model.p = Param(self.model.JSPairs, initialize=P)
        # Variables
        self.model.x = Var(self.model.JSPairs, domain=NonNegativeReals)
        self.model.y = Var(self.model.IneqPairs, domain=NonNegativeReals)
        self.model.s = Var(self.model.J, domain=NonNegativeReals, bounds=(0, self.d_max))
        self.model.e = Var(
            self.model.J, domain=NonNegativeReals, bounds=(0, 2 * self.d_max)
        )
        # Objective
        if self.cost_objective:
            self.model.obj = Objective(
                expr=sum(
                    self.model.c[j, s] * self.model.x[j, s] for j, s in self.model.JSPairs
                ),
                sense=minimize,
            )
        else:
            self.model.obj = Objective(
                expr=sum(
                    self.model.e[j] - self.tasks.Tasks[j]["due"] for j in self.model.J
                ),
                sense=minimize,
            )
        # Constraints
        self.model.Cns0 = Constraint(
            self.model.ExJS, rule=lambda mdl, j, s: self.model.x[j, s] == 0
        )
        self.model.Cns01 = Constraint(self.model.JSPairs,
                                      rule=lambda mdl, j, s: mdl.x[j, s] * (mdl.x[j, s] - 1.) <= TOLORENCE)
        self.model.Cns02 = Constraint(self.model.JSPairs,
                                      rule=lambda mdl, j, s: mdl.x[j, s] * (mdl.x[j, s] - 1.) >= -TOLORENCE)
        self.model.Cns03 = Constraint(self.model.IneqPairs,
                                      rule=lambda mdl, i, j: mdl.y[i, j] * (mdl.y[i, j] - 1.) <= TOLORENCE)
        self.model.Cns04 = Constraint(self.model.IneqPairs,
                                      rule=lambda mdl, i, j: mdl.y[i, j] * (mdl.y[i, j] - 1.) >= -TOLORENCE)
        self.model.Cns1 = Constraint(
            self.model.J,
            rule=lambda mdl, j: sum(mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 1,
        )
        self.model.Cns2 = Constraint(
            self.model.S,
            rule=lambda mdl, s: (
                                        0
                                        <= sum(
                                    mdl.p[j, s] * mdl.x[j, s] for j in mdl.J if (j, s) in mdl.JSPairs
                                )
                                )
                                <= self.d_max - self.r_min,
        )
        self.model.Cns3 = Constraint(
            self.model.J,
            rule=lambda mdl, j: mdl.s[j]
                                - mdl.e[j]
                                + sum(mdl.p[j, s] * mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 0,
        )  # CBM
        self.model.Cns4 = Constraint(
            self.model.J, rule=lambda mdl, j: self.tasks.Tasks[j]["release"] <= mdl.s[j]
        )
        # Force find a schedule within due dates
        if self.respect_due:
            self.model.Cns5 = Constraint(
                self.model.J,
                rule=lambda mdl, j: (0.0 <= mdl.e[j]) <= self.tasks.Tasks[j]["due"],
            )
        # Prerequisite
        self.model.Cns6 = Constraint(
            self.model.IneqPairs,
            rule=lambda mdl, i, j: mdl.e[i] - mdl.s[j] + U * mdl.y[i, j] <= U,
        )
        self.model.Cns7 = Constraint(
            self.model.LeqPairs, rule=lambda mdl, i, j: mdl.y[i, j] + mdl.y[j, i] <= 1
        )
        self.model.Cns8 = Constraint(
            self.model.LeqPairs * self.model.S,
            rule=lambda mdl, i, j, s: mdl.x[i, s]
                                      + mdl.x[j, s]
                                      - mdl.y[i, j]
                                      - mdl.y[j, i]
                                      <= 1,
        )
        self.model.Cns9 = Constraint(
            self.model.LeqPairs * self.model.SIneqPairs,
            rule=lambda mdl, i, j, l, s: mdl.x[i, l]
                                         + mdl.x[j, s]
                                         + mdl.y[i, j]
                                         + mdl.y[j, i]
                                         <= 2,
        )
        self.model.Cns10 = Constraint(
            self.model.Prerequisite, rule=lambda mdl, i, j: mdl.y[i, j] == 1
        )
        self.model.Cns11 = Constraint(
            self.model.StrictStart,
            rule=lambda mdl, j: mdl.s[j] == self.tasks.Tasks[j]["start"],
        )
        if self.executable is None:
            results = SolverFactory(solver).solve(self.model)
        else:
            results = SolverFactory(solver, executable=self.executable).solve(self.model)
        print(results)
        if results.solver.status == SolverStatus.ok:
            for j in self.model.J:
                self.timetable[j] = {
                    "start": self.model.s[j](),
                    "finish": self.model.e[j](),
                    "resources": [s for s in self.model.S if self.model.x[j, s]()][0],
                }
            self.timetable["Message"] = "Success"
        else:
            self.timetable["Message"] = "No feasible schedule was found."
        return self.timetable


class ScipySchedule(object):
    def __init__(self, tasks):
        from math import ceil
        self.tasks = tasks
        self.num_tasks = len(self.tasks.TaskIdx)
        self.num_resources = len(self.tasks.Resources)
        self.r_min = ceil(min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx))
        self.d_max = 1 + int(max(self.tasks.Tasks[_]["due"] for _ in self.tasks.TaskIdx))
        self.r = [0. for _ in range(self.num_tasks)]
        self.d = [self.d_max for _ in range(self.num_tasks)]
        self.w = [1. for _ in range(self.num_tasks)]
        self.p = [[THRESHOLD for _ in range(self.num_resources)] for _ in range(self.num_tasks)]
        for idx in self.tasks.Tasks:
            tsk = self.tasks.Tasks[idx]
            self.r[idx] = tsk['release']
            self.d[idx] = tsk['due']
            self.w[idx] = tsk['weight']
            for res in tsk['process']:
                self.p[idx][self.tasks.Resources.index(res)] = tsk['process'][res]

    def var_x(self, i, j):
        return i * self.num_resources + j

    def var_y(self, i, j):
        return self.num_tasks * self.num_resources + i * self.num_tasks + j

    def var_s(self, i):
        return self.num_tasks * self.num_resources + self.num_tasks * self.num_tasks + i

    def var_e(self, i):
        return self.num_tasks * self.num_resources + (self.num_tasks + 1) * self.num_tasks + i

    def form_prg(self):
        obj = lambda x, d=tuple(self.d): sum([x[self.var_e(j)] - d[j] for j in range(self.num_tasks)])
        eq_const = []
        ineq_const = []
        U = 1. + self.d_max - self.r_min
        for j in range(self.num_tasks):
            eq_const.append({'type': 'eq',
                             'fun': lambda x, j_=j, num=self.num_resources: 1. - sum(
                                 [x[self.var_x(j_, m)] for m in range(num)])})
        for m in range(self.num_resources):
            ineq_const.append({'type': 'ineq',
                               'fun': lambda x, p=tuple(self.p), m_=m, U_=U, num=self.num_resources: U - sum(
                                   [p[j][m_] * x[self.var_x(j, m_)] for j in range(num)])})
        for j in range(self.num_tasks):
            eq_const.append({'type': 'eq',
                             'fun': lambda x, j_=j, m_=self.num_resources, p=tuple(self.p): x[self.var_s(j_)] - x[
                                 self.var_e(j_)] + sum([p[j_][m] * x[self.var_x(j, m)] for m in range(m_)])})
        for i in range(self.num_tasks):
            for j in range(self.num_tasks):
                if i != j:
                    ineq_const.append({'type': 'ineq',
                                       'fun': lambda x, i_=i, j_=j, U_=U: U_ * (
                                               1. - x[self.var_y(i_, j_)] - x[self.var_e(i_)] + x[self.var_s(j_)])})
        for j in range(self.num_tasks):
            ineq_const.append({'type': 'ineq',
                               'fun': lambda x, j_=j, rj=self.r[j]: x[self.var_s(j_)] - rj})
            ineq_const.append({'type': 'ineq',
                               'fun': lambda x, j_=j, dj=self.d[j]: dj - x[self.var_e(j_)]})
        for j in range(self.num_tasks):
            for i in range(j):
                if i < j:
                    ineq_const.append({'type': 'ineq',
                                       'fun': lambda x, i_=i, j_=j: 1. - x[self.var_y(i_, j_)] - x[self.var_y(j_, i_)]})
        for m in range(self.num_resources):
            for j in range(self.num_tasks):
                for i in range(j):
                    if i < j:
                        ineq_const.append({'type': 'ineq',
                                           'fun': lambda x, i_=i, j_=j, m_=m: 1. - x[self.var_x(i_, m_)] - x[
                                               self.var_x(j_, m_)] + x[self.var_y(i_, j_)] + x[self.var_y(j_, i_)]})
        for m in range(self.num_resources):
            for n in range(self.num_resources):
                if m != n:
                    for j in range(self.num_tasks):
                        for i in range(j):
                            if i < j:
                                ineq_const.append({'type': 'ineq',
                                                   'fun': lambda x, i_=i, j_=j, m_=m, n_=n: 2. - x[self.var_x(i_, n_)] -
                                                                                            x[self.var_x(j_, m_)] - x[
                                                                                                self.var_y(i_, j_)] - x[
                                                                                                self.var_y(j_, i_)]})
        bnds = [(0. - .01, U + .01) for _ in range(self.num_tasks * self.num_resources + (self.num_tasks + 1) ** 2)]

        x0 = tuple([0. for _ in range(len(bnds))])
        for i in range(self.num_tasks):
            for j in range(self.num_resources):
                bnds[self.var_x(i, j)] = (0. - .01, 1.01)
            for k in range(self.num_tasks):
                bnds[self.var_y(i, k)] = (0. - .01, 1.01)
            bnds[self.var_e(i)] = (0. - .01, U)
            bnds[self.var_s(i)] = (0. - .01, U)
        return {'obj': obj, 'const': eq_const + ineq_const, 'bounds': bnds, 'x0': x0}

    def solve(self, prg):
        from scipy.optimize import minimize
        res = minimize(prg['obj'], prg['x0'], method='SLSQP', constraints=prg['const'], bounds=prg['bounds'])
        return res


class FCFSP(object):
    def __init__(self, tasks=None, **kwargs):
        from copy import copy
        if tasks is None:
            from scheduling.Task import Tasks
            tasks = Tasks()
        self.tasks = tasks
        self.min_start = min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx)
        tasks_copy = copy(tasks)
        for _ in tasks_copy.Tasks:
            tasks_copy.Tasks[_]['new_release'] = tasks_copy.Tasks[_]['release']
        self.tasks_list = [tasks_copy.Tasks[_] for _ in tasks_copy.Tasks]
        self.num_resources = len(self.tasks.Resources)
        self.resource_available_at = [[self.min_start, self.tasks.Resources[_]] for _ in range(self.num_resources)]
        self.timetable = {}

    def sort_tasks(self):
        srt = lambda x: (x['new_release'], -x['weight'])
        self.tasks_list.sort(key=srt)

    def shift_tasks(self):
        self.resource_available_at.sort()
        shift = self.resource_available_at[0][0]
        for idx in range(len(self.tasks_list)):
            self.tasks_list[idx]['new_release'] = max(self.tasks_list[idx]['new_release'], shift)

    def assign(self):
        from copy import copy
        self.shift_tasks()
        flag = False
        idx_res = 0
        idx_tsk = 0
        res = copy(self.resource_available_at[idx_res])
        while not flag:
            res = copy(self.resource_available_at[idx_res])
            for idx_tsk in range(len(self.tasks_list)):
                tsk = self.tasks_list[idx_tsk]
                if res[1] in tsk['process']:
                    flag = True
                    break
            idx_res += 1
        tsk = self.tasks_list.pop(idx_tsk)
        self.timetable[tsk['id']] = dict(start=max(res[0], tsk['new_release']),
                                         release=self.tasks.Tasks[tsk['id']]['release'],
                                         finish=(max(res[0], tsk['new_release']) + tsk['process'][res[1]]),
                                         resources=res[1],
                                         weight=tsk['weight'])
        self.resource_available_at[0][0] = (max(res[0], tsk['new_release']) + tsk['process'][res[1]])

    def __call__(self, *args, **kwargs):
        self.sort_tasks()
        while self.tasks_list:
            self.assign()
        self.timetable["Message"] = "Success"
        return self.timetable


class Preemptive(object):
    def __init__(self, tasks, end_time=1800, step=2, queue_wait=2):
        from copy import copy
        self.end_time = end_time
        self.step = step
        if tasks is None:
            from scheduling.Task import Tasks
            tasks = Tasks()
        self.tasks = tasks
        self.min_start = min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx)
        self.end_time = max(
            (self.tasks.Tasks[_]["release"] + max(self.tasks.Tasks[_]["process"].values())) for _ in self.tasks.TaskIdx)
        self.queue_wait = queue_wait
        self.current_time = self.min_start
        tasks_copy = copy(tasks)
        for _ in tasks_copy.Tasks:
            tasks_copy.Tasks[_]['start'] = tasks_copy.Tasks[_]['release']
            tasks_copy.Tasks[_]['resume'] = tasks_copy.Tasks[_]['release']
            tasks_copy.Tasks[_]['elapsed'] = 0
            tasks_copy.Tasks[_]['working_process'] = tasks_copy.Tasks[_]['process']
            tasks_copy.Tasks[_]['answered'] = 0
            tasks_copy.Tasks[_]['preempted'] = 0
            tasks_copy.Tasks[_]['agent'] = None
        self.tasks_list = [tasks_copy.Tasks[_] for _ in tasks_copy.Tasks]
        self.num_resources = len(self.tasks.Resources)
        self.resource_available_at = [[self.min_start, self.tasks.Resources[_]] for _ in range(self.num_resources)]
        self.agent_task = {_: None for _ in self.tasks.Resources}
        self.agents_queue = {_: [] for _ in self.tasks.Resources}
        self.agents_order = [_ for _ in self.tasks.Resources]
        self.queue = []
        self.timetable = {}

    def tasks_available_at(self, t):
        avail = []
        for tsk in self.tasks_list:
            if tsk['release'] <= t and tsk['answered'] == 0:
                avail.append(tsk)
        return avail

    def sort_tasks(self, tasks):
        order = lambda x: (-x['weight'], x['release'])
        tasks.sort(key=order)
        return tasks

    def sort_agents(self):
        # TODO: remove extra sorting heare if redundant
        agent_tasks = [(_, self.sort_tasks(self.agents_queue[_])) for _ in self.tasks.Resources]
        order = lambda x: (len(x[1]), x[1][0]['weight'] if x[1] else -1000)
        agent_tasks.sort(key=order)
        return agent_tasks

    def answer(self, agent, task):
        task['answered'] = 1
        task['start'] = self.current_time
        task['resume'] = self.current_time
        task['agent'] = agent
        return task

    def unanswered(self):
        """
        Checks if any unanswered calls left
        """
        for tsk in self.tasks_list:
            if tsk['answered'] == 0:
                return True
        return False

    def busy_agent(self):
        for _ in self.agents_queue:
            if self.agents_queue[_]:
                return True
        return False

    def assign_task(self, agent, task):
        # TODO: sort needed?
        self.agents_queue[agent] = self.sort_tasks(self.agents_queue[agent])
        if not self.agents_queue[agent]:
            tsk = self.answer(agent, task)
            self.agents_queue[agent].append(task)
        else:
            if (self.agents_queue[agent][0]['weight'] < task['weight']) and (
                    self.current_time - task['release']) > self.queue_wait:
                tsk = self.answer(agent, task)
                a_n = len(self.agents_queue[agent])
                for i in range(a_n):
                    tmp_tsk = self.agents_queue[agent][i]
                    tmp_tsk['working_process'] = {_: tmp_tsk['working_process'][_] + task['process'][_] for _ in
                                                  task['process']}
                    if tmp_tsk['preempted'] == 0:
                        tmp_tsk['elapsed'] += self.current_time - tmp_tsk['resume']
                        tmp_tsk['preempted'] = 1
                    self.agents_queue[agent][i] = tmp_tsk
                self.agents_queue[agent].insert(0, tsk)
            else:
                tsk = None
        return tsk

    def refresh_agents_queue(self, agent):
        if not self.agents_queue[agent]:
            return
        tsk = self.agents_queue[agent][0]
        tsk['elapsed'] += self.current_time - tsk['resume']
        tsk['resume'] = self.current_time
        # Task is done:
        if tsk['elapsed'] >= tsk['process'][agent]:
            tsk['end'] = self.current_time
            self.timetable[tsk['id']] = dict(start=tsk['start'],
                                             release=self.tasks.Tasks[tsk['id']]['release'],
                                             finish=self.current_time,
                                             resources=agent,
                                             weight=tsk['weight'],
                                             actual_process=tsk['process'][agent])
            self.agents_queue[agent].pop(0)
            if self.agents_queue[agent]:
                self.agents_queue[agent][0]['preempted'] = 0
                self.agents_queue[agent][0]['resume'] = self.current_time
        return

    def clear_agents(self):
        for _ in self.agents_queue:
            self.refresh_agents_queue(_)

    def __call__(self, *args, **kwargs):
        while self.unanswered():
            self.clear_agents()
            tasks = self.tasks_available_at(self.current_time)
            tasks = self.sort_tasks(tasks)
            for tsk in tasks:
                sorted_agents = self.sort_agents()
                for agent, _ in sorted_agents:
                    if agent not in tsk['process']:
                        continue
                    assigned = self.assign_task(agent, tsk)
                    if assigned:
                        break
            self.current_time += self.step
        while self.busy_agent():
            self.clear_agents()
            self.current_time += self.step
        self.timetable["Message"] = "Success"
        return self.timetable
