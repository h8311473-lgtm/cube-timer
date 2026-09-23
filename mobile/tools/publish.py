#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 cube-timer 创建 GitHub Release 并开启 GitHub Pages。

用法:
    python publish.py            # 打包 + 建 Release + 开 Pages
    python publish.py release    # 只建 Release
    python publish.py pages      # 只开 Pages

需要环境变量 GITHUB_TOKEN（GitHub Personal Access Token，repo 权限）。
用到的网络请求都走 HTTPS 代理（可用 HTTPS_PROXY 指定）。
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

OWNER = "h8311473-lgtm"
REPO = "cube-timer"
TAG = "mobile-v1.0"
TITLE = "手机版 v1.0（iPhone / 安卓 PWA）"
PROXY = os.environ.get("HTTPS_PROXY") or "http://127.0.0.1:7897"

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
MOBILE_ASSETS = [
    "index.html", "stats.js", "sw.js", "manifest.webmanifest",
    "icon-180.png", "icon-512.png", "serve.js", "README.md",
]
DESKTOP_ASSETS = [
    "cube_timer.py", "play-cube-timer.bat", "test_cube_timer.py",
    "test_cube_timer_gui.py", "README.md",
]

RELEASE_NOTES = """## 手机版 v1.0 · 魔方计时器

**按住屏幕准备 → 松开开始 → 再按一下停止**，浅色玻璃拟态界面，无夜间模式。

### 功能

- 统计：最好成绩、平均成绩、mo3、ao5、ao12、ao50、ao100（WCA 规则：去掉最好与最差各一次）
- DNF 标记、删除本次成绩 / 删除选中、撤销、导出 CSV
- 成绩保存在手机本地，离线可用；可"添加到主屏幕"当应用使用

### 怎么用

**方式一：直接打开（推荐）**

任何手机浏览器打开：<https://h8311473-lgtm.github.io/cube-timer/mobile/>

- iPhone：Safari 打开 → 分享按钮 → 添加到主屏幕
- 安卓：Chrome 打开 → 菜单 → 安装应用 / 添加到主屏幕

**方式二：用本附件离线运行**

1. 解压 `cube-timer-mobile-v1.0.zip`
2. iPhone 用"文件"App 打开其中的 `index.html`（用 Safari 打开）
3. 安卓用 Chrome 打开 `index.html` 即可

**方式三：局域网（电脑和手机同一 Wi-Fi）**

解压后在文件夹里执行 `node serve.js`，手机访问打印出来的地址。

### 附件说明

| 文件 | 内容 |
| --- | --- |
| `cube-timer-mobile-v1.0.zip` | 手机版全部文件（直接可用，含离线支持） |
| `cube-timer-desktop-v1.0.zip` | 电脑版（Python + tkinter，零第三方依赖） |

### 说明

- 不联网、不上传任何数据、不需要登录
- 成绩存在本机，各设备之间不互通
"""


DESKTOP_HOWTO = """

电脑版（desktop 文件夹）
========================
需要电脑上装有 Python 3.10+（自带 tkinter 即可，无需第三方包）。

· 双击 play-cube-timer.bat，或命令行运行 python cube_timer.py
· 按住空格键准备 → 松开开始 → 再按空格停止
· 浅色 / 夜间双主题（Ctrl+L 切换）
· 成绩保存在同目录的 cube_times.json
"""


def log(msg: str) -> None:
    print(msg, flush=True)


def api(path: str, method: str = "GET", data: dict | None = None,
        token: str = "", raw: bytes | None = None,
        content_type: str = "application/json") -> tuple[int, dict | str]:
    url = "https://api.github.com" + path
    body = raw if raw is not None else (
        json.dumps(data).encode("utf-8") if data is not None else None)
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "token " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "cube-timer-publish")
    if body is not None:
        req.add_header("Content-Type", content_type)
    handler = urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
    opener = urllib.request.build_opener(handler)
    try:
        with opener.open(req, timeout=60) as resp:
            text = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(text or "{}")
            except json.JSONDecodeError:
                return resp.status, text
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(text or "{}")
        except json.JSONDecodeError:
            return e.code, text


def build_zip(name: str, src_dir: Path, files: list[str], extra_root: str | None = None) -> Path:
    DIST.mkdir(exist_ok=True)
    out = DIST / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            p = src_dir / f
            if p.exists():
                z.write(p, ("cube-timer-mobile/" if extra_root else "") + f)
            else:
                log(f"  ! 缺少 {p}")
    # 手机版附带一份简明的中文使用说明
    return out


MOBILE_HOWTO = """魔方计时器 · 手机版 v1.0
================================

怎么打开
--------
1) 在线打开（推荐，任何网络都行）：
   https://h8311473-lgtm.github.io/cube-timer/mobile/
   iPhone 用 Safari 打开后：分享 → 添加到主屏幕，即可当应用使用。

2) 离线使用本文件夹：
   把 index.html 传到手机，用 Safari / Chrome 打开即可，功能完全一样。

怎么计时
--------
· 按住屏幕不放   → 计时区变绿（准备）
· 松开手指       → 立即开始计时
· 再按一下屏幕   → 停止并记录成绩

成绩与统计
----------
· 统计：最好成绩、平均成绩、mo3、ao5、ao12、ao50、ao100
· 平均按 WCA 规则：去掉最好与最差各一次
· 成绩保存在手机本地（浏览器的 localStorage）
· 重要成绩建议用「导出」备份 CSV，清除浏览器数据会一并清空

底部按钮
--------
删除本次 / 删除选中 / DNF / 撤销 / 导出

说明：程序不联网、不上传任何数据、不需要登录。
"""


def _find_dir(candidates: list[Path], marker: str) -> Path:
    for c in candidates:
        if (c / marker).exists():
            return c
    return candidates[0]


def make_zips() -> tuple[Path, Path, Path]:
    """打包手机版、电脑版与合集。

    目录来源优先用命令行参数（或环境变量），否则自动在若干候选位置里探测：
        python tools/publish.py --mobile <手机版目录> --desktop <电脑版目录>
    """
    argv = sys.argv[1:]
    env_m = os.environ.get("MOBILE_DIR")
    env_d = os.environ.get("DESKTOP_DIR")

    def arg_of(flag: str) -> str | None:
        return argv[argv.index(flag) + 1] if flag in argv and len(argv) > argv.index(flag) + 1 else None

    root = HERE.parent                                  # tools/ 的上一级 = mobile/
    m_given = arg_of("--mobile") or env_m
    d_given = arg_of("--desktop") or env_d

    candidates_mobile = ([Path(m_given)] if m_given else []) + [HERE, root]
    candidates_desktop = ([Path(d_given)] if d_given else []) + [root / "desktop"]
    for up in (root.parent, root.parent.parent):
        candidates_mobile += [up / "mobile"]
        candidates_desktop += [up / "desktop", up / "cube-timer"]

    mobile_dir = _find_dir(candidates_mobile, "index.html")
    desktop_dir = _find_dir(candidates_desktop, "cube_timer.py")
    log(f"手机版目录: {mobile_dir}")
    log(f"电脑版目录: {desktop_dir}")

    log("打包手机版…")
    mz = build_zip("cube-timer-mobile-v1.0.zip", mobile_dir, MOBILE_ASSETS,
                   extra_root="cube-timer-mobile")
    with zipfile.ZipFile(mz, "a", zipfile.ZIP_DEFLATED) as z:
        z.writestr("cube-timer-mobile/使用说明.txt", MOBILE_HOWTO)
    log(f"  {mz.name}  {mz.stat().st_size / 1024:.1f} KB")

    log("打包电脑版…")
    dz = build_zip("cube-timer-desktop-v1.0.zip", desktop_dir, DESKTOP_ASSETS)
    ok_desktop = (desktop_dir / "cube_timer.py").exists()
    log(f"  {dz.name}  {dz.stat().st_size / 1024:.1f} KB"
        + ("" if ok_desktop else "   ! 未找到电脑版文件"))

    log("打包合集…")
    allz = DIST / "cube-timer-v1.0-all.zip"
    with zipfile.ZipFile(allz, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        if ok_desktop:
            for f in DESKTOP_ASSETS:
                if (desktop_dir / f).exists():
                    z.write(desktop_dir / f, "cube-timer/desktop/" + f)
        for f in MOBILE_ASSETS:
            if (mobile_dir / f).exists():
                z.write(mobile_dir / f, "cube-timer/mobile/" + f)
        z.writestr("cube-timer/使用说明.txt", MOBILE_HOWTO + DESKTOP_HOWTO)
    log(f"  {allz.name}  {allz.stat().st_size / 1024:.1f} KB")
    return mz, dz, allz


def ensure_release(token: str) -> int | None:
    code, data = api(f"/repos/{OWNER}/{REPO}/releases/tags/{TAG}", token=token)
    if code == 200 and isinstance(data, dict):
        log(f"Release {TAG} 已存在，直接复用（id={data['id']}）")
        return data["id"]
    log(f"创建 Release {TAG} …")
    code, data = api(f"/repos/{OWNER}/{REPO}/releases", method="POST", token=token, data={
        "tag_name": TAG,
        "target_commitish": "main",
        "name": TITLE,
        "body": RELEASE_NOTES,
        "draft": False,
        "prerelease": False,
    })
    if code not in (200, 201):
        log(f"  ✖ 创建失败 HTTP {code}: {data}")
        return None
    log(f"  ✔ 已创建（id={data['id']}）")
    log(f"    地址: {data['html_url']}")
    return data["id"]


def upload_asset(token: str, release_id: int, path: Path, retries: int = 3) -> bool:
    """用 curl 上传附件：Python 的 SSL 在部分代理下会 UNEXPECTED_EOF，curl 更稳。"""
    import shutil
    import subprocess

    name = path.name
    code, assets = api(f"/repos/{OWNER}/{REPO}/releases/{release_id}/assets", token=token)
    if code == 200 and isinstance(assets, list):
        for a in assets:
            if a.get("name") == name:
                api(f"/repos/{OWNER}/{REPO}/releases/assets/{a['id']}",
                    method="DELETE", token=token)
                log(f"  已删除同名旧附件 {name}")

    size_kb = path.stat().st_size / 1024
    if size_kb < 1:
        log(f"  ✖ {name} 内容为空（{path}），跳过上传")
        return False

    url = (f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/"
           f"{release_id}/assets?name={name}")
    curl = shutil.which("curl") or "curl"
    log(f"上传 {name}（{size_kb:.1f} KB）…")
    for attempt in range(1, retries + 1):
        cmd = [curl, "-sS", "--max-time", "120", "-X", "POST",
               "-H", "Authorization: token " + token,
               "-H", "Content-Type: application/zip",
               "-H", "User-Agent: cube-timer-publish",
               "--data-binary", "@" + str(path), url]
        if PROXY:
            cmd[1:1] = ["-x", PROXY]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
            out = (proc.stdout or "").strip()
            if proc.returncode == 0 and '"browser_download_url"' in out:
                try:
                    log("  ✔ " + json.loads(out)["browser_download_url"])
                except Exception:
                    log("  ✔ 上传完成")
                return True
            log(f"  第 {attempt} 次失败：{out[:200] or proc.stderr[:200]}")
        except Exception as exc:
            log(f"  第 {attempt} 次失败：{type(exc).__name__}: {exc}")
        if attempt < retries:
            time.sleep(2 * attempt)
    return False


def enable_pages(token: str) -> bool:
    code, data = api(f"/repos/{OWNER}/{REPO}/pages", token=token)
    if code == 200:
        log(f"Pages 已开启：{data.get('html_url')}")
        return True
    log("开启 GitHub Pages（main 分支根目录）…")
    code, data = api(f"/repos/{OWNER}/{REPO}/pages", method="POST", token=token,
                     data={"source": {"branch": "main", "path": "/"}})
    if code in (200, 201, 204):
        log("  ✔ 已开启")
        return True
    if code == 409:      # 已存在
        log("  Pages 已存在")
        return True
    log(f"  ✖ 失败 HTTP {code}: {data}")
    return False


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        log("请先设置环境变量 GITHUB_TOKEN")
        sys.exit(1)
    action = sys.argv[1] if len(sys.argv) > 1 else "all"

    if action in ("all", "release"):
        mz, dz, allz = make_zips()
        rid = ensure_release(token)
        if rid:
            for p in (mz, dz, allz):
                upload_asset(token, rid, p)
    if action in ("all", "pages"):
        enable_pages(token)
        log("")
        log("公开访问地址（Pages 首次部署需要 1-2 分钟）：")
        log(f"  https://{OWNER}.github.io/{REPO}/          ← 项目首页")
        log(f"  https://{OWNER}.github.io/{REPO}/mobile/   ← 手机版（推荐分享这个）")


if __name__ == "__main__":
    main()
