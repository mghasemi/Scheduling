import random

from scheduling.Stochastic import GenerateSchedule, Stochastic


def make_generator():
    return GenerateSchedule(
        num_res=2,
        priorities=[1],
        n_calls={1: lambda: 3},
        durations={1: lambda: 4},
        release={1: lambda: random.randint(0, 20)},
    )


def test_stochastic_run_is_reproducible_with_random_state():
    def run():
        return Stochastic(
            model="fcfsp",
            schdl=make_generator(),
            n_iter=4,
            n_jobs=1,
            random_state=29,
        )()

    assert run() == run()
