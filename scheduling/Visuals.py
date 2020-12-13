class Visuals(object):
    """
    A class to visualize an schedule. An instance of `Visuals` accepts one argument:
    :param schedule: An instance of `Schedule`.
    """
    def __init__(self, schedule):
        # if not isinstance(schedule, Schedule):
        #     raise TypeError("'schedule' must be an instance of 'Schedule'")
        self.schedule = schedule

    def gantt(self):
        """
        Plots a gantt chart of the given schedule
        :return: the `matplotlib` plot object
        """
        import matplotlib.gridspec as gridspec
        import matplotlib.pyplot as plt

        if (self.schedule.timetable == {}) or (
            self.schedule.timetable["Message"] != "Success"
        ):
            # raise ValueError("No schedule found for visualization")
            print("No schedule found for visualization")
        jobs = self.schedule.tasks.Tasks
        graph = gridspec.GridSpec(4, 1)
        bw = 0.3
        try:
            resources = sorted(
                set([self.schedule.timetable[j]["resources"] for j in jobs.keys()])
            )
        except KeyError:
            resources = []
        plt.figure(
            figsize=(
                12,
                0.7 * (len(set(self.schedule.tasks.TaskKeys)) + len(resources)),
            )
        )
        axes_1 = plt.subplot(graph[:3, :])
        idx = 0
        for j in sorted(jobs.keys()):
            # if self.schedule.tasks.TaskKeys[j] == "Unavailable":
            #    continue
            x = jobs[j]["release"]
            y = jobs[j]["due"]
            axes_1.fill_between(
                [x, y],
                [idx - bw, idx - bw],
                [idx + bw, idx + bw],
                color="cyan",
                alpha=0.6,
            )
            try:
                x = self.schedule.timetable[j]["start"]
                y = self.schedule.timetable[j]["finish"]
            except KeyError:
                self.schedule.timetable[j] = dict()
                self.schedule.timetable[j]["start"] = jobs[j]["release"]
                y = self.schedule.timetable[j]["finish"] = jobs[j]["release"]
                x = jobs[j]["release"]
                y = x
            if self.schedule.tasks.TaskKeys[j] == "Unavailable":
                task_name = "NA"
                clr = "grey"
            else:
                # task_name = "Task " + str(self.tasks.TaskKeys[j])
                task_name = str(self.schedule.tasks.TaskKeys[j])
                clr = "red"
            axes_1.fill_between(
                [x, y], [idx - bw, idx - bw], [idx + bw, idx + bw], color=clr, alpha=0.5
            )
            axes_1.plot(
                [x, y, y, x, x],
                [idx - bw, idx - bw, idx + bw, idx + bw, idx - bw],
                color="k",
            )
            axes_1.text(
                (
                    self.schedule.timetable[j]["start"]
                    + self.schedule.timetable[j]["finish"]
                )
                / 2.0,
                idx,
                task_name,
                color="yellow",
                weight="bold",
                horizontalalignment="center",
                verticalalignment="center",
            )
            idx += 1

        # axes_1.set_ylim(-0.5, idx - 0.5)
        axes_1.set_ylim(-0.5, len(set(self.schedule.tasks.TaskKeys)) - 0.5)
        axes_1.set_title("Task Schedule")
        axes_1.set_xlabel("Time")
        axes_1.set_ylabel("Tasks")
        axes_1.set_yticks(
            range(len(list(self.schedule.tasks.TaskKeys)) + 1),
            #set(self.schedule.tasks.TaskKeys),
        )
        axes_1.grid()
        xlim = axes_1.get_xlim()

        for j in jobs.keys():
            if "resources" not in self.schedule.timetable[j].keys():
                self.schedule.timetable[j]["resources"] = 1
        Equipments = sorted(
            set([self.schedule.timetable[j]["resources"] for j in jobs.keys()])
        )

        axes_2 = plt.subplot(graph[3, :])
        for j in sorted(jobs.keys()):
            #if self.schedule.tasks.TaskKeys[j] == "Unavailable":
            #    continue
            idx = Equipments.index(self.schedule.timetable[j]["resources"])
            x = self.schedule.timetable[j]["start"]
            y = self.schedule.timetable[j]["finish"]
            if self.schedule.tasks.TaskKeys[j] == "Unavailable":
                task_name = "NA"
                clr = "grey"
            else:
                # task_name = "Task " + str(self.tasks.TaskKeys[j])
                task_name = str(self.schedule.tasks.TaskKeys[j])
                clr = "red"
            axes_2.fill_between(
                [x, y], [idx - bw, idx - bw], [idx + bw, idx + bw], color=clr, alpha=0.5
            )
            axes_2.plot(
                [x, y, y, x, x],
                [idx - bw, idx - bw, idx + bw, idx + bw, idx - bw],
                color="k",
            )
            axes_2.text(
                (
                    self.schedule.timetable[j]["start"]
                    + self.schedule.timetable[j]["finish"]
                )
                / 2.0,
                idx,
                task_name,
                color="yellow",
                weight="bold",
                horizontalalignment="center",
                verticalalignment="center",
            )
        axes_2.set_xlim(xlim)
        axes_2.set_ylim(-0.5, len(Equipments) - 0.5)
        axes_2.set_title("Resource Schedule")
        axes_2.set_yticks(range(len(Equipments)))#, Equipments)
        axes_2.set_ylabel("resources")
        axes_2.grid()

        plt.tight_layout()
        return plt