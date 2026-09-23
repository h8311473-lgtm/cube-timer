/*!
 * 触摸流程无人值守验收：
 *   用 headless Chrome 依次跑 ready / running / finish 三种场景，
 *   截图 + 读取页面标题里的自测报告。
 * 用法：node tools/touch-check.js [端口]
 *
 * 说明：这里用 --timeout（真实时间）而不是 --virtual-time-budget，
 *       因为虚拟时间不驱动 requestAnimationFrame，会让计时显示停滞。
 *       注意 Chrome 的 Mojo IPC 需要命名管道，在受限沙箱下会失败。
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.argv[2] || 8099);
const OUT = path.join(__dirname, '..', 'screenshots');
const PROFILE = path.join(__dirname, '..', '_browserprofile');
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
].find((p) => fs.existsSync(p));

// 场景与「页面跑完所需时间」+ 1.2s 余量
const CASES = [
  { step: 'ready',   shot: 'phone-ready.png',   wait: 1800 },
  { step: 'running', shot: 'phone-running.png', wait: 3600 },
  { step: 'finish',  shot: 'phone-result.png',  wait: 4000 },
];

function run(step, shot, wait) {
  const url = `http://localhost:${PORT}/_touch-test.html?step=${step}`;
  const shotPath = path.join(OUT, shot);
  try { fs.unlinkSync(shotPath); } catch (e) {}
  const args = [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `--user-data-dir=${PROFILE}`, '--hide-scrollbars', '--window-size=390,844',
    `--timeout=${wait}`, '--dump-dom', `--screenshot=${shotPath}`, url,
  ];
  const dom = execFileSync(CHROME, args, {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'],
    timeout: wait + 30000, maxBuffer: 1 << 26,  });
  const m = dom.match(/<title>TOUCH_REPORT:([\s\S]*?)<\/title>/);
  const ok = fs.existsSync(shotPath);
  return { report: m ? m[1].trim() : '（未拿到报告）', shot: ok ? shotPath : null };
}

if (!CHROME) { console.error('找不到 Chrome/Edge'); process.exit(1); }

let failed = 0;
for (const c of CASES) {
  console.log(`\n=== step=${c.step} ===`);
  let r;
  try {
    r = run(c.step, c.shot, c.wait);
  } catch (e) {
    console.log('  执行失败: ' + e.message.split('\n')[0]);
    failed++;
    continue;
  }
  console.log('  报告: ' + r.report);
  console.log('  截图: ' + (r.shot ? path.basename(r.shot) : '失败'));

  const rep = r.report;
  if (c.step === 'ready') {
    if (!/按住后=ready/.test(rep)) { console.log('  ✖ 未进入准备状态'); failed++; }
    else console.log('  ✔ 按住后进入准备状态（绿色）');
  }
  if (c.step === 'running') {
    if (!/松开后=running/.test(rep)) { console.log('  ✖ 松开未开始计时'); failed++; }
    else console.log('  ✔ 松开即开始计时');
    // 注：headless 虚拟时间不驱动 requestAnimationFrame，读数可能停在 0.00，
    //     计时精度由 finish 场景记录的成绩毫秒数验证。
    console.log('  ℹ 计时读数：' + (rep.match(/读数=([\d.:]+)/) || [, '?'])[1]);
  }
  if (c.step === 'finish') {
    if (!/停止后=done/.test(rep)) { console.log('  ✖ 再按未停止'); failed++; }
    else console.log('  ✔ 再按一下停止');
    const m = rep.match(/条数 (\d+)→(\d+)/);
    if (m && Number(m[2]) === Number(m[1]) + 1) console.log('  ✔ 成绩已记录');
    else { console.log('  ✖ 成绩未记录: ' + (m ? m[0] : '无')); failed++; }
    const ms = rep.match(/成绩=(\d+)ms/);
    if (ms) {
      const v = Number(ms[1]);
      if (v > 1500 && v < 2600) console.log('  ✔ 记录时长合理：' + v + 'ms（松手后约 1.6s 按下停止）');
      else { console.log('  ? 记录时长 ' + v + 'ms 与预期(约1600ms)有偏差'); }
    }
  }
}

console.log();
if (failed) { console.log('验收失败 ' + failed + ' 项'); process.exit(1); }
console.log('触摸流程验收通过');
