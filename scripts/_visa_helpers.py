import argparse
import json
import time
from pathlib import Path

import pyvisa


def build_common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("resource", help="VISA resource string, e.g. USB0::...::INSTR")
    parser.add_argument("--timeout", type=int, default=5000, help="VISA timeout in milliseconds")
    parser.add_argument("--read-term", default="\n", help="Read termination, default newline")
    parser.add_argument("--write-term", default="\n", help="Write termination, default newline")
    parser.add_argument("--query-delay", type=float, default=0.05, help="Delay between write/read for query")
    return parser


def open_instrument(resource: str, timeout: int, read_term: str, write_term: str, query_delay: float):
    rm = pyvisa.ResourceManager()
    instrument = rm.open_resource(resource)
    instrument.timeout = timeout
    instrument.read_termination = read_term
    instrument.write_termination = write_term
    instrument.query_delay = query_delay
    return rm, instrument


def safe_query(instrument, command: str):
    try:
        response = instrument.query(command)
        return {"ok": True, "command": command, "response": response.strip()}
    except Exception as exc:  # manual probe script
        return {"ok": False, "command": command, "error": str(exc)}


def safe_write(instrument, command: str):
    try:
        instrument.write(command)
        return {"ok": True, "command": command}
    except Exception as exc:  # manual probe script
        return {"ok": False, "command": command, "error": str(exc)}


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ensure_parent(path: str):
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
