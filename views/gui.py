import tkinter as tk
from tkinter import messagebox


class AppGUI(tk.Tk):
    def __init__(self, controller, web_address=None):
        super().__init__()
        self.title("Keysight 33500B Controller")
        self.controller = controller
        self.web_address = web_address

        resources = self.controller.list_resources()
        self.selected_address = tk.StringVar(value=self.controller.current_address or "No Device")
        self.waveform_var = tk.StringVar(value=self.controller.state["waveform"])
        self.password_var = tk.StringVar()
        self.profile_name_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self.freq_entry = tk.Entry(self)
        self.amp_entry = tk.Entry(self)
        self.offset_entry = tk.Entry(self)
        self.phase_entry = tk.Entry(self)

        self.channel_var = {1: tk.IntVar(value=1), 2: tk.IntVar(value=0)}
        self.profile_list = tk.Listbox(self, height=6)

        self.create_widgets(resources)
        self.populate_entries_from_state()
        self.refresh_profiles()

    def create_widgets(self, resources):
        row = 0
        if self.web_address:
            tk.Label(self, text=f"Web Console: http://{self.web_address[0]}:{self.web_address[1]}").grid(row=row, column=0, columnspan=3, sticky="w")
            row += 1

        tk.Label(self, text="Control Password:").grid(row=row, column=0, sticky="w")
        tk.Entry(self, textvariable=self.password_var, show="*").grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Label(self, text="Device:").grid(row=row, column=0, sticky="w")
        tk.OptionMenu(self, self.selected_address, *(resources or ["No Device"])).grid(row=row, column=1, sticky="ew")
        tk.Button(self, text="Connect", command=self.connect_device).grid(row=row, column=2, sticky="ew")
        row += 1

        tk.Label(self, text="Waveform:").grid(row=row, column=0, sticky="w")
        tk.OptionMenu(self, self.waveform_var, "SIN", "SQU", "TRI", "RAMP").grid(row=row, column=1, sticky="ew")
        tk.Button(self, text="Apply Waveform", command=self.apply_waveform).grid(row=row, column=2, sticky="ew")
        row += 1

        tk.Label(self, text="Frequency (Hz):").grid(row=row, column=0, sticky="w")
        self.freq_entry.grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Label(self, text="Amplitude (V):").grid(row=row, column=0, sticky="w")
        self.amp_entry.grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Label(self, text="Offset (V):").grid(row=row, column=0, sticky="w")
        self.offset_entry.grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Label(self, text="Phase (°):").grid(row=row, column=0, sticky="w")
        self.phase_entry.grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Button(self, text="Update Parameters", command=self.apply_parameters).grid(row=row, column=0, columnspan=3, sticky="ew")
        row += 1

        for ch in [1, 2]:
            tk.Checkbutton(
                self,
                text=f"Channel {ch}",
                variable=self.channel_var[ch],
                command=lambda c=ch: self.apply_channel_toggle(c),
            ).grid(row=row, column=ch - 1, sticky="w")
        row += 1

        tk.Button(self, text="Enable Output", command=lambda: self.set_output(True)).grid(row=row, column=0, sticky="ew")
        tk.Button(self, text="Disable Output", command=lambda: self.set_output(False)).grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Button(self, text="Run Test Sequence", command=self.run_test).grid(row=row, column=0, sticky="ew")
        tk.Button(self, text="Pause/Resume", command=self.pause_resume_test).grid(row=row, column=1, sticky="ew")
        tk.Button(self, text="Stop Test", command=self.controller.stop_test).grid(row=row, column=2, sticky="ew")
        row += 1

        tk.Button(self, text="Create Test File", command=self.controller.create_test_file).grid(row=row, column=0, sticky="ew")
        row += 1

        tk.Label(self, text="SQLite Cached Profiles:").grid(row=row, column=0, sticky="w")
        row += 1
        self.profile_list.grid(row=row, column=0, columnspan=3, sticky="nsew")
        row += 1
        tk.Entry(self, textvariable=self.profile_name_var).grid(row=row, column=0, columnspan=2, sticky="ew")
        tk.Button(self, text="Save Profile", command=self.save_profile).grid(row=row, column=2, sticky="ew")
        row += 1
        tk.Button(self, text="Load Profile", command=self.load_profile).grid(row=row, column=0, sticky="ew")
        tk.Button(self, text="Refresh Profiles", command=self.refresh_profiles).grid(row=row, column=1, sticky="ew")
        row += 1

        tk.Label(self, textvariable=self.status_var, fg="blue").grid(row=row, column=0, columnspan=3, sticky="w")

        for column in range(3):
            self.grid_columnconfigure(column, weight=1)
        self.grid_rowconfigure(row - 2, weight=1)

    def password(self):
        return self.password_var.get()

    def safe_call(self, func, success_message=None):
        try:
            result = func()
            if success_message:
                self.status_var.set(success_message)
            return result
        except Exception as exc:
            messagebox.showerror("Operation Error", str(exc))
            self.status_var.set(str(exc))
            return None

    def connect_device(self):
        self.safe_call(
            lambda: self.controller.connect_device(
                password=self.password(),
                resource_address=self.selected_address.get(),
            ),
            success_message="Device connected.",
        )

    def apply_waveform(self):
        self.safe_call(
            lambda: self.controller.update_waveform(self.waveform_var.get(), password=self.password()),
            success_message="Waveform updated.",
        )

    def apply_parameters(self):
        self.safe_call(
            lambda: self.controller.update_parameters(
                float(self.freq_entry.get()),
                float(self.amp_entry.get()),
                float(self.offset_entry.get()),
                float(self.phase_entry.get()),
                password=self.password(),
            ),
            success_message="Parameters updated.",
        )

    def apply_channel_toggle(self, channel):
        self.safe_call(
            lambda: self.controller.toggle_channel(channel, bool(self.channel_var[channel].get()), password=self.password()),
            success_message=f"Channel {channel} updated.",
        )

    def set_output(self, enabled):
        func = self.controller.enable_output if enabled else self.controller.disable_output
        self.safe_call(lambda: func(password=self.password()), success_message="Output updated.")

    def run_test(self):
        self.safe_call(lambda: self.controller.run_test_sequence(password=self.password()), success_message="Test sequence started.")

    def pause_resume_test(self):
        paused = self.controller.pause_resume_test()
        self.status_var.set("Test paused." if paused else "Test resumed.")

    def populate_entries_from_state(self):
        state = self.controller.get_status()["state"]
        self.waveform_var.set(state["waveform"])
        entries = [
            (self.freq_entry, state["frequency"]),
            (self.amp_entry, state["amplitude"]),
            (self.offset_entry, state["offset"]),
            (self.phase_entry, state["phase"]),
        ]
        for entry, value in entries:
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
        for channel, enabled in state["channels"].items():
            self.channel_var[channel].set(1 if enabled else 0)

    def refresh_profiles(self):
        self.profile_list.delete(0, tk.END)
        for profile in self.controller.list_profiles():
            self.profile_list.insert(tk.END, profile["name"])

    def save_profile(self):
        name = self.profile_name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a profile name.")
            return
        self.safe_call(
            lambda: self.controller.save_current_profile(name, password=self.password()),
            success_message=f"Profile '{name}' saved.",
        )
        self.refresh_profiles()

    def load_profile(self):
        selection = self.profile_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a cached profile.")
            return
        name = self.profile_list.get(selection[0])
        profile = self.safe_call(
            lambda: self.controller.load_profile(name, apply_to_device=True, password=self.password()),
            success_message=f"Profile '{name}' loaded.",
        )
        if profile:
            self.populate_entries_from_state()
