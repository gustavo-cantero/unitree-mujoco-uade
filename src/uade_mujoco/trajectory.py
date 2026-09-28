"""Tipos y funciones matemáticas para generar trayectorias suaves."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np


@dataclass(frozen=True)
class Pose:
    """Objetivos articulares y desplazamiento vertical de la base."""

    joints: Mapping[str, float]
    base_z_offset: float = 0.0


@dataclass(frozen=True)
class Stage:
    """Una fase de la rutina y su postura final."""

    name: str
    duration: float
    target: Pose


@dataclass(frozen=True)
class Frame:
    """Una muestra de la trayectoria en un instante."""

    time_s: float
    phase: str
    pose: Pose


def minimum_jerk(value: float) -> float:
    """Calcula 10u³ - 15u⁴ + 6u⁵ para que los extremos sean suaves."""

    u = float(np.clip(value, 0.0, 1.0))
    return 10.0 * u**3 - 15.0 * u**4 + 6.0 * u**5


def interpolate_pose(
    start: Pose,
    end: Pose,
    alpha: float,
    joint_names: Iterable[str],
) -> Pose:
    blend = minimum_jerk(alpha)
    joints = {
        name: start.joints[name]
        + (end.joints[name] - start.joints[name]) * blend
        for name in joint_names
    }
    base_z_offset = start.base_z_offset + (
        end.base_z_offset - start.base_z_offset
    ) * blend
    return Pose(joints=joints, base_z_offset=base_z_offset)


def iter_frames(
    sequence: Iterable[Stage],
    initial_pose: Pose,
    joint_names: Iterable[str],
    fps: int,
) -> Iterable[Frame]:
    """Convierte las fases en muestras listas para mostrar o verificar."""

    names = tuple(joint_names)
    current = initial_pose
    elapsed = 0.0
    yield Frame(time_s=0.0, phase="Inicio", pose=current)

    for stage in sequence:
        steps = max(1, round(stage.duration * fps))
        dt = stage.duration / steps
        for step in range(1, steps + 1):
            pose = interpolate_pose(current, stage.target, step / steps, names)
            elapsed += dt
            yield Frame(time_s=elapsed, phase=stage.name, pose=pose)
        current = stage.target


def total_duration(sequence: Iterable[Stage]) -> float:
    return sum(stage.duration for stage in sequence)
