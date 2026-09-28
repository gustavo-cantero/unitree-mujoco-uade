"""Posturas y fases editables de la demostración.

Este es el archivo principal para experimentar con el movimiento. Los valores
articulares están expresados en radianes y se validan contra el modelo antes de
abrir la ventana.
"""

from __future__ import annotations

from typing import Mapping

from .trajectory import Pose, Stage


NEUTRAL_JOINTS: dict[str, float] = {
    "left_hip_pitch_joint": 0.0,
    "left_knee_joint": 0.0,
    "left_ankle_pitch_joint": 0.0,
    "right_hip_pitch_joint": 0.0,
    "right_knee_joint": 0.0,
    "right_ankle_pitch_joint": 0.0,
    "left_shoulder_pitch_joint": 0.20,
    "left_elbow_joint": -0.30,
    "right_shoulder_pitch_joint": 0.20,
    "right_shoulder_roll_joint": 0.0,
    "right_shoulder_yaw_joint": 0.0,
    "right_elbow_joint": -0.30,
    "right_wrist_pitch_joint": 0.0,
    "right_wrist_yaw_joint": 0.0,
}

JOINT_NAMES = tuple(NEUTRAL_JOINTS)

CSV_JOINTS = (
    "left_knee_joint",
    "right_knee_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_elbow_joint",
    "right_wrist_yaw_joint",
)


def pose_with(overrides: Mapping[str, float] | None = None) -> Pose:
    joints = dict(NEUTRAL_JOINTS)
    if overrides:
        joints.update(overrides)
    return Pose(joints=joints)


def initial_pose() -> Pose:
    return pose_with()


def build_sequence() -> list[Stage]:
    """Construye la rutina completa de unos nueve segundos."""

    squat = pose_with(
        {
            "left_hip_pitch_joint": -0.55,
            "left_knee_joint": 1.05,
            "left_ankle_pitch_joint": -0.50,
            "right_hip_pitch_joint": -0.55,
            "right_knee_joint": 1.05,
            "right_ankle_pitch_joint": -0.50,
        }
    )

    arm_up_values = {
        "right_shoulder_pitch_joint": -0.20,
        "right_shoulder_roll_joint": -1.80,
        "right_shoulder_yaw_joint": 0.0,
        "right_elbow_joint": 0.80,
        "right_wrist_pitch_joint": 0.15,
        "right_wrist_yaw_joint": 0.45,
    }
    arm_up = pose_with(arm_up_values)
    wave_left = pose_with(
        arm_up_values
        | {
            "right_shoulder_yaw_joint": -0.20,
            "right_wrist_yaw_joint": -0.65,
        }
    )
    wave_right = pose_with(
        arm_up_values
        | {
            "right_shoulder_yaw_joint": 0.20,
            "right_wrist_yaw_joint": 0.65,
        }
    )

    return [
        Stage("Postura inicial", 1.00, pose_with()),
        Stage("Sentadilla: bajando", 1.60, squat),
        Stage("Sentadilla: sosteniendo", 0.70, squat),
        Stage("Sentadilla: subiendo", 1.60, pose_with()),
        Stage("Saludo: levantando el brazo", 0.90, arm_up),
        Stage("Saludo: izquierda", 0.35, wave_left),
        Stage("Saludo: derecha", 0.35, wave_right),
        Stage("Saludo: izquierda", 0.35, wave_left),
        Stage("Saludo: derecha", 0.35, wave_right),
        Stage("Volviendo a postura neutra", 0.90, pose_with()),
        Stage("Fin", 0.60, pose_with()),
    ]
