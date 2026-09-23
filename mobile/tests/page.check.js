/*!
 * 前端一致性检查（无需浏览器）：
 *   1. index.html 里用到的所有 id 都存在
 *   2. 所有 addEventListener 绑定的元素都能找到
 *   3. 调用的 CubeStats API 都存在
 *   4. 关键交互（pointerdown/up、按住阈值、状态机）都在代码里
 * 运行：node tests/page.check.js
 */
const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');

const dir = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const stats = require('../stats.js');

let failed = 0;
function check(name, fn) {
  try { fn(); console.log('  OK   ' + name); }
  catch (e) { failed++; console.log(' FAIL  ' + name + ' -> ' + e.message); }
}

// ---- 1. HTML 中定义的 id ----
const definedIds = new Set();
for (const m of html.matchAll(/\sid="([^"]+)"/g)) definedIds.add(m[1]);

// ---- 2. JS 中通过 getElementById / $() 引用的 id ----
const usedIds = new Set();
for (const m of html.matchAll(/\$\('([^']+)'\)/g)) usedIds.add(m[1]);
for (const m of html.matchAll(/getElementById\('([^']+)'\)/g)) usedIds.add(m[1]);

console.log('== HTML / JS 一致性 ==');
check('页面引用的 id 全部存在（' + [...usedIds].join(', ') + '）', () => {
  const missing = [...usedIds].filter((id) => !definedIds.has(id));
  assert.equal(missing.length, 0, '缺少 id: ' + missing.join(', '));
});
check('id 无重复定义', () => {
  const seen = new Set();
  const dup = [];
  for (const m of html.matchAll(/\sid="([^"]+)"/g)) {
    if (seen.has(m[1])) dup.push(m[1]);
    seen.add(m[1]);
  }
  assert.equal(dup.length, 0, '重复: ' + dup.join(', '));
});
check('stats.js 与 index.html 的脚本顺序正确（先 stats.js 再内联脚本）', () => {
  const a = html.indexOf('<script src="stats.js">');
  const b = html.indexOf('<script>\n(function ()');
  assert.ok(a > 0 && b > a, 'stats.js 必须先加载');
});
check('引用的本地资源都存在', () => {
  const refs = ['stats.js', 'manifest.webmanifest', 'icon-180.png'];
  const missing = refs.filter((r) => !fs.existsSync(path.join(dir, r)));
  assert.equal(missing.length, 0, '缺少文件: ' + missing.join(', '));
});
check('manifest 中的图标文件都存在', () => {
  const mf = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.webmanifest'), 'utf8'));
  const missing = mf.icons.map((i) => i.src).filter((s) => !fs.existsSync(path.join(dir, s)));
  assert.equal(missing.length, 0, '缺少图标: ' + missing.join(', '));
});

console.log('== CubeStats API 调用 ==');
check('index.html 调用的 stats API 都存在', () => {
  const called = new Set();
  for (const m of html.matchAll(/\bS\.([A-Za-z_][A-Za-z0-9_]*)/g)) called.add(m[1]);
  const missing = [...called].filter((k) => !(k in stats));
  assert.equal(missing.length, 0, '缺少 API: ' + missing.join(', '));
  console.log('       调用: ' + [...called].join(', '));
});

console.log('== 交互逻辑 ==');
check('按住阈值常量存在且在合理范围', () => {
  const m = html.match(/HOLD_MS\s*=\s*(\d+)/);
  assert.ok(m, '未找到 HOLD_MS');
  const v = Number(m[1]);
  assert.ok(v >= 150 && v <= 800, 'HOLD_MS=' + v + ' 不合理');
});
check('计时卡绑定了 pointerdown / pointerup', () => {
  assert.match(html, /card\.addEventListener\('pointerdown'/);
  assert.match(html, /card\.addEventListener\('pointerup'/);
});
check('松开逻辑：hold -> 未达阈值则回到 idle；ready -> 开始计时', () => {
  assert.match(html, /if \(timerState === 'hold'\)[\s\S]{0,400}held < HOLD_MS/);
  assert.match(html, /if \(timerState === 'ready'\) startRun\(\)/);
});
check('再按一下结束：running 时 pointerdown 调 stopRun', () => {
  assert.match(html, /if \(timerState === 'running'\) \{ stopRun\(\); return; \}/);
});
check('有兜底：手指滑出后松开也能触发', () => {
  assert.match(html, /window\.addEventListener\('pointerup'/);
});
check('防止双击缩放与下拉刷新', () => {
  assert.match(html, /dblclick/);
  assert.match(html, /touchmove[\s\S]{0,200}preventDefault/);
});
check('成绩写入 localStorage 并可读回', () => {
  assert.match(html, /localStorage\.setItem\(STORE_KEY/);
  assert.match(html, /localStorage\.getItem\(STORE_KEY/);
});
check('删除本次 / 删除选中 / DNF / 撤销 / 导出 都已绑定', () => {
  assert.match(html, /\$\('btnDelLast'\)\.addEventListener\('click', deleteLast\)/);
  assert.match(html, /\$\('btnDelSel'\)\.addEventListener\('click', deleteSelected\)/);
  assert.match(html, /\$\('btnDnf'\)\.addEventListener\('click', toggleDnf\)/);
  assert.match(html, /\$\('btnUndo'\)\.addEventListener\('click', undo\)/);
  assert.match(html, /\$\('btnCsv'\)\.addEventListener\('click', exportCsv\)/);
});
check('没有遗留夜间模式相关代码', () => {
  assert.ok(!/夜间|dark-theme|prefers-color-scheme/.test(html), '仍存在夜间模式痕迹');
});
check('玻璃效果：backdrop-filter 已使用', () => {
  assert.match(html, /backdrop-filter:\s*blur/);
});

console.log();
if (failed) { console.log('失败 ' + failed + ' 项'); process.exit(1); }
console.log('页面检查全部通过');
