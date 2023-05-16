import random
import sys
import threading
import time

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

brick_dx = 0
speed = 1


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


def can_drop(piece: list, board: list) -> bool:
    bottom = max(y for x, y in piece)
    if bottom >= HEIGHT:
        return False

    for x, y in piece:
        if y == bottom and (x < 0 or x >= WIDTH or board[y][x]):
            return False
    return True


def can_slide(piece: list, board: list) -> bool:
    left = min(x for x, y in piece)
    right = max(x for x, y in piece)

    if left < 0 or right >= WIDTH:
        return False

    for x, y in piece:
        if x == left and (y >= HEIGHT or board[y][x]):
            return False
        if x == right and (y >= HEIGHT or board[y][x]):
            return False

    return True


def init_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()
    options.rows = HEIGHT
    options.cols = WIDTH
    options.chain_length = 1
    options.parallel = 1

    matrix = RGBMatrix(options=options)
    matrix.Clear()
    return matrix


def print_board(board: list) -> None:
    print("")
    for row in board:
        print("".join(str(x) for x in row))
    print("")


def display() -> None:
    global brick_dx

    matrix = init_matrix()
    canvas = matrix.CreateFrameCanvas()

    frames = 0
    get_new_piece = True
    prev_pieces = []
    board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
    while True:
        canvas = matrix.SwapOnVSync(canvas)
        frames += 1
        if frames > 10:
            frames = 0

        if get_new_piece:
            prev_pieces = []
            piece = generate_piece(WIDTH // 2 - 1, 0)
            get_new_piece = False

        for prev_piece in prev_pieces:
            clear_piece(canvas, prev_piece)
        if len(prev_pieces) > 1:
            _ = prev_pieces.pop(0)
        print_piece(canvas, piece)

        time.sleep(0.01)
        brick_dy = frames // 10
        new_piece = move_piece(piece, brick_dx, brick_dy)
        prev_pieces.append(piece)
        if brick_dy:
            if not can_slide(new_piece, board):
                new_piece = move_piece(piece, 0, brick_dy)
            if not can_drop(new_piece, board):
                print("Locking piece")
                for x, y in piece:
                    board[y][x] = 1
                print_board(board)
                get_new_piece = True
                lock = threading.Lock()
                with lock:
                    brick_dx = 0
                prev_pieces = []
            else:
                piece = new_piece
        else:
            if can_slide(new_piece, board):
                piece = new_piece


def main() -> None:
    global brick_dx

    def left_callback(value: int) -> None:
        global brick_dx
        lock = threading.Lock()
        with lock:
            brick_dx = 0 if value == 0 else -1

        print("left", brick_dx)

    def right_callback(value: int) -> None:
        global brick_dx
        lock = threading.Lock()
        with lock:
            brick_dx = 0 if value == 0 else 1

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
    threading.Thread(target=controller.listen).start()
    display()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting ...\n")
        sys.exit(0)
