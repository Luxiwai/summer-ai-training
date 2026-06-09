# Gobang 五子棋

双人对弈五子棋游戏，基于 Python + pygame 实现。10×10 棋盘，黑方先手，五连获胜，满盘平局。

## 快速开始

```bash
pip install pygame
python run.py
```

弹出 600×680 的图形窗口：鼠标点击棋盘落子，Esc 退出，R 键或点击重新开始。

## 项目结构

```
Gobang-master/
  run.py           入口：pygame 初始化 + 游戏主循环
  renderer.py      视图层：PygameRenderer 类，负责所有绘制
  game.py          模型层：Game 类，纯逻辑（可脱离 pygame 测试）
  constants.py     常量层：棋盘几何、颜色、棋子标记，单一真相源
  test_game.py     单元测试：66 项，unittest 框架
```

**依赖方向**（单向，无循环）：

```
run ──→ renderer ──→ constants
  │                     ↑
  └──────→ game ────────┘
```

## 运行测试

```bash
python -m unittest test_game.py -v    # 全部 66 项
python -m unittest test_game.TestCheckWin -v   # 单个测试类
```

## 核心设计

### 判胜算法（双向计数）

沿水平、垂直、两条对角线共 4 条轴线，正反方向累计连续同色棋子，任意轴线 ≥5 即获胜。修复了旧版只向单一方向检查导致中间落子漏判的 bug。

### 坐标约定

`board[row][col]` — `row` 行号 0-9（显示 A-J），`col` 列号 0-9。pygame 中 `row` 映射到 y 轴（纵向），`col` 映射到 x 轴（横向）。

### 窗口尺寸

所有尺寸由 `constants.py` 中的 `CELL_SIZE` 和 `MARGIN` 推导，修改一处即可全局适配。

## 技术栈

Python 3.10+ · pygame 2.6 · unittest · 无外部依赖
