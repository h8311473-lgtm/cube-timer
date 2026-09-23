/*!
 * 生成 390x844（iPhone 竖屏）1:1 效果图。
 * 做法：用 _viewport.html 提供的固定 390px 画框渲染，再裁剪出画框区域
 *       （绕开 headless Chrome 窗口最小 526px 宽的限制）。
 * 用法：node tools/phone-shots.js [端口]
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.argv[2] || 8099);
const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'screenshots');
const TMP = path.join(ROOT, '_tmp');
const PROFILE = path.join(ROOT, '_browserprofile');
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find((p) => fs.existsSync(p));

const STATES = [
  { name: 'phone-idle.png', state: '' },
  { name: 'phone-ready.png', state: 'hold' },      // 按住不放 -> 绿色准备态
  { name: 'phone-running.png', state: 'running' },
  { name: 'phone-result.png', state: 'done' },
];

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(TMP, { recursive: true });
if (!CHROME) { console.error('找不到 Chrome/Edge'); process.exit(1); }

let failed = 0;
for (const s of STATES) {
  const raw = path.join(TMP, 'raw-' + s.name);
  const final = path.join(OUT, s.name);
  try { fs.unlinkSync(raw); } catch (e) {}
  const url = `http://localhost:${PORT}/_viewport.html` + (s.state ? '?state=' + s.state : '');
  try {
    execFileSync(CHROME, [
      '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
      `--user-data-dir=${PROFILE}`, '--hide-scrollbars', '--window-size=560,900',
      '--virtual-time-budget=2000', `--screenshot=${raw}`, url,
    ], { stdio: ['ignore', 'ignore', 'ignore'], timeout: 60000 });
    execFileSync('python', [path.join(__dirname, 'crop.py'), raw, final, '390', '844', '0', '0'],
                 { stdio: ['ignore', 'pipe', 'ignore'] });
    const size = fs.statSync(final).size;
    console.log(`  ✔ ${s.name}  ${size} 字节`);
    fs.unlinkSync(raw);
  } catch (e) {
    console.log(`  ✖ ${s.name} 失败: ` + e.message.split('\n')[0]);
    failed++;
  }
}
console.log();
if (failed) { console.log(failed + ' 张失败'); process.exit(1); }
console.log('1:1 效果图已输出到 ' + OUT);
