#!/usr/bin/env python3
"""Enforce line and branch thresholds independently; coverage's combined % cannot."""
import json
import sys


def main():
    with open(sys.argv[1], encoding="utf-8") as report:
        totals = json.load(report)["totals"]
    lines = 100 * totals["covered_lines"] / totals["num_statements"]
    branches = 100 * totals["covered_branches"] / totals["num_branches"]
    print(f"Coverage: lines {lines:.2f}%, branches {branches:.2f}% (each must be >=95%)")
    return int(lines < 95 or branches < 95)


if __name__ == "__main__":
    sys.exit(main())
