# Del simulador al robot físico

Esta guía lleva la rutina del proyecto al Unitree G1 real en etapas, de menor
a mayor riesgo. Cada etapa se prueba primero en el simulador.

| Etapa | Comando | Dónde | Qué mueve |
|---|---|---|---|
| 1 | `--fisica` | MuJoCo, sin SDK | todo el cuerpo con gravedad |
| 2 | `unitree.bat bajo-nivel` | simulador DDS | todo el cuerpo por `rt/lowcmd` |
| 3 | `unitree.bat saludo` | simulador DDS y robot | brazos por `rt/arm_sdk` |
| 4 | `unitree.bat sentadilla` | solo robot | altura de pie con `LocoClient` |
| 5 | `unitree.bat rutina` | solo robot | etapa 4 y después etapa 3 |

## Preparación

El SDK de Unitree (`unitree_sdk2_python`) necesita `cyclonedds==0.10.2`, que en
Windows solo se instala con **Python 3.10**. Por eso se usa un segundo entorno,
`.venv-robot`, separado del principal.

1. Cloná `unitree_sdk2_python` en la misma carpeta que contiene este proyecto
   (o indicá su ruta en la variable de entorno `UNITREE_SDK2_PYTHON`).
2. Ejecutá `instalar_robot.bat`. Usa Python 3.10 si está instalado y, si no,
   lo descarga con [uv](https://docs.astral.sh/uv/).

Todos los comandos se ejecutan con `unitree.bat <comando>`. Sin argumentos
muestra la ayuda. La carpeta [pruebas](../pruebas/README.md) tiene un `.bat`
por cada prueba, que se ejecuta con doble clic.

## Etapa 1: física en MuJoCo

```powershell
.\.venv\Scripts\python.exe -m uade_mujoco --fisica
```

Activa la gravedad y mueve cada motor con un control PD. Ver el README y
`src/uade_mujoco/physics.py`.

## Etapa 2: rutina completa por DDS contra el simulador

Abrí dos terminales. En la primera:

```powershell
.\unitree.bat simulador --arnes
```

En la segunda:

```powershell
.\unitree.bat bajo-nivel
```

El simulador publica `rt/lowstate` y aplica cada `rt/lowcmd` igual que el
puente oficial de `unitree_mujoco`. El programa de control es el mismo que se
usaría con el robot: lee el estado, lleva los motores suavemente desde la
posición medida a la inicial y envía la rutina.

Qué se observa:

| Simulador | `bajo-nivel` | Resultado |
|---|---|---|
| sin arnés | `--rigidez oficial` (por defecto) | se cae: no hay equilibrio |
| `--arnes` | `--rigidez oficial` | completa la rutina colgado |
| sin arnés | `--rigidez alta` | completa la rutina, con motores irrealmente rígidos |

Las rigideces "oficiales" son las del ejemplo `g1_low_level_example.py` de
Unitree. El registro queda en `resultados/unitree_bajo_nivel.csv`.

Con `--rutina saludo` se envía solo el saludo.

## Etapa 3: saludo con `arm_sdk`

Es **la primera prueba recomendada en el robot real**. El controlador de
Unitree sigue manteniendo el equilibrio y este programa solo toma cintura y
brazos, con un peso que sube de 0 a 1 al empezar y baja de 1 a 0 al terminar.

En el simulador (sin arnés: su controlador interno lo mantiene de pie):

```powershell
.\unitree.bat simulador
.\unitree.bat saludo
```

En el robot:

```powershell
.\unitree.bat saludo --robot --interfaz "Ethernet 2"
```

## Etapa 4: sentadilla con `LocoClient`

La sentadilla articulación por articulación necesita un controlador de
equilibrio. En su lugar se le pide al controlador de Unitree que baje
(`LowStand`) y vuelva a subir (`HighStand`) su altura de pie. El simulador no
implementa este servicio, así que solo funciona con el robot:

```powershell
.\unitree.bat sentadilla --interfaz "Ethernet 2"
```

## Etapa 5: rutina en el robot

```powershell
.\unitree.bat rutina --interfaz "Ethernet 2"
```

Hace la etapa 4 y después la 3.

## Conexión con el robot

- Conectá la PC al G1 por cable Ethernet y configurá el adaptador con una IP
  fija en la red del robot (en la documentación de Unitree: `192.168.123.x`,
  máscara `255.255.255.0`, sin repetir la del robot).
- `--interfaz` es el **nombre del adaptador** tal como lo muestra
  `Get-NetAdapter` en PowerShell, por ejemplo `"Ethernet 2"`. En Windows no
  sirve la dirección IP.
- Con `--robot` se usa el dominio DDS 0; el simulador usa el dominio 1, así que
  no se mezclan.

> El SDK de Unitree está pensado para Linux. En Windows este proyecto corrige
> un problema del SDK al indicar la interfaz, y la comunicación se probó con el
> simulador, pero no con un robot real. Si falla, probá desde Ubuntu.

## Seguridad

- Todo comando que va al robot pide escribir `SI` antes de moverlo.
- `bajo-nivel --robot` apaga el equilibrio de Unitree: **solo con el robot
  colgado de un soporte**. Al terminar, o ante Ctrl+C o una inclinación mayor
  a 45°, pasa a modo amortiguado.
- `--rigidez alta` está bloqueada para el robot real.
- Para `saludo`, `sentadilla` y `rutina` el robot debe estar de pie con su
  controlador normal activo, con espacio libre alrededor.
- Tené el control remoto a mano para pasar a modo amortiguado.
- Los modos de operación y los pasos exactos dependen de la versión de
  firmware: seguí siempre la documentación de Unitree para tu robot.
