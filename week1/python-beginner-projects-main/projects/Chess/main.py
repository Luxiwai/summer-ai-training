"""
Chess - A two-player local chess game built with Pygame.

Pieces are represented by single characters on an 8×8 grid:
  - Uppercase ("K", "Q", "R", "B", "N", "P") = White pieces
  - Lowercase ("k", "q", "r", "b", "n", "p") = Black pieces
  - 0 = Empty square

Rules implemented: basic movement for all pieces, turn alternation,
capture, and move legality check (cannot move into check).
Not yet implemented: castling, en passant, pawn promotion, checkmate
detection, stalemate detection.
"""

from __future__ import annotations

import os
import sys
from enum import IntEnum
from typing import Callable, Optional, Union

import pygame

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

BOARD_SIZE: int = 8
SQUARE_SIZE: int = 80
PIECE_IMAGE_WIDTH: int = 64
PIECE_IMAGE_HEIGHT: int = 85
WINDOW_SIZE: int = BOARD_SIZE * SQUARE_SIZE          # 640 × 640

# Colours
LIGHT_SQUARE_COLOR: tuple[int, int, int] = (200, 200, 200)
DARK_SQUARE_COLOR: tuple[int, int, int] = (30, 30, 30)
BACKGROUND_COLOR: tuple[int, int, int] = (12, 12, 12)
SELECTED_HIGHLIGHT_COLOR: tuple[int, int, int] = (200, 200, 0)
VALID_MOVE_COLOR: tuple[int, int, int] = (255, 121, 164)

# Mapping: piece character → index into the images list
PIECE_IMAGE_INDEX: dict[str, int] = {
    "K": 0,  "Q": 1,  "R": 2,  "B": 3,  "N": 4,  "P": 5,
    "k": 6,  "q": 7,  "r": 8,  "b": 9,  "n": 10, "p": 11,
}

# Image file names — order matches the mapping above
PIECE_IMAGE_FILES: list[str] = [
    "WhiteKing.png",   "WhiteQueen.png",  "WhiteRook.png",
    "WhiteBishop.png", "WhiteKnight.png", "WhitePawn.png",
    "BlackKing.png",   "BlackQueen.png",  "BlackRook.png",
    "BlackBishop.png", "BlackKnight.png", "BlackPawn.png",
]

# Knight move offsets (row_delta, col_delta)
KNIGHT_OFFSETS: list[tuple[int, int]] = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2),
]

# Direction vectors for sliding pieces
ROOK_DIRECTIONS: list[tuple[int, int]] = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
]
BISHOP_DIRECTIONS: list[tuple[int, int]] = [
    (1, 1), (-1, -1), (1, -1), (-1, 1),
]
QUEEN_DIRECTIONS: list[tuple[int, int]] = ROOK_DIRECTIONS + BISHOP_DIRECTIONS

# Type aliases
Piece = Union[int, str]           # 0 or a piece character
Grid = list[list[Piece]]          # 8 × 8 board
Position = list[int]              # [row, col]
MoveList = list[Position]         # List of valid destination coordinates


# ═══════════════════════════════════════════════════════════════════════════════
# Player enum
# ═══════════════════════════════════════════════════════════════════════════════

class Player(IntEnum):
    """Represents the two sides in the game.

    Being an ``IntEnum``, ``-Player.WHITE`` gives ``Player.BLACK`` and vice
    versa, so turn-switching reads naturally as ``self.current_player =
    -self.current_player``.
    """

    WHITE = 1
    BLACK = -1


# ═══════════════════════════════════════════════════════════════════════════════
# Move Generator
# ═══════════════════════════════════════════════════════════════════════════════

class ValidMoveGenerator:
    """Generates all pseudo-legal moves for a selected chess piece.

    *Pseudo-legal* means the moves follow piece movement rules but do not
    yet filter out moves that would leave the player's own king in check.
    That filtering is done separately by
    :meth:`ChessGame._would_leave_king_in_check`.
    """

    def __init__(self) -> None:
        self._moves_scratch: MoveList = []    # Raw candidate moves
        self._is_white_turn: bool = True

    # ── Public API ────────────────────────────────────────────────────────

    def generate_valid_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Return all pseudo-legal destination squares for the piece at
        *(start_row, start_col)*."""
        self._moves_scratch = []
        self._is_white_turn = str(grid[start_row][start_col]).isupper()

        piece_char: str = str(grid[start_row][start_col]).upper()

        # Each generator has the signature (int, int, Grid) -> MoveList
        move_generators: dict[str, Callable[[int, int, Grid], MoveList]] = {
            "K": self.king_moves,
            "Q": self.queen_moves,
            "R": self.rook_moves,
            "B": self.bishop_moves,
            "N": self.knight_moves,
            "P": self.pawn_moves,
        }

        generator: Optional[Callable[[int, int, Grid], MoveList]] = (
            move_generators.get(piece_char)
        )
        if generator is not None:
            return generator(start_row, start_col, grid)
        return []

    # ── Shared helpers ────────────────────────────────────────────────────

    @staticmethod
    def is_on_board(row: int, col: int) -> bool:
        """Return ``True`` if *(row, col)* lies inside the 8×8 board."""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def _same_color(self, row: int, col: int, grid: Grid) -> bool:
        """Check whether the piece on *grid[row][col]* belongs to the
        player whose turn it currently is.  Empty squares return ``False``."""
        piece: Piece = grid[row][col]
        if piece == 0:
            return False
        if self._is_white_turn:
            return str(piece).isupper()
        return str(piece).islower()

    def _sliding_moves(
        self,
        start_row: int,
        start_col: int,
        grid: Grid,
        directions: list[tuple[int, int]],
    ) -> MoveList:
        """Generate moves by sliding along each *direction* until hitting
        a piece or the board edge.  Used by Rook, Bishop, and Queen."""
        delta_row: int
        delta_col: int
        for delta_row, delta_col in directions:
            for step in range(1, BOARD_SIZE):
                target_row: int = start_row + delta_row * step
                target_col: int = start_col + delta_col * step
                if not self.is_on_board(target_row, target_col):
                    break
                target_piece: Piece = grid[target_row][target_col]
                if target_piece == 0:
                    self._moves_scratch.append([target_row, target_col])
                    continue
                if not self._same_color(target_row, target_col, grid):
                    self._moves_scratch.append([target_row, target_col])
                break               # blocked by a piece (own or opponent)
        return self._moves_scratch

    def _filter_on_board(self, moves: MoveList) -> MoveList:
        """Discard any moves whose coordinates fall outside the board."""
        return [
            [row, col] for row, col in moves
            if self.is_on_board(row, col)
        ]

    # ── Per-piece move generators ─────────────────────────────────────────

    def king_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for the King — one step in any direction."""
        self._moves_scratch = []
        delta_row: int
        delta_col: int
        target_row: int
        target_col: int
        for delta_row in range(-1, 2):
            for delta_col in range(-1, 2):
                if delta_row == 0 and delta_col == 0:
                    continue
                target_row = start_row + delta_row
                target_col = start_col + delta_col
                if self.is_on_board(target_row, target_col):
                    if not self._same_color(target_row, target_col, grid):
                        self._moves_scratch.append([target_row, target_col])
        return self._moves_scratch

    def queen_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for the Queen — Rook + Bishop combined."""
        self._moves_scratch = []
        return self._sliding_moves(
            start_row, start_col, grid, QUEEN_DIRECTIONS,
        )

    def rook_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for the Rook — horizontal / vertical sliding."""
        self._moves_scratch = []
        return self._sliding_moves(
            start_row, start_col, grid, ROOK_DIRECTIONS,
        )

    def bishop_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for the Bishop — diagonal sliding."""
        self._moves_scratch = []
        return self._sliding_moves(
            start_row, start_col, grid, BISHOP_DIRECTIONS,
        )

    def knight_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for the Knight — L-shaped jumps."""
        self._moves_scratch = []
        delta_row: int
        delta_col: int
        target_row: int
        target_col: int
        target_piece: Piece
        for delta_row, delta_col in KNIGHT_OFFSETS:
            target_row = start_row + delta_row
            target_col = start_col + delta_col
            if not self.is_on_board(target_row, target_col):
                continue
            target_piece = grid[target_row][target_col]
            if (target_piece == 0
                    or not self._same_color(target_row, target_col, grid)):
                self._moves_scratch.append([target_row, target_col])
        return self._moves_scratch

    def pawn_moves(
        self, start_row: int, start_col: int, grid: Grid,
    ) -> MoveList:
        """Generate moves for a Pawn — forward steps, double-step from
        starting rank, and diagonal captures."""
        self._moves_scratch = []
        piece: Piece = grid[start_row][start_col]

        if piece == "p":                       # Black pawn (moves downward ↓)
            self._add_pawn_moves(start_row, start_col, grid, direction=1)
        elif piece == "P":                     # White pawn (moves upward ↑)
            self._add_pawn_moves(start_row, start_col, grid, direction=-1)

        return self._filter_on_board(self._moves_scratch)

    def _add_pawn_moves(
        self, start_row: int, start_col: int, grid: Grid, direction: int,
    ) -> None:
        """Append pawn candidate moves to ``self._moves_scratch``.

        Args:
            direction: ``1`` for black (downward), ``-1`` for white (upward).
        """
        next_row: int = start_row + direction
        double_row: int = start_row + 2 * direction
        start_rank: int = 1 if direction == 1 else 6
        # The opponent-check function: black captures uppercase, white
        # captures lowercase.
        is_opponent = str.isupper if direction == 1 else str.islower

        # Double-step from starting rank
        if start_row == start_rank and grid[double_row][start_col] == 0:
            self._moves_scratch.append([double_row, start_col])

        # Single step forward (guard against pawn on final rank)
        if 0 <= next_row < BOARD_SIZE and grid[next_row][start_col] == 0:
            self._moves_scratch.append([next_row, start_col])

        # Diagonal captures
        if (start_col > 0 and 0 <= next_row < BOARD_SIZE
                and grid[next_row][start_col - 1] != 0
                and is_opponent(str(grid[next_row][start_col - 1]))):
            self._moves_scratch.append([next_row, start_col - 1])
        if (start_col < BOARD_SIZE - 1 and 0 <= next_row < BOARD_SIZE
                and grid[next_row][start_col + 1] != 0
                and is_opponent(str(grid[next_row][start_col + 1]))):
            self._moves_scratch.append([next_row, start_col + 1])


# ═══════════════════════════════════════════════════════════════════════════════
# Board (display only — no game logic)
# ═══════════════════════════════════════════════════════════════════════════════

class Board:
    """Manages the visual chessboard: squares, colors, and piece rendering.

    This class is purely concerned with *drawing*.  All game-state decisions
    happen in :class:`ChessGame`.
    """

    def __init__(self) -> None:
        self.squares: list[list[pygame.Rect]] = [
            [] for _ in range(BOARD_SIZE)
        ]
        self.colors: list[list[tuple[int, int, int]]] = [
            [] for _ in range(BOARD_SIZE)
        ]
        self.images: list[pygame.Surface] = self._load_piece_images()
        self._create_squares()

    # ── Setup ─────────────────────────────────────────────────────────────

    @staticmethod
    def _load_piece_images() -> list[pygame.Surface]:
        """Load and scale the 12 piece images from the *Assets/* folder.

        If any image file is missing or corrupt, a clear error message is
        printed and the process exits immediately — there is no point in
        continuing without piece graphics.
        """
        images: list[pygame.Surface] = []
        assets_dir: str = "Assets"
        filename: str
        filepath: str
        raw_image: pygame.Surface
        scaled_image: pygame.Surface
        for filename in PIECE_IMAGE_FILES:
            filepath = os.path.join(assets_dir, filename)
            try:
                raw_image = pygame.image.load(filepath)
            except pygame.error as exc:
                sys.exit(
                    f"Error: failed to load piece image '{filepath}'.\n"
                    f"Make sure the Assets/ folder is present and contains "
                    f"all 12 piece images.\n"
                    f"Details: {exc}"
                )
            scaled_image = pygame.transform.scale(
                raw_image, (PIECE_IMAGE_WIDTH, PIECE_IMAGE_HEIGHT),
            )
            images.append(scaled_image)
        return images

    def _create_squares(self) -> None:
        """Build 64 square rectangles and their default light / dark colours."""
        row: int
        col: int
        rect: pygame.Rect
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(
                    col * SQUARE_SIZE, row * SQUARE_SIZE,
                    SQUARE_SIZE, SQUARE_SIZE,
                )
                self.squares[row].append(rect)
                if row % 2 == col % 2:
                    self.colors[row].append(LIGHT_SQUARE_COLOR)
                else:
                    self.colors[row].append(DARK_SQUARE_COLOR)

    # ── Drawing ───────────────────────────────────────────────────────────

    def draw_board(self, surface: pygame.Surface) -> None:
        """Fill the background and paint every square with its current colour."""
        surface.fill(BACKGROUND_COLOR)
        row: int
        col: int
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                pygame.draw.rect(
                    surface, self.colors[row][col], self.squares[row][col],
                )

    def draw_pieces(self, surface: pygame.Surface, grid: Grid) -> None:
        """Blit piece images onto squares that contain a piece according
        to *grid*."""
        row: int
        col: int
        piece_char: Piece
        piece_str: str
        image_index: int
        image: pygame.Surface
        square_rect: pygame.Rect
        pos_x: float
        pos_y: float
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece_char = grid[row][col]
                if piece_char == 0:
                    continue
                piece_str = str(piece_char)
                if piece_str not in PIECE_IMAGE_INDEX:
                    continue

                image_index = PIECE_IMAGE_INDEX[piece_str]
                image = self.images[image_index]
                square_rect = self.squares[row][col]

                # Centre the image within the square
                pos_x = (
                    square_rect.x + square_rect.width / 2
                    - image.get_rect().width / 2
                )
                pos_y = (
                    square_rect.y + square_rect.height / 2
                    - image.get_rect().height / 2
                )
                surface.blit(image, (pos_x, pos_y))

    # ── Highlighting ──────────────────────────────────────────────────────

    def highlight_selected(
        self, selected_row: int, selected_col: int, valid_moves: MoveList,
    ) -> None:
        """Mark the selected square yellow and every legal destination pink."""
        self.colors[selected_row][selected_col] = SELECTED_HIGHLIGHT_COLOR
        move_row: int
        move_col: int
        for move_row, move_col in valid_moves:
            self.colors[move_row][move_col] = VALID_MOVE_COLOR

    def reset_colors(self) -> None:
        """Restore every square to its default alternating light / dark colour."""
        row: int
        col: int
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if row % 2 == col % 2:
                    self.colors[row][col] = LIGHT_SQUARE_COLOR
                else:
                    self.colors[row][col] = DARK_SQUARE_COLOR


# ═══════════════════════════════════════════════════════════════════════════════
# Game Controller
# ═══════════════════════════════════════════════════════════════════════════════

class ChessGame:
    """Top-level controller that owns **all** game state and the event loop.

    State fields
    ------------
    grid : Grid
        8×8 board representation.
    board : Board
        Visual board (squares, colours, piece images).
    current_player : Player
        ``Player.WHITE`` or ``Player.BLACK``.
    game_over : bool
        ``True`` once the game has ended (checkmate / stalemate / resignation).
    winner : Player or None
        The winning side, or ``None`` if the game is still in progress or
        ended in a draw.
    """

    def __init__(self) -> None:
        # ── Pygame initialisation ─────────────────────────────────────────
        pygame.init()
        self._surface: pygame.Surface = pygame.display.set_mode(
            (WINDOW_SIZE, WINDOW_SIZE),
        )
        pygame.display.set_caption("Chess")

        # ── Core game state ───────────────────────────────────────────────
        # 8×8 board: uppercase = White, lowercase = Black, 0 = empty
        self.grid: Grid = [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [0,   0,   0,   0,   0,   0,   0,   0],
            [0,   0,   0,   0,   0,   0,   0,   0],
            [0,   0,   0,   0,   0,   0,   0,   0],
            [0,   0,   0,   0,   0,   0,   0,   0],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ]

        self.current_player: Player = Player.WHITE
        self.game_over: bool = False
        self.winner: Optional[Player] = None

        # ── Selection state ───────────────────────────────────────────────
        self._selected: bool = False
        self._select_row: Optional[int] = None
        self._select_col: Optional[int] = None

        # ── Sub-components ────────────────────────────────────────────────
        self.board: Board = Board()
        self.move_generator: ValidMoveGenerator = ValidMoveGenerator()

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the main game loop.  Runs until the window is closed."""
        event: pygame.event.Event
        mouse_x: int
        mouse_y: int
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self._handle_click(mouse_x, mouse_y)

            self.board.draw_board(self._surface)
            self.board.draw_pieces(self._surface, self.grid)
            pygame.display.flip()

    # ── Click routing ─────────────────────────────────────────────────────

    def _handle_click(self, mouse_x: int, mouse_y: int) -> None:
        """Determine which board square was clicked and dispatch to the
        selection / move logic."""
        row: int
        col: int
        square_rect: pygame.Rect
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square_rect = self.board.squares[row][col]
                if (square_rect.left < mouse_x < square_rect.right
                        and square_rect.top < mouse_y < square_rect.bottom):
                    self._process_click(row, col)
                    return

    def _process_click(self, clicked_row: int, clicked_col: int) -> None:
        """Entry point for a click on the square at
        *(clicked_row, clicked_col)*."""
        if self._selected:
            self._handle_move_attempt(clicked_row, clicked_col)
        else:
            self._handle_selection(clicked_row, clicked_col)

    # ── Selection ─────────────────────────────────────────────────────────

    def _handle_selection(self, row: int, col: int) -> None:
        """Try to pick up a piece at *(row, col)* for the current player."""
        piece: Piece = self.grid[row][col]
        valid_moves: MoveList
        if piece != 0 and self._is_own_piece(row, col):
            self._selected = True
            self._select_row = row
            self._select_col = col
            valid_moves = self.move_generator.generate_valid_moves(
                row, col, self.grid,
            )
            self.board.highlight_selected(row, col, valid_moves)
        else:
            self._selected = False
            self._select_row = None
            self._select_col = None

    # ── Move / Deselect ───────────────────────────────────────────────────

    def _handle_move_attempt(
        self, clicked_row: int, clicked_col: int,
    ) -> None:
        """After a piece is already selected, either move it or cancel."""
        if (self._select_row != clicked_row
                or self._select_col != clicked_col):
            # Different square clicked → try to move
            if not self._would_leave_king_in_check(
                self._select_row, self._select_col,
                clicked_row, clicked_col,
            ):
                self._execute_move(clicked_row, clicked_col)
            else:
                self._clear_selection()
        else:
            # Same square clicked → cancel selection
            self._clear_selection()

        self.board.reset_colors()
        self._selected = False

    def _execute_move(self, target_row: int, target_col: int) -> None:
        """Write the move into ``self.grid`` if legal, then switch turns."""
        valid_moves: MoveList = self.move_generator.generate_valid_moves(
            self._select_row, self._select_col, self.grid,
        )
        move_row: int
        move_col: int
        for move_row, move_col in valid_moves:
            if move_row == target_row and move_col == target_col:
                self.grid[target_row][target_col] = \
                    self.grid[self._select_row][self._select_col]
                self.grid[self._select_row][self._select_col] = 0
                self._switch_turn()
                break

    def _clear_selection(self) -> None:
        """Reset selection state after a move or cancellation."""
        self._select_row = None
        self._select_col = None

    def _switch_turn(self) -> None:
        """Toggle ``current_player`` between White and Black."""
        self.current_player = -self.current_player

    # ── Turn helpers ──────────────────────────────────────────────────────

    def _is_own_piece(self, row: int, col: int) -> bool:
        """Return ``True`` when the piece at *(row, col)* belongs to
        ``self.current_player``."""
        piece_str: str = str(self.grid[row][col])
        if self.current_player == Player.WHITE:
            return piece_str.isupper()
        return piece_str.islower()

    # ── Check detection ───────────────────────────────────────────────────

    def _would_leave_king_in_check(
        self,
        from_row: int, from_col: int,
        to_row: int, to_col: int,
    ) -> bool:
        """Simulate the move and return ``True`` if the current player's own
        king would be in check afterwards."""
        # Deep-copy the grid so the simulation has no side effects
        simulated_grid: Grid = [row[:] for row in self.grid]
        simulated_grid[to_row][to_col] = self.grid[from_row][from_col]
        simulated_grid[from_row][from_col] = 0

        is_white: bool = (
            self.current_player == Player.WHITE
        )

        king_pos: Optional[tuple[int, int]] = self._find_king(
            simulated_grid, is_white,
        )
        if king_pos is None:                     # Should never happen
            return False
        king_row, king_col = king_pos

        opponent_positions: MoveList = self._collect_opponent_positions(
            simulated_grid, is_white,
        )

        # If any opponent piece can reach the king, the move is illegal
        opp_row: int
        opp_col: int
        opponent_moves: MoveList
        move_row: int
        move_col: int
        for opp_row, opp_col in opponent_positions:
            opponent_moves = self.move_generator.generate_valid_moves(
                opp_row, opp_col, simulated_grid,
            )
            for move_row, move_col in opponent_moves:
                if king_row == move_row and king_col == move_col:
                    return True
        return False

    @staticmethod
    def _find_king(
        grid: Grid, is_white: bool,
    ) -> Optional[tuple[int, int]]:
        """Locate the king belonging to *is_white* on *grid*.

        Returns:
            ``(row, col)`` if found, ``None`` otherwise.
        """
        king_char: str = "K" if is_white else "k"
        row: int
        col: int
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if grid[row][col] == king_char:
                    return (row, col)
        return None

    @staticmethod
    def _collect_opponent_positions(
        grid: Grid, is_white: bool,
    ) -> MoveList:
        """Return the positions of every opponent piece on *grid*."""
        positions: MoveList = []
        row: int
        col: int
        piece: Piece
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = grid[row][col]
                if piece == 0:
                    continue
                if is_white:
                    if str(piece).islower():
                        positions.append([row, col])
                else:
                    if str(piece).isupper():
                        positions.append([row, col])
        return positions


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    game: ChessGame = ChessGame()
    game.run()
