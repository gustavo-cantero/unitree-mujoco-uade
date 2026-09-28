import unittest

from uade_mujoco.config import JOINT_NAMES, build_sequence, initial_pose
from uade_mujoco.model import load_model, validate_project
from uade_mujoco.paths import DEFAULT_MODEL_PATH
from uade_mujoco.physics import PdController, enable_gravity
from uade_mujoco.trajectory import iter_frames


class PhysicsTests(unittest.TestCase):
    def test_routine_with_gravity_does_not_fall(self):
        model, data = load_model(DEFAULT_MODEL_PATH)
        sequence = build_sequence()
        addresses = validate_project(model, sequence, JOINT_NAMES)
        enable_gravity(model)
        controller = PdController(model, data, addresses, initial_pose(), fps=60)

        max_tilt = 0.0
        for frame in iter_frames(sequence, initial_pose(), JOINT_NAMES, fps=60):
            controller.advance(frame)
            max_tilt = max(max_tilt, controller.tilt_deg())

        self.assertFalse(controller.fallen)
        self.assertLess(max_tilt, 10.0)
        self.assertGreater(data.qpos[2], 0.7)


if __name__ == "__main__":
    unittest.main()
