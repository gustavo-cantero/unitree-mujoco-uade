"""Línea de comandos para el G1 simulado o real.

    python -m uade_mujoco.unitree simulador   [--arnes] [--sin-ventana]
    python -m uade_mujoco.unitree bajo-nivel  [--rutina saludo] [--rigidez alta]
    python -m uade_mujoco.unitree saludo      [--robot --interfaz "Ethernet 2"]
    python -m uade_mujoco.unitree sentadilla  --interfaz "Ethernet 2"
    python -m uade_mujoco.unitree rutina      --interfaz "Ethernet 2"

Sin --robot todo se conecta al simulador (dominio DDS 1). Con --robot se usa
el dominio 0 y la interfaz de red conectada al G1.
"""

from __future__ import annotations

import argparse

from .dds import ROBOT_DOMAIN, SIM_DOMAIN, confirm_robot, init_dds


def _add_target(parser: argparse.ArgumentParser, robot_only: bool = False) -> None:
    if not robot_only:
        parser.add_argument(
            "--robot",
            action="store_true",
            help="envía los comandos al robot real en lugar del simulador",
        )
    parser.add_argument(
        "--interfaz",
        required=robot_only,
        help="adaptador de red conectado al robot, por ejemplo 'Ethernet 2'",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m uade_mujoco.unitree",
        description="Rutina del G1 a través del SDK de Unitree (simulador o robot).",
    )
    commands = parser.add_subparsers(dest="comando", required=True)

    sim = commands.add_parser("simulador", help="G1 simulado que habla DDS")
    sim.add_argument("--arnes", action="store_true", help="sostiene el torso, como un soporte")
    sim.add_argument("--sin-ventana", action="store_true", help="no abre la ventana de MuJoCo")
    sim.add_argument("--duracion", type=float, help="segundos hasta cerrar solo")
    sim.add_argument("--interfaz", help="interfaz de red (por defecto automática)")

    low = commands.add_parser(
        "bajo-nivel", help="rutina motor por motor por rt/lowcmd (robot colgado)"
    )
    low.add_argument("--rutina", choices=("completa", "saludo"), default="completa")
    low.add_argument(
        "--rigidez",
        choices=("oficial", "alta"),
        default="oficial",
        help="'oficial' = ejemplo de Unitree; 'alta' = la de --fisica (solo simulador)",
    )
    _add_target(low)

    wave = commands.add_parser("saludo", help="saludo por rt/arm_sdk")
    _add_target(wave)

    squat = commands.add_parser("sentadilla", help="sentadilla con LocoClient (robot)")
    squat.add_argument("--espera", type=float, default=3.0, help="segundos abajo y arriba")
    _add_target(squat, robot_only=True)

    routine = commands.add_parser(
        "rutina", help="sentadilla con LocoClient y saludo con arm_sdk (robot)"
    )
    routine.add_argument("--espera", type=float, default=3.0, help="segundos abajo y arriba")
    _add_target(routine, robot_only=True)

    return parser.parse_args()


def _run() -> int:
    args = parse_args()
    real_robot = args.comando in ("sentadilla", "rutina") or getattr(args, "robot", False)
    if real_robot and not args.interfaz:
        raise ValueError("Con --robot hay que indicar --interfaz.")

    if args.comando == "simulador":
        from .simulator import G1Simulator

        simulator = G1Simulator(harness=args.arnes)
        init_dds(SIM_DOMAIN, args.interfaz)
        simulator.run(show_window=not args.sin_ventana, duration=args.duracion)
        return 0

    if args.comando == "bajo-nivel" and real_robot and args.rigidez == "alta":
        raise ValueError(
            "La rigidez 'alta' es solo para el simulador: en el robot real puede "
            "provocar vibraciones y movimientos bruscos."
        )

    init_dds(ROBOT_DOMAIN if real_robot else SIM_DOMAIN, args.interfaz)
    print(f"[OK] DDS en el dominio {ROBOT_DOMAIN if real_robot else SIM_DOMAIN}"
          f" ({'robot real' if real_robot else 'simulador'})")

    if args.comando == "bajo-nivel":
        from .low_level import run_low_level

        if real_robot:
            confirm_robot(
                "Control de BAJO NIVEL: se apaga el equilibrio de Unitree.\n"
                "El robot DEBE estar colgado de un soporte."
            )
        run_low_level(args.rutina, args.rigidez, real_robot)
    elif args.comando == "saludo":
        from .arm_wave import run_arm_wave

        if real_robot:
            confirm_robot(
                "Saludo por arm_sdk: el robot debe estar de pie con su\n"
                "controlador normal activo; solo se moverán cintura y brazos."
            )
        run_arm_wave()
    else:
        from .loco import run_loco_squat

        confirm_robot(
            "Sentadilla con LocoClient: el robot debe estar de pie con su\n"
            "controlador normal activo y espacio libre alrededor."
        )
        run_loco_squat(args.espera)
        if args.comando == "rutina":
            from .arm_wave import run_arm_wave

            run_arm_wave()
    return 0


def main() -> int:
    try:
        return _run()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"[ERROR] {error}")
        return 1
