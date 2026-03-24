import threading
import time
from typing import Callable, Dict, Iterable, Optional

from models.config_repository import ConfigRepository
from models.waveform_generator import WaveformGenerator
from utils.excel_handler import ExcelHandler


class Controller:
    def __init__(
        self,
        resources: Optional[Iterable[str]] = None,
        notifier: Optional[Callable[[str, str, str], None]] = None,
        control_password: Optional[str] = None,
        generator_factory: Optional[Callable[[Optional[str]], WaveformGenerator]] = None,
        config_repository: Optional[ConfigRepository] = None,
    ):
        self.resources = list(resources or [])
        self.current_address = self.resources[0] if self.resources else None
        self.control_password = control_password or "admin123"
        self.notifier = notifier or (lambda level, title, message: None)
        self.generator_factory = generator_factory or WaveformGenerator
        self.config_repository = config_repository or ConfigRepository()
        self.generator = self.generator_factory(self.current_address)
        self.test_paused = False
        self.test_stopped = False
        self.connected = False
        self._lock = threading.RLock()
        self.state: Dict = {
            "waveform": "SIN",
            "frequency": 1000.0,
            "amplitude": 1.0,
            "offset": 0.0,
            "phase": 0.0,
            "channels": {1: True, 2: False},
            "output_enabled": False,
        }

    def list_resources(self):
        return list(self.resources)

    def set_resource_address(self, resource_address: Optional[str]) -> None:
        with self._lock:
            self.current_address = resource_address
            self.generator = self.generator_factory(self.current_address)
            self.connected = False

    def _require_password(self, password: Optional[str]) -> None:
        if self.control_password and password != self.control_password:
            raise PermissionError("Invalid control password.")

    def connect_device(self, password: Optional[str] = None, resource_address: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            if resource_address and resource_address != self.current_address:
                self.set_resource_address(resource_address)
            if not self.current_address:
                raise ValueError("No device resource address selected.")
            self.connected = self.generator.connect()
            return self.connected

    def update_waveform(self, waveform: str, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            self.generator.set_waveform(waveform)
            self.state["waveform"] = waveform

    def update_parameters(self, frequency, amplitude, offset, phase, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            self.generator.set_parameters(frequency, amplitude, offset, phase)
            self.state.update(
                {
                    "frequency": float(frequency),
                    "amplitude": float(amplitude),
                    "offset": float(offset),
                    "phase": float(phase),
                }
            )

    def toggle_channel(self, channel: int, state: bool, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            enabled = bool(state)
            self.generator.toggle_channel(channel, enabled)
            self.state["channels"][channel] = enabled

    def enable_output(self, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            self.generator.enable_output()
            self.state["output_enabled"] = True

    def disable_output(self, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            self.generator.disable_output()
            self.state["output_enabled"] = False

    def stop_test(self):
        self.test_stopped = True

    def pause_resume_test(self):
        self.test_paused = not self.test_paused
        return self.test_paused

    def run_test_sequence(self, password: Optional[str] = None):
        self._require_password(password)
        self.test_stopped = False
        self.test_paused = False
        sequence = ExcelHandler.load_test_sequence()
        if sequence is None:
            return False

        try:
            for _, row in sequence.iterrows():
                if self.test_stopped:
                    self.notifier("info", "Test Stopped", "Test stopped by user.")
                    return False
                while self.test_paused:
                    time.sleep(0.1)
                self.update_waveform(row["Waveform"], password=password)
                self.update_parameters(
                    row["Frequency"],
                    row["Amplitude"],
                    row["Offset"],
                    row["Phase"],
                    password=password,
                )
                time.sleep(row.get("Delay", 1))
            self.notifier("info", "Test Completed", "Test sequence completed.")
            return True
        except Exception as exc:
            self.notifier("error", "Test Error", str(exc))
            raise

    def create_test_file(self):
        ExcelHandler.create_test_template()

    def save_current_profile(self, name: str, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            self.config_repository.save_profile(name, self.state)

    def load_profile(self, name: str, apply_to_device: bool = False, password: Optional[str] = None):
        with self._lock:
            profile = self.config_repository.load_profile(name)
            if profile is None:
                raise ValueError(f"Profile '{name}' not found.")
            if apply_to_device:
                self._require_password(password)
                self.update_waveform(profile["waveform"], password=password)
                self.update_parameters(
                    profile["frequency"],
                    profile["amplitude"],
                    profile["offset"],
                    profile["phase"],
                    password=password,
                )
                for channel, enabled in profile["channels"].items():
                    self.toggle_channel(channel, enabled, password=password)
            self.state.update(
                {
                    "waveform": profile["waveform"],
                    "frequency": profile["frequency"],
                    "amplitude": profile["amplitude"],
                    "offset": profile["offset"],
                    "phase": profile["phase"],
                    "channels": dict(profile["channels"]),
                }
            )
            return profile

    def list_profiles(self):
        return self.config_repository.list_profiles()

    def delete_profile(self, name: str, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            deleted = self.config_repository.delete_profile(name)
            if not deleted:
                raise ValueError(f"Profile '{name}' not found.")
            return True

    def rename_profile(self, old_name: str, new_name: str, password: Optional[str] = None):
        with self._lock:
            self._require_password(password)
            source_name = (old_name or "").strip()
            target_name = (new_name or "").strip()
            if not source_name:
                raise ValueError("Original profile name is required.")
            if not target_name:
                raise ValueError("New profile name is required.")
            if source_name == target_name:
                return True
            renamed = self.config_repository.rename_profile(source_name, target_name)
            if not renamed:
                raise ValueError(f"Profile '{source_name}' not found.")
            return True

    def _find_active_profile_name(self):
        current = {
            "waveform": self.state["waveform"],
            "frequency": float(self.state["frequency"]),
            "amplitude": float(self.state["amplitude"]),
            "offset": float(self.state["offset"]),
            "phase": float(self.state["phase"]),
            "channels": {1: bool(self.state["channels"].get(1, False)), 2: bool(self.state["channels"].get(2, False))},
        }
        for profile in self.list_profiles():
            candidate = {
                "waveform": profile["waveform"],
                "frequency": float(profile["frequency"]),
                "amplitude": float(profile["amplitude"]),
                "offset": float(profile["offset"]),
                "phase": float(profile["phase"]),
                "channels": {1: bool(profile["channels"].get(1, False)), 2: bool(profile["channels"].get(2, False))},
            }
            if candidate == current:
                return profile["name"]
        return None

    def get_status(self):
        with self._lock:
            return {
                "resources": self.list_resources(),
                "current_address": self.current_address,
                "connected": self.connected,
                "state": {
                    "waveform": self.state["waveform"],
                    "frequency": self.state["frequency"],
                    "amplitude": self.state["amplitude"],
                    "offset": self.state["offset"],
                    "phase": self.state["phase"],
                    "channels": dict(self.state["channels"]),
                    "output_enabled": self.state["output_enabled"],
                },
                "profiles": self.list_profiles(),
                "active_profile_name": self._find_active_profile_name(),
            }
