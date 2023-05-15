import struct


class StickCallbacks:
    def __init__(
        self,
        on_left: callable = None,
        on_right: callable = None,
        on_up: callable = None,
        on_down: callable = None,
    ):
        def do_nothing(value: int) -> None:
            pass

        self.on_left = on_left or do_nothing
        self.on_right = on_right or do_nothing
        self.on_up = on_up or do_nothing
        self.on_down = on_down or do_nothing


class ButtonCallbacks:
    def __init__(
        self,
        on_x: callable = None,
        on_y: callable = None,
        on_a: callable = None,
        on_b: callable = None,
        on_lb: callable = None,
        on_lt: callable = None,
        on_rb: callable = None,
        on_rt: callable = None,
        on_left_stick: callable = None,
        on_right_stick: callable = None,
        on_select: callable = None,
        on_start: callable = None,
        on_home: callable = None,
        on_capture: callable = None,
    ):
        def do_nothing(value: int) -> None:
            pass

        self.on_x = on_x or do_nothing
        self.on_y = on_y or do_nothing
        self.on_a = on_a or do_nothing
        self.on_b = on_b or do_nothing
        self.on_lb = on_lb or do_nothing
        self.on_lt = on_lt or do_nothing
        self.on_rb = on_rb or do_nothing
        self.on_rt = on_rt or do_nothing
        self.on_left_stick = on_left_stick or do_nothing
        self.on_right_stick = on_right_stick or do_nothing
        self.on_select = on_select or do_nothing
        self.on_start = on_start or do_nothing
        self.on_home = on_home or do_nothing
        self.on_capture = on_capture or do_nothing


class Controller:
    STRUCT_FORMAT = "lhBB"

    def __init__(
        self,
        device: str = "/dev/input/js0",
        dpad_callbacks: StickCallbacks = None,
        left_stick_callbacks: StickCallbacks = None,
        right_stick_callbacks: StickCallbacks = None,
        button_callbacks: ButtonCallbacks = None,
    ):
        self.device = device
        self.dpad_callbacks = dpad_callbacks or StickCallbacks()
        self.left_stick_callbacks = left_stick_callbacks or StickCallbacks()
        self.right_stick_callbacks = right_stick_callbacks or StickCallbacks()
        self.button_callbacks = button_callbacks or ButtonCallbacks()

    def parse_event(self, id_0: int, id_1: int, value: int):
        if id_0 == 2:  # directions
            if id_1 == 0:  # left stick left/right
                if value > 0:
                    self.left_stick_callbacks.on_right(value)
                elif value < 0:
                    self.left_stick_callbacks.on_left(abs(value))
                else:
                    self.left_stick_callbacks.on_left(value)
                    self.left_stick_callbacks.on_right(value)
            elif id_1 == 1:  # left stick up/down
                if value > 0:
                    self.left_stick_callbacks.on_down(value)
                elif value < 0:
                    self.left_stick_callbacks.on_up(abs(value))
                else:
                    self.left_stick_callbacks.on_up(value)
                    self.left_stick_callbacks.on_down(value)
            elif id_1 == 2:  # right stick left/right
                if value > 0:
                    self.right_stick_callbacks.on_right(value)
                elif value < 0:
                    self.right_stick_callbacks.on_left(abs(value))
                else:
                    self.right_stick_callbacks.on_left(value)
                    self.right_stick_callbacks.on_right(value)
            elif id_1 == 3:  # right stick up/down
                if value > 0:
                    self.right_stick_callbacks.on_down(value)
                elif value < 0:
                    self.right_stick_callbacks.on_up(abs(value))
                else:
                    self.right_stick_callbacks.on_up(value)
                    self.right_stick_callbacks.on_down(value)
            elif id_1 == 4:  # dpad left/right
                if value > 0:
                    self.dpad_callbacks.on_right(value)
                elif value < 0:
                    self.dpad_callbacks.on_left(abs(value))
                else:
                    self.dpad_callbacks.on_left(value)
                    self.dpad_callbacks.on_right(value)
            elif id_1 == 5:  # dpad up/down
                if value > 0:
                    self.dpad_callbacks.on_down(value)
                elif value < 0:
                    self.dpad_callbacks.on_up(abs(value))
                else:
                    self.dpad_callbacks.on_up(value)
                    self.dpad_callbacks.on_down(value)
        elif id_0 == 1:  # buttons
            if id_1 == 0:  # b
                self.button_callbacks.on_b(value)
            elif id_1 == 1:  # a
                self.button_callbacks.on_a(value)
            elif id_1 == 2:  # y
                self.button_callbacks.on_y(value)
            elif id_1 == 3:  # x
                self.button_callbacks.on_x(value)
            elif id_1 == 4:  # lb
                self.button_callbacks.on_lb(value)
            elif id_1 == 5:  # rb
                self.button_callbacks.on_rb(value)
            elif id_1 == 6:  # lt
                self.button_callbacks.on_lt(value)
            elif id_1 == 7:  # rt
                self.button_callbacks.on_rt(value)
            elif id_1 == 8:  # select
                self.button_callbacks.on_select(value)
            elif id_1 == 9:  # start
                self.button_callbacks.on_start(value)
            elif id_1 == 10:  # left stick
                self.button_callbacks.on_left_stick(value)
            elif id_1 == 11:  # right stick
                self.button_callbacks.on_right_stick(value)
            elif id_1 == 12:  # home (right diamond)
                self.button_callbacks.on_home(value)
            elif id_1 == 13:  # capture (left star)
                self.button_callbacks.on_capture(value)

    def listen(self):
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FORMAT)
        with open("/dev/input/js0", "rb") as device:
            while True:
                _, value, id_0, id_1 = struct.unpack(self.STRUCT_FORMAT, device.read(self.STRUCT_SIZE))

                self.parse_event(id_0, id_1, value)
