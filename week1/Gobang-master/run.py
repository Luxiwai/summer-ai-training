"""
五子棋游戏入口。

负责编排 pygame 初始化、Game 实例、PygameRenderer 三者的协作。
主循环处理以下逻辑：
  - 鼠标点击落子
  - 获胜 / 平局检测
  - 重新开始（游戏结束后点击鼠标 或 按 R 键）
  - 退出（Esc 键 或 关闭窗口）
"""

import pygame
import sys
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_STATUS_NORMAL, COLOR_STATUS_ERROR, COLOR_STATUS_WIN,
)
from game import Game
from renderer import PygameRenderer


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Gobang — 五子棋")
    clock = pygame.time.Clock()

    game = Game()
    renderer = PygameRenderer(screen)

    message = game.get_turn_message()
    msg_color = COLOR_STATUS_NORMAL

    while True:
        # ------- 事件处理 ------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- 鼠标点击 ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game.finished:
                    # ----- 对局进行中：尝试落子 -----
                    cell = renderer.get_cell_from_pos(*event.pos)
                    if cell is None:
                        message = "请点击棋盘范围内！"
                        msg_color = COLOR_STATUS_ERROR
                    else:
                        row, col = cell
                        if not game.place_piece(row, col):
                            message = "该位置已有棋子，请重新选择！"
                            msg_color = COLOR_STATUS_ERROR
                        else:
                            if game.check_win(row, col):
                                message = game.get_winner_message()
                                msg_color = COLOR_STATUS_WIN
                            elif game.is_draw():
                                game.finished = True
                                message = game.get_draw_message()
                                msg_color = COLOR_STATUS_WIN
                            else:
                                game.switch_player()
                                message = game.get_turn_message()
                                msg_color = COLOR_STATUS_NORMAL
                else:
                    # ----- 游戏已结束：点击重新开始 -----
                    game.reset()
                    message = game.get_turn_message()
                    msg_color = COLOR_STATUS_NORMAL

            # --- 键盘操作 ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game.reset()
                    message = game.get_turn_message()
                    msg_color = COLOR_STATUS_NORMAL

        # ------- 渲染 ---------------------------------------
        renderer.draw_board(game)

        if game.finished:
            renderer.draw_game_over(message, msg_color)
        else:
            renderer.draw_status(message, msg_color)

        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
