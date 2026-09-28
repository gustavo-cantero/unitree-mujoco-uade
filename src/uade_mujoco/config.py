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
    "right_wrist_pitch_joint",
)


def pose_with(overrides: Mapping[str, float] | None = None) -> Pose:
    joints = dict(NEUTRAL_JOINTS)
    if overrides:
        joints.update(overrides)
    return Pose(joints=joints)


def initial_pose() -> Pose:
    return pose_with()


RIGHT_ARM_JOINTS = (
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
)


def squat_stages() -> list[Stage]:
    """Fases de la sentadilla, desde y hacia la postura neutra."""

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
    return [
        Stage("Sentadilla: bajando", 1.60, squat),
        Stage("Sentadilla: sosteniendo", 0.70, squat),
        Stage("Sentadilla: subiendo", 1.60, pose_with()),
    ]


def wave_stages() -> list[Stage]:
    """Fases del saludo: levantar el brazo y balancear la mano dos veces.

    Termina con el brazo levantado; quien la usa agrega la vuelta al reposo.
    Solo cambia las articulaciones de RIGHT_ARM_JOINTS.
    """

    # Brazo al costado (15° sobre la horizontal), antebrazo vertical y palma
    # mirando hacia adelante.
    arm_up_values = {
        "right_shoulder_pitch_joint": 0.0,
        "right_shoulder_roll_joint": -1.71,
        "right_shoulder_yaw_joint": -1.57,
        "right_elbow_joint": 0.14,
        "right_wrist_pitch_joint": 0.0,
        "right_wrist_yaw_joint": 0.0,
    }
    arm_up = pose_with(arm_up_values)
    # En esa postura el codo y right_wrist_pitch_joint giran alrededor del eje
    # perpendicular a la palma: la mano se balancea de lado a lado sin dejar de
    # mirar hacia adelante.
    wave_left = pose_with(
        arm_up_values
        | {
            "right_elbow_joint": -0.11,
            "right_wrist_pitch_joint": -0.35,
        }
    )
    wave_right = pose_with(
        arm_up_values
        | {
            "right_elbow_joint": 0.39,
            "right_wrist_pitch_joint": 0.35,
        }
    )
    return [
        Stage("Saludo: levantando el brazo", 0.90, arm_up),
        Stage("Saludo: izquierda", 0.35, wave_left),
        Stage("Saludo: derecha", 0.35, wave_right),
        Stage("Saludo: izquierda", 0.35, wave_left),
        Stage("Saludo: derecha", 0.35, wave_right),
    ]


def build_sequence() -> list[Stage]:
    """Construye la rutina completa de unos nueve segundos."""

    return [
        Stage("Postura inicial", 1.00, pose_with()),
        *squat_stages(),
        *wave_stages(),
        Stage("Volviendo a postura neutra", 0.90, pose_with()),
        Stage("Fin", 0.60, pose_with()),
    ]
