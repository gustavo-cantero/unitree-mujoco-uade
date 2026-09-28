"""Interfaz de línea de comandos del proyecto."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import CSV_JOINTS, JOINT_NAMES, build_sequence, initial_pose
from .model import load_model, validate_project
from .paths import DEFAULT_CSV_PATH, DEFAULT_MODEL_PATH
from .reporting import write_csv
from .runner import run_headless, run_visual
from .trajectory import total_duration


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sentadilla y saludo del Unitree G1 en MuJoCo."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="valida el modelo y la trayectoria sin ejecutar la rutina",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="ejecuta la rutina sin abrir la ventana de MuJoCo",
    )
    parser.add_argument("--fps", type=int, default=60, help="fotogramas por segundo")
    parser.add_argument(
        "--repetir", type=int, default=1, help="cantidad de veces que se repite"
    )
    parser.add_argument(
        "--modelo", type=Path, default=DEFAULT_MODEL_PATH, help="escena MJCF del G1"
    )
    parser.add_argument(
        "--salida", type=Path, default=DEFAULT_CSV_PATH, help="archivo CSV de salida"
    )
    return parser.parse_args()


def _run() -> int:
    args = parse_args()
    if args.fps < 10 or args.fps > 240:
        raise ValueError("--fps debe estar entre 10 y 240.")
    if args.repetir < 1:
        raise ValueError("--repetir debe ser al menos 1.")

    model, data = load_model(args.modelo.resolve())
    sequence = build_sequence()
    addresses = validate_project(model, sequence, JOINT_NAMES)
    duration = total_duration(sequence)

    print(f"[OK] Modelo G1 cargado: nq={model.nq}, nv={model.nv}, nu={model.nu}")
    print(f"[OK] {len(sequence)} fases, {duration:.2f} segundos por ciclo")
    print("[OK] Todos los objetivos respetan los límites articulares")

    if args.check:
        return 0

    common = (
        model,
        data,
        addresses,
        sequence,
        initial_pose(),
        JOINT_NAMES,
        CSV_JOINTS,
        args.fps,
        args.repetir,
    )
    rows = run_headless(*common) if args.headless else run_visual(*common)
    if rows:
        output = args.salida.resolve()
        write_csv(output, rows)
        print(f"[OK] Trayectoria guardada en: {output}")
    print("[OK] Demostración finalizada")
    return 0


def main() -> int:
    try:
        return _run()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"[ERROR] {error}")
        return 1
