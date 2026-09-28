"""Exportación de resultados para acompañar la presentación."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

import mujoco

from .trajectory import Frame


def csv_row(
    cycle: int,
    time_offset: float,
    frame: Frame,
    data: mujoco.MjData,
    addresses: Mapping[str, int],
    csv_joints: Iterable[str],
) -> dict[str, object]:
    row: dict[str, object] = {
        "ciclo": cycle,
        "tiempo_s": f"{time_offset + frame.time_s:.4f}",
        "fase": frame.phase,
        "base_z_m": f"{data.qpos[2]:.6f}",
    }
    for name in csv_joints:
        short_name = name.removesuffix("_joint")
        row[f"{short_name}_objetivo_rad"] = f"{frame.pose.joints[name]:.6f}"
        row[f"{short_name}_medido_rad"] = f"{data.qpos[addresses[name]]:.6f}"
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
