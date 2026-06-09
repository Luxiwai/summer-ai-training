"""
PygameRenderer —— 五子棋游戏的纯视图层。

所有 pygame 绘制逻辑集中于此。Font 对象在 __init__ 中一次性创建
（消除了旧版每帧重复创建的性能问题），所有布局坐标均由 constants.py
推导得出，保证单一真相源。
"""

import pygame
from constants import (
    BOARD_SIZE, CELL_SIZE,
    MARGIN_X, MARGIN_Y, BOARD_PIXEL,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    STATUS_CENTER_Y, WINNER_TEXT_Y, HINT_TEXT_Y,
    COLOR_BG, COLOR_GRID, COLOR_LABEL, COLOR_OUTLINE,
    COLOR_BLACK_PIECE, COLOR_WHITE_PIECE, COLOR_HINT,
    EMPTY, BLACK,
)


class PygameRenderer:
    """负责五子棋棋盘及状态信息的所有 pygame 渲染。"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # ---- 预创建 Font 对象（一次性，避免每帧重复创建）----
        self.font_label = pygame.font.Font(None, 28)
        self.font_status = pygame.font.Font(None, 30)
        self.font_winner = pygame.font.Font(None, 36)
        self.font_hint = pygame.font.Font(None, 22)

    # ---------------------------------------------------------------
    # 公开接口
    # ---------------------------------------------------------------
    def draw_board(self, game) -> None:
        """
        绘制完整棋盘：背景、网格线、行列标签、全部棋子。
        参数 game 为 Game 实例，读取其 .board 和 .size。
        """
        self.screen.fill(COLOR_BG)
        self._draw_grid()
        self._draw_labels()
        self._draw_pieces(game)

    def draw_status(self, message: str, color: tuple) -> None:
        """在棋盘下方绘制单行状态信息。"""
        text = self.font_status.render(message, True, color)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, STATUS_CENTER_Y))
        self.screen.blit(text, rect)

    def draw_game_over(self, message: str, color: tuple) -> None:
        """绘制游戏结束信息及操作提示。"""
        # 主信息（获胜 / 平局）
        text = self.font_winner.render(message, True, color)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINNER_TEXT_Y))
        self.screen.blit(text, rect)

        # 操作提示
        hint = self.font_hint.render("点击鼠标重新开始  •  Esc 退出",
                                     True, COLOR_HINT)
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, HINT_TEXT_Y))
        self.screen.blit(hint, hint_rect)

    @staticmethod
    def get_cell_from_pos(mouse_x: int, mouse_y: int):
        """
        将鼠标像素坐标转换为棋盘索引 (row, col)。
        若点击落在棋盘区域之外则返回 None。
        """
        row = (mouse_y - MARGIN_Y) // CELL_SIZE
        col = (mouse_x - MARGIN_X) // CELL_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
        return None

    # ---------------------------------------------------------------
    # 内部绘制辅助方法
    # ---------------------------------------------------------------
    def _draw_grid(self) -> None:
        """绘制 10×10 网格线。"""
        for i in range(BOARD_SIZE + 1):          # 10 格需要 11 条线
            # 竖线
            x = MARGIN_X + i * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_GRID,
                             (x, MARGIN_Y),
                             (x, MARGIN_Y + BOARD_PIXEL), 1)
            # 横线
            y = MARGIN_Y + i * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_GRID,
                             (MARGIN_X, y),
                             (MARGIN_X + BOARD_PIXEL, y), 1)

    def _draw_labels(self) -> None:
        """绘制列号 (0-9) 和行号 (A-J)。"""
        # 列标签
        for col in range(BOARD_SIZE):
            text = self.font_label.render(str(col), True, COLOR_LABEL)
            rect = text.get_rect(
                center=(MARGIN_X + col * CELL_SIZE + CELL_SIZE // 2,
                        MARGIN_Y - 18))
            self.screen.blit(text, rect)

        # 行标签
        for row in range(BOARD_SIZE):
            text = self.font_label.render(chr(ord('A') + row), True,
                                          COLOR_LABEL)
            rect = text.get_rect(
                center=(MARGIN_X - 18,
                        MARGIN_Y + row * CELL_SIZE + CELL_SIZE // 2))
            self.screen.blit(text, rect)

    def _draw_pieces(self, game) -> None:
        """绘制所有已落棋子（实心圆 + 外描边）。"""
        radius = CELL_SIZE // 2 - 5
        for r in range(game.size):
            for c in range(game.size):
                piece = game.board[r][c]
                if piece == EMPTY:
                    continue
                cx = MARGIN_X + c * CELL_SIZE + CELL_SIZE // 2
                cy = MARGIN_Y + r * CELL_SIZE + CELL_SIZE // 2
                fill = (COLOR_BLACK_PIECE if piece == BLACK
                        else COLOR_WHITE_PIECE)
                pygame.draw.circle(self.screen, fill, (cx, cy), radius)
                pygame.draw.circle(self.screen, COLOR_OUTLINE,
                                   (cx, cy), radius, 1)
