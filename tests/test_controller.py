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

    def test_active_profile_tracking_and_delete(self):
        self.controller.connect_device(password="secret")
        self.controller.save_current_profile("baseline", password="secret")

        status = self.controller.get_status()
        self.assertEqual(status["active_profile_name"], "baseline")

        self.controller.update_parameters(1234, 2.0, 0.0, 0.0, password="secret")
        status = self.controller.get_status()
        self.assertIsNone(status["active_profile_name"])

        self.controller.delete_profile("baseline", password="secret")
        self.assertEqual(self.controller.list_profiles(), [])

    def test_rename_profile_changes_name_only(self):
        self.controller.connect_device(password="secret")
        self.controller.update_waveform("RAMP", password="secret")
        self.controller.update_parameters(500, 1.2, 0.1, 10, password="secret")
        self.controller.save_current_profile("original", password="secret")

        self.controller.rename_profile("original", "renamed", password="secret")
        profile = self.controller.load_profile("renamed", apply_to_device=False)

        self.assertEqual(profile["waveform"], "RAMP")
        self.assertEqual(profile["frequency"], 500)
        with self.assertRaises(ValueError):
            self.controller.load_profile("original", apply_to_device=False)

    def test_rename_profile_rejects_existing_target(self):
        self.controller.connect_device(password="secret")
        self.controller.save_current_profile("source", password="secret")
        self.controller.save_current_profile("target", password="secret")

        with self.assertRaises(ValueError):
            self.controller.rename_profile("source", "target", password="secret")


if __name__ == "__main__":
    unittest.main()
