"""Bucles de ejecución con y sin ventana."""

from __future__ import annotations

import time
from typing import Iterable, Mapping

import mujoco

from .model import apply_frame
from .physics import PdController
from .reporting import csv_row
from .trajectory import Frame, Pose, Stage, iter_frames, total_duration


def _advance(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    frame: Frame,
    physics: PdController | None,
) -> None:
    if physics is None:
        apply_frame(model, data, addresses, frame)
    else:
        physics.advance(frame)


def run_headless(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    sequence: list[Stage],
    initial_pose: Pose,
    joint_names: Iterable[str],
    csv_joints: Iterable[str],
    fps: int,
    repeats: int,
    physics: PdController | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    duration = total_duration(sequence)
    for cycle in range(1, repeats + 1):
        last_phase = ""
        for frame in iter_frames(sequence, initial_pose, joint_names, fps):
            if frame.phase != last_phase:
                print(f"[Ciclo {cycle}] {frame.phase}")
                last_phase = frame.phase
            _advance(model, data, addresses, frame, physics)
            rows.append(
                csv_row(
                    cycle,
                    (cycle - 1) * duration,
                    frame,
                    data,
                    addresses,
                    csv_joints,
                )
            )
    return rows


def run_visual(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    sequence: list[Stage],
    initial_pose: Pose,
    joint_names: Iterable[str],
    csv_joints: Iterable[str],
    fps: int,
    repeats: int,
    physics: PdController | None = None,
) -> list[dict[str, object]]:
    import mujoco.viewer

    rows: list[dict[str, object]] = []
    duration = total_duration(sequence)
    with mujoco.viewer.launch_passive(
        model, data, show_left_ui=False, show_right_ui=False
    ) as viewer:
        viewer.cam.distance = 2.4
        viewer.cam.azimuth = 145
        viewer.cam.elevation = -18
        viewer.cam.lookat[:] = [0.0, 0.0, 0.70]

        for cycle in range(1, repeats + 1):
            last_phase = ""
            for frame in iter_frames(sequence, initial_pose, joint_names, fps):
                if not viewer.is_running():
                    return rows
                started = time.perf_counter()
                if frame.phase != last_phase:
                    print(f"[Ciclo {cycle}] {frame.phase}")
                    last_phase = frame.phase
                _advance(model, data, addresses, frame, physics)
                viewer.sync()
                rows.append(
                    csv_row(
                        cycle,
                        (cycle - 1) * duration,
                        frame,
                        data,
                        addresses,
                        csv_joints,
                    )
                )
                remaining = (1.0 / fps) - (time.perf_counter() - started)
                if remaining > 0:
                    time.sleep(remaining)
    return rows
