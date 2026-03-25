"""Renderer abstraction for the Tetris game.

Provides a base class and two concrete renderers:
- LedMatrixRenderer: drives the Raspberry Pi RGB LED matrix
- TerminalRenderer: ANSI terminal fallback for development/testing
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from tetris_led.game import TetrisGame


class Renderer(ABC):
    @abstractmethod
    def draw(self, game: TetrisGame) -> None:
        """Render the current game state."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware/resources."""


class LedMatrixRenderer(Renderer):
    """Renders onto an RGB LED matrix via rgbmatrix library."""

    def __init__(
        self,
        rows: int = 32,
        cols: int = 32,
        brightness: int = 80,
        gpio_slowdown: int = 4,
        hardware_mapping: str = "adafruit-hat",
    ):
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

        options = RGBMatrixOptions()
        options.rows = rows
        options.cols = cols
        options.chain_length = 1
        options.parallel = 1
        options.brightness = brightness
        options.gpio_slowdown = gpio_slowdown
        options.hardware_mapping = hardware_mapping
        options.drop_privileges = False  # already running as root

        self._matrix = RGBMatrix(options=options)
        self._canvas = self._matrix.CreateFrameCanvas()
        self._rows = rows
        self._cols = cols

    def draw(self, game: TetrisGame) -> None:
        self._canvas.Clear()

        # Compute pixel size so the game board fits the matrix
        cell_w = self._cols // game.width
        cell_h = self._rows // game.height
        cell_size = max(1, min(cell_w, cell_h))

        # Draw locked cells
        for r in range(game.height):
            for c in range(game.width):
                color = game.board[r][c]
                if color is not None:
                    self._fill_cell(r, c, color, cell_size)

        # Draw ghost piece (dimmed)
        ghost = game.get_drop_ghost()
        if ghost is not None and not game.game_over:
            gr, gg, gb = ghost.color
            dim = (gr // 6, gg // 6, gb // 6)
            for r, c in ghost.cells:
                if r >= 0:
                    self._fill_cell(r, c, dim, cell_size)

        # Draw current piece
        if game.current_piece is not None and not game.game_over:
            for r, c in game.current_piece.cells:
                if r >= 0:
                    self._fill_cell(r, c, game.current_piece.color, cell_size)

        self._canvas = self._matrix.SwapOnVSync(self._canvas)

    def _fill_cell(
        self, row: int, col: int, color: Tuple[int, int, int], cell_size: int
    ):
        px = col * cell_size
        py = row * cell_size
        for dy in range(cell_size):
            for dx in range(cell_size):
                self._canvas.SetPixel(px + dx, py + dy, *color)

    def cleanup(self) -> None:
        self._matrix.Clear()


class TerminalRenderer(Renderer):
    """ANSI terminal renderer for development without LED hardware."""

    _COLOR_MAP = {
        (0, 240, 240): "\033[96m",     # I - cyan
        (240, 240, 0): "\033[93m",     # O - yellow
        (0, 240, 0): "\033[92m",       # S - green
        (240, 0, 0): "\033[91m",       # Z - red
        (240, 160, 0): "\033[33m",     # L - orange
        (0, 0, 240): "\033[94m",       # J - blue
        (160, 0, 240): "\033[95m",     # T - purple
    }
    _RESET = "\033[0m"

    def draw(self, game: TetrisGame) -> None:
        # Build a display grid
        grid = [
            [game.board[r][c] for c in range(game.width)]
            for r in range(game.height)
        ]

        # Overlay ghost
        ghost = game.get_drop_ghost()
        if ghost is not None and not game.game_over:
            gr, gg, gb = ghost.color
            dim = (gr // 6, gg // 6, gb // 6)
            for r, c in ghost.cells:
                if 0 <= r < game.height and grid[r][c] is None:
                    grid[r][c] = dim

        # Overlay current piece
        if game.current_piece is not None and not game.game_over:
            for r, c in game.current_piece.cells:
                if 0 <= r < game.height:
                    grid[r][c] = game.current_piece.color

        lines = [f"\033[H\033[J"]  # clear screen
        lines.append(f"Score: {game.score}  Level: {game.level}  Lines: {game.lines_cleared}")
        lines.append("+" + "--" * game.width + "+")
        for r in range(game.height):
            row_str = "|"
            for c in range(game.width):
                color = grid[r][c]
                if color is None:
                    row_str += "  "
                else:
                    ansi = self._COLOR_MAP.get(color, "\033[37m")
                    row_str += f"{ansi}[]{self._RESET}"
            row_str += "|"
            lines.append(row_str)
        lines.append("+" + "--" * game.width + "+")
        if game.game_over:
            lines.append("        GAME OVER")
        print("\n".join(lines))

    def cleanup(self) -> None:
        print(f"\033[0m\033[?25h")  # reset colors, show cursor
