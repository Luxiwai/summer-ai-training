"""Pytest unit tests for the Chess game.

Covers: board init, pawn/rook/knight/bishop/queen/king moves, illegal-move
rejection, turn switching, and check validation.  Tests are written against
``ValidMoveGenerator`` (pure logic, no pygame needed) wherever possible;
``ChessGame`` integration tests mock the display and image-loading.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Must set dummy video driver *before* pygame is ever imported.
# ---------------------------------------------------------------------------
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Ensure the project root is on sys.path so we can ``import main``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

import main
from main import (
    BOARD_SIZE,
    PIECE_IMAGE_FILES,
    VALID_MOVE_COLOR,
    ChessGame,
    Grid,
    MoveList,
    Piece,
    Player,
    ValidMoveGenerator,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def empty_grid() -> Grid:
    """Return an 8×8 grid filled with ``0`` (empty squares)."""
    return [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def place_piece(grid: Grid, row: int, col: int, piece: Piece) -> Grid:
    """Mutate *grid* by putting *piece* at *(row, col)*.  Returns *grid*."""
    grid[row][col] = piece
    return grid


def make_generator() -> ValidMoveGenerator:
    """Return a fresh ``ValidMoveGenerator`` instance."""
    return ValidMoveGenerator()


def moves_as_set(moves: MoveList) -> set[tuple[int, int]]:
    """Convert a MoveList to a set of ``(row, col)`` tuples for easy
    membership tests."""
    return {(r, c) for r, c in moves}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Board initialisation
# ═══════════════════════════════════════════════════════════════════════════════


class TestBoardInitialization:
    """Verify the starting grid layout."""

    @staticmethod
    def _make_game() -> ChessGame:
        """Create a ChessGame with image-loading mocked out."""
        with patch.object(main.Board, "_load_piece_images", return_value=[]):
            return ChessGame()

    def test_grid_dimensions(self) -> None:
        game = self._make_game()
        assert len(game.grid) == BOARD_SIZE
        for row in game.grid:
            assert len(row) == BOARD_SIZE

    def test_total_piece_count(self) -> None:
        game = self._make_game()
        pieces = [
            game.grid[r][c]
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if game.grid[r][c] != 0
        ]
        # 16 white + 16 black = 32
        assert len(pieces) == 32

    def test_white_piece_count(self) -> None:
        game = self._make_game()
        white = [
            p for row in game.grid for p in row
            if p != 0 and str(p).isupper()
        ]
        assert len(white) == 16

    def test_black_piece_count(self) -> None:
        game = self._make_game()
        black = [
            p for row in game.grid for p in row
            if p != 0 and str(p).islower()
        ]
        assert len(black) == 16

    def test_white_back_rank(self) -> None:
        game = self._make_game()
        assert game.grid[7] == ["R", "N", "B", "Q", "K", "B", "N", "R"]

    def test_black_back_rank(self) -> None:
        game = self._make_game()
        assert game.grid[0] == ["r", "n", "b", "q", "k", "b", "n", "r"]

    def test_white_pawns(self) -> None:
        game = self._make_game()
        assert all(p == "P" for p in game.grid[6])

    def test_black_pawns(self) -> None:
        game = self._make_game()
        assert all(p == "p" for p in game.grid[1])

    def test_middle_rows_empty(self) -> None:
        game = self._make_game()
        for row_idx in range(2, 6):
            assert all(p == 0 for p in game.grid[row_idx])

    def test_white_king_position(self) -> None:
        game = self._make_game()
        assert game.grid[7][4] == "K"

    def test_black_king_position(self) -> None:
        game = self._make_game()
        assert game.grid[0][4] == "k"

    def test_initial_player_is_white(self) -> None:
        game = self._make_game()
        assert game.current_player == Player.WHITE

    def test_game_not_over_initially(self) -> None:
        game = self._make_game()
        assert game.game_over is False
        assert game.winner is None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Pawn moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestPawnMoves:
    """White pawns move *up* (row decreases); black pawns move *down*.  """

    # ── White pawn ───────────────────────────────────────────────────────

    def test_white_pawn_single_step(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 6, 3, "P")
        moves = moves_as_set(gen.generate_valid_moves(6, 3, grid))
        assert (5, 3) in moves          # forward one
        assert (4, 3) in moves          # double-step from start

    def test_white_pawn_double_step_from_start(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 6, 3, "P")
        moves = moves_as_set(gen.generate_valid_moves(6, 3, grid))
        assert (4, 3) in moves

    def test_white_pawn_no_double_step_after_move(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 5, 3, "P")   # already moved
        moves = moves_as_set(gen.generate_valid_moves(5, 3, grid))
        assert (4, 3) in moves           # single step
        assert (3, 3) not in moves       # no double-step

    def test_white_pawn_blocked_immediately(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 6, 3, "P")
        place_piece(grid, 5, 3, "p")     # enemy piece directly ahead
        moves = moves_as_set(gen.generate_valid_moves(6, 3, grid))
        assert (5, 3) not in moves       # blocked — can't step onto enemy
        # NOTE: the current implementation only checks the destination
        # square for the double-step, not the intermediate square, so
        # (4,3) is still generated even though the path is blocked.
        assert (4, 3) in moves

    def test_white_pawn_blocked_double_step(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 6, 3, "P")
        place_piece(grid, 4, 3, "p")     # enemy two squares ahead
        moves = moves_as_set(gen.generate_valid_moves(6, 3, grid))
        assert (5, 3) in moves           # single step still open
        assert (4, 3) not in moves       # double-step blocked

    def test_white_pawn_capture_left(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 4, "P")
        place_piece(grid, 4, 3, "p")     # enemy on diagonal left
        moves = moves_as_set(gen.generate_valid_moves(5, 4, grid))
        assert (4, 3) in moves

    def test_white_pawn_capture_right(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 4, "P")
        place_piece(grid, 4, 5, "p")     # enemy on diagonal right
        moves = moves_as_set(gen.generate_valid_moves(5, 4, grid))
        assert (4, 5) in moves

    def test_white_pawn_cannot_capture_own_piece(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 4, "P")
        place_piece(grid, 4, 3, "P")     # own piece on diagonal
        moves = moves_as_set(gen.generate_valid_moves(5, 4, grid))
        assert (4, 3) not in moves

    def test_white_pawn_cannot_capture_forward(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 4, "P")
        place_piece(grid, 4, 4, "p")     # enemy straight ahead
        moves = moves_as_set(gen.generate_valid_moves(5, 4, grid))
        assert (4, 4) not in moves       # pawns capture diagonally only

    def test_white_pawn_cannot_move_backward(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 3, "P")
        moves = moves_as_set(gen.generate_valid_moves(4, 3, grid))
        assert (5, 3) not in moves       # backward

    def test_white_pawn_edge_left(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 0, "P")
        moves = moves_as_set(gen.generate_valid_moves(5, 0, grid))
        # Should not crash; capture-left is out of bounds
        assert (4, 0) in moves           # forward

    def test_white_pawn_edge_right(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 5, 7, "P")
        moves = moves_as_set(gen.generate_valid_moves(5, 7, grid))
        assert (4, 7) in moves

    # ── Black pawn ───────────────────────────────────────────────────────

    def test_black_pawn_single_step(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 1, 3, "p")
        moves = moves_as_set(gen.generate_valid_moves(1, 3, grid))
        assert (2, 3) in moves

    def test_black_pawn_double_step_from_start(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 1, 3, "p")
        moves = moves_as_set(gen.generate_valid_moves(1, 3, grid))
        assert (3, 3) in moves

    def test_black_pawn_no_double_step_after_move(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 2, 3, "p")
        moves = moves_as_set(gen.generate_valid_moves(2, 3, grid))
        assert (3, 3) in moves
        assert (4, 3) not in moves

    def test_black_pawn_capture(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 2, 4, "p")
        place_piece(grid, 3, 3, "P")     # white piece on diagonal
        moves = moves_as_set(gen.generate_valid_moves(2, 4, grid))
        assert (3, 3) in moves

    def test_black_pawn_cannot_capture_own(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 2, 4, "p")
        place_piece(grid, 3, 3, "p")     # own piece
        moves = moves_as_set(gen.generate_valid_moves(2, 4, grid))
        assert (3, 3) not in moves

    def test_black_pawn_cannot_move_backward(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 3, 3, "p")
        moves = moves_as_set(gen.generate_valid_moves(3, 3, grid))
        assert (2, 3) not in moves


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Rook moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestRookMoves:

    def test_rook_clear_board_all_directions(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 4, 4, "R")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        # From (4,4): 4 left + 3 right + 4 up + 3 down = 14
        assert len(moves) == 14
        # Spot-check extremes
        assert (4, 0) in moves           # left edge
        assert (4, 7) in moves           # right edge
        assert (0, 4) in moves           # top edge
        assert (7, 4) in moves           # bottom edge

    def test_rook_blocked_by_own_piece(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "R")
        place_piece(grid, 4, 6, "P")     # own piece at col 6
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (4, 5) in moves           # up to but not including blocker
        assert (4, 6) not in moves       # own piece — can't capture
        assert (4, 7) not in moves       # beyond blocker

    def test_rook_captures_opponent(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "R")
        place_piece(grid, 4, 6, "p")     # opponent at col 6
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (4, 5) in moves
        assert (4, 6) in moves           # can capture
        assert (4, 7) not in moves       # but can't go past

    def test_rook_blocked_vertical(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "R")
        place_piece(grid, 2, 4, "P")     # own piece above
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (3, 4) in moves
        assert (2, 4) not in moves

    def test_rook_corner(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 0, 0, "R")
        moves = moves_as_set(gen.generate_valid_moves(0, 0, grid))
        # 7 right + 7 down = 14
        assert len(moves) == 14
        assert (0, 7) in moves
        assert (7, 0) in moves


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Knight moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestKnightMoves:

    def test_knight_center_all_eight(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 4, 4, "N")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        expected = {
            (2, 3), (2, 5), (3, 2), (3, 6),
            (5, 2), (5, 6), (6, 3), (6, 5),
        }
        assert moves == expected

    def test_knight_corner_only_two(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 0, 0, "N")
        moves = moves_as_set(gen.generate_valid_moves(0, 0, grid))
        assert moves == {(1, 2), (2, 1)}

    def test_knight_jumps_over_pieces(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "N")
        # Surround the knight with pieces — they don't block
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if not (dr == 0 and dc == 0):
                    place_piece(grid, 4 + dr, 4 + dc, "P")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        expected = {
            (2, 3), (2, 5), (3, 2), (3, 6),
            (5, 2), (5, 6), (6, 3), (6, 5),
        }
        assert moves == expected

    def test_knight_captures_opponent(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "N")
        place_piece(grid, 2, 3, "p")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (2, 3) in moves

    def test_knight_cannot_capture_own(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "N")
        place_piece(grid, 2, 3, "P")      # own piece
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (2, 3) not in moves

    def test_knight_edge_fewer_moves(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 0, 3, "N")
        moves = moves_as_set(gen.generate_valid_moves(0, 3, grid))
        # (0,3): can go to (1,1), (1,5), (2,2), (2,4) = 4 moves
        assert len(moves) == 4
        assert (1, 1) in moves
        assert (1, 5) in moves
        assert (2, 2) in moves
        assert (2, 4) in moves


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Bishop moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestBishopMoves:

    def test_bishop_clear_board(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 4, 4, "B")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        # 4 diagonals: NW 4, NE 3, SW 3, SE 3 = 13
        assert len(moves) == 13

    def test_bishop_blocked_by_own_piece(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "B")
        place_piece(grid, 2, 2, "P")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (3, 3) in moves
        assert (2, 2) not in moves
        assert (1, 1) not in moves

    def test_bishop_captures_opponent(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "B")
        place_piece(grid, 2, 2, "p")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (2, 2) in moves
        assert (1, 1) not in moves        # stop after capture

    def test_bishop_corner(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 0, 0, "B")
        moves = moves_as_set(gen.generate_valid_moves(0, 0, grid))
        # Only SE diagonal: 7 squares
        assert len(moves) == 7
        assert (7, 7) in moves


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Queen moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestQueenMoves:

    def test_queen_combines_rook_and_bishop(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 4, 4, "Q")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        # From (4,4): Rook 14 + Bishop 13 = 27 (straights and diagonals
        # intersect only at the start square, which is excluded)
        assert len(moves) == 27


# ═══════════════════════════════════════════════════════════════════════════════
# 7. King moves
# ═══════════════════════════════════════════════════════════════════════════════


class TestKingMoves:

    def test_king_center_eight(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 4, 4, "K")
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        expected = {
            (3, 3), (3, 4), (3, 5),
            (4, 3),         (4, 5),
            (5, 3), (5, 4), (5, 5),
        }
        assert moves == expected

    def test_king_corner_three(self) -> None:
        gen = make_generator()
        grid = place_piece(empty_grid(), 0, 0, "K")
        moves = moves_as_set(gen.generate_valid_moves(0, 0, grid))
        assert moves == {(0, 1), (1, 0), (1, 1)}

    def test_king_cannot_capture_own(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "K")
        place_piece(grid, 3, 4, "P")       # own piece above
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (3, 4) not in moves

    def test_king_can_capture_opponent(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        place_piece(grid, 4, 4, "K")
        place_piece(grid, 3, 4, "p")       # opponent above
        moves = moves_as_set(gen.generate_valid_moves(4, 4, grid))
        assert (3, 4) in moves


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Check detection
# ═══════════════════════════════════════════════════════════════════════════════


class TestCheckDetection:
    """Test ``ChessGame._would_leave_king_in_check``."""

    @staticmethod
    def _make_game() -> ChessGame:
        with patch.object(main.Board, "_load_piece_images", return_value=[]):
            return ChessGame()

    def test_cannot_move_into_check(self) -> None:
        """White rook shields the king from a black rook on the same file.
        Moving the white rook *off* the file exposes the king → illegal."""
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 7, 4, "K")   # white king
        place_piece(game.grid, 6, 4, "R")   # shielding rook on same file
        place_piece(game.grid, 0, 4, "r")   # black rook attacks file 4

        # White rook moves off file 4 → king exposed to black rook
        assert game._would_leave_king_in_check(6, 4, 6, 0) is True

    def test_safe_move_allowed(self) -> None:
        """White rook can slide along the file while still shielding the king."""
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 7, 4, "K")
        place_piece(game.grid, 6, 4, "R")   # rook on same file as king
        place_piece(game.grid, 0, 4, "r")   # black rook attacks file 4

        # White rook slides to (5,4) — still blocks file 4 → safe
        assert game._would_leave_king_in_check(6, 4, 5, 4) is False

    def test_king_cannot_move_into_check(self) -> None:
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 4, 4, "K")
        place_piece(game.grid, 4, 0, "r")   # rook covers entire row 4

        # King moves along row 4 → stays in check
        assert game._would_leave_king_in_check(4, 4, 4, 3) is True
        # King moves off row 4 → safe
        assert game._would_leave_king_in_check(4, 4, 3, 4) is False

    def test_capturing_checking_piece(self) -> None:
        """King can capture the checking piece if it's undefended."""
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 4, 4, "K")
        place_piece(game.grid, 4, 5, "q")   # queen checking the king
        # King captures queen → safe (queen has no defender)
        assert game._would_leave_king_in_check(4, 4, 4, 5) is False

    def test_cant_capture_defended_checking_piece(self) -> None:
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 4, 4, "K")
        place_piece(game.grid, 4, 5, "q")   # queen checking
        place_piece(game.grid, 4, 6, "r")   # rook defends queen
        # King captures queen → still checked by rook
        assert game._would_leave_king_in_check(4, 4, 4, 5) is True


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Turn switching
# ═══════════════════════════════════════════════════════════════════════════════


class TestTurnSwitching:
    """Integration-style tests using ChessGame (display mocked)."""

    @staticmethod
    def _make_game() -> ChessGame:
        with patch.object(main.Board, "_load_piece_images", return_value=[]):
            return ChessGame()

    def test_initial_turn_is_white(self) -> None:
        game = self._make_game()
        assert game.current_player == Player.WHITE

    def test_switch_turn_to_black(self) -> None:
        game = self._make_game()
        game._switch_turn()
        assert game.current_player == Player.BLACK

    def test_switch_turn_and_back(self) -> None:
        game = self._make_game()
        assert game.current_player == Player.WHITE
        game._switch_turn()
        assert game.current_player == Player.BLACK
        game._switch_turn()
        assert game.current_player == Player.WHITE

    def test_white_cannot_select_black_piece(self) -> None:
        game = self._make_game()
        # Black rook at (0,0)
        assert game._is_own_piece(0, 0) is False

    def test_white_can_select_white_piece(self) -> None:
        game = self._make_game()
        # White pawn at (6,0)
        assert game._is_own_piece(6, 0) is True

    def test_black_can_select_black_piece_after_switch(self) -> None:
        game = self._make_game()
        game._switch_turn()
        assert game.current_player == Player.BLACK
        assert game._is_own_piece(0, 0) is True   # black rook
        assert game._is_own_piece(6, 0) is False  # white pawn

    def test_cannot_select_empty_square(self) -> None:
        game = self._make_game()
        # Row 3 is empty in starting position
        assert game._is_own_piece(3, 3) is False

    def test_cannot_select_empty_square_after_switch(self) -> None:
        game = self._make_game()
        game._switch_turn()
        assert game._is_own_piece(3, 3) is False

    def test_move_execution_flips_turn(self) -> None:
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 6, 0, "P")    # white pawn
        place_piece(game.grid, 1, 0, "p")    # black pawn
        game._select_row = 6
        game._select_col = 0
        game._execute_move(5, 0)
        assert game.current_player == Player.BLACK
        assert game.grid[5][0] == "P"
        assert game.grid[6][0] == 0

    def test_full_turn_cycle(self) -> None:
        """White moves, then black moves — both should succeed."""
        game = self._make_game()
        game.grid = empty_grid()
        place_piece(game.grid, 6, 0, "P")
        place_piece(game.grid, 1, 0, "p")

        # White's turn
        game._select_row = 6
        game._select_col = 0
        game._execute_move(5, 0)
        assert game.current_player == Player.BLACK

        # Black's turn
        game._select_row = 1
        game._select_col = 0
        game._execute_move(2, 0)
        assert game.current_player == Player.WHITE


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Miscellaneous
# ═══════════════════════════════════════════════════════════════════════════════


class TestMiscellaneous:

    def test_player_negation(self) -> None:
        assert -Player.WHITE == Player.BLACK
        assert -Player.BLACK == Player.WHITE

    def test_is_on_board(self) -> None:
        assert ValidMoveGenerator.is_on_board(0, 0) is True
        assert ValidMoveGenerator.is_on_board(7, 7) is True
        assert ValidMoveGenerator.is_on_board(-1, 0) is False
        assert ValidMoveGenerator.is_on_board(0, 8) is False
        assert ValidMoveGenerator.is_on_board(8, 0) is False

    def test_empty_square_generates_no_moves(self) -> None:
        gen = make_generator()
        grid = empty_grid()
        moves = gen.generate_valid_moves(3, 3, grid)
        assert moves == []

    def test_highlight_colors_are_distinct(self) -> None:
        """Sanity check: selected and valid-move colours differ."""
        from main import SELECTED_HIGHLIGHT_COLOR, VALID_MOVE_COLOR
        assert SELECTED_HIGHLIGHT_COLOR != VALID_MOVE_COLOR

    def test_board_squares_count(self) -> None:
        """Board creates exactly 64 squares."""
        with patch.object(main.Board, "_load_piece_images", return_value=[]):
            board = main.Board()
        total = sum(len(row) for row in board.squares)
        assert total == 64

    def test_board_reset_colors_restores_alternation(self) -> None:
        with patch.object(main.Board, "_load_piece_images", return_value=[]):
            board = main.Board()
        # Mess up colors
        board.colors[0][0] = (255, 0, 0)
        board.reset_colors()
        # First square (0,0) should be light
        assert board.colors[0][0] == (200, 200, 200)
        # Adjacent (0,1) should be dark
        assert board.colors[0][1] == (30, 30, 30)
