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
import queue
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
    action_queue = queue.Queue()
    running = True

    # DAS (Delayed Auto Shift) state for held directions
    DAS_DELAY = 0.18       # initial delay before auto-repeat starts
    DAS_REPEAT = 0.05      # repeat interval while held
    held_actions: dict[Action, float] = {}  # action -> time when next repeat fires
    held_lock = threading.Lock()

    def _direction_action(act: Action):
        """Callback for d-pad directions — supports hold-to-repeat."""
        def callback(value: int):
            with held_lock:
                if value != 0:
                    # Button pressed: queue immediate action, schedule DAS
                    action_queue.put(act)
                    held_actions[act] = time.monotonic() + DAS_DELAY
                else:
                    # Button released: stop repeating
                    held_actions.pop(act, None)
        return callback

    def _button_action(act: Action):
        """Callback for instant buttons (rotate, drop) — no auto-repeat."""
        def callback(value: int):
            if value == 0:
                return
            action_queue.put(act)
        return callback

    def _start_callback(value: int):
        nonlocal running
        if value:
            action_queue.put("restart")

    def _select_callback(value: int):
        nonlocal running
        if value:
            running = False

    def _flush_queue():
        """Drain all pending actions and clear DAS state (called on piece lock)."""
        while not action_queue.empty():
            try:
                action_queue.get_nowait()
            except queue.Empty:
                break
        with held_lock:
            held_actions.clear()

    def _process_one_action():
        """Process a single queued action and return whether something changed."""
        try:
            act = action_queue.get_nowait()
        except queue.Empty:
            return False
        with lock:
            if act == "restart":
                if game.game_over:
                    game.__init__(width=args.width, height=args.height)
                    return True
            elif not game.game_over:
                old_piece = game.current_piece
                game.action(act)
                # Piece locked (hard drop or landed) — flush stale inputs
                if game.current_piece is not old_piece:
                    _flush_queue()
                return True
        return False

    def _process_das():
        """Generate auto-repeat actions for held directions."""
        now = time.monotonic()
        with held_lock:
            for act, next_time in list(held_actions.items()):
                if now >= next_time:
                    action_queue.put(act)
                    held_actions[act] = now + DAS_REPEAT

    controller = Controller(
        device=args.device or None,
        dpad_callbacks=StickCallbacks(
            on_left=_direction_action(Action.LEFT),
            on_right=_direction_action(Action.RIGHT),
            on_up=_button_action(Action.ROTATE_CW),
            on_down=_direction_action(Action.DOWN),
        ),
        button_callbacks=ButtonCallbacks(
            on_a=_button_action(Action.ROTATE_CW),
            on_b=_button_action(Action.ROTATE_CCW),
            on_y=_button_action(Action.DROP),
            on_start=_start_callback,
            on_select=_select_callback,
        ),
    )

    controller_thread = threading.Thread(target=controller.listen, daemon=True)
    controller_thread.start()

    RENDER_INTERVAL = 0.016  # ~60 FPS render loop

    try:
        last_gravity = time.monotonic()
        while running:
            # Generate auto-repeat for held directions
            _process_das()

            # Process one queued action per frame (renders each move visibly)
            changed = _process_one_action()

            # Apply gravity on schedule
            now = time.monotonic()
            if now - last_gravity >= game.gravity_interval:
                with lock:
                    if not game.game_over:
                        old_piece = game.current_piece
                        game.tick()
                        changed = True
                        if game.current_piece is not old_piece:
                            _flush_queue()
                last_gravity = now

            # Render when something changed
            if changed:
                with lock:
                    renderer.draw(game)

            # Short sleep to stay responsive without busy-spinning
            time.sleep(RENDER_INTERVAL)
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
        "--device", default="", help="Input device path (auto-detected if not set)"
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
