import random
from enum import Enum
from typing import List, Optional, Tuple

# Standard Tetris pieces (SRS) as lists of (row, col) offsets from top-left of a 4x4 bounding box
# Each piece has 4 rotations

_PIECE_DEFS = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "L": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "J": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
}

PIECE_COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "L": (240, 160, 0),
    "J": (0, 0, 240),
    "T": (160, 0, 240),
}

PIECE_NAMES = list(_PIECE_DEFS.keys())

Cell = Optional[Tuple[int, int, int]]  # RGB or None


class Action(Enum):
    LEFT = "left"
    RIGHT = "right"
    DOWN = "down"       # soft drop
    DROP = "drop"       # hard drop
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"


class Piece:
    def __init__(self, name: str, row: int, col: int, rotation: int = 0):
        self.name = name
        self.row = row
        self.col = col
        self.rotation = rotation % 4
        self.color = PIECE_COLORS[name]

    @property
    def cells(self) -> List[Tuple[int, int]]:
        """Absolute board positions of this piece's blocks."""
        return [
            (self.row + dr, self.col + dc)
            for dr, dc in _PIECE_DEFS[self.name][self.rotation]
        ]

    def moved(self, drow: int, dcol: int) -> "Piece":
        return Piece(self.name, self.row + drow, self.col + dcol, self.rotation)

    def rotated(self, direction: int) -> "Piece":
        return Piece(self.name, self.row, self.col, self.rotation + direction)


class TetrisGame:
    """Pure game logic — no rendering, no I/O."""

    def __init__(self, width: int = 10, height: int = 20):
        self.width = width
        self.height = height
        self.board: List[List[Cell]] = [
            [None] * width for _ in range(height)
        ]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self._bag: List[str] = []
        self.current_piece: Optional[Piece] = None
        self.next_piece_name: str = self._next_from_bag()
        self._spawn_piece()

    # --- Bag randomizer (standard 7-bag) ---

    def _next_from_bag(self) -> str:
        if not self._bag:
            self._bag = list(PIECE_NAMES)
            random.shuffle(self._bag)
        return self._bag.pop()

    # --- Piece spawning ---

    def _spawn_piece(self):
        name = self.next_piece_name
        self.next_piece_name = self._next_from_bag()
        col = (self.width - 4) // 2
        piece = Piece(name, 0, col)
        if not self._fits(piece):
            self.game_over = True
            self.current_piece = piece
            return
        self.current_piece = piece

    # --- Collision detection ---

    def _fits(self, piece: Piece) -> bool:
        for r, c in piece.cells:
            if c < 0 or c >= self.width or r >= self.height:
                return False
            if r >= 0 and self.board[r][c] is not None:
                return False
        return True

    # --- Actions ---

    def action(self, act: Action) -> bool:
        """Apply an action. Returns True if it had an effect."""
        if self.game_over or self.current_piece is None:
            return False

        if act == Action.LEFT:
            return self._try_move(0, -1)
        elif act == Action.RIGHT:
            return self._try_move(0, 1)
        elif act == Action.DOWN:
            return self._try_move(1, 0)
        elif act == Action.DROP:
            self._hard_drop()
            return True
        elif act == Action.ROTATE_CW:
            return self._try_rotate(1)
        elif act == Action.ROTATE_CCW:
            return self._try_rotate(-1)
        return False

    def _try_move(self, drow: int, dcol: int) -> bool:
        candidate = self.current_piece.moved(drow, dcol)
        if self._fits(candidate):
            self.current_piece = candidate
            return True
        return False

    def _try_rotate(self, direction: int) -> bool:
        candidate = self.current_piece.rotated(direction)
        # Try basic rotation, then wall kicks (offsets 0, ±1, ±2 columns)
        for offset in [0, -1, 1, -2, 2]:
            kicked = candidate.moved(0, offset)
            if self._fits(kicked):
                self.current_piece = kicked
                return True
        return False

    def _hard_drop(self):
        while self._try_move(1, 0):
            pass
        self._lock_piece()

    # --- Gravity tick ---

    def tick(self) -> bool:
        """Advance gravity by one row. Returns True if piece moved down."""
        if self.game_over or self.current_piece is None:
            return False
        if not self._try_move(1, 0):
            self._lock_piece()
            return False
        return True

    # --- Lock & clear ---

    def _lock_piece(self):
        for r, c in self.current_piece.cells:
            if 0 <= r < self.height and 0 <= c < self.width:
                self.board[r][c] = self.current_piece.color
        cleared = self._clear_lines()
        self._update_score(cleared)
        self._spawn_piece()

    def _clear_lines(self) -> int:
        new_board = [
            row for row in self.board if any(cell is None for cell in row)
        ]
        cleared = self.height - len(new_board)
        for _ in range(cleared):
            new_board.insert(0, [None] * self.width)
        self.board = new_board
        return cleared

    def _update_score(self, cleared: int):
        self.lines_cleared += cleared
        points = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
        self.score += points.get(cleared, 800) * self.level
        self.level = 1 + self.lines_cleared // 10

    # --- Query helpers ---

    def get_drop_ghost(self) -> Optional[Piece]:
        """Where the current piece would land."""
        if self.current_piece is None:
            return None
        ghost = self.current_piece
        while True:
            moved = ghost.moved(1, 0)
            if not self._fits(moved):
                return ghost
            ghost = moved

    @property
    def gravity_interval(self) -> float:
        """Seconds between gravity ticks, based on level."""
        return max(0.05, 1.0 - (self.level - 1) * 0.08)
