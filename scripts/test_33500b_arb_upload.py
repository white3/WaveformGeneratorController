#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Upload a simple arbitrary waveform and probe whether the instrument accepts/selects it."""

import argparse
import math

from scripts._visa_helpers import open_instrument, print_json, safe_query, safe_write, timestamp



def build_waveform(points: int = 64):
    values = []
    for index in range(points):
        angle = 2 * math.pi * index / points
        values.append(f"{math.sin(angle):.6f}")
    return ",".join(values)



def main():
    parser = argparse.ArgumentParser(description="Upload simple ARB waveform to 33500B")
    parser.add_argument("resource", help="VISA resource string")
    parser.add_argument("--name", default="CodexSine", help="ARB name to store in volatile memory")
    parser.add_argument("--points", type=int, default=64, help="Number of points in generated sine waveform")
    parser.add_argument("--timeout", type=int, default=10000)
    parser.add_argument("--read-term", default="\n")
    parser.add_argument("--write-term", default="\n")
    parser.add_argument("--query-delay", type=float, default=0.1)
    args = parser.parse_args()

    rm, instrument = open_instrument(args.resource, args.timeout, args.read_term, args.write_term, args.query_delay)
    waveform = build_waveform(args.points)
    report = {
        "timestamp": timestamp(),
        "resource": args.resource,
        "arb_name": args.name,
        "points": args.points,
        "steps": [],
    }

    try:
        report["steps"].append(safe_write(instrument, "*CLS"))
        report["steps"].append(safe_write(instrument, "DATA:VOL:CLE"))
        report["steps"].append(safe_write(instrument, f"SOUR1:DATA:ARB {args.name},{waveform}"))
        report["steps"].append(safe_write(instrument, f"SOUR1:FUNC:ARB {args.name}"))
        report["steps"].append(safe_write(instrument, "SOUR1:FUNC ARB"))
        report["steps"].append(safe_write(instrument, "SOUR1:VOLT 1.0"))
        report["steps"].append(safe_query(instrument, "FUNC?"))
        report["steps"].append(safe_query(instrument, "SOUR1:FUNC?"))
        report["steps"].append(safe_query(instrument, "SYST:ERR?"))
    finally:
        instrument.close()
        rm.close()

    print_json(report)


if __name__ == "__main__":
    main()
