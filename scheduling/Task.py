"""
============================
Tasks Module
============================
"""

from collections.abc import Mapping
from math import isfinite
from numbers import Real


class Tasks(object):
    """
    Initiates an object to add tasks to a tentative task list.

    The following attributes are associated to a task:
        + Task name: a string place holder for the task
        + Release date: the earliest time that a task can be processed
        + Due date: a date-time that the task should be completed by then
        + Process time: the length of time that a resources requires to finish a given task
        + Start time: a specific date-time for the start of a task
        + Unavailable: a period where a resources is not available (takes time off, etc.)
        + Prerequisite: when task A should be finished before task B

    A `Tasks` instance handles the association of the above attributes in a task list through 3 methods.
    """

    def __init__(self):
        self.TaskNum = 0
        self.Tasks = {}
        self.Resources = []
        self.TaskKeys = []
        self.TaskIdx = []
        self.Prerequisite = []

    def add_task(
            self, task_name=None, release=0, due=1, weight=1, process=None, start=None
    ):
        """
        Adds a task to the list to be scheduled

        :param task_name: *optional*, a given name for the task
        :param release: Release date; the earliest time that a task can be processed
        :param due: Due date; a date-time that the task should be completed by then
        :param weight: *optional*, contribution coefficient to the cost/profit
        :param process: a dictionary of the task's processing time for each resources, capable of handling the task
        :param start: *optional*, a specific date-time for the start of a task
        :return: `None`
        """
        if task_name is None:
            task_key = str(self.TaskNum)
        else:
            task_key = str(task_name)
        jm_process = {"M1": 1} if process is None else process
        if not isinstance(jm_process, Mapping) or not jm_process:
            raise ValueError("process must be a non-empty mapping of resources to durations")
        jm_process = dict(jm_process)
        if any(not isinstance(resource, str) or not resource for resource in jm_process):
            raise ValueError("resource names must be non-empty strings")
        if any(
            not isinstance(duration, Real) or not isfinite(duration) or duration < 0
            for duration in jm_process.values()
        ):
            raise ValueError("processing durations must be finite, non-negative numbers")
        if task_key in self.TaskKeys:
            raise ValueError("task name {!r} already exists".format(task_key))
        task_resources = set(jm_process.keys())
        self.Resources = list(set(self.Resources).union(task_resources))
        self.Tasks[self.TaskNum] = {
            "release": release,
            "due": due,
            "process": jm_process,
            "weight": weight,
            "id": self.TaskNum,
        }
        if start is not None:
            self.Tasks[self.TaskNum]["start"] = start
        self.TaskIdx.append(self.TaskNum)
        self.TaskKeys.append(task_key)
        self.TaskNum += 1

    def schedule_unavailable(self, resource, process, release=0, start=None, due=None):
        """
        Schedules an unavailable time for a resources

        :param resource: the name of the resources
        :param process: the length of time off
        :param release: the earliest time to be unavailable
        :param start: a sharp date-time to take time off
        :param due: the time resources returns (becomes available)
        :return: `None`
        """
        task_key = "Unavailable"
        jm_process = {resource: process}
        self.Resources = list(set(self.Resources).union({resource}))
        weight = 0
        if start is not None:
            due = start + process
        elif due is None:
            due = max(self.Tasks[_]["due"] for _ in self.Tasks)
        self.Tasks[self.TaskNum] = {
            "release": release,
            "due": due,
            "process": jm_process,
            "weight": weight,
            "id": self.TaskNum,
        }
        if start is not None:
            self.Tasks[self.TaskNum]["start"] = start
        self.TaskKeys.append(task_key)
        self.TaskIdx.append(self.TaskNum)
        self.TaskNum += 1

    def add_prerequisite(self, task1, task2):
        """
        Sets prerequisite for tasks

        :param task1: the task to be followed by `task2`
        :param task2: the followup task
        :return: None
        """
        self.Prerequisite.append(
            (self.TaskKeys.index(task1), self.TaskKeys.index(task2))
        )
