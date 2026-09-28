import unittest

from uade_mujoco.config import RIGHT_ARM_JOINTS, initial_pose, wave_stages
from uade_mujoco.model import load_model
from uade_mujoco.paths import DEFAULT_MODEL_PATH
from uade_mujoco.unitree.g1 import (
    ARM_SDK_JOINTS,
    MOTOR_INDEX,
    MOTOR_JOINTS,
    NUM_MOTORS,
    OFFICIAL_KD,
    OFFICIAL_KP,
    targets_from_joints,
)


class UnitreeG1Tests(unittest.TestCase):
    def test_motor_order_matches_model_actuators(self):
        model, _ = load_model(DEFAULT_MODEL_PATH)
        actuator_joints = tuple(
            model.joint(int(model.actuator_trnid[i][0])).name for i in range(model.nu)
        )
        self.assertEqual(actuator_joints, MOTOR_JOINTS)

    def test_gain_tables_cover_every_motor(self):
        self.assertEqual(NUM_MOTORS, 29)
        self.assertEqual(len(OFFICIAL_KP), NUM_MOTORS)
        self.assertEqual(len(OFFICIAL_KD), NUM_MOTORS)

    def test_wave_only_uses_arm_sdk_joints(self):
        for name in RIGHT_ARM_JOINTS:
            self.assertIn(MOTOR_INDEX[name], ARM_SDK_JOINTS)
        neutral = initial_pose().joints
        for stage in wave_stages():
            changed = {
                name for name, value in stage.target.joints.items()
                if value != neutral[name]
            }
            self.assertLessEqual(changed, set(RIGHT_ARM_JOINTS), stage.name)

    def test_targets_from_joints_fills_the_rest(self):
        targets = targets_from_joints({"left_knee_joint": 1.0}, base=[0.5] * NUM_MOTORS)
        self.assertEqual(targets[MOTOR_INDEX["left_knee_joint"]], 1.0)
        self.assertEqual(targets[MOTOR_INDEX["right_knee_joint"]], 0.5)


if __name__ == "__main__":
    unittest.main()
