# -*- coding: utf-8 -*-
"""统计逻辑自测（对照 WCA 规则），不需要图形界面。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cube_timer import (Solve, compute_stats, format_ms, mean_of_3,
                        rolling_average, trimmed_average, load_solves, save_solves)

fails = []


def check(name, got, want):
    ok = got == want
    print(("  OK  " if ok else " FAIL ") + f"{name}: got={got!r} want={want!r}")
    if not ok:
        fails.append(name)


def T(*ms, dnf=()):
    """构造 Solve 列表；dnf 为需要标记为 DNF 的下标（从 1 开始）。"""
    out = []
    for i, v in enumerate(ms, 1):
        out.append(Solve(time_ms=v, dnf=(i in dnf)))
    return out


print("== format_ms ==")
check("0", format_ms(0), "0.00")
check("1234ms", format_ms(1234), "1.23")
check("1235ms 进位", format_ms(1235), "1.24")
check("9944ms 舍", format_ms(9944), "9.94")
check("9949ms 入", format_ms(9949), "9.95")
check("9950ms 进位", format_ms(9950), "9.95")
check("9999ms 进位到 10.00", format_ms(9999), "10.00")
check("59999ms", format_ms(59999), "1:00.00")
check("60000ms", format_ms(60000), "1:00.00")
check("61234ms", format_ms(61234), "1:01.23")
check("3661230ms", format_ms(3661230), "1:01:01.23")

print("== trimmed_average (ao5/ao12) ==")
# 10.00, 12.00, 11.00, 99.00, 11.00 -> 去掉 9.9s 与 10.00 -> (11+11+12)/3 = 11.333
w = T(10000, 12000, 11000, 99000, 11000)
check("ao5 去最高最低", round(trimmed_average(w), 1), 11333.3)
check("ao5 全部相同", trimmed_average(T(5000, 5000, 5000, 5000, 5000)), 5000.0)
# 含 DNF 时，DNF 视为最差被去掉 -> 平均仍有效
w = T(10000, 11000, 12000, 13000, 0, dnf=(5,))
check("ao5 DNF 被当作最差去掉", trimmed_average(w), 12000.0)
# 两个 DNF：去掉一个最好、一个最差(DNF)，剩余中仍有 DNF -> DNF
w = T(10000, 11000, 0, 0, 13000, dnf=(3, 4))
check("ao5 两个 DNF = DNF", trimmed_average(w), "DNF")
# 全部 DNF
check("ao5 全 DNF = DNF", trimmed_average(T(0, 0, 0, 0, 0, dnf=(1, 2, 3, 4, 5))), "DNF")
check("样本不足", trimmed_average(T(1000, 2000, 3000, 4000)), 2500.0)

print("== rolling_average ==")
five = T(10000, 20000, 30000, 40000, 50000)
check("不足 5 次 -> None", rolling_average(five[:4], 5), None)
check("刚好 5 次", rolling_average(five, 5), 30000.0)
check("ao12 不足 -> None", rolling_average(five, 12), None)

print("== mo3 ==")
check("mo3 不足 3 次 -> None", mean_of_3(T(1000, 2000)), None)
check("mo3 = 算术平均", mean_of_3(T(10000, 20000, 30000)), 20000.0)
check("mo3 含 DNF -> DNF", mean_of_3(T(10000, 20000, 0, dnf=(3,))), "DNF")

print("== compute_stats ==")
solves = T(10000, 9000, 11000, 12000, 0, 8000, dnf=(5,))   # 6 次，第 5 次为 DNF
st = compute_stats(solves)
check("次数", st.count, 6)
check("有效次数", st.valid, 5)
check("DNF 次数", st.dnf_count, 1)
check("best", st.best.time_ms, 8000)
check("worst", st.worst.time_ms, 12000)
check("mean", round(st.mean, 1), 10000.0)
check("ao5(最近5次: 9,11,12,DNF,8 -> 去 8 与 DNF -> (9+11+12)/3)",
      round(st.values["ao5"], 1), 10666.7)
check("mo3(最近3次: 12,DNF,8) = DNF", st.values["mo3"], "DNF")
check("ao12 不足 -> None", st.values["ao12"], None)
check("空列表 mean", compute_stats([]).mean, None)
check("空列表 best", compute_stats([]).best, None)

print("== 持久化往返 ==")
tmp = Path("_tmp") / "roundtrip_test.json"
tmp.parent.mkdir(exist_ok=True)
save_solves(solves, tmp)
back = load_solves(tmp)
check("数量一致", len(back), len(solves))
check("内容一致", [s.to_dict() for s in back], [s.to_dict() for s in solves])
tmp.unlink()

print()
if fails:
    print(f"FAILED: {len(fails)} 项 -> {fails}")
    sys.exit(1)
print("ALL PASSED")
