"""Simple AI that plays Tetris automatically for demo/screensaver mode.

Uses a basic heuristic: for each possible placement, score by:
  - Minimizing aggregate height
  - Maximizing completed lines
  - Minimizing holes
  - Minimizing bumpiness (height differences between adjacent columns)
"""

from tetris_led.game import Action, Piece, TetrisGame

# Weights tuned for a "pleasant to watch" demo (not hyper-optimized)
_W_HEIGHT = -0.51
_W_LINES = 0.76
_W_HOLES = -0.36
_W_BUMPINESS = -0.18


def _column_heights(board, width, height):
    heights = [0] * width
    for c in range(width):
        for r in range(height):
            if board[r][c] is not None:
                heights[c] = height - r
                break
    return heights


def _count_holes(board, width, height):
    holes = 0
    for c in range(width):
        found_block = False
        for r in range(height):
            if board[r][c] is not None:
                found_block = True
            elif found_block:
                holes += 1
    return holes


def _completed_lines(board, width, height):
    return sum(
        1 for r in range(height) if all(board[r][c] is not None for c in range(width))
    )


def _evaluate(board, width, height):
    col_heights = _column_heights(board, width, height)
    agg_height = sum(col_heights)
    lines = _completed_lines(board, width, height)
    holes = _count_holes(board, width, height)
    bumpiness = sum(abs(col_heights[i] - col_heights[i + 1]) for i in range(width - 1))

    return (
        _W_HEIGHT * agg_height
        + _W_LINES * lines
        + _W_HOLES * holes
        + _W_BUMPINESS * bumpiness
    )


def _simulate_placement(game: TetrisGame, piece: Piece):
    """Simulate dropping a piece and return the resulting board score."""
    import copy

    board = [row[:] for row in game.board]

    # Drop piece to bottom
    test = piece
    while True:
        moved = test.moved(1, 0)
        fits = True
        for r, c in moved.cells:
            if c < 0 or c >= game.width or r >= game.height:
                fits = False
                break
            if r >= 0 and board[r][c] is not None:
                fits = False
                break
        if not fits:
            break
        test = moved

    # Lock onto board
    for r, c in test.cells:
        if 0 <= r < game.height and 0 <= c < game.width:
            board[r][c] = test.color

    return _evaluate(board, game.width, game.height)


def compute_best_actions(game: TetrisGame) -> list[Action]:
    """Compute the sequence of actions to reach the best placement."""
    if game.current_piece is None or game.game_over:
        return []

    best_score = float("-inf")
    best_rotation = 0
    best_col_offset = 0

    piece = game.current_piece

    for rot in range(4):
        rotated = Piece(piece.name, piece.row, piece.col, rot)

        # Find valid column range for the rotated piece
        cells = rotated.cells
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)

        for col_offset in range(-min_c, game.width - max_c):
            candidate = Piece(piece.name, piece.row, piece.col + col_offset, rot)

            # Check if the candidate fits at spawn position
            fits = True
            for r, c in candidate.cells:
                if c < 0 or c >= game.width:
                    fits = False
                    break
                if r >= 0 and r < game.height and game.board[r][c] is not None:
                    fits = False
                    break
            if not fits:
                continue

            score = _simulate_placement(game, candidate)
            if score > best_score:
                best_score = score
                best_rotation = rot
                best_col_offset = col_offset

    # Build action sequence
    actions: list[Action] = []

    # Rotations
    rotations_needed = (best_rotation - piece.rotation) % 4
    if rotations_needed == 3:
        actions.append(Action.ROTATE_CCW)
    else:
        actions.extend([Action.ROTATE_CW] * rotations_needed)

    # Horizontal movement
    if best_col_offset > 0:
        actions.extend([Action.RIGHT] * best_col_offset)
    elif best_col_offset < 0:
        actions.extend([Action.LEFT] * abs(best_col_offset))

    actions.append(Action.DROP)
    return actions
