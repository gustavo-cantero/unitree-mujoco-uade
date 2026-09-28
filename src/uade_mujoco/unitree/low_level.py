"""Rutina completa enviada motor por motor por rt/lowcmd.

Es el equivalente de `--fisica` pero a través de DDS: el programa calcula la
trayectoria y cada motor recibe (q, kp, kd). En el robot real esto apaga el
controlador de equilibrio de Unitree, así que solo debe hacerse con el robot
colgado de un soporte.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

from ..config import (
    CSV_JOINTS,
    JOINT_NAMES,
    build_sequence,
    initial_pose,
    pose_with,
    wave_stages,
)
from ..paths import PROJECT_ROOT
from ..physics import gains_for
from ..reporting import write_csv
from ..trajectory import Stage, iter_frames, minimum_jerk
from .dds import TOPIC_LOWCMD, LowCmdWriter, LowStateReader, Ticker
from .g1 import MOTOR_INDEX, MOTOR_JOINTS, OFFICIAL_KD, OFFICIAL_KP, targets_from_joints

# 500 Hz en el robot, como el ejemplo oficial. El simulador en Python no alcanza
# a procesar tantos mensajes sin atrasarse, así que con él se usan 200 Hz.
ROBOT_CONTROL_DT = 0.002
SIM_CONTROL_DT = 0.005
RAMP_S = 3.0
HOLD_S = 2.0
DAMPING_S = 1.0
FALL_ANGLE_RAD = math.radians(45.0)
CSV_PERIOD_S = 0.02
DEFAULT_CSV = PROJECT_ROOT / "resultados" / "unitree_bajo_nivel.csv"


def _stages(routine: str) -> list[Stage]:
    if routine == "completa":
        return build_sequence()
    return [
        Stage("Postura inicial", 1.00, pose_with()),
        *wave_stages(),
        Stage("Volviendo a postura neutra", 0.90, pose_with()),
    ]


def _gains(stiffness: str) -> tuple[list[float], list[float]]:
    if stiffness == "oficial":
        return list(OFFICIAL_KP), list(OFFICIAL_KD)
    gains = [gains_for(name) for name in MOTOR_JOINTS]
    return [kp for kp, _ in gains], [kd for _, kd in gains]


def run_low_level(
    routine: str,
    stiffness: str,
    real_robot: bool,
    csv_path: Path = DEFAULT_CSV,
) -> None:
    if real_robot:
        _release_motion_mode()

    state = LowStateReader()
    state.wait_first()
    writer = LowCmdWriter(TOPIC_LOWCMD)
    kp, kd = _gains(stiffness)
    mode_machine = state.mode_machine()
    knee_kp = kp[MOTOR_INDEX["left_knee_joint"]]
    print(f"[OK] Estado recibido. Rigidez '{stiffness}' (kp rodilla = {knee_kp:.0f})")

    start_q = state.joint_positions()
    first = targets_from_joints(initial_pose().joints)
    stages = _stages(routine)
    control_dt = ROBOT_CONTROL_DT if real_robot else SIM_CONTROL_DT
    csv_every = max(1, round(CSV_PERIOD_S / control_dt))
    frames = iter_frames(stages, initial_pose(), JOINT_NAMES, fps=round(1 / control_dt))

    rows: list[dict[str, object]] = []
    ticker = Ticker(control_dt)
    tick = 0
    phase = ""
    fell = False

    def send(targets: list[float], label: str) -> bool:
        nonlocal tick
        writer.set_all(targets, kp, kd)
        writer.send(mode_machine)
        roll, pitch, _ = state.rpy()
        if tick % csv_every == 0:
            q = state.joint_positions()
            row: dict[str, object] = {
                "tiempo_s": f"{tick * control_dt - RAMP_S:.3f}",
                "fase": label,
                "roll_rad": f"{roll:.4f}",
                "pitch_rad": f"{pitch:.4f}",
            }
            for name in CSV_JOINTS:
                short = name.removesuffix("_joint")
                row[f"{short}_objetivo_rad"] = f"{targets[MOTOR_INDEX[name]]:.5f}"
                row[f"{short}_medido_rad"] = f"{q[MOTOR_INDEX[name]]:.5f}"
            rows.append(row)
        tick += 1
        ticker.wait()
        return abs(roll) < FALL_ANGLE_RAD and abs(pitch) < FALL_ANGLE_RAD

    try:
        print("[Fase] Llevando los motores desde la posición medida a la inicial")
        ramp_ticks = round(RAMP_S / control_dt)
        for step in range(1, ramp_ticks + 1):
            blend = minimum_jerk(step / ramp_ticks)
            targets = [a + (b - a) * blend for a, b in zip(start_q, first)]
            if not send(targets, "Rampa inicial"):
                fell = True
                break

        targets = first
        if not fell:
            for frame in frames:
                if frame.phase != phase:
                    print(f"[Fase] {frame.phase}")
                    phase = frame.phase
                targets = targets_from_joints(frame.pose.joints)
                if not send(targets, frame.phase):
                    fell = True
                    break

        if fell:
            print("[AVISO] El robot se inclinó más de 45°: se interrumpe la rutina.")
        else:
            print(f"[Fase] Manteniendo la postura final {HOLD_S:.0f} s")
            for _ in range(round(HOLD_S / control_dt)):
                send(targets, "Fin")
    except KeyboardInterrupt:
        print("[AVISO] Interrumpido con Ctrl+C.")
    finally:
        if real_robot:
            print("[Fase] Pasando a modo amortiguado")
            end = time.perf_counter() + DAMPING_S
            while time.perf_counter() < end:
                writer.set_damping()
                writer.send(mode_machine)
                ticker.wait()
        if rows:
            write_csv(csv_path, rows)
            print(f"[OK] Registro guardado en: {csv_path}")

    if fell:
        raise RuntimeError(
            "El robot se cayó. Con rigideces realistas hace falta un controlador "
            "de equilibrio (o el arnés del simulador)."
        )


def _release_motion_mode() -> None:
    """Apaga el controlador de Unitree para poder mandar rt/lowcmd."""

    from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import (
        MotionSwitcherClient,
    )

    client = MotionSwitcherClient()
    client.SetTimeout(5.0)
    client.Init()
    for _ in range(10):
        code, result = client.CheckMode()
        if code != 0:
            raise RuntimeError(f"MotionSwitcher respondió con el código {code}.")
        if not result or not result.get("name"):
            print("[OK] Controlador de Unitree liberado")
            return
        print(f"[..] Liberando el modo '{result['name']}'")
        client.ReleaseMode()
        time.sleep(1.0)
    raise RuntimeError("No se pudo liberar el controlador de Unitree.")
