import threading
from typing import Optional

try:
    import pyvisa
except ImportError:  # pragma: no cover - optional during tests
    pyvisa = None


class WaveformGenerator:
    def __init__(self, resource_address: Optional[str], resource_manager=None):
        self.rm = resource_manager or (pyvisa.ResourceManager() if pyvisa else None)
        self.device = None
        self.address = resource_address
        self._lock = threading.RLock()

    def connect(self):
        if not self.address:
            raise ValueError("No device resource address selected.")
        if self.rm is None:
            raise RuntimeError("pyvisa is required to connect to the waveform generator.")
        with self._lock:
            self.device = self.rm.open_resource(self.address)
            if hasattr(self.device, "query"):
                self.device.query("*IDN?")
            else:
                self.device.write("*IDN?")
            return True

    def disconnect(self):
        with self._lock:
            if self.device:
                self.device.close()
                self.device = None

    def _write(self, command: str):
        if self.device is None:
            raise RuntimeError("Device is not connected.")
        with self._lock:
            self.device.write(command)

    def set_waveform(self, waveform):
        self._write(f"FUNC {waveform}")

    def set_parameters(self, frequency, amplitude, offset, phase):
        self._write(f"FREQ {frequency}")
        self._write(f"VOLT {amplitude}")
        self._write(f"VOLT:OFFSET {offset}")
        self._write(f"PHAS {phase}")

    def toggle_channel(self, channel, state):
        self._write(f"OUTP{channel} {'ON' if state else 'OFF'}")

    def enable_output(self):
        self._write("OUTP ON")

    def disable_output(self):
        self._write("OUTP OFF")
