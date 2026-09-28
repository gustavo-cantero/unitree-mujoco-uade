import unittest

from uade_mujoco.config import JOINT_NAMES, build_sequence
from uade_mujoco.model import load_model, validate_project
from uade_mujoco.paths import DEFAULT_MODEL_PATH


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.data = load_model(DEFAULT_MODEL_PATH)

    def test_official_model_has_29_actuators(self):
        self.assertEqual(self.model.nu, 29)

    def test_sequence_is_valid_for_model(self):
        addresses = validate_project(self.model, build_sequence(), JOINT_NAMES)
        self.assertEqual(set(addresses), set(JOINT_NAMES))


if __name__ == "__main__":
    unittest.main()
