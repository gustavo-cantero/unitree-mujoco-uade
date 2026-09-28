# Pruebas paso a paso

Cada `.bat` de esta carpeta es una prueba que se ejecuta con doble clic. Están
numeradas en el orden recomendado: primero todo en la PC y, recién cuando eso
funciona, en el robot.

| # | Archivo | Dónde | Qué comprueba |
|---|---|---|---|
| 1 | `01_fisica_mujoco.bat` | PC | la rutina con gravedad en MuJoCo |
| 2 | `02_sim_bajo_nivel_con_arnes.bat` | PC | la rutina completa por DDS, robot colgado |
| 3 | `03_sim_bajo_nivel_sin_arnes.bat` | PC | por qué hace falta equilibrio: se cae |
| 4 | `04_sim_bajo_nivel_rigidez_alta.bat` | PC | la rutina completa con motores muy rígidos |
| 5 | `05_sim_saludo_arm_sdk.bat` | PC | el saludo por `arm_sdk` |
| 6 | `06_robot_saludo.bat` | robot | el saludo por `arm_sdk` |
| 7 | `07_robot_sentadilla.bat` | robot | la sentadilla con `LocoClient` |
| 8 | `08_robot_rutina.bat` | robot | sentadilla y saludo |
| 9 | `09_robot_bajo_nivel_colgado.bat` | robot colgado | la rutina completa por `rt/lowcmd` |

## Antes de empezar

- La prueba 1 necesita `instalar.bat`.
- Las pruebas 2 a 9 necesitan `instalar_robot.bat`, que crea `.venv-robot` con
  Python 3.10 y el SDK de Unitree (`unitree_sdk2_python`, clonado junto a esta
  carpeta del proyecto).
- Las pruebas 2 a 5 abren el simulador en una segunda ventana, que se cierra
  sola. **Esperá a que se cierre antes de lanzar la siguiente prueba**: si
  quedara uno abierto, el nuevo simulador muestra un error y no arranca.
- Las pruebas 2 a 4 y 9 guardan un registro en
  `resultados/unitree_bajo_nivel.csv` (objetivo y medición de cada
  articulación, e inclinación del cuerpo).

## Pruebas en la PC

### 1. Física en MuJoCo

Ejecuta la rutina con gravedad: cada motor recibe un torque de control PD y el
robot tiene que sostenerse sobre sus pies. No usa DDS ni el SDK de Unitree.

**Resultado esperado:** completa la rutina sin caerse.

**En el robot:** no se ejecuta en el robot; es la base de las pruebas 2 a 4.

### 2. Rutina completa por DDS, con arnés

Un programa de control, igual al que se usaría con el robot, envía la rutina
motor por motor por `rt/lowcmd` con las rigideces del ejemplo oficial de
Unitree. El simulador tiene activo un arnés virtual que cuelga el torso de un
punto sobre la cabeza.

**Resultado esperado:** completa la rutina; las articulaciones siguen al
objetivo con algo de atraso, porque los motores son más blandos.

**En el robot:** es la prueba 9, con el robot colgado de un soporte real.

### 3. Rutina completa por DDS, sin arnés

Lo mismo que la prueba 2, sin sostener el robot.

**Resultado esperado:** el robot **se cae** en los primeros segundos y el
programa lo detecta (inclinación mayor a 45°) y se detiene. Muestra que, con
rigideces realistas, controlar cada motor no alcanza: hace falta un
controlador de equilibrio.

**En el robot:** **nunca**. Es exactamente lo que no hay que hacer con el robot
real sin soporte.

### 4. Rutina completa por DDS, rigidez alta

Sin arnés, pero con las rigideces de la prueba 1 (entre 8 y 13 veces mayores
que las de Unitree en las piernas).

**Resultado esperado:** completa la rutina. La rigidez reemplaza al control de
equilibrio.

**En el robot:** **no se puede**. Con el robot real, esa rigidez puede provocar
vibraciones y movimientos bruscos; el programa rechaza la combinación.

### 5. Saludo por `arm_sdk`

El simulador imita al controlador de Unitree, que mantiene al robot de pie. El
programa solo toma cintura y brazos por `rt/arm_sdk`, mezclando su control con
el de Unitree: el peso sube de 0 a 1 al empezar y baja de 1 a 0 al terminar.

**Resultado esperado:** el robot levanta el brazo derecho, saluda dos veces y
lo baja, sin perder el equilibrio.

**En el robot:** es la prueba 6.

## Pruebas en el robot

> Todas piden el nombre del adaptador de red conectado al robot y, antes de
> moverlo, que escribas `SI`. Tené el control remoto a mano para pasar a modo
> amortiguado (damping) ante cualquier problema.

### Preparar la conexión

1. Conectá la PC al G1 por cable Ethernet.
2. Configurá ese adaptador con una IP fija en la red del robot
   (`192.168.123.x`, máscara `255.255.255.0`, sin repetir la del robot; ver la
   documentación de Unitree).
3. Averiguá el nombre del adaptador en PowerShell:

   ```powershell
   Get-NetAdapter
   ```

   Es la columna `Name`, por ejemplo `Ethernet 2`. En Windows no sirve la IP.

Cada prueba del robot se puede ejecutar con doble clic (pregunta el adaptador y
muestra la lista) o desde una terminal, pasándolo como argumento:

```powershell
.\pruebas\06_robot_saludo.bat "Ethernet 2"
```

### 6. Saludo en el robot

Mismo programa que la prueba 5.

**Estado del robot:** de pie, con su controlador normal activo (como queda al
encenderlo y ponerlo de pie con el control remoto), con espacio libre alrededor
de los brazos.

**Qué pasa:** Unitree mantiene el equilibrio; solo se mueven cintura y brazos.
Si se interrumpe con Ctrl+C, el programa devuelve el control a Unitree de forma
gradual.

**Es la primera prueba recomendada en el robot.**

### 7. Sentadilla en el robot

Le pide al controlador de Unitree que baje su altura de pie (`LowStand`),
espera 3 segundos y la vuelve a subir (`HighStand`). El simulador no tiene este
servicio, por eso no hay prueba equivalente en la PC.

**Estado del robot:** de pie, con su controlador normal activo y espacio libre.

**A tener en cuenta:** `HighStand` lleva el robot a la altura alta de pie, que
puede no ser la misma que tenía al empezar.

### 8. Sentadilla y saludo en el robot

Hace la prueba 7 y a continuación la 6. Conviene ejecutarla solo después de
que ambas funcionaron por separado.

### 9. Rutina completa en el robot (colgado)

Mismo programa que la prueba 2: apaga el controlador de Unitree y envía la
rutina motor por motor por `rt/lowcmd`, con las rigideces del ejemplo oficial.

> **PELIGRO:** sin el controlador de Unitree el robot no mantiene el
> equilibrio. **Solo con el robot colgado de un soporte**, como en la prueba 2.

**Qué pasa:** lleva los motores suavemente desde la posición medida a la
inicial, hace la rutina, mantiene 2 segundos la postura final y pasa a modo
amortiguado. También pasa a modo amortiguado con Ctrl+C o si el cuerpo se
inclina más de 45°.

## Limitaciones

- El SDK de Unitree está pensado para Linux. La comunicación desde Windows se
  probó con el simulador, pero no con un robot real.
- Los modos de operación y los pasos exactos dependen de la versión de
  firmware: seguí siempre la documentación de Unitree para tu robot.

Más detalle sobre cada etapa en [Del simulador al robot físico](../docs/ROBOT_FISICO.md).
