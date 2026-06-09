# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 1. 技术栈

语言  Python 3.10+ |
图形库 pygame 2.6.x（窗口渲染、事件处理） |
标准库 `sys`（退出进程） |
运行环境 Windows / Linux / macOS，需图形桌面环境 |
依赖安装 `pip install pygame` |

---

## 2. 代码规范

缩进：4 空格，无 Tab
类型注解：公开方法参数和返回值均标注类型（`x: int`、`-> bool`、`-> None`）
注释语言：所有 docstring 和行内注释使用中文
导入顺序：标准库 → 第三方库 → 项目内模块，每组之间空行分隔
布尔返回值：使用 `True` / `False`，不使用 0/1

---

## 3. 常用命令

```bash
# 运行游戏
python run.py

# 语法检查（全部文件）
python -m py_compile constants.py && python -m py_compile game.py && python -m py_compile renderer.py && python -m py_compile run.py
```

---

## 4. 测试方式

使用 Python 标准库 `unittest` 框架，测试文件为 [test_game.py](test_game.py)，共 **66 项测试**、12 个测试类。

```bash
# 运行全部测试（详细输出）
python -m unittest test_game.py -v

# 直接运行
python test_game.py

# 运行单个测试类
python -m unittest test_game.TestCheckWin -v

# 运行单个测试方法
python -m unittest test_game.TestCheckWin.test_horizontal_middle -v
```

## 5. 项目结构

```
Gobang-master/
  run.py          ← 入口 + 控制层：pygame 初始化、事件循环编排
  renderer.py     ← 视图层：PygameRenderer 类，所有绘制逻辑
  game.py         ← 模型层：Game 类，状态机 + 业务逻辑（可独立测试）
  constants.py    ← 常量层：几何参数、颜色、棋子标记、玩家编码
```


### 各层职责

**constants.py** — 单一真相源
- 棋盘几何：`BOARD_SIZE`、`CELL_SIZE`、`MARGIN_X/Y`
- 窗口尺寸由几何参数推导：`WINDOW_WIDTH = MARGIN_X * 2 + BOARD_PIXEL`
- 全部颜色（`COLOR_BG`、`COLOR_GRID`、`COLOR_BLACK_PIECE` 等）
- 棋子字符（`EMPTY = '-'`、`BLACK = '*'`、`WHITE = 'o'`）
- 玩家编码（`PLAYER_BLACK = 1`、`PLAYER_WHITE = -1`）及显示名映射 `PLAYER_NAME`

**game.py** — 纯逻辑，无 pygame 依赖
- `Game` 类封装一局完整游戏的生命周期
- 状态字段：`board`（10×10 二维列表）、`cur_player`、`finished`、`winner`、`move_count`
- 核心方法：`place_piece()`、`check_win()`、`is_draw()`、`switch_player()`、`reset()`
- 消息方法：`get_turn_message()`、`get_winner_message()`、`get_draw_message()`
- **判胜算法**：沿 4 条轴线（水平/垂直/两对角线）双向累计连续同色棋子，≥5 判胜
- **坐标约定**：`board[row][col]` — `row` 行号 0-9（显示 A-J），`col` 列号 0-9

**renderer.py** — 纯视图，只读 Game 状态
- `PygameRenderer` 类在 `__init__` 预创建 4 个 Font 对象（避免每帧重复分配）
- 公开方法：`draw_board()`、`draw_status()`、`draw_game_over()`、`get_cell_from_pos()`
- 内部方法：`_draw_grid()`、`_draw_labels()`、`_draw_pieces()`
- 像素坐标转换：`get_cell_from_pos()` 中 `row = (mouse_y - MARGIN_Y) // CELL_SIZE`
- 棋子绘制：实心圆 + 1px 外描边

**run.py** — 事件循环编排
- `main()` 函数：初始化 → 创建 Game + Renderer → 进入主循环
- 鼠标点击流程：坐标转换 → 落子 → 判胜 → 判平 → 切换玩家
- 游戏结束后：点击或按 R 键重新开始，Esc 退出
- 帧率：`clock.tick(60)`
