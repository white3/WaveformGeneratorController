#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Speculative waveform readback probe for 33500B.

This script intentionally tries several common SCPI patterns used by AWGs/oscilloscopes
because the currently reviewed official 33500 Series user guide clearly documents waveform
upload and selection, but does not clearly document a sample-by-sample output readback
command. Run this on real hardware and return the JSON results.
"""

import argparse
import json

from scripts._visa_helpers import open_instrument, timestamp


CANDIDATES = [
    "SOUR1:FUNC?",
    "SOUR1:FUNC:ARB?",
    "SOUR1:DATA:ARB?",
    "DATA:ARB?",
    "DATA:VOL:CAT?",
    "MMEM:CAT?",
    "MMEM:CAT:DATA?",
    "TRAC:DATA?",
    "TRACE:DATA?",
    "WLIST:WAVEFORM:DATA?",
]



def probe_raw(inst, command: str):
    try:
        inst.write(command)
        raw = inst.read_raw()
        try:
            decoded = raw.decode("utf-8", errors="replace").strip()
        except Exception:
            decoded = None
        return {
            "command": command,
            "ok": True,
            "raw_length": len(raw),
            "decoded_preview": decoded[:200] if decoded else None,
            "raw_prefix_hex": raw[:32].hex(),
        }
    except Exception as exc:
        return {"command": command, "ok": False, "error": str(exc)}



def main():
    parser = argparse.ArgumentParser(description="Probe speculative waveform readback commands on 33500B")
    parser.add_argument("resource", help="VISA resource string")
    parser.add_argument("--timeout", type=int, default=2000)
    parser.add_argument("--read-term", default="\n")
    parser.add_argument("--write-term", default="\n")
    parser.add_argument("--query-delay", type=float, default=0.05)
    args = parser.parse_args()

    rm, inst = open_instrument(args.resource, args.timeout, args.read_term, args.write_term, args.query_delay)
    report = {"timestamp": timestamp(), "resource": args.resource, "results": []}
    try:
        for command in CANDIDATES:
            report["results"].append(probe_raw(inst, command))
    finally:
        inst.close()
        rm.close()

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
