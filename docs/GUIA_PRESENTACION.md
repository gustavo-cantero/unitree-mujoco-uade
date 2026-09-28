# Guía breve para presentar el proyecto

## Introducción

“Usé el modelo oficial de 29 grados de libertad del Unitree G1 en MuJoCo. La
demostración genera una sentadilla y un saludo a partir de posturas articulares
propias.”

## Qué hace el programa

- Carga el archivo MJCF y las mallas del G1.
- Busca las articulaciones por nombre.
- Define posturas objetivo para la sentadilla y el brazo derecho.
- Interpola suavemente entre esas posturas.
- Verifica que ningún objetivo supere los límites del modelo.
- Guarda un CSV con la trayectoria para poder analizarla.

## Idea técnica principal

La interpolación de mínimo tirón evita cambios bruscos al inicio y al final de
cada movimiento. El parámetro normalizado `u` va de cero a uno y se transforma
con `10u³ - 15u⁴ + 6u⁵`.

## Limitación que conviene decir explícitamente

El proyecto es cinemático: mantiene la base controlada y no resuelve el
equilibrio dinámico. Es una decisión consciente para concentrarse en la
generación y validación de trayectorias. El paso siguiente sería usar control
PD y un controlador de equilibrio.

## Demostración sugerida

1. Ejecutar la validación y mostrar los tres mensajes `[OK]`.
2. Abrir la demostración visual.
3. Mostrar `resultados/trayectoria_g1.csv` y señalar los ángulos de las
   rodillas durante la sentadilla y de la muñeca durante el saludo.
