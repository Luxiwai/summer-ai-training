"""
Game 类的单元测试。

覆盖范围：
  - Game 初始化与可重入性
  - 落子（成功、占位拒绝、边界）
  - 判胜（水平/垂直/两对角线的双向计数、边界、6连、混色拒绝）
  - 平局检测
  - 玩家切换、重置、cur_piece 属性
  - 界面消息汉化
  - constants.py 常量正确性
  - PygameRenderer.get_cell_from_pos() 像素坐标转换

运行方式：
  python -m pytest test_game.py -v
  python -m unittest test_game.py -v
  python test_game.py
"""

import unittest

from constants import (
    BOARD_SIZE, CELL_SIZE, MARGIN_X, MARGIN_Y, BOARD_PIXEL,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    EMPTY, BLACK, WHITE,
    PLAYER_BLACK, PLAYER_WHITE, PLAYER_NAME,
)
from game import Game
from renderer import PygameRenderer


# ================================================================
# Game 初始化
# ================================================================
class TestGameInit(unittest.TestCase):
    """测试 Game.__init__()"""

    def test_creates_empty_board(self):
        g = Game()
        self.assertEqual(len(g.board), BOARD_SIZE)
        self.assertEqual(len(g.board[0]), BOARD_SIZE)
        for row in g.board:
            for cell in row:
                self.assertEqual(cell, EMPTY)

    def test_default_state(self):
        g = Game()
        self.assertEqual(g.cur_player, PLAYER_BLACK)
        self.assertFalse(g.finished)
        self.assertIsNone(g.winner)
        self.assertEqual(g.move_count, 0)
        self.assertEqual(g.size, BOARD_SIZE)

    def test_instances_are_independent(self):
        """多次创建互不干扰（修复了旧 init_board 不可重入的 bug）"""
        g1 = Game()
        g2 = Game()
        g1.place_piece(0, 0)
        self.assertEqual(g2.board[0][0], EMPTY)
        self.assertIsNot(g1.board, g2.board)


# ================================================================
# 落子
# ================================================================
class TestPlacePiece(unittest.TestCase):
    """测试 Game.place_piece()"""

    def setUp(self):
        self.game = Game()

    def test_place_on_empty(self):
        self.assertTrue(self.game.place_piece(0, 0))
        self.assertEqual(self.game.board[0][0], BLACK)
        self.assertEqual(self.game.move_count, 1)

    def test_place_on_occupied(self):
        self.game.place_piece(0, 0)
        self.assertFalse(self.game.place_piece(0, 0))
        self.assertEqual(self.game.move_count, 1)

    def test_black_first(self):
        self.game.place_piece(5, 5)
        self.assertEqual(self.game.board[5][5], BLACK)

    def test_white_second(self):
        self.game.place_piece(0, 0)
        self.game.switch_player()
        self.game.place_piece(1, 1)
        self.assertEqual(self.game.board[1][1], WHITE)

    def test_four_corners(self):
        """边界：四个角落均可落子"""
        for r, c in [(0, 0), (0, 9), (9, 0), (9, 9)]:
            g = Game()
            self.assertTrue(g.place_piece(r, c))

    def test_move_count_tracks_all_placements(self):
        for i in range(10):
            self.game.place_piece(0, i)
        self.assertEqual(self.game.move_count, 10)


# ================================================================
# 判胜（双向计数）
# ================================================================
class TestCheckWin(unittest.TestCase):
    """测试 Game.check_win() — 四条轴线、边界、拒绝误判"""

    def setUp(self):
        self.game = Game()

    def _set_row(self, row, cols, piece=BLACK):
        for c in cols:
            self.game.board[row][c] = piece
        self.game.move_count = sum(
            1 for r in self.game.board for c in r if c != EMPTY
        )

    def _set_col(self, col, rows, piece=BLACK):
        for r in rows:
            self.game.board[r][col] = piece
        self.game.move_count = sum(
            1 for r in self.game.board for c in r if c != EMPTY
        )

    # ----- 水平 -----
    def test_horizontal_start(self):
        self._set_row(0, [0, 1, 2, 3, 4])
        self.assertTrue(self.game.check_win(0, 0))

    def test_horizontal_end(self):
        self._set_row(0, [5, 6, 7, 8, 9])
        self.assertTrue(self.game.check_win(0, 9))

    def test_horizontal_middle(self):
        """新子落在五连中间 —— 双向累计修复旧版漏判"""
        self._set_row(0, [1, 2, 4, 5])
        self.game.board[0][3] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(0, 3))

    def test_horizontal_white(self):
        self.game.cur_player = PLAYER_WHITE
        self._set_row(3, [2, 3, 4, 5, 6], WHITE)
        self.assertTrue(self.game.check_win(3, 4))
        self.assertEqual(self.game.winner, PLAYER_WHITE)

    # ----- 垂直 -----
    def test_vertical_middle(self):
        self._set_col(4, [1, 2, 3, 4, 5])
        self.assertTrue(self.game.check_win(3, 4))

    def test_vertical_top(self):
        self._set_col(0, [0, 1, 2, 3, 4])
        self.assertTrue(self.game.check_win(0, 0))

    def test_vertical_bottom(self):
        self._set_col(9, [5, 6, 7, 8, 9])
        self.assertTrue(self.game.check_win(9, 9))

    # ----- 对角线 \ -----
    def test_diag_backslash_middle(self):
        for i in [0, 1, 2, 3, 4]:
            self.game.board[i][i] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(2, 2))

    def test_diag_backslash_corner(self):
        for i in [5, 6, 7, 8, 9]:
            self.game.board[i][i] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(9, 9))

    def test_diag_backslash_middle_piece(self):
        """对角线 \ 中间落子"""
        for i in [0, 1, 3, 4]:
            self.game.board[i][i] = BLACK
        self.game.board[2][2] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(2, 2))

    # ----- 对角线 / -----
    def test_diag_slash_middle(self):
        for i in [0, 1, 2, 3, 4]:
            self.game.board[i][9 - i] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(2, 7))

    def test_diag_slash_bottom_left(self):
        for i in [5, 6, 7, 8, 9]:
            self.game.board[i][9 - i] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(9, 0))

    def test_diag_slash_middle_piece(self):
        """对角线 / 中间落子"""
        for i in [0, 1, 3, 4]:
            self.game.board[i][9 - i] = BLACK
        self.game.board[2][7] = BLACK
        self.game.move_count = 5
        self.assertTrue(self.game.check_win(2, 7))

    # ----- 拒绝误判 -----
    def test_four_pieces_no_win(self):
        self._set_row(0, [0, 1, 2, 3])
        self.assertFalse(self.game.check_win(0, 0))
        self.assertFalse(self.game.finished)

    def test_scattered_no_win(self):
        """不连续的五子（中间有空格）"""
        self._set_row(0, [0, 1, 2, 4, 5])
        self.assertFalse(self.game.check_win(0, 2))

    def test_mixed_colors_no_win(self):
        self._set_row(0, [0, 1, 2, 3], BLACK)
        self.game.board[0][4] = WHITE
        self.game.move_count = 5
        self.assertFalse(self.game.check_win(0, 3))

    def test_empty_cell_no_win(self):
        self.assertFalse(self.game.check_win(0, 0))

    # ----- 边界 + 特殊 -----
    def test_six_in_a_row(self):
        """6 连也应判胜"""
        self._set_row(0, [0, 1, 2, 3, 4, 5])
        self.assertTrue(self.game.check_win(0, 0))

    def test_win_sets_finished_and_winner(self):
        self._set_row(0, [0, 1, 2, 3, 4])
        self.game.check_win(0, 2)
        self.assertTrue(self.game.finished)
        self.assertEqual(self.game.winner, PLAYER_BLACK)

    def test_win_on_different_row(self):
        """非首行也能正确判胜"""
        self._set_row(7, [2, 3, 4, 5, 6])
        self.assertTrue(self.game.check_win(7, 4))

    def test_check_win_without_recent_place(self):
        """即使 move_count 未更新，只要棋盘上有五连就能检出"""
        g = Game()
        for c in range(5):
            g.board[0][c] = BLACK
        g.move_count = 0  # 模拟未正常落子的情况
        self.assertTrue(g.check_win(0, 2))


# ================================================================
# 平局
# ================================================================
class TestDraw(unittest.TestCase):
    """测试 Game.is_draw()"""

    def test_full_board_is_draw(self):
        g = Game()
        g.move_count = 100
        self.assertTrue(g.is_draw())

    def test_not_full_is_not_draw(self):
        g = Game()
        g.move_count = 99
        self.assertFalse(g.is_draw())

    def test_finished_not_draw(self):
        g = Game()
        g.move_count = 100
        g.finished = True
        self.assertFalse(g.is_draw())

    def test_empty_is_not_draw(self):
        self.assertFalse(Game().is_draw())

    def test_one_move_is_not_draw(self):
        g = Game()
        g.move_count = 1
        self.assertFalse(g.is_draw())


# ================================================================
# 玩家切换
# ================================================================
class TestSwitchPlayer(unittest.TestCase):
    """测试 Game.switch_player()"""

    def test_black_to_white(self):
        g = Game()
        g.switch_player()
        self.assertEqual(g.cur_player, PLAYER_WHITE)
        self.assertEqual(g.cur_piece, WHITE)

    def test_white_to_black(self):
        g = Game()
        g.switch_player()
        g.switch_player()
        self.assertEqual(g.cur_player, PLAYER_BLACK)
        self.assertEqual(g.cur_piece, BLACK)

    def test_even_switches_restore_black(self):
        g = Game()
        for _ in range(10):
            g.switch_player()
        self.assertEqual(g.cur_player, PLAYER_BLACK)

    def test_odd_switches_yield_white(self):
        g = Game()
        for _ in range(7):
            g.switch_player()
        self.assertEqual(g.cur_player, PLAYER_WHITE)


# ================================================================
# 重置
# ================================================================
class TestReset(unittest.TestCase):
    """测试 Game.reset()"""

    def test_clears_board(self):
        g = Game()
        for i in range(5):
            g.place_piece(i, i)
        g.reset()
        for row in g.board:
            for cell in row:
                self.assertEqual(cell, EMPTY)

    def test_restores_initial_state(self):
        g = Game()
        g.place_piece(3, 3)
        g.switch_player()
        g.reset()
        self.assertEqual(g.cur_player, PLAYER_BLACK)
        self.assertFalse(g.finished)
        self.assertIsNone(g.winner)
        self.assertEqual(g.move_count, 0)

    def test_place_after_reset(self):
        g = Game()
        g.place_piece(0, 0)
        g.reset()
        self.assertTrue(g.place_piece(0, 0))

    def test_reset_after_win(self):
        g = Game()
        for c in range(5):
            g.board[0][c] = BLACK
        g.move_count = 5
        g.check_win(0, 2)
        g.reset()
        self.assertFalse(g.finished)
        self.assertIsNone(g.winner)


# ================================================================
# cur_piece 属性
# ================================================================
class TestCurPiece(unittest.TestCase):
    """测试 Game.cur_piece 属性"""

    def test_initial_is_black(self):
        self.assertEqual(Game().cur_piece, BLACK)

    def test_after_switch_is_white(self):
        g = Game()
        g.switch_player()
        self.assertEqual(g.cur_piece, WHITE)

    def test_after_reset_is_black(self):
        g = Game()
        g.switch_player()
        g.reset()
        self.assertEqual(g.cur_piece, BLACK)


# ================================================================
# 界面消息
# ================================================================
class TestMessages(unittest.TestCase):
    """测试 Game 的消息方法"""

    def test_turn_black(self):
        msg = Game().get_turn_message()
        self.assertIn('黑方', msg)
        self.assertIn('的回合', msg)

    def test_turn_white(self):
        g = Game()
        g.switch_player()
        msg = g.get_turn_message()
        self.assertIn('白方', msg)
        self.assertIn('的回合', msg)

    def test_winner_black(self):
        g = Game()
        g.winner = PLAYER_BLACK
        msg = g.get_winner_message()
        self.assertIn('黑方', msg)
        self.assertIn('获胜', msg)

    def test_winner_white(self):
        g = Game()
        g.winner = PLAYER_WHITE
        msg = g.get_winner_message()
        self.assertIn('白方', msg)
        self.assertIn('获胜', msg)

    def test_winner_none_returns_draw(self):
        msg = Game().get_winner_message()
        self.assertIn('平局', msg)

    def test_draw_message_content(self):
        msg = Game().get_draw_message()
        self.assertIn('棋盘已满', msg)
        self.assertIn('平局', msg)


# ================================================================
# 常量
# ================================================================
class TestConstants(unittest.TestCase):
    """测试 constants.py 中的常量和推导关系"""

    def test_board_pixel_derivation(self):
        self.assertEqual(BOARD_PIXEL, BOARD_SIZE * CELL_SIZE)

    def test_window_width_derivation(self):
        self.assertEqual(WINDOW_WIDTH, MARGIN_X * 2 + BOARD_PIXEL)

    def test_window_height_derivation(self):
        self.assertEqual(WINDOW_HEIGHT, MARGIN_Y * 2 + BOARD_PIXEL + 80)

    def test_player_values_distinct(self):
        self.assertNotEqual(PLAYER_BLACK, PLAYER_WHITE)

    def test_piece_chars_distinct(self):
        self.assertNotEqual(EMPTY, BLACK)
        self.assertNotEqual(EMPTY, WHITE)
        self.assertNotEqual(BLACK, WHITE)

    def test_player_name_maps_both(self):
        self.assertIn(PLAYER_BLACK, PLAYER_NAME)
        self.assertIn(PLAYER_WHITE, PLAYER_NAME)


# ================================================================
# Renderer 静态方法（无需 pygame 窗口）
# ================================================================
class TestGetCellFromPos(unittest.TestCase):
    """测试 PygameRenderer.get_cell_from_pos() 像素坐标转换"""

    def test_center_of_cell(self):
        px = MARGIN_X + 3 * CELL_SIZE + CELL_SIZE // 2
        py = MARGIN_Y + 2 * CELL_SIZE + CELL_SIZE // 2
        self.assertEqual(
            PygameRenderer.get_cell_from_pos(px, py), (2, 3)
        )

    def test_top_left_corner(self):
        self.assertEqual(
            PygameRenderer.get_cell_from_pos(MARGIN_X, MARGIN_Y), (0, 0)
        )

    def test_bottom_right_corner(self):
        px = MARGIN_X + 9 * CELL_SIZE + 1
        py = MARGIN_Y + 9 * CELL_SIZE + 1
        self.assertEqual(
            PygameRenderer.get_cell_from_pos(px, py), (9, 9)
        )

    def test_outside_top_left(self):
        self.assertIsNone(PygameRenderer.get_cell_from_pos(0, 0))

    def test_outside_bottom(self):
        self.assertIsNone(PygameRenderer.get_cell_from_pos(300, 700))

    def test_outside_right(self):
        self.assertIsNone(PygameRenderer.get_cell_from_pos(700, 300))

    def test_negative_coordinates(self):
        self.assertIsNone(PygameRenderer.get_cell_from_pos(-1, -1))

    def test_on_grid_line(self):
        """点击网格线应归入右下方的格子"""
        px = MARGIN_X + 1 * CELL_SIZE  # 恰好在第 1 条竖线上
        py = MARGIN_Y + 1 * CELL_SIZE  # 恰好在第 1 条横线上
        self.assertEqual(
            PygameRenderer.get_cell_from_pos(px, py), (1, 1)
        )


if __name__ == '__main__':
    unittest.main()
