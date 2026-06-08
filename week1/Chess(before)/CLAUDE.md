# CLAUDE.md — Chess

Two-player local chess game built with **Pygame**.  8×8 board, full piece
movement, turn alternation, and move-legality check (can't move into check).

## Project layout

```
Chess/
├── main.py           # All source code (719 lines)
├── Assets/           # 12 piece images (WhiteKing.png … BlackPawn.png)
└── test_chess.py     # pytest test suite
```

## Architecture

```
Player(IntEnum)          WHITE=1, BLACK=-1  (negation-safe)
─────────────────────────────────────────────────────────
ValidMoveGenerator       Pure move generation — zero external state
  ├── _sliding_moves()   Shared by Rook / Bishop / Queen
  ├── _filter_on_board() Bounds filter
  └── _add_pawn_moves()  Unified black + white pawn logic (direction param)
─────────────────────────────────────────────────────────
Board                    Pure display — squares, colours, piece rendering
  ├── _load_piece_images()  try/except pygame.error → clear message + exit
  └── highlight_selected()  Yellow selected square, pink valid moves
─────────────────────────────────────────────────────────
ChessGame                Sole state-holder + event loop (13 methods)
  ├── grid, current_player, game_over, winner
  ├── _find_king()            Static helper → Optional[tuple[int,int]]
  ├── _collect_opponent_positions()  Static helper → MoveList
  └── _would_leave_king_in_check()  41 lines — simulated move + legality
```

**Design rules**
- **No `global` statements** — all state lives on `ChessGame`
- `Board` and `ValidMoveGenerator` are *stateless services*; they receive
  state via parameters, never by reaching into `ChessGame`
- `Piece = Union[int, str]`  (0 = empty, everything else = piece character)
- Coordinates are always `[row, col]` lists (top-left origin)

## Code conventions

| Rule | Detail |
|---|---|
| Type annotations | **100 %** coverage — every parameter, return type, instance var, and most locals |
| Docstrings | RST-style (`"""…"""`) on every public method and the module header |
| Constants | Named `UPPER_CASE` in the constants block (lines 27–72) — no magic numbers |
| Method length | All ≤ **50 lines**; longest is `_would_leave_king_in_check` at 41 |
| Naming | `snake_case` methods, `_private` helpers, descriptive names (no `x`/`y`/`vMoves`) |
| Imports | `from __future__ import annotations` at top; `Callable`, `Optional`, `Union` from typing |
| Strings | Double-quote docstrings, single-quote inline strings |

## Running

```bash
# Launch the game
cd Chess
python main.py
```

Requires **Pygame** (`pip install pygame`).  The `Assets/` folder must be
present beside `main.py`.

```bash
# Run tests
pytest test_chess.py -v
```

Tests use **pytest**.  No special fixtures or conftest needed.

## Known design gaps (not bugs — future work)

| Missing feature | Where it would go |
|---|---|
| Castling | `ValidMoveGenerator.king_moves` + `ChessGame._execute_move` |
| En passant | `ValidMoveGenerator._add_pawn_moves` + grid history |
| Pawn promotion | `ChessGame._execute_move` |
| Checkmate / stalemate detection | `ChessGame._would_leave_king_in_check` + new `_is_checkmate` |
| `game_over` / `winner` fields | Already declared — not yet written to |

## Bugs fixed (regression notes)

1. **Queen move duplication** — original `Queen()` called `Rook()` then
   `Bishop()`, each appending to the *same* `self.vMoves` list, then
   iterated the list and appended again.  Fixed by using `QUEEN_DIRECTIONS`
   directly with `_sliding_moves`.
2. **`validMovegen` vs `validMoveGen`** — `global validMovegen` declared a
   name that never matched the module-level `validMoveGen`.  Eliminated
   entirely when globals were removed.
3. **`turnCheck` selected empty squares** — original `turnCheck` returned
   `True` for `grid[i][j] == 0`, meaning empty squares could pass the
   "own piece" check (caller had a guard, but the logic was wrong).
   Fixed in `_is_own_piece` which returns `False` for empty squares.
4. **Double `reset_colors()` call** — `_execute_move` and
   `_handle_move_attempt` both called `board.reset_colors()` after a
   successful move.  Removed the call inside `_execute_move`.

## When editing

- Keep **all state on `ChessGame`** — never introduce new module-level
  variables or `global` declarations.
- If adding a new piece rule, touch **only** `ValidMoveGenerator`.
- If adding UI (highlights, animations), touch **only** `Board`.
- New constants go in the constants block; use existing type aliases
  (`Grid`, `MoveList`, `Position`) rather than spelling out `list[list[…]]`.
- Any new public method needs a docstring, type annotations, and should
  stay under 50 lines.
