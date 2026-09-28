import unittest

from uade_mujoco.config import JOINT_NAMES, build_sequence, initial_pose
from uade_mujoco.trajectory import iter_frames, minimum_jerk, total_duration


class TrajectoryTests(unittest.TestCase):
    def test_minimum_jerk_endpoints(self):
        self.assertAlmostEqual(minimum_jerk(0.0), 0.0)
        self.assertAlmostEqual(minimum_jerk(1.0), 1.0)

    def test_sequence_duration_and_final_pose(self):
        sequence = build_sequence()
        frames = list(iter_frames(sequence, initial_pose(), JOINT_NAMES, fps=60))
        self.assertAlmostEqual(frames[-1].time_s, total_duration(sequence))
        self.assertEqual(frames[-1].pose, initial_pose())


if __name__ == "__main__":
    unittest.main()
