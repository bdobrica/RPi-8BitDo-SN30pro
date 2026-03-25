import glob
import os
import struct
from typing import Callable, Optional


def _noop(value: int) -> None:
    pass


def find_controller_device() -> Optional[str]:
    """Auto-detect the controller device path.

    Checks /dev/input/js* first, then falls back to /dev/input/event*.
    Returns the first device whose name matches the 8BitDo SN30 Pro.
    """
    # Prefer joystick device if available
    js_devices = sorted(glob.glob("/dev/input/js*"))
    if js_devices:
        return js_devices[0]

    # Fall back to evdev — find the right event device by name
    for sysfs in sorted(glob.glob("/sys/class/input/event*/device/name")):
        try:
            with open(sysfs) as f:
                name = f.read().strip().lower()
            if "8bitdo" in name or "sn30" in name or "pro controller" in name:
                event_dev = "/dev/input/" + sysfs.split("/")[4]
                if os.path.exists(event_dev):
                    return event_dev
        except OSError:
            continue

    # Last resort: first event device
    event_devices = sorted(glob.glob("/dev/input/event*"))
    if event_devices:
        return event_devices[0]

    return None


class StickCallbacks:
    def __init__(
        self,
        on_left: Optional[Callable[[int], None]] = None,
        on_right: Optional[Callable[[int], None]] = None,
        on_up: Optional[Callable[[int], None]] = None,
        on_down: Optional[Callable[[int], None]] = None,
    ):
        self.on_left = on_left or _noop
        self.on_right = on_right or _noop
        self.on_up = on_up or _noop
        self.on_down = on_down or _noop


class ButtonCallbacks:
    def __init__(
        self,
        on_x: Optional[Callable[[int], None]] = None,
        on_y: Optional[Callable[[int], None]] = None,
        on_a: Optional[Callable[[int], None]] = None,
        on_b: Optional[Callable[[int], None]] = None,
        on_lb: Optional[Callable[[int], None]] = None,
        on_lt: Optional[Callable[[int], None]] = None,
        on_rb: Optional[Callable[[int], None]] = None,
        on_rt: Optional[Callable[[int], None]] = None,
        on_left_stick: Optional[Callable[[int], None]] = None,
        on_right_stick: Optional[Callable[[int], None]] = None,
        on_select: Optional[Callable[[int], None]] = None,
        on_start: Optional[Callable[[int], None]] = None,
        on_home: Optional[Callable[[int], None]] = None,
        on_capture: Optional[Callable[[int], None]] = None,
    ):
        self.on_x = on_x or _noop
        self.on_y = on_y or _noop
        self.on_a = on_a or _noop
        self.on_b = on_b or _noop
        self.on_lb = on_lb or _noop
        self.on_lt = on_lt or _noop
        self.on_rb = on_rb or _noop
        self.on_rt = on_rt or _noop
        self.on_left_stick = on_left_stick or _noop
        self.on_right_stick = on_right_stick or _noop
        self.on_select = on_select or _noop
        self.on_start = on_start or _noop
        self.on_home = on_home or _noop
        self.on_capture = on_capture or _noop


class Controller:
    # Joystick API (/dev/input/js*) struct: timestamp(u32), value(s16), type(u8), number(u8)
    _JS_FORMAT = "lhBB"
    _JS_SIZE = struct.calcsize(_JS_FORMAT)

    # Evdev API (/dev/input/event*) struct: tv_sec(long), tv_usec(long), type(u16), code(u16), value(s32)
    _EV_FORMAT = "llHHi"
    _EV_SIZE = struct.calcsize(_EV_FORMAT)

    # Evdev event types
    _EV_KEY = 0x01
    _EV_ABS = 0x03

    # Evdev button codes -> callback method name
    _EVDEV_BUTTON_MAP = {
        0x130: "on_a",       # BTN_SOUTH / BTN_A
        0x131: "on_b",       # BTN_EAST / BTN_B
        0x133: "on_y",       # BTN_NORTH / BTN_Y  (0x132 skipped)
        0x134: "on_x",       # BTN_WEST / BTN_X
        0x136: "on_lb",      # BTN_TL
        0x137: "on_rb",      # BTN_TR
        0x138: "on_lt",      # BTN_TL2
        0x139: "on_rt",      # BTN_TR2
        0x13a: "on_select",  # BTN_SELECT
        0x13b: "on_start",   # BTN_START
        0x13c: "on_home",    # BTN_MODE
        0x13d: "on_left_stick",   # BTN_THUMBL
        0x13e: "on_right_stick",  # BTN_THUMBR
    }

    # Evdev axis codes -> (callbacks_attr, axis)
    _EVDEV_AXIS_MAP = {
        0x00: ("left_stick_callbacks", "x"),   # ABS_X
        0x01: ("left_stick_callbacks", "y"),   # ABS_Y
        0x03: ("right_stick_callbacks", "x"),  # ABS_RX
        0x04: ("right_stick_callbacks", "y"),  # ABS_RY
        0x10: ("dpad_callbacks", "x"),         # ABS_HAT0X
        0x11: ("dpad_callbacks", "y"),         # ABS_HAT0Y
    }

    # Joystick API axis mapping: (type, number) -> (callbacks_attr, axis)
    _JS_AXIS_MAP = {
        (2, 0): ("left_stick_callbacks", "x"),
        (2, 1): ("left_stick_callbacks", "y"),
        (2, 2): ("right_stick_callbacks", "x"),
        (2, 3): ("right_stick_callbacks", "y"),
        (2, 4): ("dpad_callbacks", "x"),
        (2, 5): ("dpad_callbacks", "y"),
    }

    # Joystick API button mapping: number -> callback method name
    _JS_BUTTON_MAP = {
        0: "on_b",
        1: "on_a",
        2: "on_y",
        3: "on_x",
        4: "on_lb",
        5: "on_rb",
        6: "on_lt",
        7: "on_rt",
        8: "on_select",
        9: "on_start",
        10: "on_left_stick",
        11: "on_right_stick",
        12: "on_home",
        13: "on_capture",
    }

    def __init__(
        self,
        device: Optional[str] = None,
        dpad_callbacks: Optional[StickCallbacks] = None,
        left_stick_callbacks: Optional[StickCallbacks] = None,
        right_stick_callbacks: Optional[StickCallbacks] = None,
        button_callbacks: Optional[ButtonCallbacks] = None,
    ):
        self.device = device
        self._running = False
        self.dpad_callbacks = dpad_callbacks or StickCallbacks()
        self.left_stick_callbacks = left_stick_callbacks or StickCallbacks()
        self.right_stick_callbacks = right_stick_callbacks or StickCallbacks()
        self.button_callbacks = button_callbacks or ButtonCallbacks()

    def _is_evdev(self) -> bool:
        return "event" in os.path.basename(self.device)

    def _dispatch_stick(self, callbacks: StickCallbacks, axis: str, value: int):
        if axis == "x":
            if value > 0:
                callbacks.on_right(value)
            elif value < 0:
                callbacks.on_left(abs(value))
            else:
                callbacks.on_left(0)
                callbacks.on_right(0)
        elif axis == "y":
            if value > 0:
                callbacks.on_down(value)
            elif value < 0:
                callbacks.on_up(abs(value))
            else:
                callbacks.on_up(0)
                callbacks.on_down(0)

    def _parse_js_event(self, ev_type: int, number: int, value: int):
        if ev_type == 2:
            key = (ev_type, number)
            if key in self._JS_AXIS_MAP:
                attr, axis = self._JS_AXIS_MAP[key]
                self._dispatch_stick(getattr(self, attr), axis, value)
        elif ev_type == 1:
            if number in self._JS_BUTTON_MAP:
                getattr(self.button_callbacks, self._JS_BUTTON_MAP[number])(value)

    def _parse_evdev_event(self, ev_type: int, code: int, value: int):
        if ev_type == self._EV_KEY:
            if code in self._EVDEV_BUTTON_MAP:
                getattr(self.button_callbacks, self._EVDEV_BUTTON_MAP[code])(value)
        elif ev_type == self._EV_ABS:
            if code in self._EVDEV_AXIS_MAP:
                attr, axis = self._EVDEV_AXIS_MAP[code]
                self._dispatch_stick(getattr(self, attr), axis, value)

    def listen(self):
        if self.device is None:
            self.device = find_controller_device()
        if self.device is None:
            raise FileNotFoundError(
                "No controller found. Make sure it's connected via Bluetooth "
                "and a /dev/input/js* or /dev/input/event* device exists."
            )

        evdev = self._is_evdev()
        fmt = self._EV_FORMAT if evdev else self._JS_FORMAT
        size = self._EV_SIZE if evdev else self._JS_SIZE

        self._running = True
        with open(self.device, "rb") as device:
            while self._running:
                data = device.read(size)
                if not data:
                    break
                if evdev:
                    _, _, ev_type, code, value = struct.unpack(fmt, data)
                    self._parse_evdev_event(ev_type, code, value)
                else:
                    _, value, ev_type, number = struct.unpack(fmt, data)
                    self._parse_js_event(ev_type, number, value)

    def stop(self):
        self._running = False
