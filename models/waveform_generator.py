import pyvisa
from tkinter import messagebox

class WaveformGenerator:
    def __init__(self, resource_address):
        self.rm = pyvisa.ResourceManager()
        self.device = None
        self.address = resource_address

    def connect(self):
        try:
            self.device = self.rm.open_resource(self.address)
            self.device.write('*IDN?')
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            return False

    def disconnect(self):
        if self.device:
            self.device.close()

    def set_waveform(self, waveform):
        self.device.write(f"FUNC {waveform}")

    def set_parameters(self, frequency, amplitude, offset, phase):
        self.device.write(f"FREQ {frequency}")
        self.device.write(f"VOLT {amplitude}")
        self.device.write(f"VOLT:OFFSET {offset}")
        self.device.write(f"PHAS {phase}")

    def toggle_channel(self, channel, state):
        self.device.write(f"OUTP{channel} {'ON' if state else 'OFF'}")

    def enable_output(self):
        self.device.write("OUTP ON")

    def disable_output(self):
        self.device.write("OUTP OFF")
