import tempfile
import unittest
from pathlib import Path

from controllers.controller import Controller
from models.config_repository import ConfigRepository


class FakeGenerator:
    def __init__(self, address):
        self.address = address
        self.commands = []

    def connect(self):
        self.commands.append(("connect", self.address))
        return True

    def set_waveform(self, waveform):
        self.commands.append(("waveform", waveform))

    def set_parameters(self, frequency, amplitude, offset, phase):
        self.commands.append(("parameters", frequency, amplitude, offset, phase))

    def toggle_channel(self, channel, state):
        self.commands.append(("channel", channel, state))

    def enable_output(self):
        self.commands.append(("output", True))

    def disable_output(self):
        self.commands.append(("output", False))


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "profiles.sqlite3"
        self.controller = Controller(
            resources=["USB::TEST"],
            control_password="secret",
            generator_factory=FakeGenerator,
            config_repository=ConfigRepository(str(db_path)),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_control_requires_password(self):
        with self.assertRaises(PermissionError):
            self.controller.connect_device(password="wrong")

    def test_save_and_apply_profile(self):
        self.controller.connect_device(password="secret")
        self.controller.update_waveform("SQU", password="secret")
        self.controller.update_parameters(2000, 3.3, 0.1, 45, password="secret")
        self.controller.toggle_channel(2, True, password="secret")
        self.controller.save_current_profile("lab-mode", password="secret")

        loaded = self.controller.load_profile("lab-mode", apply_to_device=True, password="secret")

        self.assertEqual(loaded["waveform"], "SQU")
        self.assertEqual(loaded["channels"][2], True)
        self.assertEqual(self.controller.state["frequency"], 2000)
        self.assertIn(("waveform", "SQU"), self.controller.generator.commands)


if __name__ == "__main__":
    unittest.main()
