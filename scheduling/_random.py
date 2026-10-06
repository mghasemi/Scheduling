"""Helpers for isolating reproducible draws from legacy global RNG APIs."""

from contextlib import contextmanager
import random


@contextmanager
def seeded_random(seed):
    """Temporarily seed Python and NumPy's legacy global random generators."""
    if seed is None:
        yield
        return

    import numpy as np

    python_state = random.getstate()
    numpy_state = np.random.get_state()
    random.seed(int(seed))
    np.random.seed(int(seed))
    try:
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
