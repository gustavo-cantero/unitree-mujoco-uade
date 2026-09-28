"""Simulación dinámica con gravedad y control PD de torque.

En el modo cinemático (model.apply_frame) cada postura se asigna directamente.
Aquí, en cambio, MuJoCo integra la física: cada motor recibe un torque

    tau = kp * (q_objetivo - q) - kd * dq

y el robot debe sostenerse sobre sus pies. Es el mismo tipo de orden que
aceptan los motores del G1 real, aunque las rigideces que siguen son mucho más
altas que las que se usarían en el robot físico: aquí la rigidez reemplaza a un
controlador de equilibrio.
"""

from __future__ import annotations

from typing import Mapping

import mujoco
import numpy as np

from .model import apply_pose
from .trajectory import Frame, Pose


GRAVITY_M_S2 = 9.81
FALL_TILT_DEG = 45.0

# (kp en N·m/rad, kd en N·m·s/rad) según el tipo de articulación.
# Con piernas por debajo de ~500 el robot se cae en la sentadilla.
LEG_GAINS = (800.0, 15.0)
ARM_GAINS = (100.0, 2.5)
WRIST_GAINS = (50.0, 1.25)


def enable_gravity(model: mujoco.MjModel) -> None:
    model.opt.gravity[:] = (0.0, 0.0, -GRAVITY_M_S2)


def _gains_for(joint_name: str) -> tuple[float, float]:
    if "wrist" in joint_name:
        return WRIST_GAINS
    if any(part in joint_name for part in ("shoulder", "elbow")):
        return ARM_GAINS
    return LEG_GAINS


class PdController:
    """Aplica la trayectoria como objetivos de un control PD por motor."""

    def __init__(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        addresses: Mapping[str, int],
        initial_pose: Pose,
        fps: int,
    ) -> None:
        self.model = model
        self.data = data
        joint_ids = [int(model.actuator_trnid[i][0]) for i in range(model.nu)]
        self.names = [model.joint(j).name for j in joint_ids]
        self.qpos_adr = np.array([model.jnt_qposadr[j] for j in joint_ids])
        self.qvel_adr = np.array([model.jnt_dofadr[j] for j in joint_ids])
        gains = np.array([_gains_for(name) for name in self.names])
        self.kp, self.kd = gains[:, 0], gains[:, 1]
        self.low, self.high = model.actuator_ctrlrange.T
        self.substeps = max(1, round(1.0 / (fps * model.opt.timestep)))
        self.fallen = False

        # Arranca en reposo con los pies apoyados, igual que el modo cinemático.
        apply_pose(model, data, addresses, initial_pose)

    def advance(self, frame: Frame) -> None:
        """Simula el intervalo de un fotograma persiguiendo la postura dada."""

        target = self.model.qpos0[self.qpos_adr].copy()
        for index, name in enumerate(self.names):
            if name in frame.pose.joints:
                target[index] = frame.pose.joints[name]

        for _ in range(self.substeps):
            torque = self.kp * (target - self.data.qpos[self.qpos_adr])
            torque -= self.kd * self.data.qvel[self.qvel_adr]
            self.data.ctrl[:] = np.clip(torque, self.low, self.high)
            mujoco.mj_step(self.model, self.data)

        if not self.fallen and self.tilt_deg() > FALL_TILT_DEG:
            self.fallen = True
            print(f"[AVISO] El robot se cayó durante '{frame.phase}'.")

    def tilt_deg(self) -> float:
        """Inclinación del tronco respecto de la vertical, en grados."""

        pelvis_z_axis = self.data.xmat[self.model.body("pelvis").id][8]
        return float(np.degrees(np.arccos(np.clip(pelvis_z_axis, -1.0, 1.0))))
