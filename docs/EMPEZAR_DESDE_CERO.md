# Empezar desde cero

## 1. Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- Conexión a Internet solamente durante la instalación de dependencias.

Para comprobar Python, abrí PowerShell y ejecutá:

```powershell
py -3 --version
```

## 2. Instalar

Hacé doble clic en `instalar.bat`. El archivo crea una carpeta oculta llamada
`.venv`; ahí instala una copia aislada de las dependencias, sin modificar otros
proyectos de Python de la computadora.

Las dependencias son:

- `mujoco`: carga el modelo, calcula la cinemática y muestra el visor 3D;
- `numpy`: realiza las interpolaciones y operaciones numéricas;
- `setuptools`: instala el paquete ubicado dentro de `src`.

## 3. Verificar

Hacé doble clic en `verificar.bat`. Se comprueba que:

- el modelo oficial carga;
- tiene 29 actuadores;
- existen todas las articulaciones usadas;
- las posturas respetan sus límites;
- la trayectoria termina en la postura inicial;
- las pruebas automáticas pasan.

## 4. Ejecutar

Hacé doble clic en `iniciar_demo.bat`. Cerrá la ventana de MuJoCo si querés
interrumpir la demostración.

## Problemas frecuentes

### “No se encontró Python”

Instalá Python desde python.org y marcá la opción para agregar el lanzador `py`.

### La ventana no abre

Actualizá el controlador de video. Para comprobar el proyecto sin OpenGL usá:

```powershell
.\.venv\Scripts\python.exe -m uade_mujoco --headless
```

### Un cambio de postura queda fuera de rango

El programa se detiene antes de abrir el visor e indica la articulación, el
valor solicitado y el rango válido. Corregí el valor en
`src/uade_mujoco/config.py`.
