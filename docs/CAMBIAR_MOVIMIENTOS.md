# Cómo modificar los movimientos

Todos los cambios normales se hacen en:

```text
src/uade_mujoco/config.py
```

## Cambiar la profundidad de la sentadilla

Dentro de `build_sequence`, buscá la variable `squat`. Los valores principales
son `left_knee_joint`, `right_knee_joint` y `base_z_offset`.

- Una rodilla más positiva se flexiona más.
- Un `base_z_offset` más negativo baja el cuerpo.
- Las dos piernas deben conservar valores simétricos.

## Cambiar el saludo

Buscá `arm_up_values`, `wave_left` y `wave_right`. La oscilación visible usa
principalmente `right_wrist_yaw_joint` y `right_shoulder_yaw_joint`.

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
