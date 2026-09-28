"""Rutas del proyecto centralizadas en un único lugar."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "g1" / "scene_29dof.xml"
DEFAULT_CSV_PATH = PROJECT_ROOT / "resultados" / "trayectoria_g1.csv"
