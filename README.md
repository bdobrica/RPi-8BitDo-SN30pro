# RPi-8BitDo-SN30pro

Tetris on a Raspberry Pi RGB LED matrix, controlled by an **8BitDo SN30 Pro** Bluetooth controller — or in auto-play demo mode as a living room screensaver.

## Features

- **Play mode** — Control Tetris with your Bluetooth controller (D-pad to move, A/B to rotate, Y to hard drop)
- **Demo mode** — AI plays Tetris automatically in a loop, great for ambient display
- Standard SRS Tetris pieces with wall kicks, line clearing, scoring, and increasing speed
- Works on terminal (ANSI) for development or on RGB LED matrix hardware

## Hardware

- Raspberry Pi (any model with GPIO)
- [RGB LED Matrix](https://github.com/hzeller/rpi-rgb-led-matrix) (32x32 or similar)
- 8BitDo SN30 Pro Bluetooth controller

## Setup

### 1. Install the RGB LED matrix driver

```bash
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
cd ..
```

### 2. Install this project

```bash
cd RPi-8BitDo-SN30pro
pip install .
```

### 3. Pair your Bluetooth controller

```bash
sudo ./add-controller.sh
```

## Usage

### Play with controller

```bash
# On the Raspberry Pi with LED matrix:
sudo tetris-led play

# For development/testing in terminal:
tetris-led play --terminal --device /dev/input/js0
```

### Demo mode (auto-play screensaver)

```bash
# On the Raspberry Pi with LED matrix:
sudo tetris-led demo

# For development/testing in terminal:
tetris-led demo --terminal
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--terminal` | Use ANSI terminal rendering instead of LED matrix | off |
| `--device` | Joystick device path (play mode only) | `/dev/input/js0` |
| `--width` | Board width in cells | 10 |
| `--height` | Board height in cells | 20 |
| `--led-rows` | LED panel rows | 32 |
| `--led-cols` | LED panel columns | 32 |
| `--brightness` | LED brightness (1-100) | 80 |
| `--gpio-slowdown` | GPIO slowdown factor (increase for Pi 3/4/5) | 4 |
| `--hardware-mapping` | `regular`, `adafruit-hat`, or `adafruit-hat-pwm` | `adafruit-hat` |

### Troubleshooting

- **No output on LED matrix** — Try increasing `--gpio-slowdown` (e.g. `5` or `6` on Pi 4/5). If using an Adafruit HAT, pass `--hardware-mapping adafruit-hat`.
- **Flickering** — Disable on-board audio: add `dtparam=audio=off` to `/boot/config.txt` and reboot.
- **Permission denied** — The LED matrix requires root; run with `sudo`.

## Controls (Play Mode)

| Button | Action |
|---|---|
| D-pad Left/Right | Move piece |
| D-pad Down | Soft drop |
| D-pad Up / A | Rotate clockwise |
| B | Rotate counter-clockwise |
| Y | Hard drop |
| Start | Restart after game over |
| Select | Quit |

## Project Structure

```
src/
  bt_8bitdo_30snpro/     # Bluetooth controller bindings
    controller.py        # Event parsing & callback system
  tetris_led/            # Tetris game
    game.py              # Pure game logic (no I/O)
    renderer.py          # LED matrix & terminal renderers
    demo_ai.py           # Auto-play AI for demo mode
    main.py              # CLI entry point
add-controller.sh        # Bluetooth pairing helper
```

## License

See [LICENSE](LICENSE).
