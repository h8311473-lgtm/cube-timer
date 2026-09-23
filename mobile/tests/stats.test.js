/*!
 * 手机版统计逻辑测试（Node 内置测试框架，无需依赖）
 * 运行：node tests/stats.test.js
 */
const test = require('node:test');
const assert = require('node:assert/strict');
const S = require('../stats.js');

/** 构造成绩列表：D(10000, 12000) */
function D(...times) {
  return times.map((ms, i) => ({
    ms, dnf: false, ts: 1700000000000 + i * 1000, id: 's' + i,
  }));
}

/** 把指定下标（从 1 开始）标记为 DNF */
function dnf(solves, ...idxs) {
  idxs.forEach((n) => { if (solves[n - 1]) solves[n - 1].dnf = true; });
  return solves;
}

test('formatMs：百分秒与进位', () => {
  assert.equal(S.formatMs(0), '0.00');
  assert.equal(S.formatMs(1234), '1.23');
  assert.equal(S.formatMs(1235), '1.24');
  assert.equal(S.formatMs(9944), '9.94');
  assert.equal(S.formatMs(9949), '9.95');
  assert.equal(S.formatMs(9999), '10.00');
  assert.equal(S.formatMs(60000), '1:00.00');
  assert.equal(S.formatMs(61234), '1:01.23');
  assert.equal(S.formatMs(3661230), '1:01:01.23');
});

test('formatStat：样本不足与 DNF', () => {
  assert.equal(S.formatStat(null), '—');
  assert.equal(S.formatStat(undefined), '—');
  assert.equal(S.formatStat('DNF'), 'DNF');
  assert.equal(S.formatStat(11333.333), '11.33');
});

test('ao5：去掉最好与最差各一个', () => {
  assert.equal(Math.round(S.trimmedAverage(D(10000, 12000, 11000, 99000, 11000)) * 10) / 10,
               11333.3);
  assert.equal(S.trimmedAverage(D(5000, 5000, 5000, 5000, 5000)), 5000);
  // DNF 天然是最差，会被去掉，因此平均仍有效：(10000+11000+12000)/3
  assert.equal(S.trimmedAverage(dnf(D(10000, 11000, 12000, 13000, 15000), 5)), 12000);
  // 两个 DNF：去掉一个最好、一个最差后仍含 DNF -> DNF
  assert.equal(S.trimmedAverage(dnf(D(10000, 11000, 12000, 13000, 14000), 3, 4)), 'DNF');
  // 全部 DNF
  assert.equal(S.trimmedAverage(dnf(D(1, 2, 3, 4, 5), 1, 2, 3, 4, 5)), 'DNF');
  // 不足 5 个时全部计入
  assert.equal(S.trimmedAverage(D(1000, 2000, 3000, 4000)), 2500);
});

test('rollingAverage：样本不足返回 null', () => {
  const five = D(10000, 20000, 30000, 40000, 50000);
  assert.equal(S.rollingAverage(five.slice(0, 4), 5), null);
  assert.equal(S.rollingAverage(five, 5), 30000);
  assert.equal(S.rollingAverage(five, 12), null);
  assert.equal(S.rollingAverage(five, 0), null);
});

test('mo3：三次平均，含 DNF 即 DNF', () => {
  assert.equal(S.meanOf3(D(1000, 2000)), null);
  assert.equal(S.meanOf3(D(10000, 20000, 30000)), 20000);
  assert.equal(S.meanOf3(dnf(D(10000, 20000, 30000), 3)), 'DNF');
});

test('computeStats：汇总正确', () => {
  const solves = dnf(D(10000, 9000, 11000, 12000, 15000, 8000), 5);
  const st = S.computeStats(solves);
  assert.equal(st.count, 6);
  assert.equal(st.valid, 5);
  assert.equal(st.dnfCount, 1);
  assert.equal(st.best.ms, 8000);
  assert.equal(st.worst.ms, 12000);
  assert.equal(st.mean, 10000);
  // 最近 5 次：9000,11000,12000,DNF,8000 -> 去掉 8000 与 DNF -> (9000+11000+12000)/3
  assert.equal(Math.round(st.values.ao5 * 10) / 10, 10666.7);
  assert.equal(st.values.mo3, 'DNF');
  assert.equal(st.values.ao12, null);
  assert.equal(st.values.ao50, null);
  assert.equal(st.values.ao100, null);
});

test('computeStats：空列表', () => {
  const st = S.computeStats([]);
  assert.equal(st.count, 0);
  assert.equal(st.best, null);
  assert.equal(st.mean, null);
  assert.equal(st.values.best, null);
  assert.equal(st.values.ao5, null);
});

test('bestIndex：取最早的最快一次，忽略 DNF', () => {
  assert.equal(S.bestIndex(D(12000, 9000, 9000, 11000)), 1);
  assert.equal(S.bestIndex(dnf(D(7000, 9000, 11000), 1)), 1);   // 最快那条是 DNF，顺延
  assert.equal(S.bestIndex([]), -1);
  assert.equal(S.bestIndex(dnf(D(9000), 1)), -1);
});

test('solveText：DNF 保留原始时间', () => {
  assert.equal(S.solveText({ ms: 12340, dnf: false }), '12.34');
  assert.equal(S.solveText({ ms: 12340, dnf: true }), 'DNF (12.34)');
  assert.equal(S.solveText(null), '—');
});

test('toCSV：包含表头、每行平均与统计汇总', () => {
  const csv = S.toCSV(D(10000, 12000, 11000, 13000, 10000, 11000));
  const lines = csv.split('\r\n');
  assert.match(lines[0], /^#,成绩\(毫秒\),成绩,ao5,ao12,状态,记录时间$/);
  assert.match(lines[1], /^1,10000,10\.00,—,—,OK,/);
  // 第 6 行：最近 5 次 12000,11000,13000,10000,11000 -> 去 13000 与 10000 -> (11000+11000+12000)/3
  assert.match(lines[6], /^6,11000,11\.00,11\.33,—,OK,/);
  assert.ok(lines.some((l) => l.startsWith('最好成绩,10.00')));
  assert.ok(lines.some((l) => l === '总次数,6'));
  assert.ok(lines.some((l) => l === 'DNF 次数,0'));
});

test('toCSV：含 DNF 与逗号时格式安全', () => {
  const list = dnf(D(12340, 15000), 2);
  const csv = S.toCSV(list);
  const lines = csv.split('\r\n');
  assert.match(lines[2], /^2,15000,DNF,—,—,DNF,/);
  assert.ok(lines.some((l) => l === 'DNF 次数,1'));
});
