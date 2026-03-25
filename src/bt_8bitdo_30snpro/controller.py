import struct
from typing import Callable, Optional


def _noop(value: int) -> None:
    pass


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
    STRUCT_FORMAT = "lhBB"
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(
        self,
        device: str = "/dev/input/js0",
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

    # Axis mapping: (callbacks_attr, axis)
    _AXIS_MAP = {
        (2, 0): ("left_stick_callbacks", "x"),
        (2, 1): ("left_stick_callbacks", "y"),
        (2, 2): ("right_stick_callbacks", "x"),
        (2, 3): ("right_stick_callbacks", "y"),
        (2, 4): ("dpad_callbacks", "x"),
        (2, 5): ("dpad_callbacks", "y"),
    }

    # Button mapping: callback method name
    _BUTTON_MAP = {
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

    def parse_event(self, id_0: int, id_1: int, value: int):
        if id_0 == 2:
            key = (id_0, id_1)
            if key in self._AXIS_MAP:
                attr, axis = self._AXIS_MAP[key]
                self._dispatch_stick(getattr(self, attr), axis, value)
        elif id_0 == 1:
            if id_1 in self._BUTTON_MAP:
                getattr(self.button_callbacks, self._BUTTON_MAP[id_1])(value)

    def listen(self):
        self._running = True
        with open(self.device, "rb") as device:
            while self._running:
                data = device.read(self.STRUCT_SIZE)
                if not data:
                    break
                _, value, id_0, id_1 = struct.unpack(self.STRUCT_FORMAT, data)
                self.parse_event(id_0, id_1, value)

    def stop(self):
        self._running = False
