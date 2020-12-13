class MultiMachineMILP(object):
    def __init__(self, tasks=None, **kwargs):
        from math import ceil
        if tasks is None:
            from scheduling.Task import Tasks
            tasks = Tasks()
        self.tasks = tasks
        if self.tasks.Tasks != {}:
            self.Rmin = ceil(
                min(self.tasks.Tasks[_]["release"] for _ in self.tasks.TaskIdx)
            )
            self.Dmax = 1 + int(max(self.tasks.Tasks[_]["due"] for _ in self.tasks.TaskIdx))
        else:
            self.Rmin = 0
            self.Dmax = 0
        self.T = range(self.Rmin, self.Dmax)
        self.Model = None
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
            Binary,
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

        self.Model = ConcreteModel()
        # Parameters
        self.Model.J = Set(initialize=self.tasks.TaskIdx)
        self.Model.S = Set(initialize=self.tasks.Resources)
        self.Model.JSPairs = Set(
            initialize=self.Model.J * self.Model.S,
            dimen=2,
            filter=lambda mdl, j, s: True,  # m in self.tasks.Tasks[j]["process"],
        )
        self.Model.ExJS = Set(
            initialize=self.Model.J * self.Model.S,
            dimen=2,
            filter=lambda mdl, j, s: not (s in self.tasks.Tasks[j]["process"]),
        )
        self.Model.IneqPairs = Set(
            initialize=self.Model.J * self.Model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 != j1,
        )
        self.Model.LeqPairs = Set(
            initialize=self.Model.J * self.Model.J,
            dimen=2,
            filter=lambda mdl, j0, j1: j0 < j1,
        )
        self.Model.SIneqPairs = Set(
            initialize=self.Model.S * self.Model.S,
            dimen=2,
            filter=lambda mdl, s0, s1: s0 != s1,
        )
        self.Model.Prerequisite = Set(
            initialize=self.Model.J * self.Model.J,
            dimen=2,
            filter=lambda mdl, i, j: (i, j) in self.tasks.Prerequisite,
        )
        self.Model.StrictStart = Set(
            initialize=self.Model.J,
            dimen=1,
            filter=lambda mdl, j: "start" in self.tasks.Tasks[j],
        )
        C = {k: self.tasks.Tasks[k[0]]["weight"] for k in self.Model.JSPairs}
        P = {
            k: self.tasks.Tasks[k[0]]["process"][k[1]]
            if k[1] in self.tasks.Tasks[k[0]]["process"]
            else 0
            for k in self.Model.JSPairs
        }
        U = self.Dmax - self.Rmin
        self.Model.c = Param(self.Model.JSPairs, initialize=C, default=1)
        self.Model.p = Param(self.Model.JSPairs, initialize=P)
        # Variables
        self.Model.x = Var(self.Model.JSPairs, domain=Binary)
        self.Model.y = Var(self.Model.IneqPairs, domain=Binary)
        self.Model.s = Var(self.Model.J, domain=NonNegativeReals, bounds=(0, self.Dmax))
        self.Model.e = Var(
            self.Model.J, domain=NonNegativeReals, bounds=(0, 2 * self.Dmax)
        )
        # Objective
        if self.cost_objective:
            self.Model.obj = Objective(
                expr=sum(
                    self.Model.c[j, s] * self.Model.x[j, s] for j, s in self.Model.JSPairs
                ),
                sense=minimize,
            )
        else:
            self.Model.obj = Objective(
                expr=sum(
                    self.Model.e[j] - self.tasks.Tasks[j]["due"] for j in self.Model.J
                ),
                sense=minimize,
            )
        # Constraints
        self.Model.Cns0 = Constraint(
            self.Model.ExJS, rule=lambda mdl, j, s: self.Model.x[j, s] == 0
        )
        self.Model.Cns1 = Constraint(
            self.Model.J,
            rule=lambda mdl, j: sum(mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 1,
        )
        self.Model.Cns2 = Constraint(
            self.Model.S,
            rule=lambda mdl, s: (
                                        0
                                        <= sum(
                                    mdl.p[j, s] * mdl.x[j, s] for j in mdl.J if (j, s) in mdl.JSPairs
                                )
                                )
                                <= self.Dmax - self.Rmin,
        )
        self.Model.Cns3 = Constraint(
            self.Model.J,
            rule=lambda mdl, j: mdl.s[j]
                                - mdl.e[j]
                                + sum(mdl.p[j, s] * mdl.x[j, s] for s in mdl.S if (j, s) in mdl.JSPairs)
                                == 0,
        )  # CBM
        self.Model.Cns4 = Constraint(
            self.Model.J, rule=lambda mdl, j: self.tasks.Tasks[j]["release"] <= mdl.s[j]
        )
        # Force find a schedule within due dates
        if self.respect_due:
            self.Model.Cns5 = Constraint(
                self.Model.J,
                rule=lambda mdl, j: (0.0 <= mdl.e[j]) <= self.tasks.Tasks[j]["due"],
            )
        # Prerequisite
        self.Model.Cns6 = Constraint(
            self.Model.IneqPairs,
            rule=lambda mdl, i, j: mdl.e[i] - mdl.s[j] + U * mdl.y[i, j] <= U,
        )
        self.Model.Cns7 = Constraint(
            self.Model.LeqPairs, rule=lambda mdl, i, j: mdl.y[i, j] + mdl.y[j, i] <= 1
        )
        self.Model.Cns8 = Constraint(
            self.Model.LeqPairs * self.Model.S,
            rule=lambda mdl, i, j, s: mdl.x[i, s]
                                      + mdl.x[j, s]
                                      - mdl.y[i, j]
                                      - mdl.y[j, i]
                                      <= 1,
        )
        self.Model.Cns9 = Constraint(
            self.Model.LeqPairs * self.Model.SIneqPairs,
            rule=lambda mdl, i, j, l, s: mdl.x[i, l]
                                         + mdl.x[j, s]
                                         + mdl.y[i, j]
                                         + mdl.y[j, i]
                                         <= 2,
        )
        self.Model.Cns10 = Constraint(
            self.Model.Prerequisite, rule=lambda mdl, i, j: mdl.y[i, j] == 1
        )
        self.Model.Cns11 = Constraint(
            self.Model.StrictStart,
            rule=lambda mdl, j: mdl.s[j] == self.tasks.Tasks[j]["start"],
        )
        if self.executable is None:
            results = SolverFactory(solver).solve(self.Model)
        else:
            results = SolverFactory(solver, executable=self.executable).solve(self.Model)

        if results.solver.status == SolverStatus.ok:
            for j in self.Model.J:
                self.timetable[j] = {
                    "start": self.Model.s[j](),
                    "finish": self.Model.e[j](),
                    "resources": [s for s in self.Model.S if self.Model.x[j, s]()][0],
                }
            self.timetable["Message"] = "Success"
        else:
            self.timetable["Message"] = "No feasible schedule was found."
        return self.timetable
