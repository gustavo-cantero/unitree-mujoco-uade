# Arquitectura del proyecto

El flujo principal es pequeño y deliberadamente lineal:

```text
cli.py
  ├─ lee los argumentos
  ├─ config.py crea las fases
  ├─ model.py carga y valida el G1
  └─ runner.py ejecuta cada muestra
       ├─ trajectory.py interpola las posturas
       ├─ model.py aplica la muestra a MuJoCo
       │  (o physics.py la persigue con torques si se usa --fisica)
       └─ reporting.py registra el CSV
```

## Módulos

### `config.py`

Contiene los únicos valores que normalmente modifica un alumno: posturas,
duraciones y articulaciones incluidas en el CSV.

### `trajectory.py`

No conoce MuJoCo. Convierte una lista de fases en muestras temporales usando la
interpolación de mínimo tirón. Se puede probar de manera aislada.

### `model.py`

Es la frontera con MuJoCo. Carga el MJCF, busca direcciones articulares,
comprueba límites y aplica cada postura. Al aplicarla calcula la altura de
la base para que los pies queden apoyados justo sobre el suelo.

### `runner.py`

Tiene dos modos que consumen exactamente la misma trayectoria: visual y sin
ventana. Esto permite verificar la lógica aunque una computadora no tenga un
entorno gráfico disponible.

### `physics.py`

Modo opcional `--fisica`. Activa la gravedad y, en lugar de asignar cada
postura, calcula en cada paso de simulación el torque de un control PD por
motor y deja que MuJoCo integre la dinámica. Las ganancias están al comienzo del
archivo: con rigideces bajas en las piernas el robot se cae en la sentadilla,
porque no hay un controlador de equilibrio.

### `reporting.py`

Convierte las muestras ejecutadas en filas de CSV. Está separado para que una
futura ampliación pueda agregar gráficos sin modificar el simulador.

## Decisión cinemática

Un G1 real necesita equilibrio activo. Implementarlo correctamente implicaría
control de torque, estimación del centro de masa y realimentación. Este proyecto
mantiene la base y asigna las posiciones para que el alcance sea apropiado para
una primera entrega y para que la demostración sea reproducible en Windows.
