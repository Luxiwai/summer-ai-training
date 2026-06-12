"""
将海报 HTML 文件转换为 PNG 图片。

用法:
    python generate_image.py                  # 默认转换 duanwu-poster.html
    python generate_image.py poster.html      # 指定 HTML 文件
    python generate_image.py poster.html -o out.png  # 指定输出文件名

依赖:
    pip install playwright
    playwright install chromium
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("output")

# ---------------------------------------------------------------------------
# 书法字体本地化补丁
# Google Fonts 在国内无法访问，用 Windows 自带书法字体替代。
# 同时尝试从国内 CDN 加载思源字体作为后备。
# ---------------------------------------------------------------------------

FONT_REPLACEMENT_CSS = """
/* === 书法字体本地化（替代 Google Fonts）=== */

/* 马山正 → 华文行楷（Windows 自带毛笔书法字体） */
@font-face {
    font-family: 'Ma Shan Zheng';
    src: local('STXingkai'), local('华文行楷'), local('KaiTi');
    font-display: swap;
}

/* 站酷小薇 → 华文楷体 */
@font-face {
    font-family: 'ZCOOL XiaoWei';
    src: local('STKaiti'), local('华文楷体'), local('KaiTi');
    font-display: swap;
}

/* 站酷快快体 → 方正舒体（也有毛笔感） */
@font-face {
    font-family: 'ZCOOL KuaiLe';
    src: local('FZShuTi'), local('方正舒体'), local('STXingkai'), local('华文行楷');
    font-display: swap;
}

/* 思源宋体 → 华文宋体 / 宋体 */
@font-face {
    font-family: 'Noto Serif SC';
    src: local('STSong'), local('华文宋体'), local('SimSun'), local('NSimSun');
    font-display: swap;
    /* 尝试从国内 CDN 加载真正的思源宋体 */
    /* LiteOcr 字体镜像——如加载成功则覆盖 local */
}

/* 补充：从国内镜像尝试下载思源宋体（中等字重） */
@font-face {
    font-family: 'Noto Serif SC Web';
    src: local('STSong'), local('SimSun'),
         url('https://cdn.jsdelivr.net/npm/@aspect-build/aspect-fonts@1.0.0/NotoSerifSC-Regular.otf') format('opentype');
    font-display: swap;
}
"""

# 匹配 Google Fonts 的 @import 语句
_GOOGLE_FONTS_RE = re.compile(
    r"@import\s+url\(['\"]https?://fonts\.googleapis\.com/[^)]+\)\s*;",
    re.IGNORECASE,
)


def patch_html_for_fonts(html_path: Path) -> Path:
    """
    读取 HTML 文件，将 Google Fonts 引用替换为本地字体定义。
    返回（可能已修补的）HTML 文件路径。
    """
    content = html_path.read_text(encoding="utf-8")

    if not _GOOGLE_FONTS_RE.search(content):
        return html_path  # 无需修改

    # 替换 Google Fonts @import
    patched = _GOOGLE_FONTS_RE.sub(
        f"/* Google Fonts 已替换为本地书法字体 */\n{FONT_REPLACEMENT_CSS}",
        content,
    )

    # 写入临时文件
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", prefix="poster_",
        encoding="utf-8", delete=False,
    )
    tmp.write(patched)
    tmp.close()
    return Path(tmp.name)


def html_to_png(html_path: str, output_path: str | None = None) -> str:
    """
    将 HTML 文件渲染为 PNG 截图。

    Args:
        html_path: HTML 文件路径
        output_path: 输出 PNG 路径，默认与 HTML 同名（放入 output/ 目录）

    Returns:
        输出 PNG 的绝对路径
    """
    from playwright.sync_api import sync_playwright

    html_file = Path(html_path).resolve()
    if not html_file.exists():
        raise FileNotFoundError(f"HTML 文件不存在: {html_file}")

    # 处理 Google Fonts → 本地书法字体
    render_file = patch_html_for_fonts(html_file)
    is_temp = render_file != html_file

    # 确定输出路径
    if output_path is None:
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_file = OUTPUT_DIR / f"{html_file.stem}.png"
    else:
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    file_url = render_file.as_uri()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": 1080, "height": 1440},
                device_scale_factor=2,  # 2x 高清输出 → 2160×2880
            )

            page.goto(file_url, wait_until="networkidle")

            # 等待本地字体渲染完成
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)

            page.screenshot(
                path=str(output_file),
                full_page=False,
            )

            browser.close()
    finally:
        # 删除临时文件
        if is_temp and render_file.exists():
            os.unlink(render_file)

    print(f"[OK] 图片已生成: {output_file} ({output_file.stat().st_size // 1024} KB)")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="将海报 HTML 转为 PNG 图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python generate_image.py
    python generate_image.py duanwu-poster.html
    python generate_image.py poster.html -o my_poster.png
        """,
    )
    parser.add_argument(
        "html",
        nargs="?",
        default="duanwu-poster.html",
        help="HTML 文件路径 (默认: duanwu-poster.html)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出 PNG 路径 (默认: output/<html文件名>.png)",
    )
    args = parser.parse_args()

    try:
        html_to_png(args.html, args.output)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError:
        print("[ERROR] 缺少 playwright 依赖，请先安装:", file=sys.stderr)
        print("   pip install playwright", file=sys.stderr)
        print("   playwright install chromium", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
