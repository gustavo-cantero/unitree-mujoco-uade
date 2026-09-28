"""Carga, validación y actualización del modelo MuJoCo."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import mujoco

from .trajectory import Frame, Pose, Stage


MIN_BASE_HEIGHT_M = 0.45


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


def foot_contact_geoms(model: mujoco.MjModel) -> list[int]:
    """Devuelve las esferas de contacto que el MJCF coloca bajo cada pie."""

    geoms = [
        geom_id
        for geom_id in range(model.ngeom)
        if model.geom_type[geom_id] == mujoco.mjtGeom.mjGEOM_SPHERE
        and model.body(model.geom_bodyid[geom_id]).name.endswith("_ankle_roll_link")
    ]
    if not geoms:
        raise ValueError("El modelo no tiene esferas de contacto en los pies.")
    return geoms


def apply_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    pose: Pose,
) -> None:
    """Aplica una postura y ajusta la altura de la base para apoyar los pies.

    Primero se calcula la cinemática con la base en su altura inicial; luego se
    sube o baja la base lo justo para que el punto más bajo de los pies toque
    el suelo (z = 0).
    """

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    for name, value in pose.joints.items():
        data.qpos[addresses[name]] = value
    mujoco.mj_kinematics(model, data)
    lowest = min(
        data.geom_xpos[geom_id][2] - model.geom_size[geom_id][0]
        for geom_id in foot_contact_geoms(model)
    )
    data.qpos[2] -= lowest
    mujoco.mj_forward(model, data)


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

    data = mujoco.MjData(model)
    for stage in stages:
        apply_pose(model, data, addresses, stage.target)
        if data.qpos[2] <= MIN_BASE_HEIGHT_M:
            raise ValueError(
                f"La fase '{stage.name}' baja demasiado la base del robot: "
                f"{data.qpos[2]:.3f} m (mínimo {MIN_BASE_HEIGHT_M} m)."
            )
    return addresses


def apply_frame(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    frame: Frame,
) -> None:
    """Aplica una muestra de la trayectoria al modelo."""

    apply_pose(model, data, addresses, frame.pose)
