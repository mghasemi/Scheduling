"""Public API for the scheduling toolkit.

Optional features are loaded on first access so using the core task and
heuristic-scheduling APIs does not require the data-science or plotting extras.
"""

from importlib import import_module

__all__ = [
    "MultiMachineMILP",
    "MultiMachineQP",
    "FCFSP",
    "Preemptive",
    "Tasks",
    "Visuals",
    "Evaluate",
    "GenerateSchedule",
    "Stochastic",
]

_EXPORTS = {
    "MultiMachineMILP": ".MultiMachine",
    "MultiMachineQP": ".MultiMachine",
    "FCFSP": ".MultiMachine",
    "Preemptive": ".MultiMachine",
    "Tasks": ".Task",
    "Visuals": ".Visuals",
    "Evaluate": ".Stochastic",
    "GenerateSchedule": ".Stochastic",
    "Stochastic": ".Stochastic",
}

_DEPRECATED_EXPORTS = {
    "Perimeter",
    "Primary911",
    "find_asas",
    "utilizations",
    "conf_int",
}


def __getattr__(name):
    """Load a public API symbol only when it is requested."""
    if name in _DEPRECATED_EXPORTS:
        import warnings

        warnings.warn(
            "Import PCB helpers from scheduling.use_cases.pcb instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        value = getattr(import_module(".use_cases.pcb", __name__), name)
        globals()[name] = value
        return value
    try:
        module_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name)) from None
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
