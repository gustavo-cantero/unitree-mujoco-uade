# Unitree G1: sentadilla y saludo en MuJoCo

Proyecto universitario completo y autónomo para mostrar una rutina sencilla
del robot bípedo Unitree G1. El robot hace una sentadilla, vuelve a levantarse,
saluda dos veces con el brazo derecho y regresa a la postura inicial.

Está preparado para Windows y para una persona que recién recibe el proyecto.
No requiere el SDK de Unitree, CycloneDDS ni una conexión de red: solamente
Python, NumPy y MuJoCo.

## La forma más fácil de empezar

1. Hacé doble clic en `instalar.bat` una sola vez.
2. Cuando termine, hacé doble clic en `verificar.bat`.
3. Si todo aparece como `[OK]`, hacé doble clic en `iniciar_demo.bat`.

La ventana de MuJoCo se abre, ejecuta la rutina y se cierra al finalizar.

## Instalación manual

Desde PowerShell, dentro de esta carpeta:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

El modo editable (`-e`) permite cambiar el código dentro de `src` sin tener que
reinstalarlo después de cada modificación.

## Comandos útiles

```powershell
# Comprobar modelo, articulaciones y límites sin abrir una ventana
.\.venv\Scripts\python.exe -m uade_mujoco --check

# Ejecutar toda la rutina sin ventana y generar el CSV
.\.venv\Scripts\python.exe -m uade_mujoco --headless

# Abrir la demostración visual
.\.venv\Scripts\python.exe -m uade_mujoco

# Repetir la rutina tres veces
.\.venv\Scripts\python.exe -m uade_mujoco --repetir 3

# Ejecutar las pruebas automáticas
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Qué genera

Después de ejecutar la rutina se crea
`resultados/trayectoria_g1.csv`. El archivo contiene:

- instante y fase de la rutina;
- altura de la base;
- ángulos objetivo y medidos de ambas rodillas;
- ángulos del hombro, codo y muñeca derechos.

## Cómo está organizado

```text
UADE-Mujoco/
├── src/uade_mujoco/          código principal del proyecto
│   ├── cli.py                argumentos y coordinación general
│   ├── config.py             posturas y tiempos que el alumno puede cambiar
│   ├── trajectory.py         interpolación de mínimo tirón
│   ├── model.py              carga y validación de MuJoCo
│   ├── runner.py             ejecución visual y sin ventana
│   ├── reporting.py          exportación del CSV
│   └── paths.py              rutas centralizadas
├── tests/                    pruebas automáticas
├── docs/                     documentación paso a paso
├── models/g1/                modelo oficial y mallas del G1
├── resultados/               archivos producidos al ejecutar
├── pyproject.toml            metadatos y dependencias
├── instalar.bat              crea el entorno e instala dependencias
├── verificar.bat             corre validaciones y pruebas
└── iniciar_demo.bat          abre la demostración
```

Documentación recomendada:

- [Empezar desde cero](docs/EMPEZAR_DESDE_CERO.md)
- [Arquitectura del proyecto](docs/ARQUITECTURA.md)
- [Cómo modificar los movimientos](docs/CAMBIAR_MOVIMIENTOS.md)
- [Guía para la presentación](docs/GUIA_PRESENTACION.md)

## Idea técnica

Cada fase tiene una postura objetivo. La transición usa el polinomio de mínimo
tirón:

```text
s(u) = 10u³ - 15u⁴ + 6u⁵,   con 0 <= u <= 1
```

Esto evita arrancar o frenar de golpe. Antes de mostrar la rutina, el programa
comprueba que el modelo tenga 29 actuadores, que existan las articulaciones y
que todos los valores estén dentro de sus límites MJCF.

## Alcance y limitación

Esta es una **demostración cinemática educativa**. La gravedad se desactiva y
la base se mantiene controlada para concentrar el trabajo en la generación de
trayectorias. No es un controlador de equilibrio, no es sim-to-real y no debe
usarse para enviar comandos a un robot físico.

Como ampliación futura se puede implementar un controlador PD de torque, un
soporte virtual y, finalmente, un controlador de equilibrio.

## Modelo y licencia

El MJCF y las mallas provienen del repositorio oficial `unitree_mujoco` de
Unitree Robotics. Su licencia BSD de 3 cláusulas está incluida en
`THIRD_PARTY_LICENSE_UNITREE.txt`.
