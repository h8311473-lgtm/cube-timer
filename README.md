# Cube Timer · 魔方计时器

简洁的魔方计时器，两个版本共用同一套统计口径（WCA 规则）：

| 版本 | 目录 | 技术栈 | 运行环境 |
| --- | --- | --- | --- |
| **电脑版** | [`desktop/`](desktop/) | Python + tkinter（零第三方依赖） | Windows / macOS / Linux |
| **手机版** | [`mobile/`](mobile/) | 原生 HTML + CSS + JS（PWA，零依赖） | iPhone Safari / 安卓 Chrome |

## 共同功能

- **按住准备 → 松开开始 → 再按停止**（电脑版按住空格键；手机版按住屏幕）
- 统计：最好成绩、平均成绩、mo3、ao5、ao12、ao50、ao100
- 平均遵循 **WCA 规则**：去掉最好与最差各一次后取算术平均；样本不足显示 `—`，计入部分含 DNF 则显示 `DNF`
- DNF 标记、**删除本次成绩** / 删除选中、撤销、导出 CSV
- 成绩自动保存在本地（电脑版 JSON 文件，手机版 localStorage）
- 界面随窗口/屏幕尺寸自适应，高分屏（DPI）下清晰不裁切

## 电脑版

```bash
cd desktop
python cube_timer.py          # 或双击 play-cube-timer.bat
```

- 界面：浅色 / 夜间双主题（`Ctrl+L` 切换，会被记住）、大圆角卡片、柔和渐变
- 详细说明：[`desktop/README.md`](desktop/README.md)
- 截图：[`desktop/screenshots/`](desktop/screenshots/)

## 手机版

```bash
cd mobile
node serve.js                 # 零依赖静态服务器，会打印手机访问地址
```

手机与电脑连同一 Wi-Fi，iPhone 用 **Safari** / 安卓用 **Chrome** 打开该地址，
再「添加到主屏幕」即可当应用用（全屏、离线可用）。

- 界面：浅色玻璃拟态（磨砂 + 高光 + 柔和渐变），无夜间模式
- 详细说明：[`mobile/README.md`](mobile/README.md)
- 截图：[`mobile/screenshots/`](mobile/screenshots/)

## 自测

```bash
cd desktop && python test_cube_timer.py && python test_cube_timer_gui.py
cd mobile  && node tests/stats.test.js && node tests/page.check.js
```

## 说明

- 两个版本都不联网、不上传任何数据，也不需要登录。
- 成绩各自保存在本机，电脑版与手机版之间不互通。
- 手机版是网页应用（PWA），装上主屏后与原生应用体验接近，但不是 App Store / 应用商店的安装包。
