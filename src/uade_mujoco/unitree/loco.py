"""Sentadilla con el controlador de alto nivel de Unitree (LocoClient).

En lugar de mover cada articulación, se le pide al controlador del robot que
baje y suba la altura de pie; él se ocupa del equilibrio. Solo funciona en el
robot real: el simulador no implementa el servicio "sport".
"""

from __future__ import annotations

import time


def run_loco_squat(hold_s: float) -> None:
    from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

    client = LocoClient()
    client.SetTimeout(10.0)
    client.Init()

    print("[Fase] Sentadilla: bajando (LowStand)")
    client.LowStand()
    time.sleep(hold_s)
    print("[Fase] Sentadilla: subiendo (HighStand)")
    client.HighStand()
    time.sleep(hold_s)
    print("[OK] Sentadilla terminada")
