import random
import time

from bt_8bitdo_30snpro import Controller
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix.core import FrameCanvas

WIDTH = 32
HEIGHT = 32
PIECES = [
    0b11110000,  # line
    0b11001100,  # square
    0b11000110,  # S
    0b01101100,  # Z
    0b11100010,  # L
    0b11100010,  # J
    0b11100100,  # T
]


def generate_piece(x, y) -> list:
    piece = random.choice(PIECES)
    result = []
    for c in range(8):
        if piece & (1 << c):
            result.append((x + c // 4, y + c % 4))
    return result


def print_piece(canvas: FrameCanvas, piece: list) -> None:
    for x, y in piece:
        canvas.SetPixel(x, y, 255, 255, 255)


def clear_piece(canvas: FrameCanvas, piece: list) -> None:
    for x, y in piece:
        canvas.SetPixel(x, y, 0, 0, 0)


def move_piece(piece: list, dx: int, dy: int) -> list:
    return [(x + dx, y + dy) for x, y in piece]


def detect_collision(piece: list, board: list) -> bool:
    left = min(x for x, y in piece)
    right = max(x for x, y in piece)
    bottom = max(y for x, y in piece)

    if left < 0 or right >= WIDTH or bottom >= HEIGHT:
        return True


def init_matrix() -> FrameCanvas:
    options = RGBMatrixOptions()
    options.hardware_mapping = "adafruit-hat-pwm"
    options.rows = HEIGHT
    options.cols = WIDTH
    options.chain_length = 1
    options.parallel = 1
    options.row_address_type = 0
    options.multiplexing = 0
    options.pwm_bits = 11
    options.brightness = 100
    options.pwm_lsb_nanoseconds = 130
    options.led_rgb_sequence = "RGB"
    options.pixel_mapper_config = ""
    options.panel_type = ""
    options.gpio_slowdown = 1
    options.disable_hardware_pulsing = False

    matrix = RGBMatrix(options=options)
    matrix.Clear()
    return matrix.CreateFrameCanvas()


def main() -> None:
    canvas = init_matrix()

    get_new_piece = True
    prev_piece = None
    while True:
        if get_new_piece:
            prev_piece = None
            piece = generate_piece(0, 0)
            get_new_piece = False

        if prev_piece:
            clear_piece(canvas, prev_piece)
        print_piece(canvas, piece)

        time.sleep(0.5)
        prev_piece = piece
        piece = move_piece(piece, 0, 1)
        if detect_collision(piece):
            get_new_piece = True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting ...\n")
        sys.exit(0)
