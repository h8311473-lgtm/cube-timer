# -*- coding: utf-8 -*-
"""GUI 烟雾测试：真实创建窗口、模拟空格走完一次计时流程，并截图确认渲染。

注意：成绩列表是自绘的 Canvas 组件（SolveList），不是 ttk.Treeview，
因此这里通过 app.listview.solves / selection 来断言。
测试通过环境变量把数据/设置文件重定向到 _tmp/，不会动真实成绩。
"""
import ctypes
import os
import struct
import sys
import time
import tkinter as tk
import zlib
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
(HERE / "_tmp").mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))
os.environ["CUBE_TIMER_DATA"] = str(HERE / "_tmp" / "test_cube_times.json")
os.environ["CUBE_TIMER_SETTINGS"] = str(HERE / "_tmp" / "test_cube_settings.json")

from cube_timer import (CubeTimerApp, Solve, apply_palette, compute_stats,
                        enable_dpi_awareness, ensure_fonts, format_ms, format_stat)
import cube_timer

HERE = Path(__file__).resolve().parent
SHOT_IDLE = HERE / "_tmp" / "ui_idle.png"
SHOT_READY = HERE / "_tmp" / "ui_ready.png"
SHOT_RESULT = HERE / "_tmp" / "ui_result.png"
SHOT_IDLE.parent.mkdir(exist_ok=True)


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.008)


def grab(root, path):
    """用 PrintWindow 抓窗口位图并手写 PNG（不依赖 Pillow）。"""
    root.update_idletasks()
    try:
        hwnd = int(root.frame(), 16)
    except Exception:
        hwnd = ctypes.windll.user32.FindWindowW(None, root.title())
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top

    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)

    class BMIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    bi = BMIH()
    bi.biSize = ctypes.sizeof(BMIH)
    bi.biWidth, bi.biHeight = w, -h
    bi.biPlanes, bi.biBitCount, bi.biCompression = 1, 24, 0
    row = (w * 3 + 3) & ~3
    buf = ctypes.create_string_buffer(row * h)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)

    raw = bytearray()
    data = buf.raw
    for y in range(h):
        raw.append(0)
        line = data[y * row: y * row + w * 3]
        raw += bytes(b for p in range(w)
                     for b in (line[p * 3 + 2], line[p * 3 + 1], line[p * 3]))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
                     + chunk(b"IEND", b""))

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return path


fails = []


def check(name, got, want=True):
    ok = got == want
    print(("  OK  " if ok else " FAIL ") + f"{name}: got={got!r} want={want!r}")
    if not ok:
        fails.append(name)


seed = [Solve(time_ms=v, timestamp=f"2025-01-0{i+1} 10:0{i}:00")
        for i, v in enumerate([13450, 12980, 15230, 14210, 13020, 12110, 15990])]

root = tk.Tk()
scale = enable_dpi_awareness()
try:
    root.tk.call("tk", "scaling", 1.3333 * scale)
except tk.TclError:
    pass
print(f"       [诊断] 建窗后屏幕 = {root.winfo_screenwidth()}x{root.winfo_screenheight()}"
      f"  dpi缩放 = {scale}  tk scaling = {root.tk.call('tk', 'scaling')}")
ensure_fonts(root)
apply_palette("light")          # 断言基于日间主题，先固定为日间
app = CubeTimerApp(root, seed)
app.ui_scale = scale
pump(root, 1.0)
print(f"       显示器缩放 = {scale}  窗口 = {root.winfo_width()}x{root.winfo_height()}"
      f"  屏幕 = {root.winfo_screenwidth()}x{root.winfo_screenheight()}"
      f"  布局比例 = {app._factor}")
print(f"       列表区 = {app.listview.winfo_width()}x{app.listview.winfo_height()}"
      f"  行高 = {app.listview.geom[0] if app.listview.geom else None}")

print("== 初始渲染 ==")
check("列表数据 7 条", len(app.listview.solves), 7)
check("状态 idle", app.state, "idle")
st = compute_stats(app.solves)
check("最好成绩", app.stat_values["best"].cget("text"), format_ms(12110))
check("最好成绩为绿色", app.stat_values["best"].cget("fg"), "#12a15c")
check("ao5 标签", app.stat_values["ao5"].cget("text"), format_stat(st.values["ao5"]))
check("ao12 样本不足", app.stat_values["ao12"].cget("text"), "—")
check("mo3 标签", app.stat_values["mo3"].cget("text"), format_stat(st.values["mo3"]))
check("ao50 样本不足", app.stat_values["ao50"].cget("text"), "—")
check("顶栏统计", "共 7 次" in app.meta_label.cget("text"))
check("计时区显示最新成绩", app.timer_label.cget("text"), format_ms(15990))
check("计时区为深色文字", app.timer_label.cget("fg"), "#1f2033")
check("计时卡片为白底", app.timer_label.cget("bg"), "#ffffff")
grab(root, SHOT_IDLE)

print("== 计时状态机 ==")
app._on_space_press()
check("按下 -> holding", app.state, "holding")
pump(root, 0.5)
check("按住 0.5s -> ready", app.state, "ready")
check("准备文字为绿色", app.timer_label.cget("fg"), "#12a15c")
check("准备时卡片变浅绿", app.timer_label.cget("bg"), "#e7f8ef")
grab(root, SHOT_READY)
app._on_space_release()
check("松开 -> running", app.state, "running")
pump(root, 0.8)
print(f"       计时中显示 = {app.timer_label.cget('text')}")
check("计时中为紫色", app.timer_label.cget("fg"), "#5b4bd6")
check("计时中卡片浅紫", app.timer_label.cget("bg"), "#f1eefe")
app._on_space_press()
check("再按 -> 停止", app.state, "idle")
check("记录一条成绩", len(app.solves), 8)
recorded = app.solves[-1].time_ms
print(f"       记录 = {recorded} ms ({format_ms(recorded)})")
check("时长合理 700~1000ms", 700 <= recorded <= 1000)
check("本次成绩用紫色显示", app.timer_label.cget("fg"), "#5b4bd6")
pump(root, 0.3)
check("列表同步为 8 条", len(app.listview.solves), 8)
check("列表自动选中最新一条", app.listview.selected_indexes(), [7])
check("卡片恢复白底", app.timer_label.cget("bg"), "#ffffff")

print("== 轻点空格不应开始 ==")
before = len(app.solves)
app._on_space_press()
app._on_space_release()
check("轻点后仍 idle", app.state, "idle")
check("轻点未新增成绩", len(app.solves), before)

print("== Esc 作废 ==")
app._on_space_press()
pump(root, 0.45)
check("进入 ready", app.state, "ready")
app._on_space_release()
check("running", app.state, "running")
pump(root, 0.3)
app.cancel_run()
check("Esc 后 idle", app.state, "idle")
check("Esc 未记录", len(app.solves), before)
check("卡片恢复白底", app.timer_label.cget("bg"), "#ffffff")

print("== 删除本次成绩 ==")
app.delete_last()
pump(root, 0.2)
check("删除后 7 条", len(app.solves), 7)
check("删的是最新那条", recorded in [s.time_ms for s in app.solves], False)
check("列表 7 条", len(app.listview.solves), 7)

print("== 撤销 ==")
app.undo()
pump(root, 0.2)
check("撤销后 8 条", len(app.solves), 8)
app.undo()
pump(root, 0.1)
check("空撤销栈无异常", app.state, "idle")

print("== 选中 / 删除选中 / DNF ==")
app.listview.select_only(0)
check("选中第 1 行", app.listview.selected_indexes(), [0])
app.delete_selected()
pump(root, 0.2)
check("删除选中后 7 条", len(app.solves), 7)
app.listview.select_only(0)
app.toggle_dnf_selected()
pump(root, 0.2)
check("DNF 计数 1", compute_stats(app.solves).dnf_count, 1)
check("顶栏含 DNF", "DNF 1" in app.meta_label.cget("text"))
app.undo()
pump(root, 0.2)
check("撤销 DNF 后计数 0", compute_stats(app.solves).dnf_count, 0)
app.listview.select_range(0, 2)
check("范围多选 3 行", app.listview.selected_indexes(), [0, 1, 2])
app.listview.clear_selection()
check("清空选中", app.listview.selected_indexes(), [])

print("== 空状态 ==")
app._push_undo("全部清空")
app.solves.clear()
app.refresh_all()
pump(root, 0.2)
check("清空后 0 条", len(app.solves), 0)
check("空表统计为 —", app.stat_values["best"].cget("text"), "—")
check("空表计时区 0.00", app.timer_label.cget("text"), "0.00")
app.undo()
pump(root, 0.2)
check("撤销清空恢复 7 条", len(app.solves), 7)

print("== 夜间模式 ==")
SHOT_DARK = HERE / "_tmp" / "ui_dark.png"
app.set_theme("dark")
pump(root, 0.4)
check("主题已切换", cube_timer.THEME, "dark")
check("卡片底色变深", app.timer_label.cget("bg"), cube_timer.t("CARD"))
check("卡片底色为深色", int(cube_timer.t("CARD")[1:3], 16) < 60, True)
check("卡片描边为深紫", cube_timer.t("CARD_LINE"), "#2e2745")
check("主文字变浅", app.timer_label.cget("fg"), "#f2f2f7")
check("窗口底色变深", root.cget("bg"), "#0a0a0f")
check("夜间按钮为选中态", app.btn_theme.active, True)
st_now = compute_stats(app.solves)
check("统计仍正确", app.stat_values["best"].cget("text"),
      format_stat(st_now.values["best"]))
app._on_space_press()
pump(root, 0.5)
check("夜间准备态为深绿", app.timer_label.cget("bg"), "#122a1e")
check("夜间准备文字为亮绿", app.timer_label.cget("fg"), "#32d978")
grab(root, SHOT_DARK)
app.cancel_run()
pump(root, 0.2)
app.set_theme("light")
pump(root, 0.4)
check("切回日间", cube_timer.THEME, "light")
check("卡片恢复白色", app.timer_label.cget("bg"), "#ffffff")
check("夜间按钮取消选中", app.btn_theme.active, False)

print("== 窗口缩放（响应式）==")
root.geometry("1000x700")
pump(root, 0.5)
check("小窗口布局比例变化", app._factor != 0.966, True)
print(f"       1000x700 -> 比例 {app._factor} 计时字号 {app.timer_label.cget('font')}")
root.geometry("1500x1100")
pump(root, 0.5)
print(f"       1500x1100 -> 比例 {app._factor} 计时字号 {app.timer_label.cget('font')}")
grab(root, SHOT_RESULT)

# 按大屏真实窗口尺寸（2K 200% 缩放时的默认尺寸）出一张夜间模式效果图
SHOT_BIG = HERE / "_tmp" / "ui_dark_large.png"
app.set_theme("dark")
root.geometry("1760x1440")
pump(root, 0.8)
grab(root, SHOT_BIG)
print(f"       大窗口 {root.winfo_width()}x{root.winfo_height()} -> 比例 {app._factor}"
      f" 计时字号 {app.timer_label.cget('font')}")

print(f"\n截图：{SHOT_IDLE.name} / {SHOT_READY.name} / {SHOT_RESULT.name} / {SHOT_DARK.name}")
app.on_close()
print()
if fails:
    print(f"FAILED: {fails}")
    sys.exit(1)
print("GUI SMOKE TEST PASSED")
