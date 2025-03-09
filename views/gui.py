import tkinter as tk
from tkinter import messagebox
from controllers.controller import Controller

class AppGUI(tk.Tk):
    def __init__(self, resources):
        super().__init__()
        self.title("Keysight 33500B Controller")
        self.controller = Controller(resources[0] if resources else None)

        self.selected_address = tk.StringVar(value=resources[0] if resources else "No Device")
        self.waveform_var = tk.StringVar(value="SIN")

        self.freq_entry = tk.Entry(self)
        self.amp_entry = tk.Entry(self)
        self.offset_entry = tk.Entry(self)
        self.phase_entry = tk.Entry(self)

        self.channel_var = {1: tk.IntVar(value=1), 2: tk.IntVar(value=0)}

        self.create_widgets(resources)

    def create_widgets(self, resources):
        tk.Label(self, text="Device:").grid(row=0, column=0)
        tk.OptionMenu(self, self.selected_address, *resources).grid(row=0, column=1)
        tk.Button(self, text="Connect", command=self.controller.connect_device).grid(row=0, column=2)

        tk.Label(self, text="Waveform:").grid(row=1, column=0)
        tk.OptionMenu(self, self.waveform_var, "SIN", "SQU", "TRI", "RAMP",
                      command=self.controller.update_waveform).grid(row=1, column=1)

        tk.Label(self, text="Frequency (Hz):").grid(row=2, column=0)
        self.freq_entry.grid(row=2, column=1)

        tk.Label(self, text="Amplitude (V):").grid(row=3, column=0)
        self.amp_entry.grid(row=3, column=1)

        tk.Label(self, text="Offset (V):").grid(row=4, column=0)
        self.offset_entry.grid(row=4, column=1)

        tk.Label(self, text="Phase (°):").grid(row=5, column=0)
        self.phase_entry.grid(row=5, column=1)

        tk.Button(self, text="Update Parameters",
                  command=lambda: self.controller.update_parameters(
                      float(self.freq_entry.get()),
                      float(self.amp_entry.get()),
                      float(self.offset_entry.get()),
                      float(self.phase_entry.get())
                  )).grid(row=6, columnspan=2)

        for ch in [1, 2]:
            tk.Checkbutton(self, text=f"Channel {ch}",
                           variable=self.channel_var[ch],
                           command=lambda c=ch: self.controller.toggle_channel(c, self.channel_var[c].get())
                           ).grid(row=7, column=ch-1)

        tk.Button(self, text="Enable Output", command=self.controller.enable_output).grid(row=8, column=0)
        tk.Button(self, text="Disable Output", command=self.controller.disable_output).grid(row=8, column=1)

        tk.Button(self, text="Run Test Sequence", command=self.controller.run_test_sequence).grid(row=9, column=0)
        tk.Button(self, text="Pause/Resume", command=self.controller.pause_resume_test).grid(row=9, column=1)
        tk.Button(self, text="Stop Test", command=self.controller.stop_test).grid(row=10, column=0)

        tk.Button(self, text="Create Test File", command=self.controller.create_test_file).grid(row=10, column=1)
