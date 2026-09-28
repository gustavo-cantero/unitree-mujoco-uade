# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Educational, Windows-first university demo: the Unitree G1 humanoid (29-DoF official MJCF from `unitree_mujoco`) does a squat and a right-arm wave in MuJoCo. Only dependencies are `mujoco` and `numpy` — no Unitree SDK, no DDS, no network. The audience is students who may be new to Python, so user-facing text, docs, CLI flags (`--repetir`, `--modelo`, `--salida`), messages and identifiers in comments/docs are in **Spanish (rioplatense, voseo: "ejecutá", "hacé")**. Keep that language and tone when editing.

## Commands

Setup (or double-click `instalar.bat`, which does the same and then runs `--check`):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

The package lives in `src/` (src layout), so it must be installed (editable) before tests or `demo_g1.py` can import `uade_mujoco`.

```powershell
.\.venv\Scripts\python.exe -m uade_mujoco --check       # load + validate model/trajectory, no window
.\.venv\Scripts\python.exe -m uade_mujoco --headless    # run routine without viewer, writes resultados/trayectoria_g1.csv
.\.venv\Scripts\python.exe -m uade_mujoco               # visual demo (mujoco.viewer passive window)
.\.venv\Scripts\python.exe -m uade_mujoco --repetir 3 --fps 60

# Tests (stdlib unittest, no pytest)
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m unittest tests.test_trajectory -v
.\.venv\Scripts\python.exe -m unittest tests.test_model.ModelTests.test_sequence_is_valid_for_model
```

`verificar.bat` = `--check` + full test suite. No linter/formatter is configured.

Robot/DDS side (needs `.venv-robot`, Python 3.10, created by `instalar_robot.bat` from `../unitree_sdk2_python`; `cyclonedds==0.10.2` only has Windows wheels for 3.10):

```powershell
.\unitree.bat simulador [--arnes] [--sin-ventana --duracion 10]   # terminal 1
.\unitree.bat bajo-nivel [--rutina saludo] [--rigidez alta]       # terminal 2
.\unitree.bat saludo [--robot --interfaz "Ethernet 2"]
```

## Architecture

Linear pipeline driven by `cli.py`: `config.build_sequence()` → `model.load_model()` + `model.validate_project()` → `runner.run_headless|run_visual` → `reporting.write_csv()`.

- **`trajectory.py`** is pure (no MuJoCo import): `Pose` (joint targets only), `Stage` (name, duration, target pose), `Frame`. `iter_frames` walks the stages, interpolating from the previous stage's target with the minimum-jerk blend `10u³−15u⁴+6u⁵`. Keep it MuJoCo-free so it stays testable in isolation.
- **`config.py`** is the file students are meant to edit: `NEUTRAL_JOINTS` defines which joints are animated (its keys become `JOINT_NAMES`; every `Pose` must contain all of them, which `pose_with()` guarantees by overlaying overrides on the neutral pose). `CSV_JOINTS` picks which joints go to the CSV. Values are radians.
- **`model.py`** is the only MuJoCo boundary. `load_model` **sets gravity to zero** on purpose — this is a kinematic demo, not a balance controller. `validate_project` enforces: `model.nu == 29`, all joints exist, every stage target lies within MJCF `jnt_range`, positive durations, and base height stays above 0.45 m. `apply_pose` resets `qpos` to `qpos0`, writes joint values into `qpos`, runs `mj_kinematics`, then shifts base z so the lowest foot contact sphere sits exactly at z=0, then `mj_forward` (no dynamics stepping, no actuator control). Base height is therefore derived, never specified in config.
- **`physics.py`** (`--fisica`): re-enables gravity and replaces `apply_frame` with `PdController.advance`, which runs `mj_step` substeps applying PD torques (`ctrl` is torque; actuators are `<motor>`). Leg/waist gains are deliberately very stiff (kp 800) because there is no balance controller: below ~500 the robot falls in the squat, around 1200 the sim goes unstable. Any change to poses should keep `tests/test_physics.py` passing (no fall, tilt < 10°).
- **`runner.py`**: headless and visual modes consume the identical frame stream and both return CSV rows; `_advance` picks kinematic vs. physics per frame. Only the visual one sleeps for real-time pacing and can exit early when the window closes.
- **`unitree/`** (only importable with `unitree_sdk2py`, except `g1.py`): sends the same `config`/`trajectory` output over DDS as `unitree_hg` `LowCmd_`. `g1.MOTOR_JOINTS` is the SDK motor order and must equal the MJCF actuator order (tested). `simulator.py` is our own DDS sim (the official `unitree_mujoco/simulate_python` does not run on Windows and lacks `arm_sdk`): publishes `rt/lowstate`, applies `rt/lowcmd` like the official bridge, and until the first lowcmd runs an internal stiff "Unitree controller" that `rt/arm_sdk` blends into by `motor_cmd[29].q`. `dds.init_dds` patches the SDK's interface config (it logs to `/tmp`, which breaks on Windows); on Windows `--interfaz` is the adapter name, not an IP. Low-level control runs at 500 Hz for the robot but 200 Hz for the sim (the Python sim can't decode 500 msg/s without lagging). Real-robot paths require typing `SI`, block `--rigidez alta`, and end in damping. `LocoClient` (squat) is robot-only.
- **`paths.py`**: `PROJECT_ROOT` is computed as `parents[2]` of the module file, so default model/CSV paths assume the editable src-layout install.
- `cli.main` converts `FileNotFoundError`/`RuntimeError`/`ValueError` into `[ERROR] ...` and exit code 1; validation errors should raise `ValueError` with a Spanish message to surface cleanly.

## Notes

- `models/g1/` (MJCF + meshes) is third-party BSD-3 from Unitree; don't modify it — see `THIRD_PARTY_LICENSE_UNITREE.txt`.
- `resultados/*.csv` is git-ignored output.
- `docs/` holds student-facing guides (`CAMBIAR_MOVIMIENTOS.md`, `ARQUITECTURA.md`, etc.); update them when behavior or config structure changes.
