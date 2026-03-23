#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Basic query validation for Keysight/Agilent 33500B via PyVISA."""

from scripts._visa_helpers import build_common_parser, open_instrument, print_json, safe_query, safe_write, timestamp


COMMAND_GROUPS = {
    "identity": ["*IDN?", "SYST:VERS?", "*TST?", "SYST:ERR?"],
    "query_candidates": [
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
        "OUTP1?",
        "OUTP?",
    ],
}


def main():
    parser = build_common_parser("Basic SCPI query probe for 33500B")
    args = parser.parse_args()

    rm, instrument = open_instrument(args.resource, args.timeout, args.read_term, args.write_term, args.query_delay)
    report = {
        "timestamp": timestamp(),
        "resource": args.resource,
        "writes": [],
        "queries": {},
    }

    try:
        report["writes"].append(safe_write(instrument, "*CLS"))
        for group_name, commands in COMMAND_GROUPS.items():
            report["queries"][group_name] = [safe_query(instrument, command) for command in commands]
    finally:
        instrument.close()
        rm.close()

    print_json(report)


if __name__ == "__main__":
    main()
