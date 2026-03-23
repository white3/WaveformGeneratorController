#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Poll current generator state into CSV for later plotting or Web design evaluation."""

import argparse
import csv
import time

from scripts._visa_helpers import ensure_parent, open_instrument, safe_query, timestamp


POLL_COMMANDS = [
    "FUNC?",
    "FREQ?",
    "VOLT?",
    "VOLT:OFFSET?",
    "PHAS?",
    "OUTP1?",
    "SYST:ERR?",
]


def main():
    parser = argparse.ArgumentParser(description="Poll 33500B state and save CSV")
    parser.add_argument("resource", help="VISA resource string")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds")
    parser.add_argument("--count", type=int, default=40, help="Number of samples to capture")
    parser.add_argument("--output", default="artifacts/33500b_state_poll.csv", help="CSV output path")
    parser.add_argument("--timeout", type=int, default=5000)
    parser.add_argument("--read-term", default="\n")
    parser.add_argument("--write-term", default="\n")
    parser.add_argument("--query-delay", type=float, default=0.05)
    args = parser.parse_args()

    ensure_parent(args.output)
    rm, instrument = open_instrument(args.resource, args.timeout, args.read_term, args.write_term, args.query_delay)

    try:
        with open(args.output, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "command", "ok", "value_or_error"])
            for _ in range(args.count):
                current_time = timestamp()
                for command in POLL_COMMANDS:
                    result = safe_query(instrument, command)
                    writer.writerow([
                        current_time,
                        command,
                        result["ok"],
                        result.get("response", result.get("error", "")),
                    ])
                handle.flush()
                time.sleep(args.interval)
    finally:
        instrument.close()
        rm.close()

    print(f"Saved poll data to {args.output}")


if __name__ == "__main__":
    main()
