import time
from tkinter import messagebox
from models.waveform_generator import WaveformGenerator
from utils.excel_handler import ExcelHandler

class Controller:
    def __init__(self, resource_address):
        self.generator = WaveformGenerator(resource_address)
        self.test_paused = False
        self.test_stopped = False

    def connect_device(self):
        return self.generator.connect()

    def update_waveform(self, waveform):
        self.generator.set_waveform(waveform)

    def update_parameters(self, frequency, amplitude, offset, phase):
        self.generator.set_parameters(frequency, amplitude, offset, phase)

    def toggle_channel(self, channel, state):
        self.generator.toggle_channel(channel, state)

    def enable_output(self):
        self.generator.enable_output()

    def disable_output(self):
        self.generator.disable_output()

    def stop_test(self):
        self.test_stopped = True

    def pause_resume_test(self):
        self.test_paused = not self.test_paused

    def run_test_sequence(self):
        self.test_stopped = False
        self.test_paused = False
        sequence = ExcelHandler.load_test_sequence()
        if sequence is None:
            return

        try:
            for _, row in sequence.iterrows():
                if self.test_stopped:
                    messagebox.showinfo("Test Stopped", "Test stopped by user.")
                    return
                while self.test_paused:
                    time.sleep(0.1)
                self.generator.set_waveform(row['Waveform'])
                self.generator.set_parameters(
                    row['Frequency'],
                    row['Amplitude'],
                    row['Offset'],
                    row['Phase']
                )
                delay = row.get('Delay', 1)
                time.sleep(delay)
            messagebox.showinfo("Test Completed", "Test sequence completed.")
        except Exception as e:
            messagebox.showerror("Test Error", str(e))

    def create_test_file(self):
        ExcelHandler.create_test_template()
