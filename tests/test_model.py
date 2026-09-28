import unittest

from uade_mujoco.config import JOINT_NAMES, build_sequence, initial_pose
from uade_mujoco.model import (
    apply_frame,
    foot_contact_geoms,
    load_model,
    validate_project,
)
from uade_mujoco.paths import DEFAULT_MODEL_PATH
from uade_mujoco.trajectory import iter_frames


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.data = load_model(DEFAULT_MODEL_PATH)

    def test_official_model_has_29_actuators(self):
        self.assertEqual(self.model.nu, 29)

    def test_sequence_is_valid_for_model(self):
        addresses = validate_project(self.model, build_sequence(), JOINT_NAMES)
        self.assertEqual(set(addresses), set(JOINT_NAMES))

    def test_feet_never_go_below_floor(self):
        sequence = build_sequence()
        addresses = validate_project(self.model, sequence, JOINT_NAMES)
        feet = foot_contact_geoms(self.model)
        for frame in iter_frames(sequence, initial_pose(), JOINT_NAMES, fps=60):
            apply_frame(self.model, self.data, addresses, frame)
            lowest = min(
                self.data.geom_xpos[g][2] - self.model.geom_size[g][0] for g in feet
            )
            self.assertAlmostEqual(lowest, 0.0, places=6, msg=frame.phase)


if __name__ == "__main__":
    unittest.main()
