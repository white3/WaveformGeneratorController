#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Probe multiple candidate query commands and save a JSON report for later analysis."""

import argparse
import json

from scripts._visa_helpers import ensure_parent, open_instrument, safe_query, timestamp


CANDIDATE_QUERIES = [
    "*IDN?",
    "SYST:VERS?",
    "SYST:ERR?",
    "*TST?",
    "FUNC?",
    "SOUR1:FUNC?",
    "FREQ?",
    "SOUR1:FREQ?",
    "VOLT?",
    "SOUR1:VOLT?",
    "VOLT:OFFSET?",
    "SOUR1:VOLT:OFFSET?",
    "PHAS?",
    "SOUR1:PHAS?",
    "OUTP?",
    "OUTP1?",
    "BURS:STAT?",
    "SOUR1:BURS:STAT?",
    "TRIG:SOUR?",
    "SOUR1:FUNC:ARB?",
    "MMEM:CAT?",
]



def main():
    parser = argparse.ArgumentParser(description="Probe 33500B candidate queries and save JSON")
    parser.add_argument("resource", help="VISA resource string")
    parser.add_argument("--output", default="artifacts/33500b_query_matrix.json", help="JSON output path")
    parser.add_argument("--timeout", type=int, default=5000)
    parser.add_argument("--read-term", default="\n")
    parser.add_argument("--write-term", default="\n")
    parser.add_argument("--query-delay", type=float, default=0.05)
    args = parser.parse_args()

    ensure_parent(args.output)
    rm, instrument = open_instrument(args.resource, args.timeout, args.read_term, args.write_term, args.query_delay)
    report = {
        "timestamp": timestamp(),
        "resource": args.resource,
        "results": [safe_query(instrument, command) for command in CANDIDATE_QUERIES],
    }

    try:
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    finally:
        instrument.close()
        rm.close()

    print(f"Saved query matrix report to {args.output}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
