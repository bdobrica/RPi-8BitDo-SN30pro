import random
import sys
import time
from threading import Thread

sys.path.append("../src")

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix.core import FrameCanvas

from bt_8bitdo_30snpro.controller import Controller, StickCallbacks

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
    print(f"print: {piece}")
    for x, y in piece:
        canvas.SetPixel(x, y, 255, 255, 255)


def clear_piece(canvas: FrameCanvas, piece: list) -> None:
    print(f"clear: {piece}")
    for x, y in piece:
        canvas.SetPixel(x, y, 0, 0, 0)


def move_piece(piece: list, dx: int, dy: int) -> list:
    return [(x + dx, y + dy) for x, y in piece]


def detect_collision(piece: list, board: list = None) -> bool:
    left = min(x for x, y in piece)
    right = max(x for x, y in piece)
    bottom = max(y for x, y in piece)

    if left < 0 or right >= WIDTH or bottom >= HEIGHT:
        return True
    return False


def init_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()
    options.rows = HEIGHT
    options.cols = WIDTH
    options.chain_length = 1
    options.parallel = 1

    matrix = RGBMatrix(options=options)
    matrix.Clear()
    return matrix


def display() -> None:
    global brick_dx

    matrix = init_matrix()
    canvas = matrix.CreateFrameCanvas()

    get_new_piece = True
    prev_pieces = []
    while True:
        if get_new_piece:
            prev_piece = None
            piece = generate_piece(WIDTH // 2 - 1, 0)
            get_new_piece = False

        for prev_piece in prev_pieces:
            clear_piece(canvas, prev_piece)
        if len(prev_pieces) > 1:
            _ = prev_pieces.pop(0)
        print_piece(canvas, piece)

        time.sleep(0.1)
        prev_pieces.append(piece)
        piece = move_piece(piece, brick_dx, 1)
        if detect_collision(piece):
            print("Collision!")
            get_new_piece = True
        print("")
        canvas = matrix.SwapOnVSync(canvas)


def main() -> None:
    global brick_dx
    brick_dx = 0

    def left_callback(value: int) -> None:
        brick_dx = 0
        if value == 1:
            brick_dx -= 1
        print("left", brick_dx)

    def right_callback(value: int) -> None:
        brick_dx = 0
        if value == 1:
            brick_dx += 1
        print("right", brick_dx)

    def up_callback(value: int) -> None:
        pass

    def down_callback(value: int) -> None:
        pass

    controller = Controller(
        dpad_callbacks=StickCallbacks(
            on_left=left_callback,
            on_right=right_callback,
            on_up=up_callback,
            on_down=down_callback,
        )
    )
    Thread(target=display).start()
    Thread(target=controller.listen).start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting ...\n")
        sys.exit(0)
