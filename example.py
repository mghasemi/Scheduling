from scheduling.MultiMachine import MultiMachineMILP
from scheduling.Task import Tasks
from scheduling.Visuals import Visuals

J = Tasks()
J.add_task(task_name='A', release=2, due=10, process={'R1': 5, 'R2': 5})
J.add_task(task_name='B', release=5, due=21, process={'R1': 6, 'R2': 5})
J.add_task(task_name='C', release=4, due=22, process={'R1': 9, 'R2': 8})
J.add_task(task_name='D', release=0, due=10, process={'R1': 4, 'R2': 4})
J.add_task(task_name='E', release=0, due=5, process={'R1': 2, 'R2': 2})
J.add_task(task_name='F', release=8, due=15, process={'R1': 3, 'R2': 5})
J.add_task(task_name='G', release=9, due=22, process={'R1': 4, 'R2': 4})
J.add_task(task_name='H', release=9, due=20, process={'R1': 1, 'R2': 1})
J.add_task(task_name='I', release=9, due=20, process={'R1': 1, 'R2': 1})

J.add_prerequisite('G', 'I')
J.add_prerequisite('H', 'B')
J.add_prerequisite('I', 'B')
J.schedule_unavailable(resource='R1', process=1, release=10, start=11, due=None)
J.schedule_unavailable(resource='R2', process=2, release=5, start=None, due=26)

A = MultiMachineMILP(J, **{'solver': 'cplex', # 'cbc',#'cplex',
                           'respect_due': True,
                           'executable': "/opt/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux/cplex"
                           })
print(A())
print(A.tasks.__dict__)
V = Visuals(A)
V.gantt().show()
