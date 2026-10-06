"""Run a small PCB workload use case against a user-supplied Perimeter export."""

import argparse
from pathlib import Path

from scheduling.use_cases.pcb import Perimeter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "perimeter_export",
        type=Path,
        help="path to a compatible CSV or Excel Perimeter export",
    )
    parser.add_argument(
        "--slot",
        type=int,
        default=18,
        help="30-minute slot index to sample (0-47; default: 18)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("./data/sim_calls.csv"),
        help="path for generated synthetic calls (default: ./data/sim_calls.csv)",
    )
    args = parser.parse_args()
    if not 0 <= args.slot < 48:
        parser.error("--slot must be between 0 and 47")

    analysis = Perimeter(fname=args.perimeter_export, cache_path=args.cache)
    asa, utilization, _ = analysis.evaluation_schedule(
        args.slot,
        model="fcfsp",
        priority=True,
    )
    print("Average speed of answer by priority:", asa)
    print("Busy time by resource:", utilization)


if __name__ == "__main__":
    main()
