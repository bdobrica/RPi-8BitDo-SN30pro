"""Main entry point: play Tetris with a controller or watch the demo AI.

Usage:
    tetris-led play   [--device /dev/input/js0] [--terminal]
    tetris-led demo   [--terminal]

Flags:
    --terminal   Use ANSI terminal rendering instead of LED matrix
    --device     Joystick device path (default: /dev/input/js0)
    --width      Board width in cells (default: 10)
    --height     Board height in cells (default: 20)
"""

import argparse
import signal
import sys
import threading
import time

from tetris_led.game import Action, TetrisGame


def _make_renderer(args):
    if args.terminal:
        from tetris_led.renderer import TerminalRenderer
        return TerminalRenderer()
    else:
        from tetris_led.renderer import LedMatrixRenderer
        return LedMatrixRenderer(
            rows=args.led_rows,
            cols=args.led_cols,
            brightness=args.brightness,
            gpio_slowdown=args.gpio_slowdown,
            hardware_mapping=args.hardware_mapping,
        )


def _run_play(args):
    """Play mode: human controls via 8BitDo SN30 Pro controller."""
    from bt_8bitdo_30snpro.controller import (
        ButtonCallbacks,
        Controller,
        StickCallbacks,
    )

    game = TetrisGame(width=args.width, height=args.height)
    renderer = _make_renderer(args)
    lock = threading.Lock()
    running = True

    def _action(act: Action):
        def callback(value: int):
            if value == 0:
                return
            with lock:
                game.action(act)
        return callback

    def _start_callback(value: int):
        nonlocal running
        if value:
            with lock:
                if game.game_over:
                    game.__init__(width=args.width, height=args.height)

    def _select_callback(value: int):
        nonlocal running
        if value:
            running = False

    controller = Controller(
        device=args.device,
        dpad_callbacks=StickCallbacks(
            on_left=_action(Action.LEFT),
            on_right=_action(Action.RIGHT),
            on_up=_action(Action.ROTATE_CW),
            on_down=_action(Action.DOWN),
        ),
        button_callbacks=ButtonCallbacks(
            on_a=_action(Action.ROTATE_CW),
            on_b=_action(Action.ROTATE_CCW),
            on_y=_action(Action.DROP),
            on_start=_start_callback,
            on_select=_select_callback,
        ),
    )

    controller_thread = threading.Thread(target=controller.listen, daemon=True)
    controller_thread.start()

    try:
        while running:
            with lock:
                if not game.game_over:
                    game.tick()
                renderer.draw(game)
            time.sleep(game.gravity_interval)
    finally:
        controller.stop()
        renderer.cleanup()


def _run_demo(args):
    """Demo mode: AI plays Tetris automatically in a loop."""
    from tetris_led.demo_ai import compute_best_actions

    renderer = _make_renderer(args)
    running = True

    def _on_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    try:
        while running:
            game = TetrisGame(width=args.width, height=args.height)

            while running and not game.game_over:
                actions = compute_best_actions(game)

                for act in actions:
                    if not running:
                        break
                    game.action(act)
                    renderer.draw(game)
                    time.sleep(0.12)  # animate each move step

                # If no hard drop in actions, tick gravity
                if actions and actions[-1] != Action.DROP:
                    game.tick()
                    renderer.draw(game)

                time.sleep(0.4)  # pause between pieces for visual appeal

            # Game over — brief pause, then restart
            if running:
                renderer.draw(game)
                time.sleep(3.0)
    finally:
        renderer.cleanup()


def _add_led_args(parser):
    """Add LED matrix hardware options to a subparser."""
    led = parser.add_argument_group("LED matrix options")
    led.add_argument("--led-rows", type=int, default=32, help="LED panel rows (default: 32)")
    led.add_argument("--led-cols", type=int, default=32, help="LED panel columns (default: 32)")
    led.add_argument("--brightness", type=int, default=80, help="Brightness 1-100 (default: 80)")
    led.add_argument(
        "--gpio-slowdown", type=int, default=4,
        help="GPIO slowdown factor, increase for Pi 3/4/5 (default: 4)"
    )
    led.add_argument(
        "--hardware-mapping", default="adafruit-hat",
        help="Hardware mapping: regular, adafruit-hat, adafruit-hat-pwm (default: adafruit-hat)"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Tetris on Raspberry Pi RGB LED matrix"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Play sub-command
    play_parser = subparsers.add_parser("play", help="Play with a Bluetooth controller")
    play_parser.add_argument(
        "--device", default="/dev/input/js0", help="Joystick device path"
    )
    play_parser.add_argument(
        "--terminal", action="store_true", help="Use terminal renderer"
    )
    play_parser.add_argument("--width", type=int, default=10)
    play_parser.add_argument("--height", type=int, default=20)
    _add_led_args(play_parser)

    # Demo sub-command
    demo_parser = subparsers.add_parser("demo", help="Auto-play demo (screensaver)")
    demo_parser.add_argument(
        "--terminal", action="store_true", help="Use terminal renderer"
    )
    demo_parser.add_argument("--width", type=int, default=10)
    demo_parser.add_argument("--height", type=int, default=20)
    _add_led_args(demo_parser)

    args = parser.parse_args()

    if args.mode == "play":
        _run_play(args)
    elif args.mode == "demo":
        _run_demo(args)


if __name__ == "__main__":
    main()
