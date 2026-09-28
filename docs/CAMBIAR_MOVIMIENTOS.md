# Cómo modificar los movimientos

Todos los cambios normales se hacen en:

```text
src/uade_mujoco/config.py
```

## Cambiar la profundidad de la sentadilla

Dentro de `build_sequence`, buscá la variable `squat`. Los valores principales
son la cadera (`*_hip_pitch_joint`), la rodilla (`*_knee_joint`) y el tobillo
(`*_ankle_pitch_joint`) de cada pierna.

- Una rodilla más positiva se flexiona más.
- La altura del cuerpo no se escribe a mano: el programa la calcula en cada
  instante para que los pies queden apoyados en el suelo.
- Para que la planta del pie quede horizontal, la suma
  `hip_pitch + knee + ankle_pitch` debe dar `0`
  (por ejemplo `-0.55 + 1.05 - 0.50 = 0`).
- Las dos piernas deben conservar valores simétricos.

## Cambiar el saludo

Buscá `arm_up_values`, `wave_left` y `wave_right`. En `arm_up_values` el brazo
queda al costado, con el antebrazo vertical y la palma hacia adelante.

La oscilación usa `right_elbow_joint` y `right_wrist_pitch_joint`: en esa
postura ambos giran alrededor del eje perpendicular a la palma, así que la mano
se balancea de lado a lado. `right_wrist_yaw_joint` movería la mano hacia
adelante y atrás, como un abanico, por eso no se usa para saludar.

## Cambiar la duración

Cada objeto `Stage` recibe nombre, duración en segundos y postura objetivo:

```python
Stage("Sentadilla: bajando", 1.60, squat)
```

Subir `1.60` hace la transición más lenta.

## Comprobar un cambio

Ejecutá siempre:

```powershell
.\.venv\Scripts\python.exe -m uade_mujoco --check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La validación evita enviar al modelo un ángulo que exceda sus límites.
