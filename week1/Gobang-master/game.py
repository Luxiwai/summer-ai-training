"""
Game 类 —— 封装全部游戏状态与核心逻辑。

取代了旧的全局变量 (variables.py) 以及散落在 board.py / win.py / play.py
中的逻辑，集中为一个可单独测试的单元。
"""

from constants import BOARD_SIZE, EMPTY, BLACK, WHITE, PLAYER_BLACK, PLAYER_WHITE, PLAYER_NAME


class Game:
    """一局五子棋游戏。"""

    def __init__(self):
        self.size = BOARD_SIZE
        # 每次实例化都创建全新棋盘（可重入 —— 修复了旧 init_board()
        # 重复调用会不断追加行的 bug）。
        self.board = [[EMPTY] * self.size for _ in range(self.size)]
        self.cur_player = PLAYER_BLACK          # 黑方先手
        self.finished = False                    # 游戏是否结束
        self.winner = None                       # None | PLAYER_BLACK | PLAYER_WHITE
        self.move_count = 0                      # 已落子数

    # ----------------------------------------------------------
    # 派生属性
    # ----------------------------------------------------------
    @property
    def cur_piece(self) -> str:
        """当前玩家对应的棋子字符。"""
        return BLACK if self.cur_player == PLAYER_BLACK else WHITE

    # ----------------------------------------------------------
    # 核心操作
    # ----------------------------------------------------------
    def place_piece(self, x: int, y: int) -> bool:
        """
        尝试在 (x, y) 落子。
        成功返回 True，若该位置已有棋子则返回 False。
        x — 行索引 (0-9)，  y — 列索引 (0-9)。
        """
        if self.board[x][y] != EMPTY:
            return False
        self.board[x][y] = self.cur_piece
        self.move_count += 1
        return True

    def check_win(self, x: int, y: int) -> bool:
        """
        判断刚落在 (x, y) 的棋子是否形成五连。

        ** 修复了原版单向检测的 bug **
        旧算法只从落子位置向单一方向检查 4 格，当新子落在五连的
        *中间* 位置时（如两侧各有 2 子）会漏判。本实现沿每条轴线
        双向累计连续同色棋子数，正确识别任意形态的五连。
        """
        piece = self.board[x][y]
        if piece == EMPTY:
            return False

        # 四条轴线：水平、垂直、对角线\、对角线/
        axes = ((0, 1), (1, 0), (1, 1), (1, -1))

        for dx, dy in axes:
            count = 1  # 刚落下的这枚棋子

            # 正方向累计连续同色棋子
            i = 1
            while (0 <= x + i * dx < self.size
                   and 0 <= y + i * dy < self.size
                   and self.board[x + i * dx][y + i * dy] == piece):
                count += 1
                i += 1

            # 反方向累计连续同色棋子
            i = 1
            while (0 <= x - i * dx < self.size
                   and 0 <= y - i * dy < self.size
                   and self.board[x - i * dx][y - i * dy] == piece):
                count += 1
                i += 1

            if count >= 5:
                self.finished = True
                self.winner = self.cur_player
                return True

        return False

    def is_draw(self) -> bool:
        """棋盘已满且无人获胜时返回 True。"""
        return self.move_count >= self.size * self.size and not self.finished

    def switch_player(self):
        """切换当前玩家（黑 ↔ 白）。"""
        self.cur_player = (PLAYER_WHITE if self.cur_player == PLAYER_BLACK
                           else PLAYER_BLACK)

    def reset(self):
        """清空棋盘，开始新的一局。"""
        self.board = [[EMPTY] * self.size for _ in range(self.size)]
        self.cur_player = PLAYER_BLACK
        self.finished = False
        self.winner = None
        self.move_count = 0

    # ----------------------------------------------------------
    # 界面消息辅助方法（消除玩家常量→显示字符串的重复映射）
    # ----------------------------------------------------------
    def get_turn_message(self) -> str:
        """例如 '黑方 (*) 的回合'"""
        return f"{PLAYER_NAME[self.cur_player]} 的回合"

    def get_winner_message(self) -> str:
        """例如 '黑方 (*) 获胜！' —— 仅在 winner 已设置时调用。"""
        if self.winner is None:
            return "平局！"
        return f"{PLAYER_NAME[self.winner]} 获胜！"

    def get_draw_message(self) -> str:
        """平局提示信息。"""
        return "棋盘已满，平局！"
