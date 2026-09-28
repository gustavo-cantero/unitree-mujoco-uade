"""Simulador del G1 que habla DDS igual que el robot real.

Sigue al puente oficial de unitree_mujoco (simulate_python) y agrega lo que
hace falta para probar este proyecto en Windows:

- publica rt/lowstate (ángulos, velocidades, torques e IMU) con el mismo modelo;
- aplica rt/lowcmd como el puente oficial:
  tau = tau_ff + kp·(q_cmd − q) + kd·(dq_cmd − dq), recalculado en cada paso;
- hasta recibir el primer rt/lowcmd, un "controlador interno" mantiene al robot
  de pie, como hace el controlador de Unitree en el robot real;
- mezcla rt/arm_sdk con ese controlador interno según el peso de motor_cmd[29].q;
- opcionalmente cuelga el robot de un arnés virtual: un resorte sujeto a un
  punto sobre la cabeza, como el soporte que se usa con el robot real.

No simula los servicios de alto nivel (LocoClient, MotionSwitcher).
"""

from __future__ import annotations

import threading
import time

import mujoco
import numpy as np

from ..config import JOINT_NAMES, initial_pose
from ..model import apply_pose, joint_addresses, load_model
from ..paths import DEFAULT_MODEL_PATH
from ..physics import enable_gravity, gains_for
from .dds import (
    TOPIC_ARM_SDK,
    TOPIC_LOWCMD,
    TOPIC_LOWSTATE,
    Ticker,
    quaternion_to_rpy,
)
from .g1 import ARM_SDK_JOINTS, ARM_SDK_WEIGHT_INDEX, MOTOR_JOINTS, NUM_MOTORS

SIM_DT = 0.002
STATE_EVERY_STEPS = 2  # rt/lowstate a 250 Hz
VIEWER_DT = 1.0 / 60.0
ARM_SDK_TIMEOUT_S = 0.5
HARNESS_STIFFNESS = 3000.0  # N/m
HARNESS_DAMPING = 300.0  # N·s/m
HARNESS_POINT = np.array([0.0, 0.0, 0.45])  # sobre la cabeza, en el torso


class _Command:
    """Copia numérica de un LowCmd_ para no leer el mensaje en cada paso."""

    def __init__(self, msg) -> None:
        motors = [msg.motor_cmd[i] for i in range(NUM_MOTORS)]
        self.q = np.array([m.q for m in motors])
        self.dq = np.array([m.dq for m in motors])
        self.kp = np.array([m.kp for m in motors])
        self.kd = np.array([m.kd for m in motors])
        self.tau = np.array([m.tau for m in motors])
        self.weight = float(np.clip(msg.motor_cmd[ARM_SDK_WEIGHT_INDEX].q, 0.0, 1.0))
        self.received = time.perf_counter()

    def torque(self, q: np.ndarray, dq: np.ndarray) -> np.ndarray:
        return self.tau + self.kp * (self.q - q) + self.kd * (self.dq - dq)


class G1Simulator:
    def __init__(self, harness: bool) -> None:
        self.model, self.data = load_model(DEFAULT_MODEL_PATH)
        enable_gravity(self.model)
        self.model.opt.timestep = SIM_DT

        actuator_joints = [
            self.model.joint(int(self.model.actuator_trnid[i][0])).name
            for i in range(self.model.nu)
        ]
        if tuple(actuator_joints) != MOTOR_JOINTS:
            raise ValueError("El orden de actuadores del modelo no coincide con el SDK.")

        joint_ids = [int(self.model.actuator_trnid[i][0]) for i in range(self.model.nu)]
        self.qpos_adr = np.array([self.model.jnt_qposadr[j] for j in joint_ids])
        self.qvel_adr = np.array([self.model.jnt_dofadr[j] for j in joint_ids])
        self.low, self.high = self.model.actuator_ctrlrange.T

        # Controlador interno: sostiene la postura de pie con PD rígido.
        stand = initial_pose()
        self.stand_targets = np.array(
            [stand.joints.get(name, 0.0) for name in MOTOR_JOINTS]
        )
        gains = np.array([gains_for(name) for name in MOTOR_JOINTS])
        self.stand_kp, self.stand_kd = gains[:, 0], gains[:, 1]
        self.arm_mask = np.zeros(NUM_MOTORS, dtype=bool)
        self.arm_mask[list(ARM_SDK_JOINTS)] = True

        # Pies apoyados en el suelo, igual que el resto del proyecto.
        addresses = joint_addresses(self.model, JOINT_NAMES)
        apply_pose(self.model, self.data, addresses, stand)

        self.torso = self.model.body("torso_link").id
        self.harness = harness
        self.harness_anchor = self._harness_point()

        self._lock = threading.Lock()
        self._lowcmd: _Command | None = None
        self._arm_sdk: _Command | None = None
        self._lowcmd_msg = None
        self._arm_sdk_msg = None
        self._announced_lowcmd = False
        self._announced_arm_sdk = False

        self._imu_quat = self.model.sensor("imu_quat").adr[0]
        self._imu_gyro = self.model.sensor("imu_gyro").adr[0]
        self._imu_acc = self.model.sensor("imu_acc").adr[0]

    # --- DDS -------------------------------------------------------------

    def connect(self) -> None:
        from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_

        self.state_msg = unitree_hg_msg_dds__LowState_()
        self.state_publisher = ChannelPublisher(TOPIC_LOWSTATE, LowState_)
        self.state_publisher.Init()
        self.lowcmd_subscriber = ChannelSubscriber(TOPIC_LOWCMD, LowCmd_)
        self.lowcmd_subscriber.Init(self._on_lowcmd, 10)
        self.arm_sdk_subscriber = ChannelSubscriber(TOPIC_ARM_SDK, LowCmd_)
        self.arm_sdk_subscriber.Init(self._on_arm_sdk, 10)

    # Los manejadores solo guardan el mensaje; se convierte en el lazo de
    # simulación y únicamente el más reciente, para no atrasarse.
    def _on_lowcmd(self, msg) -> None:
        with self._lock:
            self._lowcmd_msg = msg

    def _on_arm_sdk(self, msg) -> None:
        with self._lock:
            self._arm_sdk_msg = msg

    def publish_state(self, tick: int) -> None:
        msg = self.state_msg
        q = self.data.qpos[self.qpos_adr]
        dq = self.data.qvel[self.qvel_adr]
        for i in range(NUM_MOTORS):
            motor = msg.motor_state[i]
            motor.q = float(q[i])
            motor.dq = float(dq[i])
            motor.tau_est = float(self.data.actuator_force[i])
        sensors = self.data.sensordata
        quat = sensors[self._imu_quat : self._imu_quat + 4]
        msg.imu_state.quaternion[:] = [float(v) for v in quat]
        msg.imu_state.gyroscope[:] = [
            float(v) for v in sensors[self._imu_gyro : self._imu_gyro + 3]
        ]
        msg.imu_state.accelerometer[:] = [
            float(v) for v in sensors[self._imu_acc : self._imu_acc + 3]
        ]
        msg.imu_state.rpy[:] = [float(v) for v in quaternion_to_rpy(*quat)]
        msg.tick = tick
        self.state_publisher.Write(msg)

    # --- Física ------------------------------------------------------------

    def _control(self) -> None:
        q = self.data.qpos[self.qpos_adr]
        dq = self.data.qvel[self.qvel_adr]
        with self._lock:
            lowcmd_msg, self._lowcmd_msg = self._lowcmd_msg, None
            arm_sdk_msg, self._arm_sdk_msg = self._arm_sdk_msg, None
        if lowcmd_msg is not None:
            self._lowcmd = _Command(lowcmd_msg)
        if arm_sdk_msg is not None:
            self._arm_sdk = _Command(arm_sdk_msg)
        lowcmd, arm_sdk = self._lowcmd, self._arm_sdk

        if lowcmd is not None:
            if not self._announced_lowcmd:
                print("[SIM] Llegó rt/lowcmd: se apaga el controlador interno.")
                self._announced_lowcmd = True
            torque = lowcmd.torque(q, dq)
        else:
            torque = self.stand_kp * (self.stand_targets - q) - self.stand_kd * dq
            fresh = (
                arm_sdk is not None
                and time.perf_counter() - arm_sdk.received < ARM_SDK_TIMEOUT_S
            )
            if fresh and arm_sdk.weight > 0.0:
                if not self._announced_arm_sdk:
                    print("[SIM] Llegó rt/arm_sdk: se mezcla con el controlador interno.")
                    self._announced_arm_sdk = True
                w = arm_sdk.weight
                arm_torque = arm_sdk.torque(q, dq)
                torque = np.where(
                    self.arm_mask, (1.0 - w) * torque + w * arm_torque, torque
                )

        self.data.ctrl[:] = np.clip(torque, self.low, self.high)

        if self.harness:
            self._apply_harness()

    def _harness_point(self) -> np.ndarray:
        rotation = self.data.xmat[self.torso].reshape(3, 3)
        return self.data.xpos[self.torso] + rotation @ HARNESS_POINT

    def _apply_harness(self) -> None:
        point = self._harness_point()
        velocity6 = np.zeros(6)
        mujoco.mj_objectVelocity(
            self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.torso, velocity6, 0
        )
        angular, linear = velocity6[:3], velocity6[3:]
        point_velocity = linear + np.cross(angular, point - self.data.xpos[self.torso])
        force = (
            HARNESS_STIFFNESS * (self.harness_anchor - point)
            - HARNESS_DAMPING * point_velocity
        )
        self.data.qfrc_applied[:] = 0.0
        mujoco.mj_applyFT(
            self.model,
            self.data,
            force,
            np.zeros(3),
            point,
            self.torso,
            self.data.qfrc_applied,
        )

    def run(self, show_window: bool, duration: float | None) -> None:
        self.connect()
        print("[SIM] G1 simulado publicando rt/lowstate; escucha rt/lowcmd y rt/arm_sdk.")
        if self.harness:
            print("[SIM] Arnés virtual activo: el torso queda sostenido.")
        print("[SIM] Ctrl+C para terminar.")

        viewer = None
        if show_window:
            from mujoco import viewer as mujoco_viewer

            viewer = mujoco_viewer.launch_passive(
                self.model, self.data, show_left_ui=False, show_right_ui=False
            )
            viewer.cam.distance = 2.6
            viewer.cam.azimuth = 145
            viewer.cam.elevation = -15
            viewer.cam.lookat[:] = [0.0, 0.0, 0.75]

        ticker = Ticker(SIM_DT)
        start = time.perf_counter()
        last_view = 0.0
        step = 0
        try:
            while True:
                if viewer is not None and not viewer.is_running():
                    break
                if duration is not None and time.perf_counter() - start >= duration:
                    break
                self._control()
                mujoco.mj_step(self.model, self.data)
                step += 1
                if step % STATE_EVERY_STEPS == 0:
                    self.publish_state(step)
                now = time.perf_counter()
                if viewer is not None and now - last_view >= VIEWER_DT:
                    viewer.sync()
                    last_view = now
                ticker.wait()
        except KeyboardInterrupt:
            pass
        finally:
            if viewer is not None:
                viewer.close()
        elapsed = time.perf_counter() - start
        print(
            f"[SIM] Fin: {step * SIM_DT:.1f} s simulados en {elapsed:.1f} s reales."
        )
