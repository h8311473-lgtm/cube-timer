#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔方计时器 (Cube Timer) —— 电脑端桌面程序
风格：浅色 / 大圆角卡片 / 柔和渐变 / 药丸按钮（苹果风）

操作方式
    按住 [空格] 不放  ->  计时区进入“准备”（绿色）
    松开 [空格]       ->  立即开始计时
    再按 [空格]       ->  停止计时并记录成绩
    [Esc]             ->  取消本次（不记录）

成绩统计
    最好成绩 / 平均成绩 / mo3 / ao5 / ao12 / ao50 / ao100
    平均采用 WCA 规则：去掉最好与最差后取算术平均
    （样本不足显示 “—”，被计入的部分含 DNF 则该平均为 DNF）

成绩管理
    删除本次成绩（最新一条）/ 删除选中 / 全部清空，均可 Ctrl+Z 撤销
    成绩自动保存在程序同目录 cube_times.json，可导出 CSV

仅依赖 Python 标准库（tkinter），无需安装第三方包。
"""

from __future__ import annotations

import csv
import ctypes
import json
import os
import statistics
import time
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

# --------------------------------------------------------------------------
# 基本常量
# --------------------------------------------------------------------------

APP_TITLE = "魔方计时器"
APP_VERSION = "2.0"
DATA_FILE = Path(__file__).resolve().parent / "cube_times.json"
SETTINGS_FILE = Path(__file__).resolve().parent / "cube_settings.json"

# 可用环境变量重定向数据/设置文件（自动化测试用，避免碰到真实成绩）
if os.environ.get("CUBE_TIMER_DATA"):
    DATA_FILE = Path(os.environ["CUBE_TIMER_DATA"])
if os.environ.get("CUBE_TIMER_SETTINGS"):
    SETTINGS_FILE = Path(os.environ["CUBE_TIMER_SETTINGS"])

HOLD_MS = 350                 # 按住超过该时长才进入“准备”，防手滑
UI_TICK_MS = 25               # 计时刷新间隔
UNDO_LIMIT = 8
MAX_DISPLAY_MS = 59 * 60 * 1000 + 99900

# ---- 配色 ----
# 所有颜色都放在主题调色板里，运行时可通过 视图 菜单或 Ctrl+L 切换日间/夜间。
LIGHT_THEME = {
    "name": "日间",
    "BG_TOP": "#fbfbfe",      # 背景渐变起点
    "BG_BOTTOM": "#e9e9f8",   # 背景渐变终点（淡紫）
    "CARD": "#f6f6fc",
    "CARD_TOP": "#fbfbff",
    "CARD_BOTTOM": "#eef0fb",
    "CARD_LINE": "#e4e2f2",
    "CARD_HIGHLIGHT": "#ffffff",
    "TEXT": "#1f2033",        # 主文字
    "MUTED": "#6f7189",       # 次要文字
    "FAINT": "#a2a4b8",       # 更弱提示
    "TRACK": "#f2f2f8",       # 分隔线 / 轨道
    "ACCENT": "#7c6cf0",
    "ACCENT_DEEP": "#5b4bd6",
    "READY_TXT": "#12a15c",   # 准备就绪
    "READY_BG": "#e7f8ef",
    "READY_LINE": "#c7eeda",
    "RUN_TXT": "#5b4bd6",     # 计时中
    "RUN_BG": "#f1eefe",
    "RUN_LINE": "#ded8fb",
    "BEST_TXT": "#12a15c",
    "DNF_TXT": "#e0473f",
    "LATEST_TXT": "#6d5ef0",
    "ROW_HOVER": "#f7f6fe",
    "SEL_BG": "#f1eefe",
    "SHADOW": "#c9c7e4",
    "SCROLL": "#dcd9ef",
    "SOFT_BTN_FILL": "#fdecec",
    "SOFT_BTN_LINE": "#f8d7d6",
    "SOFT_BTN_TEXT": "#d93a32",
    "SOFT_BTN_HOVER": "#fbdcdb",
    "GHOST_BTN_FILL": "#ffffff",
    "GHOST_BTN_LINE": "#e6e3f3",
    "GHOST_BTN_TEXT": "#6f7189",
    "GHOST_BTN_HOVER": "#f5f3fd",
    "ACTIVE_BTN_FILL": "#efeafd",
    "ACTIVE_BTN_LINE": "#ddd4fb",
    "ACTIVE_BTN_TEXT": "#5b4bd6",
    "ACCENT_SOFT": "#7c6cf0",
}

DARK_THEME = {
    "name": "夜间",
    "BG_TOP": "#0a0a0f",
    "BG_BOTTOM": "#14141d",
    "CARD": "#1a1924",            # 玻璃卡片基色
    "CARD_TOP": "#22202e",
    "CARD_BOTTOM": "#15151e",
    "CARD_LINE": "#38314f",
    "CARD_HIGHLIGHT": "#4a4264",
    "TEXT": "#f2f2f7",
    "MUTED": "#9a9aa8",
    "FAINT": "#6e6e7d",
    "TRACK": "#2b2742",
    "ACCENT": "#8b7cff",
    "ACCENT_DEEP": "#6d5ce0",
    "READY_TXT": "#32d978",
    "READY_BG": "#122a1e",
    "READY_LINE": "#1f4a34",
    "RUN_TXT": "#a99cff",
    "RUN_BG": "#1a1830",
    "RUN_LINE": "#2c2750",
    "BEST_TXT": "#32d978",
    "DNF_TXT": "#ff6b6b",
    "LATEST_TXT": "#a99cff",
    "ROW_HOVER": "#1e1e26",
    "SEL_BG": "#26233d",
    "SHADOW": "#06050c",          # 阴影：偏紫黑
    "SCROLL": "#3a3a46",
    "SOFT_BTN_FILL": "#2a1618",
    "SOFT_BTN_LINE": "#452226",
    "SOFT_BTN_TEXT": "#ff8a8a",
    "SOFT_BTN_HOVER": "#3a1c20",
    "GHOST_BTN_FILL": "#1b1b22",
    "GHOST_BTN_LINE": "#3a3159",   # 深紫描边
    "GHOST_BTN_TEXT": "#b8b8c4",
    "GHOST_BTN_HOVER": "#26262f",
    "ACTIVE_BTN_FILL": "#241f3d",
    "ACTIVE_BTN_LINE": "#3a3163",
    "ACTIVE_BTN_TEXT": "#b3a7ff",
    "ACCENT_SOFT": "#8b7cff",
}

THEMES = {"light": LIGHT_THEME, "dark": DARK_THEME}
# 当前生效的调色板（模块级可变字典：切换主题时原地更新，各处引用自动生效）
PALETTE = dict(LIGHT_THEME)
THEME = "light"


def apply_palette(mode: str) -> None:
    """切换全局调色板（原地更新 PALETTE 并同步模块级颜色常量）。"""
    global THEME
    THEME = mode if mode in THEMES else "light"
    PALETTE.update(THEMES[THEME])
    globals().update({k: v for k, v in PALETTE.items() if k.isupper()})


def t(key: str) -> str:
    """取当前主题的颜色。"""
    return PALETTE.get(key, "#000000")


apply_palette("light")

# ---- 字体 ----
# 说明：优先使用 Windows 11 自带的可变字体（Segoe UI Variable，跟 SF Pro 很接近），
# 中文用 Noto Sans SC（思源黑体）或微软雅黑 UI。数字用等宽数字的 UI 字体，
# 既避免计时跳动，也比 Consolas 秀气。
FONT_UI_NAMES = ("Microsoft YaHei UI", "Noto Sans SC", "Microsoft YaHei",
                 "PingFang SC", "Segoe UI", "Arial")
FONT_DISPLAY_NAMES = ("Segoe UI Variable Display", "Segoe UI Variable Text",
                      "Segoe UI", "Microsoft YaHei UI", "Arial")
FONT_DISPLAY_LIGHT_NAMES = ("Segoe UI Variable Display Light",
                            "Segoe UI Variable Text Light", "Segoe UI Light",
                            "Microsoft YaHei UI Light")
FONT_UI_STACK = "Microsoft YaHei UI"
FONT_DISPLAY_STACK = "Segoe UI"
FONT_DISPLAY_LIGHT = "Segoe UI Light"

FONT_UI = "Microsoft YaHei UI"
FONT_NUM = "Segoe UI"

# ---- 响应式：以窗口可用高度为基准等比缩放 ----
BASE_H = 820
MIN_SCALE, MAX_SCALE = 0.78, 1.40

# 统计项：(键, 显示名, 窗口大小)  窗口 0 表示特殊项
STAT_ITEMS = [
    ("best",  "最好成绩",   0),
    ("ao5",   "五次平均",   5),
    ("ao12",  "十二次平均", 12),
    ("mo3",   "三次平均",   3),
    ("ao50",  "五十次平均", 50),
    ("ao100", "一百次平均", 100),
]


def enable_dpi_awareness() -> float:
    """开启 DPI 感知，返回系统缩放比例（1.0 = 96dpi / 100%）。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # 每显示器 DPI 感知
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    return get_ui_scale()


def get_ui_scale() -> float:
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        if dpi:
            return max(1.0, dpi / 96.0)
    except Exception:
        pass
    try:
        dc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)   # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, dc)
        if dpi:
            return max(1.0, dpi / 96.0)
    except Exception:
        pass
    return 1.0


def choose_font_family(root: tk.Misc, names: tuple, fallback: str) -> str:
    """挑第一个系统里真实存在的字体族（不区分大小写的包含匹配）。"""
    try:
        available = {f.lower(): f for f in tkfont.families(root)}
    except tk.TclError:
        return fallback
    for name in names:
        if name.lower() in available:
            return available[name.lower()]
    for name in names:                       # 退一步：包含匹配
        for low, real in available.items():
            if name.lower() in low:
                return real
    return fallback


def ensure_fonts(root: tk.Misc) -> None:
    """启动时确定字体栈，取到更漂亮的字体就用它。"""
    global FONT_UI, FONT_NUM, FONT_UI_STACK, FONT_DISPLAY_STACK, FONT_DISPLAY_LIGHT
    FONT_UI_STACK = choose_font_family(root, FONT_UI_NAMES, "Microsoft YaHei UI")
    FONT_DISPLAY_STACK = choose_font_family(root, FONT_DISPLAY_NAMES, "Segoe UI")
    FONT_DISPLAY_LIGHT = choose_font_family(root, FONT_DISPLAY_LIGHT_NAMES,
                                            FONT_DISPLAY_STACK)
    FONT_UI = FONT_UI_STACK
    FONT_NUM = FONT_DISPLAY_STACK


def UI(size: float, weight: str = "normal") -> tuple:
    s = max(7, int(round(size)))
    return (FONT_UI, s, weight) if weight != "normal" else (FONT_UI, s)


def NUM(size: float, weight: str = "normal") -> tuple:
    s = max(7, int(round(size)))
    return (FONT_NUM, s, weight) if weight != "normal" else (FONT_NUM, s)


def px(value: float, factor: float) -> int:
    return max(1, int(round(value * factor)))


def ui_factor(height_px: int) -> float:
    return max(MIN_SCALE, min(MAX_SCALE, height_px / BASE_H))


def _rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def blend(c1: str, c2: str, t: float) -> str:
    """两色插值，t=0 取 c1。"""
    t = max(0.0, min(1.0, t))
    a, b = _rgb(c1), _rgb(c2)
    return _hex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def mix_white(color: str, amount: float) -> str:
    return blend(color, "#ffffff", amount)


# --------------------------------------------------------------------------
# 数据模型
# --------------------------------------------------------------------------

@dataclass
class Solve:
    """一次还原记录。"""

    time_ms: int = 0
    dnf: bool = False
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {"time_ms": int(self.time_ms), "dnf": bool(self.dnf),
                "timestamp": self.timestamp}

    @staticmethod
    def from_dict(raw: dict) -> "Solve":
        try:
            t = int(raw.get("time_ms", 0))
        except (TypeError, ValueError):
            t = 0
        return Solve(time_ms=max(0, t), dnf=bool(raw.get("dnf", False)),
                     timestamp=str(raw.get("timestamp", "")))

    def display(self) -> str:
        return "DNF" if self.dnf else format_ms(self.time_ms)

    def display_full(self) -> str:
        return f"DNF ({format_ms(self.time_ms)})" if self.dnf else format_ms(self.time_ms)

    def sort_key(self) -> float:
        return float("inf") if self.dnf else float(self.time_ms)


@dataclass
class Stats:
    count: int = 0
    valid: int = 0
    dnf_count: int = 0
    best: Solve | None = None
    worst: Solve | None = None
    mean: float | None = None
    values: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# 纯函数：格式化与统计（WCA 规则）
# --------------------------------------------------------------------------

def format_ms(ms: float) -> str:
    """毫秒 -> 计时字符串：12.34 / 1:02.34 / 1:02:03.45"""
    total_cs = int(round(max(0.0, float(ms)) / 10.0))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    if h:
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    if m:
        return f"{m}:{s:02d}.{cs:02d}"
    return f"{s}.{cs:02d}"


def format_stat(value) -> str:
    if value is None:
        return "—"
    if value == "DNF":
        return "DNF"
    return format_ms(value)


def trimmed_average(window: list[Solve]) -> float | str | None:
    """WCA 平均：去掉最好与最差各一个后取算术平均。"""
    n = len(window)
    if n == 0:
        return None
    if n >= 5:
        middle = sorted(window, key=lambda s: s.sort_key())[1:-1]
        if any(s.dnf for s in middle):
            return "DNF"
        return statistics.fmean(s.time_ms for s in middle)
    if any(s.dnf for s in window):
        return "DNF"
    return statistics.fmean(s.time_ms for s in window)


def rolling_average(solves: list[Solve], window: int) -> float | str | None:
    if window <= 0 or len(solves) < window:
        return None
    return trimmed_average(solves[-window:])


def mean_of_3(solves: list[Solve]) -> float | str | None:
    if len(solves) < 3:
        return None
    window = solves[-3:]
    if any(s.dnf for s in window):
        return "DNF"
    return statistics.fmean(s.time_ms for s in window)


def compute_stats(solves: list[Solve]) -> Stats:
    st = Stats(count=len(solves))
    valid = [s for s in solves if not s.dnf]
    st.valid = len(valid)
    st.dnf_count = st.count - st.valid
    if valid:
        st.best = min(valid, key=lambda s: s.time_ms)
        st.worst = max(valid, key=lambda s: s.time_ms)
        st.mean = statistics.fmean(s.time_ms for s in valid)
    for key, _label, window in STAT_ITEMS:
        if key == "best":
            st.values[key] = float(st.best.time_ms) if st.best else None
        elif key == "mo3":
            st.values[key] = mean_of_3(solves)
        else:
            st.values[key] = rolling_average(solves, window)
    return st


# --------------------------------------------------------------------------
# 存取
# --------------------------------------------------------------------------

def load_solves(path: Path = DATA_FILE) -> list[Solve]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        try:
            path.replace(path.with_suffix(".json.bak"))
        except OSError:
            pass
        return []
    items = raw.get("solves", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    return [Solve.from_dict(x) for x in items if isinstance(x, dict)]


def save_solves(solves: list[Solve], path: Path = DATA_FILE) -> None:
    payload = {
        "app": APP_TITLE, "version": APP_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "solves": [s.to_dict() for s in solves],
    }
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict, path: Path = SETTINGS_FILE) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def text_width(widget: tk.Widget, text: str, font: tuple) -> int:
    """用真实字体度量文字宽度（避免按字符数估算导致按钮重叠）。"""
    try:
        f = tkfont.Font(root=widget, font=font)
        return f.measure(text)
    except tk.TclError:
        size = font[1] if len(font) > 1 else 10
        return int(len(text) * size * 1.1)


class FontRuler:
    """
    按“目标像素高度”反算字号。

    重要：tk 的字号单位是 point，实际像素高度 = point × tk_scaling / 72 × 每 em 行高。
    高分屏（如 200% 缩放）下若直接把像素当字号用，字会大一倍多并被裁切。
    这里先按比例估算，再用真实字体度量修正，因此在任何 DPI 下都精准。
    """

    def __init__(self, root: tk.Misc):
        self.root = root
        self._cache: dict[tuple, tuple] = {}
        try:
            self.scaling = float(root.tk.call("tk", "scaling")) or 1.3333
        except tk.TclError:
            self.scaling = 1.3333

    def fit(self, family: str, weight: str, target_px: float) -> tuple:
        weight = weight if weight != "normal" else ""
        key = (family, weight, int(target_px))
        if key in self._cache:
            return self._cache[key]
        size = max(7.0, target_px * 72.0 / (self.scaling * 1.28))
        weight = weight or "normal"
        for _ in range(6):
            spec = (family, int(round(size)), weight) if weight != "normal" \
                else (family, int(round(size)))
            try:
                h = tkfont.Font(root=self.root, font=spec).metrics("linespace")
            except tk.TclError:
                break
            if h <= 0:
                break
            ratio = target_px / h
            if 0.985 <= ratio <= 1.015:
                break
            size *= ratio
            if size < 7:
                size = 7
                break
        spec = (family, int(round(size)), weight) if weight != "normal" \
            else (family, int(round(size)))
        self._cache[key] = spec
        return spec


# --------------------------------------------------------------------------
# 基础绘制：圆角矩形 + 柔和阴影 + 渐变
# --------------------------------------------------------------------------

def _rr_points(x0: float, y0: float, x1: float, y1: float, r: float) -> list[float]:
    r = max(0.0, min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0))
    return [
        x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
        x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
        x0, y1, x0, y1 - r, x0, y0 + r, x0, y0,
    ]


def draw_round_rect(canvas: tk.Canvas, x0, y0, x1, y1, r, fill,
                    outline: str | None = None, width: int = 1, tags=()):
    return canvas.create_polygon(
        _rr_points(x0, y0, x1, y1, r), fill=fill,
        outline=outline or "", width=width, smooth=True, splinesteps=24, tags=tags)


def draw_gradient_rect(canvas: tk.Canvas, x0, y0, x1, y1, r, c_top, c_bottom, tags=()):
    """圆角矩形内填充竖向渐变：逐行画线，行宽按圆角圆弧收边。"""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    h = y1 - y0
    if h <= 0 or x1 <= x0:
        return []
    r = max(0.0, min(float(r), (x1 - x0) / 2.0, h / 2.0))
    a, b = _rgb(c_top), _rgb(c_bottom)
    items = []
    for i in range(h):
        y = y0 + i
        t = i / max(1, h - 1)
        col = _hex(tuple(p + (q - p) * t for p, q in zip(a, b)))
        if r <= 0:
            dx = 0.0
        elif y < y0 + r:
            dy = (y0 + r) - y
            dx = r - (r * r - dy * dy) ** 0.5
        elif y > y1 - r:
            dy = y - (y1 - r)
            dx = r - (r * r - dy * dy) ** 0.5
        else:
            dx = 0.0
        items.append(canvas.create_line(x0 + dx, y, x1 - dx, y, fill=col, tags=tags))
    return items


def draw_soft_shadow(canvas: tk.Canvas, x0, y0, x1, y1, r, base="#c9c7e4", tags=()):
    """
    用几层渐淡的圆角矩形模拟柔和阴影（无外部依赖）。
    注意：阴影只向上与左右扩散，向下仅留 1px，避免压住下方的内容（如按钮）。
    """
    items = []
    for i in range(5, 0, -1):
        grow = i * 1.6
        col = mix_white(base, 0.42 + 0.11 * (5 - i))
        items.append(draw_round_rect(canvas, x0 - grow, y0 - grow * 0.4 + 1,
                                     x1 + grow, y1 + min(grow * 0.25, 1.5),
                                     r + grow, fill=col, tags=tags))
    return items


def draw_background_glow(canvas: tk.Canvas, cx: float, cy: float, radius: float,
                        color: str, steps: int = 9, tags=()):
    """用同背景色插值的同心圆模拟柔和环境光晕。"""
    items = []
    bg = t("BG_TOP")
    for i in range(steps, 0, -1):
        p = i / steps
        r = radius * (0.35 + 0.65 * p)
        fill = blend(bg, color, 0.055 * (1.0 - p) + 0.012)
        items.append(canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                        fill=fill, outline="", tags=tags))
    return items


# --------------------------------------------------------------------------
# 组件：圆角卡片
# --------------------------------------------------------------------------

class Card:
    """自绘圆角卡片：阴影 + 卡片底 + 极细描边。内容由外部用 place 放上去。"""

    def __init__(self, canvas: tk.Canvas, radius: int = 26, outline: str | None = None):
        self.canvas = canvas
        self.radius = radius
        self.outline = outline
        self.items: list[int] = []

    def draw(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.draw_at(x0, y0, x1, y1)

    def draw_at(self, x0, y0, x1, y1) -> None:
        c = self.canvas
        for i in self.items:
            c.delete(i)
        self.items = []
        self.items += draw_soft_shadow(c, x0, y0 + 1, x1, y1, self.radius,
                                       base=t("SHADOW"))
        # Tkinter 原生控件没有真正的 backdrop-filter，因此用多层渐变、
        # 内高光和细边框模拟玻璃折射/反射，视觉上比纯色卡片更通透。
        self.items += draw_gradient_rect(c, x0, y0, x1, y1, self.radius,
                                         t("CARD_TOP"), t("CARD_BOTTOM"))
        self.items.append(draw_round_rect(c, x0, y0, x1, y1, self.radius,
                                          fill="", outline=self.outline or t("CARD_LINE"),
                                          width=1))
        self.items.append(draw_round_rect(c, x0 + 1, y0 + 1, x1 - 1, y0 + 3,
                                          max(4, self.radius - 1), fill=t("CARD_HIGHLIGHT")))
        self.items.append(draw_round_rect(c, x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5,
                                          max(4, self.radius - 1.5),
                                          fill="", outline=t("CARD_LINE"), width=1))


class PillButton:
    """圆角药丸按钮：实心 / 浅色 / 幽灵 三种，带悬停反馈。"""

    def __init__(self, parent: tk.Widget, canvas: tk.Canvas, text: str, command,
                 style: str = "ghost"):
        self.canvas = canvas
        self.command = command
        self.style = style          # solid / soft / ghost
        self.enabled = True
        self.active = False         # 选中态（如“夜间模式”按钮）
        self.rect = (0, 0, 0, 0)
        self.items: list[int] = []
        self.label = tk.Label(parent, text=text, bd=0, cursor="hand2")
        self.sync_colors()
        self._hover = False
        self.label.bind("<Enter>", self._on_enter)
        self.label.bind("<Leave>", self._on_leave)
        self.label.bind("<Button-1>", lambda e: self._press())
        self.label.bind("<ButtonRelease-1>", self._release)

    def sync_colors(self) -> None:
        """按当前主题刷新配色（切换主题时调用）。"""
        if self.active:
            self.fill, self.line = t("ACTIVE_BTN_FILL"), t("ACTIVE_BTN_LINE")
            self.fg, self.hover_fill = t("ACTIVE_BTN_TEXT"), t("ACTIVE_BTN_FILL")
        elif self.style == "solid":
            self.fill = self.line = t("ACCENT")
            self.fg = "#ffffff"
            self.hover_fill = t("ACCENT_DEEP")
        elif self.style == "soft":
            self.fill, self.line = t("SOFT_BTN_FILL"), t("SOFT_BTN_LINE")
            self.fg, self.hover_fill = t("SOFT_BTN_TEXT"), t("SOFT_BTN_HOVER")
        else:
            self.fill, self.line = t("GHOST_BTN_FILL"), t("GHOST_BTN_LINE")
            self.fg, self.hover_fill = t("GHOST_BTN_TEXT"), t("GHOST_BTN_HOVER")
        self.label.config(bg=self.fill, fg=self.fg)

    def set_active(self, active: bool) -> None:
        if active != self.active:
            self.active = bool(active)
            self.sync_colors()
            if self.items:
                self.canvas.itemconfigure(self.items[0], fill=self.fill,
                                          outline=self.line)

    # ---- 生命周期 ----
    def place(self, x: int, y: int, w: int, h: int, radius: int,
              font: tuple, bg: str = CARD) -> None:
        self.rect = (x, y, x + w, y + h)
        x0, y0, x1, y1 = self.rect
        for i in self.items:
            self.canvas.delete(i)
        self.items = [
            draw_round_rect(self.canvas, x0, y0, x1, y1, radius, fill=self.fill,
                            outline=self.line, width=1),
        ]
        self.label.config(font=font, bg=self.fill, fg=self.fg)
        self.label.place(in_=self.canvas, x=x, y=y, width=w, height=h)

    def _repaint(self, fill: str) -> None:
        if self.items:
            self.canvas.itemconfigure(self.items[0], fill=fill)
        self.label.config(bg=fill)

    # ---- 交互 ----
    def _on_enter(self, _e=None):
        if self.enabled:
            self._hover = True
            self._repaint(self.hover_fill)

    def _on_leave(self, _e=None):
        self._hover = False
        self._repaint(self.fill)

    def _press(self):
        if self.enabled:
            self._repaint(blend(self.hover_fill, "#000000", 0.05))

    def _release(self, _e=None):
        if not self.enabled:
            return
        self._repaint(self.hover_fill if self._hover else self.fill)
        if self.command:
            self.command()


# --------------------------------------------------------------------------
# 组件：自绘成绩列表（Canvas 实现，支持悬停 / 多选 / 滚轮 / 滚动条）
# --------------------------------------------------------------------------

class SolveList(tk.Canvas):
    ROW_FONT_W = 7       # 字符宽度估算：等宽字体约为 0.55em
    PAD = 22

    def __init__(self, parent: tk.Widget, on_change=None):
        super().__init__(parent, bg=t("CARD"), highlightthickness=0, bd=0)
        self.solves: list[Solve] = []
        self.aos: list[tuple[str, str]] = []
        self.best_idx: int | None = None
        self.selection: set[int] = set()
        self.hover: int | None = None
        self.offset = 0
        self.geom = None            # (row_h, font, small_font)
        self.on_change = on_change
        self._anchor: int | None = None
        self._last_click = (0.0, None)

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<Button-1>", self._on_click)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Button-4>", lambda e: self._scroll(-1))
        self.bind("<Button-5>", lambda e: self._scroll(1))

    # ---- 数据 ----
    def set_data(self, solves: list[Solve]) -> None:
        self.solves = solves
        self.aos = []
        for i in range(len(solves)):
            a5 = format_stat(rolling_average(solves[: i + 1], 5))
            a12 = format_stat(rolling_average(solves[: i + 1], 12))
            self.aos.append((a5, a12))
        st = compute_stats(solves)
        self.best_idx = None
        if st.best is not None:
            for i, s in enumerate(solves):
                if s is st.best or (not s.dnf and s.time_ms == st.best.time_ms):
                    self.best_idx = i
                    break
        self.selection = {i for i in self.selection if 0 <= i < len(solves)}
        self._clamp_offset()
        self.redraw()

    def set_geometry(self, row_h: int, font: tuple, small_font: tuple) -> None:
        self.geom = (row_h, font, small_font)
        self.redraw()

    # ---- 选中 ----
    def selected_indexes(self) -> list[int]:
        return sorted(self.selection)

    def has_selection(self) -> bool:
        return bool(self.selection)

    def select_only(self, idx: int | None) -> None:
        self.selection = set() if idx is None else {idx}
        self._scroll_into_view(idx)
        self.redraw()
        if self.on_change:
            self.on_change()

    def toggle_select(self, idx: int) -> None:
        if idx in self.selection:
            self.selection.discard(idx)
        else:
            self.selection.add(idx)
        self.redraw()
        if self.on_change:
            self.on_change()

    def clear_selection(self) -> None:
        if self.selection:
            self.selection = set()
            self.redraw()
            if self.on_change:
                self.on_change()

    def select_range(self, a: int, b: int) -> None:
        lo, hi = sorted((a, b))
        self.selection = set(range(lo, hi + 1))
        self.redraw()
        if self.on_change:
            self.on_change()

    def ensure_last_visible(self) -> None:
        if self.solves:
            self.select_only(len(self.solves) - 1)

    # ---- 滚动 ----
    def _row_h(self) -> int:
        return self.geom[0] if self.geom else 32

    def _total_h(self) -> int:
        return len(self.solves) * self._row_h()

    def _clamp_offset(self) -> None:
        view = max(0, self.winfo_height())
        self.offset = max(0, min(self.offset, max(0, self._total_h() - view)))

    def _scroll(self, steps: int) -> None:
        self.offset += steps * self._row_h() * 3
        self._clamp_offset()
        self.redraw()

    def _on_wheel(self, event):
        self._scroll(-1 if event.delta > 0 else 1)

    def _scroll_into_view(self, idx: int | None) -> None:
        if idx is None or not self.geom:
            return
        row, view = self._row_h(), self.winfo_height()
        y0, y1 = idx * row - self.offset, (idx + 1) * row - self.offset
        if y0 < 0:
            self.offset = idx * row
        elif y1 > view:
            self.offset = (idx + 1) * row - view
        self._clamp_offset()

    # ---- 交互 ----
    def _index_at(self, y: int) -> int | None:
        if not self.geom:
            return None
        idx = (y + self.offset) // self._row_h()
        return int(idx) if 0 <= idx < len(self.solves) else None

    def _on_motion(self, event):
        self._set_hover(self._index_at(event.y))

    def _set_hover(self, idx: int | None) -> None:
        if idx != self.hover:
            self.hover = idx
            self.redraw()

    def _on_click(self, event):
        idx = self._index_at(event.y)
        if idx is None:
            self.clear_selection()
            return
        ctrl = bool(event.state & 0x0004)
        shift = bool(event.state & 0x0001)
        now = time.time()
        if shift and self._anchor is not None:
            self.select_range(self._anchor, idx)
        elif ctrl:
            self._anchor = idx
            self.toggle_select(idx)
        else:
            # 双击同一条 = 切换选中
            if now - self._last_click[0] < 0.4 and self._last_click[1] == idx:
                self._anchor = idx
                self.toggle_select(idx)
            else:
                self._anchor = idx
                self.select_only(idx)
        self._last_click = (now, idx)

    # ---- 绘制 ----
    def redraw(self) -> None:
        self.delete("all")
        if not self.geom:
            return
        row_h, font, small_font = self.geom
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return

        if not self.solves:
            self.create_text(w / 2, h / 2, text="还没有成绩，按空格开始第一次计时",
                             fill=t("FAINT"), font=font)
            return

        first = max(0, self.offset // row_h)
        last = min(len(self.solves), (self.offset + h) // row_h + 2)
        pad = self.PAD
        n = len(self.solves)
        num_w = max(38, int(row_h * 1.15))
        time_w = max(94, int(row_h * 3.0))
        ao_w = max(78, int(row_h * 2.5))
        when_w = max(96, int(row_h * 3.0))
        x_time = num_w + pad
        x_ao5 = x_time + time_w + pad
        x_ao12 = x_ao5 + ao_w + pad
        x_when = w - pad

        for i in range(first, last):
            s = self.solves[i]
            y0 = i * row_h - self.offset
            y1 = y0 + row_h
            mid = y0 + row_h / 2
            if i in self.selection:
                draw_round_rect(self, pad * 0.4, y0 + 1, w - pad * 0.4, y1 - 1,
                                max(8, row_h // 3), fill=t("SEL_BG"))
            elif i == self.hover:
                draw_round_rect(self, pad * 0.4, y0 + 1, w - pad * 0.4, y1 - 1,
                                max(8, row_h // 3), fill=t("ROW_HOVER"))

            num_fg = t("FAINT")
            if s.dnf:
                t_fg = t("DNF_TXT")
            elif i == n - 1:
                t_fg = t("LATEST_TXT")
            elif i == self.best_idx:
                t_fg = t("BEST_TXT")
            else:
                t_fg = t("TEXT")
            fg_meta = t("MUTED") if i in self.selection else t("FAINT")

            self.create_text(pad, mid, text=str(i + 1), anchor="w",
                             fill=num_fg, font=small_font)
            self.create_text(x_time, mid, text=s.display_full(), anchor="w",
                             fill=t_fg, font=font)
            self.create_text(x_ao5, mid, text=self.aos[i][0], anchor="w",
                             fill=fg_meta, font=small_font)
            self.create_text(x_ao12, mid, text=self.aos[i][1], anchor="w",
                             fill=fg_meta, font=small_font)
            self.create_text(x_when, mid, text=s.timestamp[5:16], anchor="e",
                             fill=t("FAINT"), font=small_font)

        self._draw_scrollbar(h)

    def _draw_scrollbar(self, view_h: int) -> None:
        total = self._total_h()
        if total <= view_h or view_h <= 0:
            return
        w = self.winfo_width()
        bar_h = max(28, int(view_h * view_h / total))
        bar_y = int((view_h - bar_h) * (self.offset / max(1, total - view_h)))
        draw_round_rect(self, w - 5, bar_y + 2, w - 2, bar_y + bar_h - 2,
                        (3) / 2 + 1, fill=t("SCROLL"))


# --------------------------------------------------------------------------
# 主界面
# --------------------------------------------------------------------------

class CubeTimerApp:
    def __init__(self, root: tk.Tk, solves: list[Solve] | None = None):
        self.root = root
        self.solves: list[Solve] = list(solves or [])
        self.undo_stack: list[tuple[list[Solve], str]] = []

        # 计时状态机：idle -> holding -> ready -> (松手) -> running -> idle
        self.state = "idle"
        self.hold_start = 0.0
        self.start_time = 0.0
        self.final_ms: float | None = None

        self.ui_scale = 1.0
        self.ruler = FontRuler(root)      # 按目标像素高度反算字号
        self._geo: dict | None = None     # 最近一次布局算出的几何
        self._factor = None
        self._size = (0, 0)
        self._resize_job = None
        self._flash_job = None

        self._build_ui()
        self._bind_keys()
        self.refresh_all()

    # ---------------- 界面骨架 ----------------
    def _build_ui(self) -> None:
        r = self.root
        r.title(APP_TITLE)
        r.configure(bg=t("BG_TOP"))
        self._build_menu()
        self._center()
        r.minsize(880, 640)

        # 背景画布：渐变 + 阴影 + 圆角卡片 + 药丸按钮
        self.bg = tk.Canvas(r, bg=t("BG_TOP"), highlightthickness=0, bd=0)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # ---- 卡片 ----
        self.timer_card = Card(self.bg, radius=30)
        self.stats_card = Card(self.bg, radius=30)
        self.list_card = Card(self.bg, radius=30)

        # ---- 计时区内容 ----
        self.timer_label = tk.Label(r, text="0.00", bg=t("CARD"), fg=t("TEXT"),
                                    font=NUM(90), bd=0)
        self.status_label = tk.Label(r, text="", bg=t("CARD"), fg=t("MUTED"),
                                     font=UI(11), bd=0)
        self.meta_label = tk.Label(r, text="", bg=t("CARD"), fg=t("FAINT"),
                                   font=UI(10), bd=0)

        # ---- 统计区内容 ----
        self.stat_titles: list[tk.Label] = []
        self.stat_values: dict[str, tk.Label] = {}
        for key, label, _w in STAT_ITEMS:
            self.stat_titles.append(tk.Label(r, text=label, bg=t("CARD"), fg=t("FAINT"),
                                             font=UI(10), bd=0))
            v = tk.Label(r, text="—", bg=t("CARD"), fg=t("TEXT"), font=NUM(22), bd=0)
            self.stat_values[key] = v

        # ---- 列表区内容 ----
        self.list_title = tk.Label(r, text="成绩记录", bg=t("CARD"), fg=t("MUTED"),
                                   font=UI(10), bd=0)
        self.list_hint = tk.Label(r, text="", bg=t("CARD"), fg=t("FAINT"), font=UI(9), bd=0)
        self.listview = SolveList(r, on_change=self._render_list_hint)

        # ---- 底部按钮 ----
        d = dict(parent=r, canvas=self.bg)
        self.btn_delete_last = PillButton(text="删除本次成绩", command=self.delete_last,
                                          style="soft", **d)
        self.btn_delete_sel = PillButton(text="删除选中", command=self.delete_selected,
                                         style="ghost", **d)
        self.btn_undo = PillButton(text="撤销", command=self.undo, style="ghost", **d)
        self.btn_dnf = PillButton(text="标为 DNF", command=self.toggle_dnf_selected,
                                  style="ghost", **d)
        self.btn_clear = PillButton(text="清空", command=self.clear_all, style="ghost", **d)
        self.btn_export = PillButton(text="导出 CSV", command=self.export_csv,
                                     style="ghost", **d)
        self.btn_theme = PillButton(text="日间" if THEME == "dark" else "夜间",
                                    command=self.toggle_theme, style="ghost", **d)
        self.btn_theme.set_active(THEME == "dark")

        r.bind("<Configure>", self._on_resize)
        self._relayout()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root, tearoff=0)
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="导出 CSV…", command=self.export_csv)
        m_file.add_command(label="撤销", command=self.undo)
        m_file.add_separator()
        m_file.add_command(label="删除本次成绩", command=self.delete_last)
        m_file.add_command(label="全部清空", command=self.clear_all)
        m_file.add_separator()
        m_file.add_command(label="退出", command=self.root.destroy)
        menubar.add_cascade(label="文件", menu=m_file)

        m_view = tk.Menu(menubar, tearoff=0)
        self.theme_var = tk.StringVar(value=THEME)
        m_view.add_radiobutton(label="日间模式", value="light", variable=self.theme_var,
                               command=lambda: self.set_theme("light"))
        m_view.add_radiobutton(label="夜间模式", value="dark", variable=self.theme_var,
                               command=lambda: self.set_theme("dark"))
        m_view.add_separator()
        m_view.add_command(label="切换日间/夜间 (Ctrl+L)", command=self.toggle_theme)
        menubar.add_cascade(label="视图", menu=m_view)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="操作说明", command=self.show_help)
        m_help.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=m_help)
        self.root.config(menu=menubar)

    def _center(self) -> None:
        """
        按屏幕尺寸决定窗口大小并居中。

        注意：winfo_screen* 的数值取决于进程是否成功开启 DPI 感知
        （感知到则是物理像素，否则是缩放后的逻辑像素），因此这里不乘缩放，
        只按屏幕比例取值并留出边距，两种坐标系下都能得到合适的大小。
        """
        try:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        except tk.TclError:
            sw, sh = 1920, 1080
        w = max(1000, min(1760, int(sw * 0.82)))
        h = max(680, min(1440, int(sh * 0.88)))
        w, h = min(w, int(sw * 0.94)), min(h, int(sh * 0.94))
        self.root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")

    # ---------------- 响应式布局 ----------------
    def _on_resize(self, _event=None) -> None:
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(90, self._relayout)

    def _relayout(self) -> None:
        self._resize_job = None
        W, H = self.root.winfo_width(), self.root.winfo_height()
        if W <= 1 or H <= 1:
            return
        if (W, H) == self._size and self._factor is not None:
            return
        self._size = (W, H)
        f = self._factor = round(ui_factor(H), 3)

        self.bg.delete("bg")
        draw_gradient_rect(self.bg, 0, 0, W, H, 0, t("BG_TOP"), t("BG_BOTTOM"), tags="bg")
        draw_background_glow(self.bg, W * 0.12, H * 0.10, min(W, H) * 0.34,
                             "#9aa8ff", tags="bg")
        draw_background_glow(self.bg, W * 0.88, H * 0.18, min(W, H) * 0.30,
                             "#f2a9d0", tags="bg")
        draw_background_glow(self.bg, W * 0.54, H * 1.03, min(W, H) * 0.40,
                             "#8ed7ff", tags="bg")

        margin = px(22, f)
        gap = px(14, f)
        footer_h = px(54, f)
        row_h = px(32, f)
        stat_px = px(18, f)
        meta_px = px(15, f)
        hero_ideal = px(170, f)
        stat_line_h = px(stat_px * 1.6, 1.0)
        meta_line_h = px(meta_px * 1.6, 1.0)

        # ---- 竖向空间分配 ----
        # 三块内容按比例分配可用高度，并各自留有上下限，保证：
        #   · 统计卡永远装得下两行
        #   · 列表至少 2 行、最多 620px
        #   · 计时卡在剩余空间里尽量大（数字字号随卡片高度反算）
        avail_h = max(px(300, f), H - margin * 2 - footer_h - gap * 2)

        hero_need = hero_ideal + stat_line_h + meta_line_h + px(36, f)
        units = (0.50, 0.22, 0.28)                    # 计时 / 统计 / 列表
        stats_min_h = px(178, f)                      # 统计卡最小高度（两行 + 标签）
        timer_card_h = max(hero_need, avail_h * units[0])
        stats_card_h = max(stats_min_h, avail_h * units[1])
        list_card_h = max(row_h * 3 + px(96, f),
                          avail_h - timer_card_h - stats_card_h)

        want_list = avail_h * units[2]
        if list_card_h < want_list:                   # 空间紧张：按多余空间等比收缩
            deficit = want_list - list_card_h
            t_room = max(0.0, timer_card_h - hero_need)
            s_room = max(0.0, stats_card_h - stats_min_h)
            total = t_room + s_room
            if total > 0:
                take_t = min(t_room, deficit * t_room / total)
                take_s = min(s_room, deficit - take_t)
                timer_card_h -= take_t
                stats_card_h -= take_s
                deficit -= take_t + take_s
            if deficit > 0:                           # 还不够就从列表自己的富余里减
                list_card_h = max(row_h * 2 + px(84, f), list_card_h - deficit)
            else:
                list_card_h = avail_h - timer_card_h - stats_card_h
        elif list_card_h > px(620, f):                # 列表太高：把空间还给计时卡
            give = list_card_h - px(620, f)
            timer_card_h += give
            list_card_h -= give

        # 兜底：列表至少两行，不够再从计时卡里借
        need2 = row_h * 2 + px(132, f)
        if list_card_h < need2:
            borrow = min(need2 - list_card_h,
                         max(0.0, timer_card_h - hero_need))
            timer_card_h -= borrow
            list_card_h += borrow

        top = margin
        stats_top = top + timer_card_h + gap
        list_top = stats_top + stats_card_h + gap

        # 计时卡片高度确定后，再定数字大小（留出状态行与会话信息行的位置）
        hero_max_px = max(px(48, f),
                          timer_card_h - stat_line_h - meta_line_h - px(44, f))
        hero_px = max(px(48, f), min(hero_ideal, hero_max_px))
        list_bottom = list_top + list_card_h

        L, R = margin, W - margin
        self._geo = dict(L=L, R=R, top=top, timer_h=timer_card_h,
                         stats_top=stats_top, stats_h=stats_card_h,
                         list_top=list_top, list_h=list_card_h, list_bottom=list_bottom)
        self.timer_card.draw(L, top, R, top + timer_card_h)
        self.stats_card.draw(L, stats_top, R, stats_top + stats_card_h)
        self.list_card.draw(L, list_top, R, list_bottom)

        # ---- 计时区内容（三段：数字 / 状态 / 会话信息）----
        # 字号按“目标像素高度”反算，任何 DPI 下都不裁切
        self.timer_label.config(font=self.ruler.fit(FONT_DISPLAY_LIGHT, "normal", hero_px))
        self.status_label.config(font=self.ruler.fit(FONT_UI_STACK, "normal", stat_px))
        self.meta_label.config(font=self.ruler.fit(FONT_UI_STACK, "normal", meta_px))
        cx = (L + R) / 2
        num_h = px(hero_px * 1.1, 1.0)
        stat_h = px(stat_px * 1.45, 1.0)
        meta_h = px(meta_px * 1.45, 1.0)
        y0 = top + (timer_card_h - (num_h + stat_h + meta_h)) / 2
        self._place_center(self.timer_label, cx, y0, num_h)
        self._place_center(self.status_label, cx, y0 + num_h, stat_h)
        self._place_center(self.meta_label, cx, y0 + num_h + stat_h, meta_h)

        # ---- 统计区内容（3 列 × 2 行）----
        inner_pad = px(34, f)
        col_w = (R - L - inner_pad * 2) / 3
        row_gap = px(22, f)
        v_gap = px(34, f)
        cell_h = (stats_card_h - v_gap - row_gap) / 2
        title_h = px(14, f)
        value_h = px(30, f)
        title_font = self.ruler.fit(FONT_UI_STACK, "normal", title_h)
        value_font = self.ruler.fit(FONT_DISPLAY_STACK, "bold", value_h)
        for i, (key, _label, _w) in enumerate(STAT_ITEMS):
            row, col = divmod(i, 3)
            x = L + inner_pad + col * col_w
            y = stats_top + v_gap / 2 + row * (cell_h + row_gap)
            self.stat_titles[i].config(font=title_font)
            self.stat_titles[i].place(x=int(x), y=int(y), height=int(title_h * 1.8))
            self.stat_values[key].config(font=value_font)
            self.stat_values[key].place(x=int(x), y=int(y + title_h * 1.4),
                                        height=int(value_h * 1.7))

        # ---- 列表区内容 ----
        lp = px(26, f)
        list_left = L + lp
        list_right = R - lp
        f_row = self.ruler.fit(FONT_DISPLAY_STACK, "normal", px(16, f))
        f_small = self.ruler.fit(FONT_DISPLAY_STACK, "normal", px(14.5, f))
        f_head = self.ruler.fit(FONT_UI_STACK, "normal", px(13, f))

        self.list_title.config(font=self.ruler.fit(FONT_UI_STACK, "bold", px(15, f)))
        self.list_title.place(x=int(list_left), y=int(list_top + px(14, f)))
        self.list_hint.config(font=f_head)
        self.list_hint.place(x=int(list_right), y=int(list_top + px(17, f)), anchor="ne")

        head_y = list_top + px(58, f)
        self.bg.delete("thead")
        draw_round_rect(self.bg, list_left, head_y, list_right, head_y + 1, 0,
                        fill=t("TRACK"), tags="thead")
        for text, anchor, x in zip(("#", "成绩", "ao5", "ao12", "时间"),
                                   ("w", "w", "w", "w", "e"),
                                   self._list_columns(list_left, list_right, f)):
            self.bg.create_text(x, head_y + px(15, f), text=text, anchor=anchor,
                                fill=t("FAINT"), font=f_head, tags="thead")

        self.listview.place(x=int(list_left), y=int(head_y + px(30, f)),
                            width=int(list_right - list_left),
                            height=int(max(row_h * 2, list_bottom - head_y - px(44, f))))
        self.listview.set_geometry(row_h, f_row, f_small)

        # ---- 底部按钮（宽度按文字实际宽度计算）----
        btn_h = px(36, f)
        btn_y = H - margin - btn_h
        btn_font = self.ruler.fit(FONT_UI_STACK, "normal", px(15, f))
        bx = margin + px(4, f)
        for btn, extra in ((self.btn_delete_last, 30), (self.btn_delete_sel, 22),
                           (self.btn_undo, 16), (self.btn_dnf, 22), (self.btn_clear, 16)):
            w = text_width(self.root, btn.label.cget("text"), btn_font) + px(extra, f)
            btn.place(bx, btn_y, w, btn_h, btn_h // 2, btn_font)
            bx += w + px(8, f)
        exp_w = text_width(self.root, "导出 CSV", btn_font) + px(22, f)
        self.btn_export.place(R - exp_w, btn_y, exp_w, btn_h, btn_h // 2, btn_font)
        th_w = text_width(self.root, "日间模式", btn_font) + px(24, f)
        self.btn_theme.place(R - exp_w - px(8, f) - th_w, btn_y, th_w, btn_h,
                             btn_h // 2, btn_font)

        self._apply_state_colors()
        self._render_list_hint()
        if os.environ.get("CUBE_TIMER_DEBUG"):
            print(f"[layout] W={W} H={H} f={f} avail={avail_h} "
                  f"timer={timer_card_h:.0f} stats={stats_card_h:.0f} "
                  f"list={list_card_h:.0f} hero_px={hero_px:.0f} "
                  f"stats_top={stats_top:.0f} list_top={list_top:.0f} "
                  f"list_bottom={list_bottom:.0f}")

    def _list_columns(self, list_left: int, list_right: int, f: float) -> list[int]:
        """表头与列表行共用同一套列坐标（与 SolveList 内部布局一致）。"""
        pad = SolveList.PAD
        row_h = px(32, f)
        left = list_left + pad * 0.4
        num_w = max(38, int(row_h * 1.15))
        time_w = max(94, int(row_h * 3.0))
        ao_w = max(78, int(row_h * 2.5))
        x_time = left + num_w
        x_ao5 = x_time + time_w + pad
        x_ao12 = x_ao5 + ao_w + pad
        return [left, x_time, x_ao5, x_ao12, list_right - pad * 0.4]

    def _place_center(self, widget: tk.Widget, cx: float, y: float, h: float) -> None:
        widget.place(x=int(cx), y=int(y), anchor="n", height=int(h))

    def _apply_state_colors(self) -> None:
        """根据计时状态给计时卡片上色（准备=绿 / 计时中=紫 / 其他=卡片底色）。"""
        geo = getattr(self, "_geo", None)
        if not geo:                       # 尚未完成布局
            return
        L, R = geo["L"], geo["R"]
        top, h = geo["top"], geo["timer_h"]
        self.bg.delete("tint")

        if self.state in ("ready", "running"):
            fill, line = ((t("READY_BG"), t("READY_LINE")) if self.state == "ready"
                          else (t("RUN_BG"), t("RUN_LINE")))
            for i in range(6, 0, -1):
                grow = i * 1.6
                draw_round_rect(self.bg, L - grow, top - grow * 0.35 + 2, R + grow,
                                top + h + grow, 30 + grow,
                                fill=mix_white(line, 0.42 + 0.11 * (6 - i)), tags="tint")
            draw_round_rect(self.bg, L, top, R, top + h, 30,
                            fill=fill, outline=line, width=1, tags="tint")
            self.bg.tag_raise("tint")
            card_bg = fill
        else:
            card_bg = t("CARD")

        for w in (self.timer_label, self.status_label, self.meta_label):
            w.config(bg=card_bg)

    # ---------------- 主题（日间 / 夜间）----------------
    def toggle_theme(self) -> None:
        self.set_theme("light" if THEME == "dark" else "dark")

    def set_theme(self, mode: str) -> None:
        """切换日间/夜间配色，并立即重绘整个界面。"""
        if mode not in THEMES or mode == THEME:
            return
        apply_palette(mode)
        try:
            self.theme_var.set(mode)
        except AttributeError:
            pass
        self.btn_theme.label.config(text="日间" if THEME == "dark" else "夜间")
        self.btn_theme.set_active(THEME == "dark")
        self._apply_theme()

    def _apply_theme(self) -> None:
        """把当前主题应用到所有控件并重绘卡片/列表。"""
        r = self.root
        r.configure(bg=t("BG_TOP"))
        self.bg.configure(bg=t("BG_TOP"))

        for w in (self.timer_label, self.status_label, self.meta_label,
                  self.list_title, self.list_hint, *self.stat_titles,
                  *self.stat_values.values()):
            w.config(bg=t("CARD"))
        self._render_stats()          # 统计数值的颜色（最好成绩绿色 / DNF 红色等）
        self._render_idle()           # 计时区文字颜色

        for btn in (self.btn_delete_last, self.btn_delete_sel, self.btn_undo,
                    self.btn_dnf, self.btn_clear, self.btn_export, self.btn_theme):
            btn.sync_colors()
            if btn.items:
                self.bg.itemconfigure(btn.items[0], fill=btn.fill, outline=btn.line)

        self.listview.configure(bg=t("CARD"))
        self.listview.redraw()

        self._size = (0, 0)           # 让 _relayout 重新计算并重绘卡片
        self._relayout()
        self.flash("夜间模式 · Ctrl+L 切换" if THEME == "dark"
                   else "日间模式 · Ctrl+L 切换")

    # ---------------- 键盘 / 状态机 ----------------
    def _bind_keys(self) -> None:
        r = self.root
        r.bind_all("<KeyPress-space>", self._on_space_press)
        r.bind_all("<KeyRelease-space>", self._on_space_release)
        r.bind_all("<Escape>", lambda e: self.cancel_run())
        r.bind_all("<Delete>", lambda e: self.delete_last())
        r.bind_all("<Control-d>", lambda e: self.delete_last())
        r.bind_all("<Control-z>", lambda e: self.undo())
        r.bind_all("<Control-e>", lambda e: self.export_csv())
        r.bind_all("<KeyPress-d>", lambda e: self.toggle_dnf_selected())
        r.bind_all("<KeyPress-D>", lambda e: self.toggle_dnf_selected())
        r.bind_all("<Control-a>", lambda e: self._select_all_rows())
        r.bind_all("<Control-l>", lambda e: self.toggle_theme())
        r.protocol("WM_DELETE_WINDOW", self.on_close)
        r.after(UI_TICK_MS, self._tick)

    def _on_space_press(self, _event=None):
        if self.state == "holding":        # 长按产生的自动重复，忽略
            return "break"
        if self.state == "running":
            self.stop_run()
        elif self.state == "idle":
            self.state = "holding"
            self.hold_start = time.perf_counter()
            self.final_ms = None
            self._apply_state_colors()
            self._set_timer("0.00", t("MUTED"))
            self._set_status("按住不放…")
        return "break"

    def _on_space_release(self, _event=None):
        if self.state == "holding":
            held = (time.perf_counter() - self.hold_start) * 1000.0
            if held < HOLD_MS:              # 轻点：不开始，防手滑
                self.state = "idle"
                self._apply_state_colors()
                self._render_idle(show_last=True)
                self.flash("再按住一会儿，松手才会开始")
            else:
                self.start_run()
        elif self.state == "ready":
            self.start_run()
        return "break"

    def start_run(self) -> None:
        self.state = "running"
        self.start_time = time.perf_counter()
        self.final_ms = None
        self._apply_state_colors()
        self._set_status("计时中 · 按空格停止")
        self._render_list_hint()

    def stop_run(self) -> None:
        if self.state != "running":
            return
        elapsed = (time.perf_counter() - self.start_time) * 1000.0
        self.state = "idle"
        self.final_ms = elapsed
        self.solves.append(Solve(time_ms=int(round(elapsed)),
                                 timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.save()
        self._apply_state_colors()
        self.refresh_all()
        # refresh_all 会把计时区恢复成“上一次成绩”，这里改成本次成绩（紫色）
        self._set_timer(format_ms(elapsed), t("RUN_TXT"))
        self._set_status("已记录 · 空格开始下一次 · Del 删除本次")
        self.listview.select_only(len(self.solves) - 1)

    def cancel_run(self) -> None:
        if self.state in ("holding", "ready", "running"):
            was_running = self.state == "running"
            self.state = "idle"
            self.final_ms = None
            self._apply_state_colors()
            self._render_idle()
            self.flash("本次计时已作废，未记录成绩" if was_running else "已取消")

    def _tick(self) -> None:
        try:
            if self.state == "holding":
                held = (time.perf_counter() - self.hold_start) * 1000.0
                if held >= HOLD_MS:
                    self.state = "ready"
                    self._apply_state_colors()
                    self._set_timer("0.00", t("READY_TXT"))
                    self._set_status("准备就绪 · 松开空格立即开始")
                else:
                    self._set_timer("0.00", blend(t("MUTED"), t("READY_TXT"), held / HOLD_MS))
            elif self.state == "running":
                elapsed = (time.perf_counter() - self.start_time) * 1000.0
                self._set_timer(format_ms(min(elapsed, MAX_DISPLAY_MS)), t("RUN_TXT"))
        finally:
            self.root.after(UI_TICK_MS, self._tick)

    # ---------------- 渲染 ----------------
    def _set_timer(self, text: str, color: str) -> None:
        if self.timer_label.cget("text") != text or self.timer_label.cget("fg") != color:
            self.timer_label.config(text=text, fg=color)

    def _set_status(self, text: str, color: str | None = None) -> None:
        color = color or t("MUTED")
        if self.status_label.cget("text") != text or self.status_label.cget("fg") != color:
            self.status_label.config(text=text, fg=color)

    def _render_idle(self, show_last: bool = False) -> None:
        if show_last and self.final_ms is not None:
            self._set_timer(format_ms(self.final_ms), t("RUN_TXT"))
            self._set_status("已记录 · 空格开始下一次 · Del 删除本次")
            return
        if self.solves:
            last = self.solves[-1]
            self._set_timer(last.display_full(), t("DNF_TXT") if last.dnf else t("TEXT"))
        else:
            self._set_timer("0.00", t("TEXT"))
        self._set_status("按住空格，变绿后松开即开始")

    def _render_list_hint(self) -> None:
        if self.state == "running":
            self.list_hint.config(text="计时中…")
        elif self.listview.has_selection():
            self.list_hint.config(text="已选中 · D 标记 DNF · 再次点击取消选中")
        else:
            self.list_hint.config(text="单击选中 · 滚轮浏览")

    def flash(self, text: str) -> None:
        """把提示显示在计时卡片的状态行上，2 秒后自动恢复。"""
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except tk.TclError:
                pass
        self._set_status(text, t("MUTED"))
        self._flash_job = self.root.after(2200, self._clear_flash)

    def _clear_flash(self) -> None:
        self._flash_job = None
        if self.state == "idle":
            self._render_idle(show_last=self.final_ms is not None)

    def refresh_all(self) -> None:
        self._render_stats()
        self.listview.set_data(self.solves)
        self._render_idle()
        self._render_list_hint()

    def _render_stats(self) -> None:
        st = compute_stats(self.solves)
        for key, _label, _w in STAT_ITEMS:
            value = st.values.get(key)
            lab = self.stat_values[key]
            color = t("TEXT")
            if value is None:
                color = t("FAINT")
            elif value == "DNF":
                color = t("DNF_TXT")
            elif key == "best":
                color = t("BEST_TXT")
            lab.config(text=format_stat(value), fg=color)

        bits = [f"共 {st.count} 次"]
        if st.dnf_count:
            bits.append(f"DNF {st.dnf_count}")
        if st.mean is not None:
            bits.append(f"平均 {format_stat(st.mean)}")
        if st.worst is not None:
            bits.append(f"最慢 {st.worst.display_full()}")
        self.meta_label.config(text="   ·   ".join(bits))
    def _select_all_rows(self) -> None:
        if self.solves:
            self.listview.select_range(0, len(self.solves) - 1)

    # ---------------- 删除 / 撤销 ----------------
    def _push_undo(self, reason: str) -> None:
        self.undo_stack.append(([Solve(**s.to_dict()) for s in self.solves], reason))
        if len(self.undo_stack) > UNDO_LIMIT:
            self.undo_stack.pop(0)

    def delete_last(self) -> None:
        """删除本次成绩（列表中最新的一条）。"""
        if not self.solves:
            self.flash("还没有成绩可以删除")
            return
        self._push_undo("删除本次成绩")
        removed = self.solves.pop()
        self.final_ms = None
        self.save()
        self.refresh_all()
        self._set_timer("0.00", t("TEXT")) if not self.solves else self._render_idle()
        self.flash(f"已删除本次成绩 {removed.display_full()} · Ctrl+Z 可撤销")

    def delete_selected(self) -> None:
        idxs = self.listview.selected_indexes()
        if not idxs:
            self.flash("请先点击选中要删除的成绩")
            return
        self._push_undo("删除选中的成绩")
        for i in reversed(idxs):
            if 0 <= i < len(self.solves):
                self.solves.pop(i)
        self.save()
        self.refresh_all()
        self.flash(f"已删除 {len(idxs)} 条成绩 · Ctrl+Z 可撤销")

    def clear_all(self) -> None:
        if not self.solves:
            self.flash("列表已经是空的")
            return
        if not messagebox.askyesno("清空", f"确定删除全部 {len(self.solves)} 条成绩吗？\n"
                                          "（可用 Ctrl+Z 撤销一次）"):
            return
        self._push_undo("全部清空")
        self.solves.clear()
        self.final_ms = None
        self.save()
        self.refresh_all()
        self._set_timer("0.00", t("TEXT"))
        self.flash("已清空 · Ctrl+Z 可撤销")

    def undo(self) -> None:
        if not self.undo_stack:
            self.flash("没有可撤销的操作")
            return
        snaps, reason = self.undo_stack.pop()
        self.solves = snaps
        self.save()
        self.refresh_all()
        self.flash(f"已撤销：{reason}")

    def toggle_dnf_selected(self) -> None:
        idxs = self.listview.selected_indexes()
        if not idxs:
            self.flash("请先点击选中一条成绩再标记 DNF")
            return
        self._push_undo("标记 DNF")
        for i in idxs:
            if 0 <= i < len(self.solves):
                self.solves[i].dnf = not self.solves[i].dnf
        self.save()
        self.refresh_all()
        self.flash("已切换 DNF 标记 · Ctrl+Z 可撤销")

    # ---------------- 导出 / 帮助 ----------------
    def export_csv(self) -> None:
        if not self.solves:
            self.flash("还没有成绩可以导出")
            return
        path = filedialog.asksaveasfilename(
            title="导出成绩", defaultextension=".csv",
            initialfile=f"cube_times_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")])
        if not path:
            return
        st = compute_stats(self.solves)
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["#", "成绩(毫秒)", "成绩", "ao5", "ao12", "状态", "记录时间"])
                for i, s in enumerate(self.solves, 1):
                    w.writerow([i, s.time_ms, s.display(),
                                format_stat(rolling_average(self.solves[:i], 5)),
                                format_stat(rolling_average(self.solves[:i], 12)),
                                "DNF" if s.dnf else "OK", s.timestamp])
                w.writerow([])
                w.writerow(["统计项", "数值"])
                for key, label, _w in STAT_ITEMS:
                    w.writerow([label, format_stat(st.values.get(key))])
                w.writerow(["平均成绩", format_stat(st.mean)])
                w.writerow(["总次数", st.count])
                w.writerow(["有效次数", st.valid])
                w.writerow(["DNF 次数", st.dnf_count])
            self.flash(f"已导出到 {path}")
        except OSError as exc:
            messagebox.showerror("导出失败", f"无法写入文件：\n{exc}")

    def show_help(self) -> None:
        messagebox.showinfo(
            "操作说明",
            "计时\n"
            "  按住 [空格] 不放 → 计时卡片变绿（准备）\n"
            "  松开 [空格]     → 立即开始计时\n"
            "  再按 [空格]     → 停止并记录成绩\n"
            "  [Esc]           → 作废本次（不记录）\n\n"
            "统计\n"
            "  最好成绩 / 平均成绩 / mo3 / ao5 / ao12 / ao50 / ao100\n"
            "  平均按 WCA 规则：去掉最好与最差后取平均；\n"
            "  样本不足显示 “—”，被计入部分含 DNF 则显示 DNF。\n\n"
            "成绩管理\n"
            "  单击成绩行选中（再次点击取消），Shift/Ctrl 可多选\n"
            "  Del 或 Ctrl+D  → 删除本次成绩（最新一条）\n"
            "  删除选中        → 删除选中的成绩\n"
            "  D              → 将选中成绩标为 DNF（或取消）\n"
            "  Ctrl+Z         → 撤销删除 / 清空 / DNF 标记\n"
            "  Ctrl+E         → 导出 CSV\n\n"
            "界面\n"
            "  Ctrl+L 或点右下角按钮 → 切换日间 / 夜间模式（会被记住）\n"
            "  拖动窗口大小 → 字号与排版自动适配\n\n"
            f"成绩自动保存在：{DATA_FILE}")

    def show_about(self) -> None:
        messagebox.showinfo("关于", f"{APP_TITLE}  v{APP_VERSION}\n\n"
                                    "用 Python 标准库（tkinter）实现的桌面计时器。\n"
                                    f"数据文件：{DATA_FILE}")

    # ---------------- 收尾 ----------------
    def save(self) -> None:
        save_solves(self.solves)

    def on_close(self) -> None:
        self.save()
        try:
            settings = load_settings()
            settings["theme"] = THEME
            save_settings(settings)
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    scale = enable_dpi_awareness()
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.3333 * scale)   # 字号随 DPI 放大
    except tk.TclError:
        pass
    ensure_fonts(root)                                  # 选择系统里最好看的字体
    apply_palette(load_settings().get("theme", "dark"))  # 记住上次的日间/夜间选择（默认夜间）
    app = CubeTimerApp(root, load_solves())
    app.ui_scale = scale
    root.mainloop()


if __name__ == "__main__":
    main()
