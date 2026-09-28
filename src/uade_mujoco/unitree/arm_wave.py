"""Saludo con el brazo derecho a través de rt/arm_sdk.

El controlador de Unitree sigue manteniendo el equilibrio; este programa solo
toma el control de cintura y brazos, mezclándose con un peso que sube de 0 a 1
al empezar y baja de 1 a 0 al terminar. Es el primer paso recomendado en el
robot real.
"""

from __future__ import annotations

import time

from ..config import RIGHT_ARM_JOINTS, wave_stages
from ..trajectory import Pose, Stage, iter_frames
from .dds import TOPIC_ARM_SDK, LowCmdWriter, LowStateReader, Ticker
from .g1 import (
    ARM_SDK_JOINTS,
    ARM_SDK_KD,
    ARM_SDK_KP,
    ARM_SDK_WEIGHT_INDEX,
    MOTOR_INDEX,
    MOTOR_JOINTS,
)

CONTROL_DT = 0.02  # 50 Hz, como el ejemplo oficial de arm_sdk
BLEND_S = 1.0
LOWER_ARM_S = 1.2


def run_arm_wave() -> None:
    state = LowStateReader()
    state.wait_first()
    writer = LowCmdWriter(TOPIC_ARM_SDK)
    ticker = Ticker(CONTROL_DT)

    start_q = state.joint_positions()
    start_pose = Pose({name: start_q[MOTOR_INDEX[name]] for name in RIGHT_ARM_JOINTS})
    stages = [*wave_stages(), Stage("Saludo: bajando el brazo", LOWER_ARM_S, start_pose)]

    def send(right_arm: dict[str, float], weight: float) -> None:
        for index in ARM_SDK_JOINTS:
            name = MOTOR_JOINTS[index]
            # Lo que no es el brazo derecho se mantiene donde estaba al empezar.
            target = right_arm.get(name, start_q[index])
            writer.set_motor(index, target, ARM_SDK_KP, ARM_SDK_KD)
        writer.msg.motor_cmd[ARM_SDK_WEIGHT_INDEX].q = weight
        writer.send()
        ticker.wait()

    blend_ticks = round(BLEND_S / CONTROL_DT)
    weight = 0.0
    try:
        print("[Fase] Tomando el control de los brazos (peso de 0 a 1)")
        for step in range(1, blend_ticks + 1):
            weight = step / blend_ticks
            send({}, weight)

        phase = ""
        for frame in iter_frames(stages, start_pose, RIGHT_ARM_JOINTS, fps=round(1 / CONTROL_DT)):
            if frame.phase != phase:
                print(f"[Fase] {frame.phase}")
                phase = frame.phase
            send(dict(frame.pose.joints), 1.0)
    except KeyboardInterrupt:
        print("[AVISO] Interrumpido con Ctrl+C: devolviendo el control.")
    finally:
        print("[Fase] Devolviendo el control a Unitree (peso de 1 a 0)")
        current = weight
        for step in range(1, blend_ticks + 1):
            send({}, current * (1.0 - step / blend_ticks))
        time.sleep(0.1)
    print("[OK] Saludo terminado")
