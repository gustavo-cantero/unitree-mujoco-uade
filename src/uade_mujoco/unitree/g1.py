"""Datos del G1 de 29 motores tal como los expone el SDK de Unitree.

No importa el SDK: se puede usar y probar desde el entorno principal.
"""

from __future__ import annotations

from typing import Mapping, Sequence

# Orden de LowCmd_.motor_cmd y LowState_.motor_state (unitree_hg). Coincide con
# el orden de los actuadores del MJCF; tests/test_unitree_g1.py lo comprueba.
MOTOR_JOINTS = (
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "waist_yaw_joint",
    "waist_roll_joint",
    "waist_pitch_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
)
NUM_MOTORS = len(MOTOR_JOINTS)
MOTOR_INDEX = {name: index for index, name in enumerate(MOTOR_JOINTS)}

# Rigideces del ejemplo oficial g1_low_level_example.py (unitree_sdk2_python).
# Son valores razonables para el robot real.
OFFICIAL_KP = (
    60, 60, 60, 100, 40, 40,
    60, 60, 60, 100, 40, 40,
    60, 40, 40,
    40, 40, 40, 40, 40, 40, 40,
    40, 40, 40, 40, 40, 40, 40,
)
OFFICIAL_KD = (
    1, 1, 1, 2, 1, 1,
    1, 1, 1, 2, 1, 1,
    1, 1, 1,
    1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1,
)

# Amortiguación para dejar el robot "blando" al terminar o ante un problema.
DAMPING_KD = 2.0

# arm_sdk (g1_arm7_sdk_dds_example.py): cintura y brazos, índices 12 a 28.
# El peso de mezcla con el controlador de Unitree viaja en motor_cmd[29].q.
ARM_SDK_JOINTS = tuple(range(12, NUM_MOTORS))
ARM_SDK_WEIGHT_INDEX = 29
ARM_SDK_KP = 60.0
ARM_SDK_KD = 1.5


def targets_from_joints(
    joints: Mapping[str, float],
    base: Sequence[float] | None = None,
) -> list[float]:
    """Vector de 29 objetivos: los de `joints` y, el resto, de `base` (o 0)."""

    targets = list(base) if base is not None else [0.0] * NUM_MOTORS
    for name, value in joints.items():
        targets[MOTOR_INDEX[name]] = value
    return targets
