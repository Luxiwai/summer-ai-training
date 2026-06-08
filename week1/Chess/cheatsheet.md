# Chess 项目常用命令速查表

## 环境准备

```bash
# 安装依赖
pip install pygame pytest
```

## 运行游戏

```bash
cd Chess
python main.py
```

| 操作 | 说明 |
|---|---|
| 点击己方棋子 | 选中，黄色高亮 |
| 点击粉色目标格 | 走子 |
| 再次点击选中棋子 / 点击空白 | 取消选中 |
| 关闭窗口 | 退出游戏 |

## 测试

```bash
pytest test_chess.py -v               # 全部 72 个测试（详细）
pytest test_chess.py -v -k "Pawn"     # 仅兵相关
pytest test_chess.py -v -k "Rook"     # 仅车相关
pytest test_chess.py -v -k "Knight"   # 仅马相关
pytest test_chess.py -v -k "Bishop"   # 仅象相关
pytest test_chess.py -v -k "King"     # 仅王相关
pytest test_chess.py -v -k "Queen"    # 仅后相关
pytest test_chess.py -v -k "Check"    # 仅将军检测
pytest test_chess.py -v -k "Turn"     # 仅回合切换
pytest test_chess.py -v -k "Board"    # 仅棋盘初始化
pytest test_chess.py -v --tb=short    # 失败时精简回溯
pytest test_chess.py -v --tb=long     # 失败时完整回溯
pytest test_chess.py -q               # 安静模式（仅统计）
pytest test_chess.py --co             # 仅显示已收集的测试名（不执行）
```

## 代码质量

```bash
# 语法检查（不执行）
python -c "import ast; ast.parse(open('main.py').read()); print('OK')"
python -c "import ast; ast.parse(open('test_chess.py').read()); print('OK')"

# 编译检查
python -m py_compile main.py

# 行数统计
wc -l main.py test_chess.py
```

## 文件结构速览

```
Chess/
├── main.py            # 游戏源码（~720 行）
├── test_chess.py      # 单元测试（72 cases）
├── CLAUDE.md          # 项目架构文档
├── Assets/            # 12 张棋子图片
│   ├── WhiteKing.png … WhitePawn.png
│   └── BlackKing.png … BlackPawn.png
└── cheatsheet.md      # 本文件
```

## 架构速查

| 类 | 职责 | 方法数 |
|---|---|---|
| `Player` | IntEnum: WHITE=1, BLACK=-1 | — |
| `ValidMoveGenerator` | 纯走法计算 | 13 |
| `Board` | 纯显示（绘制、高亮）| 7 |
| `ChessGame` | 状态持有 + 事件循环 | 13 |

## 编码规范速查

| 规则 | 示例 |
|---|---|
| 类型注解 100% | `def func(row: int, grid: Grid) -> MoveList:` |
| RST docstring | `"""Return ..."""` 所有公开方法 |
| 零 `global` | 状态全在 `ChessGame` |
| 常量大写 | `BOARD_SIZE`, `LIGHT_SQUARE_COLOR` |
| 私有方法 `_` 前缀 | `_same_color()`, `_find_king()` |
| 坐标 `[row, col]` | 左上角为原点 |
| 空格子 = `0` | `Piece = Union[int, str]` |
