import pandas as pd
import os
from tkinter import filedialog, messagebox

class ExcelHandler:
    @staticmethod
    def load_test_sequence():
        filepath = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if filepath:
            return pd.read_excel(filepath)
        return None

    @staticmethod
    def create_test_template():
        template_data = {
            "Waveform": ["SIN", "SQU", "TRI", "RAMP"],
            "Frequency": ["Enter Frequency (Hz)"] * 4,
            "Amplitude": ["Enter Amplitude (V)"] * 4,
            "Offset": ["Enter Offset (V)"] * 4,
            "Phase": ["Enter Phase (°)"] * 4,
            "Delay": ["Enter Delay (s)"] * 4
        }
        df = pd.DataFrame(template_data)
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if filepath:
            df.to_excel(filepath, index=False)
            messagebox.showinfo("Template Created", f"Template saved at: {filepath}")
            os.startfile(filepath)
