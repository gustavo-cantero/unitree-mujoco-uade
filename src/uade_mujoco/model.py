"""Carga, validación y actualización del modelo MuJoCo."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import mujoco

from .trajectory import Frame, Stage


def load_model(path: Path) -> tuple[mujoco.MjModel, mujoco.MjData]:
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el modelo: {path}")
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)

    # Decisión de alcance: se estudia la trayectoria sin resolver el equilibrio
    # dinámico del bípedo. El README explica esta limitación explícitamente.
    model.opt.gravity[:] = 0.0
    return model, data


def joint_addresses(
    model: mujoco.MjModel,
    joint_names: Iterable[str],
) -> dict[str, int]:
    addresses: dict[str, int] = {}
    for name in joint_names:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if joint_id < 0:
            raise ValueError(f"El modelo no contiene la articulación '{name}'.")
        addresses[name] = int(model.jnt_qposadr[joint_id])
    return addresses


def validate_project(
    model: mujoco.MjModel,
    sequence: Iterable[Stage],
    joint_names: Iterable[str],
) -> dict[str, int]:
    """Valida estructura, duración, límites articulares y altura mínima."""

    stages = list(sequence)
    if model.nu != 29:
        raise ValueError(
            f"Se esperaba el G1 de 29 actuadores, pero el modelo informa {model.nu}."
        )

    addresses = joint_addresses(model, joint_names)
    for stage in stages:
        if stage.duration <= 0:
            raise ValueError(f"La fase '{stage.name}' tiene duración no positiva.")
        for name, value in stage.target.joints.items():
            joint_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_JOINT, name
            )
            if bool(model.jnt_limited[joint_id]):
                low, high = model.jnt_range[joint_id]
                if not (low <= value <= high):
                    raise ValueError(
                        f"Objetivo fuera de límite en {stage.name}: "
                        f"{name}={value:.3f}, rango=[{low:.3f}, {high:.3f}]"
                    )

    min_offset = min(stage.target.base_z_offset for stage in stages)
    if float(model.qpos0[2]) + min_offset <= 0.45:
        raise ValueError("La trayectoria baja demasiado la base del robot.")
    return addresses


def apply_frame(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    frame: Frame,
) -> None:
    """Aplica una muestra y recalcula la cinemática completa del modelo."""

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    data.qpos[2] = model.qpos0[2] + frame.pose.base_z_offset
    for name, value in frame.pose.joints.items():
        data.qpos[addresses[name]] = value
    mujoco.mj_forward(model, data)
