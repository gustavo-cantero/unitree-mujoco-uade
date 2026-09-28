"""Entrada sencilla para quien prefiere ejecutar un archivo directamente."""

try:
    from uade_mujoco.cli import main
except ImportError as error:
    raise SystemExit(
        "El proyecto todavía no está instalado. Ejecutá instalar.bat una vez "
        "y luego volvé a abrir iniciar_demo.bat."
    ) from error


if __name__ == "__main__":
    raise SystemExit(main())
