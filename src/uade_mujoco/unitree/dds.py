"""Conexión DDS, lectura de estado y envío de comandos al G1."""

from __future__ import annotations

import math
import re
import sys
import threading
import time
from typing import Sequence

from .g1 import DAMPING_KD, NUM_MOTORS

SIM_DOMAIN = 1
ROBOT_DOMAIN = 0
TOPIC_LOWSTATE = "rt/lowstate"
TOPIC_LOWCMD = "rt/lowcmd"
TOPIC_ARM_SDK = "rt/arm_sdk"


def _require_sdk() -> None:
    try:
        import unitree_sdk2py  # noqa: F401
    except ImportError as error:
        raise RuntimeError(
            "Falta unitree_sdk2py. Ejecutá instalar_robot.bat y usá "
            ".venv-robot\\Scripts\\python.exe."
        ) from error


def improve_windows_timer() -> None:
    """Pide al sistema una resolución de 1 ms para time.sleep.

    Python 3.10 en Windows duerme de a ~15 ms, demasiado para un lazo de control.
    """

    if sys.platform == "win32":
        import ctypes

        ctypes.windll.winmm.timeBeginPeriod(1)


def init_dds(domain: int, interface: str | None) -> None:
    """Inicializa CycloneDDS en el dominio dado.

    Sin interfaz, CycloneDDS elige una automáticamente (sirve para el
    simulador en la misma PC). Para el robot hay que indicar el adaptador
    conectado a él, por ejemplo "Ethernet 2".
    """

    _require_sdk()
    improve_windows_timer()
    from unitree_sdk2py.core import channel

    # La configuración del SDK para una interfaz fija escribe un registro en
    # /tmp/cdds.LOG, que no existe en Windows, y la inicialización falla.
    channel.ChannelConfigHasInterface = re.sub(
        r"\s*<Tracing>.*?</Tracing>",
        "",
        channel.ChannelConfigHasInterface,
        flags=re.S,
    )
    try:
        channel.ChannelFactoryInitialize(domain, interface)
    except Exception as error:
        detail = f" con la interfaz '{interface}'" if interface else ""
        raise RuntimeError(
            f"No se pudo iniciar DDS en el dominio {domain}{detail}. "
            "En Windows la interfaz es el nombre del adaptador que muestra "
            "Get-NetAdapter (por ejemplo 'Ethernet 2')."
        ) from error


class Ticker:
    """Marca un período fijo combinando sleep y espera activa."""

    def __init__(self, period: float) -> None:
        self.period = period
        self.next_tick = time.perf_counter()

    def wait(self) -> None:
        self.next_tick += self.period
        remaining = self.next_tick - time.perf_counter()
        if remaining < -5 * self.period:
            # Nos atrasamos mucho: se reinicia en lugar de acumular deuda.
            self.next_tick = time.perf_counter()
            return
        if remaining > 0.002:
            time.sleep(remaining - 0.0015)
        while time.perf_counter() < self.next_tick:
            pass


def quaternion_to_rpy(w: float, x: float, y: float, z: float) -> tuple[float, float, float]:
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


class LowStateReader:
    """Guarda el último rt/lowstate recibido."""

    def __init__(self) -> None:
        from unitree_sdk2py.core.channel import ChannelSubscriber
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

        self._lock = threading.Lock()
        self._msg = None
        self._subscriber = ChannelSubscriber(TOPIC_LOWSTATE, LowState_)
        self._subscriber.Init(self._handler, 10)

    def _handler(self, msg) -> None:
        with self._lock:
            self._msg = msg

    def wait_first(self, timeout: float = 5.0) -> None:
        deadline = time.perf_counter() + timeout
        while self.latest() is None:
            if time.perf_counter() > deadline:
                raise RuntimeError(
                    f"No llegan mensajes de {TOPIC_LOWSTATE} después de "
                    f"{timeout:.0f} s. ¿Está corriendo el simulador, o el robot "
                    "encendido y conectado a esa interfaz?"
                )
            time.sleep(0.05)

    def latest(self):
        with self._lock:
            return self._msg

    def joint_positions(self) -> list[float]:
        msg = self.latest()
        return [float(msg.motor_state[i].q) for i in range(NUM_MOTORS)]

    def rpy(self) -> tuple[float, float, float]:
        """Orientación del cuerpo calculada desde el cuaternión de la IMU."""

        w, x, y, z = self.latest().imu_state.quaternion
        return quaternion_to_rpy(w, x, y, z)

    def mode_machine(self) -> int:
        return int(self.latest().mode_machine)


class LowCmdWriter:
    """Arma, firma con CRC y publica mensajes LowCmd_ en un tópico."""

    def __init__(self, topic: str) -> None:
        from unitree_sdk2py.core.channel import ChannelPublisher
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
        from unitree_sdk2py.utils.crc import CRC

        self.msg = unitree_hg_msg_dds__LowCmd_()
        self._crc = CRC()
        self._publisher = ChannelPublisher(topic, LowCmd_)
        self._publisher.Init()

    def set_motor(self, index: int, q: float, kp: float, kd: float) -> None:
        motor = self.msg.motor_cmd[index]
        motor.mode = 1  # 1: habilitado
        motor.q = float(q)
        motor.dq = 0.0
        motor.tau = 0.0
        motor.kp = float(kp)
        motor.kd = float(kd)

    def set_all(
        self,
        targets: Sequence[float],
        kp: Sequence[float],
        kd: Sequence[float],
    ) -> None:
        for index in range(NUM_MOTORS):
            self.set_motor(index, targets[index], kp[index], kd[index])

    def set_damping(self) -> None:
        for index in range(NUM_MOTORS):
            self.set_motor(index, 0.0, 0.0, DAMPING_KD)

    def send(self, mode_machine: int | None = None) -> None:
        self.msg.mode_pr = 0  # articulaciones de tobillo en modo pitch/roll
        if mode_machine is not None:
            self.msg.mode_machine = mode_machine
        self.msg.crc = self._crc.Crc(self.msg)
        self._publisher.Write(self.msg)


def confirm_robot(description: str) -> None:
    """Pide una confirmación explícita antes de mover el robot real."""

    print()
    print("=" * 70)
    print("ATENCIÓN: se van a enviar comandos al ROBOT REAL.")
    print(description)
    print("Verificá que no haya personas ni obstáculos cerca y tené a mano el")
    print("control remoto para pasar a modo amortiguado (damping).")
    print("=" * 70)
    answer = input("Escribí SI para continuar: ").strip()
    if answer != "SI":
        raise RuntimeError("Operación cancelada por el usuario.")
