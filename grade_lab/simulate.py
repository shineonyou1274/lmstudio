"""중간고사 뒤 기말 시뮬레이션. AI는 쓰지 않는다.

질문: "기말에서 몇 점을 받으면 목표 성취도/석차등급이 되나?"

- 성취도(A~E)는 내 점수만으로 정해진다 → 필요한 기말 점수를 정확히 계산한다.
- 석차등급(1~5)은 다른 학생 점수에 따라 달라진다 → 하나로 단정하지 않는다.
  다른 학생들의 기말 점수를 여러 번(runs) 모의로 만들어 보고,
  "이 점수면 목표 등급이 나온 경우가 몇 %인가"로 보여 준다.

다른 학생 기말 점수를 만드는 방법(가정)
  1학기 '중간 → 기말' 자료로 직선(기말 = a + b × 중간)을 맞추고, 그 직선에서 벗어난 정도(표준편차)만큼
  무작위로 흔든다. 시나리오마다 전체 평균을 몇 점 올리거나 내린다.
  다른 학생 수행평가는 각자 1학기 수행 비율과 같다고 둔다(1학기 자료가 없으면 전체 중앙값).
  같은 seed면 언제나 같은 결과가 나온다.
"""
from __future__ import annotations

import bisect
import math
import random
from decimal import Decimal

import naesin
from naesin import D, round_half_up, semester_total, needed_final


def change_model(data: dict, sem_prev: dict) -> dict:
    """1학기 중간→기말 직선 맞춤. 자료가 10쌍 미만이면 '변화 없음 ± 8점'으로 가정한다."""
    mid = {s["student_id"]: s["raw"] for s in data["scores"]
           if s["exam_id"] == sem_prev["midterm"] and s["status"] != "결시" and s["raw"] is not None}
    fin = {s["student_id"]: s["raw"] for s in data["scores"]
           if s["exam_id"] == sem_prev["final"] and s["status"] != "결시" and s["raw"] is not None}
    pairs = [(mid[k], fin[k]) for k in mid if k in fin]
    if len(pairs) < 10:
        return {"a": 0.0, "b": 1.0, "sd": 8.0, "n": len(pairs), "mean_change": 0.0, "fallback": True}
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    b = sum((x - mx) * (y - my) for x, y in pairs) / sxx if sxx else 1.0
    a = my - b * mx
    sd = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in pairs) / n)
    return {"a": a, "b": b, "sd": sd, "n": n, "mean_change": my - mx, "fallback": False}


def min_units_for_grade(srt: list, v_self: int, limit: int, w2: int, top: int) -> int:
    """srt: 모의 원점수(정수 단위) 전체를 정렬한 목록(나 자신의 값 v_self 포함).
    나를 뺀 다른 학생들 사이에서 석차 기여(두 배 값)가 limit 이하가 되는 가장 낮은 원점수.
    만점(top)이어도 안 되면 top+1."""
    n = len(srt)

    def f2_others(T):
        lo, hi = bisect.bisect_left(srt, T), bisect.bisect_right(srt, T)
        c_self = 2 if v_self > T else (w2 if v_self == T else 0)
        return 2 * (n - hi) + w2 * (hi - lo) - c_self

    lo, hi = 0, top + 1
    while lo < hi:  # f2_others는 T가 커질수록 줄어든다(늘지 않는다)
        T = (lo + hi) // 2
        if f2_others(T) <= limit:
            hi = T
        else:
            lo = T + 1
    return lo


def max_rank2(g: int, n: int, cumulative: list, cut_method: str) -> int:
    """석차등급 g 안에 드는 가장 큰 석차(두 배 값). naesin.grade_of_rank2와 같은 기준."""
    c = D(cumulative[g - 1])
    if cut_method == "백분율":
        return int((2 * n * c / 100).to_integral_value(rounding="ROUND_FLOOR"))
    return int(2 * round_half_up(D(n) * c / 100))


def _num_text(d) -> str:
    t = f"{D(d):f}"
    return t.rstrip("0").rstrip(".") if "." in t else t


def _quantile_needed(fs: list, q: float):
    """fs: 모의마다 필요한 기말 점수(None=만점이어도 안 됨). q 비율 이상에서 목표를 이루는 가장 낮은 점수."""
    inf = Decimal(10 ** 6)
    s = sorted(f if f is not None else inf for f in fs)
    v = s[max(0, math.ceil(q * len(s)) - 1)]
    return None if v == inf else v


def simulate(data: dict, rules: dict, sem: dict, sem_prev: dict | None) -> dict | None:
    exam_ids = {e["exam_id"] for e in data["exams"]}
    if sem["midterm"] not in exam_ids:
        return None
    sim_cfg = rules["simulation"]
    places = int(rules["total_rounding"]["places"])
    scale = 10 ** places
    cum = rules["grade_ratio"]["cumulative"]
    cut = rules["cut_method"]["value"]
    w2 = naesin.tie_weight2(rules["tie_method"]["value"])
    weights, perf_max = sem["weights"], D(sem["performance_max"])
    step = D(sim_cfg.get("score_step", 1))

    mid_rows = {s["student_id"]: s for s in data["scores"] if s["exam_id"] == sem["midterm"]}
    pop, excluded = [], []
    for st in data["students"]:
        r = mid_rows.get(st["student_id"])
        if r is None or r["status"] == "결시" or r["raw"] is None:
            excluded.append({"student_id": st["student_id"], "reason": "중간고사 결시/빈칸 → 학교 규정의 인정점 필요"})
        else:
            pop.append(st["student_id"])
    if len(pop) < 5:
        return None
    mid = {sid: D(mid_rows[sid]["raw"]) for sid in pop}
    n = len(pop)

    # 다른 학생 수행평가 가정: 1학기 수행 비율
    prev_perf = naesin.performance_map(data, sem_prev["semester"]) if sem_prev else {}
    ratios = {sid: D(p["score"]) / D(p["max_score"]) for sid, p in prev_perf.items()
              if p["status"] != "결시" and p["score"] is not None}
    rs = sorted(ratios.values())
    med_ratio = (rs[len(rs) // 2] if len(rs) % 2 else (rs[len(rs) // 2 - 1] + rs[len(rs) // 2]) / 2) if rs else D("0.9")
    others_perf = {sid: ratios.get(sid, med_ratio) * perf_max for sid in pop}

    model = change_model(data, sem_prev) if sem_prev else {"a": 0.0, "b": 1.0, "sd": 8.0, "n": 0,
                                                            "mean_change": 0.0, "fallback": True}

    # 석차등급 g 이상이 되려면: rank2 <= R[g]  ⇔  다른 학생 기여(f2) <= R[g] - 2
    limit = {g: max_rank2(g, n, cum, cut) - 2 for g in range(1, 5)}

    rng = random.Random(sim_cfg["seed"])
    runs = int(sim_cfg["runs"])
    noise = [[rng.gauss(0, model["sd"]) for _ in pop] for _ in range(runs)]
    top = 100 * scale

    # 학생별 수행평가 가정 목록
    def perf_levels(sid):
        levels = []
        if sid in ratios:
            sc = round_half_up(ratios[sid] * perf_max, 1)
            levels.append({"key": "prev", "label": f"1학기와 같은 비율 ({_num_text(sc)}/{_num_text(perf_max)})", "score": sc})
        for key, ratio in (("p100", 1), ("p90", D("0.9")), ("p80", D("0.8")), ("p70", D("0.7"))):
            sc = round_half_up(perf_max * ratio, 1)
            if not any(l["score"] == sc for l in levels):
                levels.append({"key": key, "label": f"{int(ratio * 100)}% ({_num_text(sc)}/{_num_text(perf_max)})", "score": sc})
        return levels

    levels_of = {sid: perf_levels(sid) for sid in pop}
    results = {sid: {"grade": {}, "predict": {}} for sid in pop}

    for scen in sim_cfg["scenarios"]:
        # thresholds[sid][g] = 모의마다 필요한 원점수(정수 단위 = 10^-places)
        thr = {sid: {g: [] for g in range(1, 5)} for sid in pop}
        for k in range(runs):
            units = []
            for i, sid in enumerate(pop):
                f = model["a"] + model["b"] * float(mid[sid]) + scen["shift"] + noise[k][i]
                f = min(D(100), max(D(0), round_half_up(D(f) / step) * step))
                _, t = semester_total(mid[sid], f, others_perf[sid], perf_max, weights, places)
                units.append(int(t * scale))
            srt = sorted(units)
            for i, sid in enumerate(pop):
                for g in range(1, 5):
                    thr[sid][g].append(min_units_for_grade(srt, units[i], limit[g], w2, top))

        for sid in pop:
            memo = {}
            res_g, res_p = {}, {}
            for lv in levels_of[sid]:
                def need(T):
                    key = (lv["key"], T)
                    if key not in memo:
                        memo[key] = None if T > top else needed_final(
                            mid[sid], lv["score"], perf_max, weights, places, D(T) / scale, step)
                    return memo[key]
                per_g, fs_by_g = {}, {}
                for g in range(1, 5):
                    fs = [need(T) for T in thr[sid][g]]
                    fs_by_g[g] = fs
                    per_g[g] = {
                        "p50": _quantile_needed(fs, 0.5),
                        "p80": _quantile_needed(fs, 0.8),
                        "p_at_max": sum(1 for f in fs if f is not None) / runs,
                    }
                # 기말에서 중간과 같은 점수를 받으면 몇 등급이 나오나
                counts = [0] * 5
                for k in range(runs):
                    g_hit = 5
                    for g in range(1, 5):
                        f = fs_by_g[g][k]
                        if f is not None and f <= mid[sid]:
                            g_hit = g
                            break
                    counts[g_hit - 1] += 1
                res_g[lv["key"]] = per_g
                res_p[lv["key"]] = [c / runs for c in counts]
            results[sid]["grade"][scen["key"]] = res_g
            results[sid]["predict"][scen["key"]] = res_p

    # 성취도는 다른 학생과 상관없이 정확히 계산
    cutoffs = sem["achievement"]["cutoffs"]
    for sid in pop:
        results[sid]["achievement"] = {
            lv["key"]: {L: needed_final(mid[sid], lv["score"], perf_max, weights, places, cutoffs[L], step)
                        for L in "ABCD"}
            for lv in levels_of[sid]}
        results[sid]["mid"] = mid[sid]
        results[sid]["perf_levels"] = levels_of[sid]

    return {"semester": sem["semester"], "subject": sem["subject"], "n": n,
            "midterm": sem["midterm"], "weights": weights, "performance_max": perf_max,
            "model": model, "runs": runs, "scenarios": sim_cfg["scenarios"],
            "others_perf_note": "다른 학생 수행평가는 각자 1학기 수행 비율과 같다고 가정",
            "students": results, "excluded": excluded}
