/*!
 * 魔方计时器 —— 统计核心（纯函数，无依赖）
 * 同时供浏览器（window.CubeStats）与 Node 测试（module.exports）使用。
 *
 * 数据模型：solve = { ms: Number, dnf: Boolean, ts: Number(毫秒时间戳), id: String }
 * 平均规则与 WCA 一致：去掉最好与最差各一次后取算术平均。
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CubeStats = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const STAT_ITEMS = [
    { key: 'best', label: '最好成绩', window: 0 },
    { key: 'ao5', label: '五次平均', window: 5 },
    { key: 'ao12', label: '十二次平均', window: 12 },
    { key: 'mo3', label: '三次平均', window: 3 },
    { key: 'ao50', label: '五十次平均', window: 50 },
    { key: 'ao100', label: '一百次平均', window: 100 },
  ];

  /** 毫秒 -> 计时字符串：12.34 / 1:02.34 / 1:02:03.45 */
  function formatMs(ms) {
    const totalCs = Math.round(Math.max(0, Number(ms) || 0) / 10);
    const cs = totalCs % 100;
    const totalS = Math.floor(totalCs / 100);
    const s = totalS % 60;
    const m = Math.floor(totalS / 60) % 60;
    const h = Math.floor(totalS / 3600);
    if (h) return h + ':' + pad(m) + ':' + pad(s) + '.' + pad(cs);
    if (m) return m + ':' + pad(s) + '.' + pad(cs);
    return s + '.' + pad(cs);
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  /** 统计值 -> 显示字符串；null=样本不足，'DNF'=计入部分含 DNF */
  function formatStat(v) {
    if (v === null || v === undefined) return '—';
    if (v === 'DNF') return 'DNF';
    return formatMs(v);
  }

  const key = (s) => (s && s.dnf ? Infinity : Number(s && s.ms) || 0);

  /** WCA 平均：去掉最好与最差各一个 */
  function trimmedAverage(window) {
    const n = window.length;
    if (!n) return null;
    if (n >= 5) {
      const sorted = window.slice().sort((a, b) => key(a) - key(b));
      const middle = sorted.slice(1, -1);
      if (middle.some((s) => s.dnf)) return 'DNF';
      return middle.reduce((sum, s) => sum + s.ms, 0) / middle.length;
    }
    if (window.some((s) => s.dnf)) return 'DNF';
    return window.reduce((sum, s) => sum + s.ms, 0) / n;
  }

  /** 最近 window 次的平均，不足则 null */
  function rollingAverage(solves, window) {
    if (window <= 0 || solves.length < window) return null;
    return trimmedAverage(solves.slice(-window));
  }

  /** 三次平均：含任一 DNF 即为 DNF */
  function meanOf3(solves) {
    if (solves.length < 3) return null;
    const w = solves.slice(-3);
    if (w.some((s) => s.dnf)) return 'DNF';
    return w.reduce((sum, s) => sum + s.ms, 0) / 3;
  }

  /** 汇总全部统计项 */
  function computeStats(solves) {
    const list = solves || [];
    const valid = list.filter((s) => !s.dnf);
    const st = {
      count: list.length,
      valid: valid.length,
      dnfCount: list.length - valid.length,
      best: null,
      worst: null,
      mean: null,
      values: {},
    };
    if (valid.length) {
      st.best = valid.reduce((a, b) => (b.ms < a.ms ? b : a));
      st.worst = valid.reduce((a, b) => (b.ms > a.ms ? b : a));
      st.mean = valid.reduce((sum, s) => sum + s.ms, 0) / valid.length;
    }
    for (const item of STAT_ITEMS) {
      if (item.key === 'best') st.values.best = st.best ? st.best.ms : null;
      else if (item.key === 'mo3') st.values.mo3 = meanOf3(list);
      else st.values[item.key] = rollingAverage(list, item.window);
    }
    return st;
  }

  /** 单次成绩的显示文本 */
  function solveText(s) {
    if (!s) return '—';
    return s.dnf ? 'DNF (' + formatMs(s.ms) + ')' : formatMs(s.ms);
  }

  /** 列表中“最好成绩”所在下标（同成绩取最早一次）；无有效成绩返回 -1 */
  function bestIndex(solves) {
    let idx = -1;
    let best = Infinity;
    (solves || []).forEach((s, i) => {
      if (!s.dnf && s.ms < best) { best = s.ms; idx = i; }
    });
    return idx;
  }

  /** 导出 CSV 文本（含统计汇总） */
  function toCSV(solves) {
    const rows = [['#', '成绩(毫秒)', '成绩', 'ao5', 'ao12', '状态', '记录时间']];
    const list = solves || [];
    list.forEach((s, i) => {
      const slice = list.slice(0, i + 1);
      rows.push([
        i + 1, s.ms, s.dnf ? 'DNF' : formatMs(s.ms),
        formatStat(rollingAverage(slice, 5)), formatStat(rollingAverage(slice, 12)),
        s.dnf ? 'DNF' : 'OK',
        s.ts ? new Date(s.ts).toLocaleString() : '',
      ]);
    });
    const st = computeStats(list);
    rows.push([]);
    rows.push(['统计项', '数值']);
    for (const item of STAT_ITEMS) rows.push([item.label, formatStat(st.values[item.key])]);
    rows.push(['平均成绩', formatStat(st.mean)]);
    rows.push(['总次数', st.count]);
    rows.push(['有效次数', st.valid]);
    rows.push(['DNF 次数', st.dnfCount]);
    return rows
      .map((r) => r.map((c) => {
        const s = String(c === null || c === undefined ? '' : c);
        return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
      }).join(','))
      .join('\r\n');
  }

  return {
    STAT_ITEMS, formatMs, formatStat, trimmedAverage, rollingAverage,
    meanOf3, computeStats, solveText, bestIndex, toCSV,
  };
});
