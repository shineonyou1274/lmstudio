"""고1·2 내신 학기 성적 계산 (5등급 상대평가 + 성취도 A~E). AI는 쓰지 않는다.

학교마다 다른 규칙(반영 비율, 성취도 기준, 동점자 처리, 반올림)은 코드에 박지 않고
자료 폴더의 rules.json에서 읽는다. 확인되지 않은 규칙은 화면에 '가정'으로 표시한다.

정확한 계산을 위해 점수는 Decimal(십진수)로 다룬다. 반올림은 '사사오입'(0.5는 올림)이다.
파이썬 기본 round()는 0.5를 짝수 쪽으로 보내므로 쓰지 않는다.
"""
from __future__ import annotations

import json
from copy import deepcopy
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path

LETTERS = "ABCDE"

DEFAULT_RULES = {
    "_설명": "학교·교과마다 다른 성적 규칙. 학교 학업성적관리규정을 확인한 뒤 status를 '확인됨'으로 바꾼다.",
    "grade_ratio": {
        "cumulative": [10, 34, 66, 90, 100],
        "status": "확인됨",
        "source": "5등급 상대평가 비율 10/24/32/24/10% (서울신문 2023.10.11 보도)",
    },
    "tie_method": {
        "value": "중간석차",
        "choices": {"중간석차": "동점자 석차의 가운데 값 (예: 6·7·8등 동점 → 7)",
                    "최고석차": "동점자 모두 가장 높은 석차 (예: 6·7·8등 동점 → 6)"},
        "status": "가정",
    },
    "cut_method": {
        "value": "백분율",
        "choices": {"백분율": "석차 ÷ 수강자 수 × 100 이 누적 비율 이하이면 그 등급",
                    "인원반올림": "수강자 수 × 누적 비율을 반올림한 인원 안에 들면 그 등급"},
        "status": "가정",
    },
    "total_rounding": {
        "places": 0,
        "note": "학기 합계(원점수)를 소수 몇째 자리까지 남길지. 0이면 정수로 반올림",
        "status": "가정",
    },
    "semesters": [
        {
            "semester": 1, "subject": "공통영어1", "credits": 4,
            "midterm": "N1M", "final": "N1F",
            "weights": {"midterm": 30, "final": 30, "performance": 40},
            "performance_max": 40,
            "weights_status": "가정",
            "achievement": {"mode": "고정분할", "cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60}, "status": "가정"},
        },
        {
            "semester": 2, "subject": "공통영어2", "credits": 4,
            "midterm": "N2M", "final": "N2F",
            "weights": {"midterm": 30, "final": 30, "performance": 40},
            "performance_max": 40,
            "weights_status": "가정",
            "achievement": {"mode": "고정분할", "cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60}, "status": "가정"},
        },
    ],
    "simulation": {
        "runs": 400,
        "seed": 20261101,
        "score_step": 1,
        "scenarios": [
            {"key": "base", "label": "1학기 흐름 그대로", "shift": 0},
            {"key": "hard", "label": "기말이 더 어려움 (평균 5점 낮게)", "shift": -5},
            {"key": "easy", "label": "기말이 더 쉬움 (평균 5점 높게)", "shift": 5},
        ],
    },
}


def load_rules(data_dir: Path) -> dict:
    path = Path(data_dir) / "rules.json"
    if not path.exists():
        return deepcopy(DEFAULT_RULES)
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


# ---------- 숫자 ----------

def D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def round_half_up(x, places: int = 0) -> Decimal:
    return D(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def semester_total(mid, fin, perf, perf_max, weights: dict, places: int) -> tuple[Decimal, Decimal]:
    """(반올림 전 합계, 반올림한 원점수). 지필은 100점 만점으로 본다."""
    raw = (D(mid) * D(weights["midterm"]) / 100
           + D(fin) * D(weights["final"]) / 100
           + D(perf) / D(perf_max) * D(weights["performance"]))
    return raw, round_half_up(raw, places)


def achievement(total, cutoffs: dict) -> str:
    t = D(total)
    for letter in "ABCD":
        if t >= D(cutoffs[letter]):
            return letter
    return "E"


# ---------- 석차와 석차등급 ----------
# 석차는 0.5 단위가 나올 수 있어(중간석차) 두 배 한 정수(rank2)로 다룬다.

def tie_weight2(tie_method: str) -> int:
    """동점자 한 명이 내 석차에 더하는 값의 두 배. 중간석차 1(=0.5명), 최고석차 0."""
    if tie_method == "중간석차":
        return 1
    if tie_method == "최고석차":
        return 0
    raise ValueError(f"알 수 없는 동점자 처리: {tie_method}")


def grade_of_rank2(rank2: int, n: int, cumulative: list, cut_method: str) -> int:
    """석차(두 배 값)와 수강자 수로 석차등급(1~5)을 구한다."""
    for g, cum in enumerate(cumulative, start=1):
        if cut_method == "백분율":
            ok = rank2 * 100 <= 2 * n * D(cum)          # 석차/n*100 <= 누적%
        elif cut_method == "인원반올림":
            ok = rank2 <= 2 * round_half_up(D(n) * D(cum) / 100)
        else:
            raise ValueError(f"알 수 없는 등급 경계 방식: {cut_method}")
        if ok:
            return g
    return len(cumulative)


def rank_grades(totals: dict, rules: dict) -> dict:
    """{학생: 원점수} → {학생: {"rank": 석차, "grade": 석차등급}}. 높은 점수가 1등."""
    w2 = tie_weight2(rules["tie_method"]["value"])
    cum = rules["grade_ratio"]["cumulative"]
    cut = rules["cut_method"]["value"]
    vals = list(totals.values())
    n = len(vals)
    out = {}
    for sid, t in totals.items():
        higher = sum(1 for v in vals if v > t)
        same_others = sum(1 for v in vals if v == t) - 1
        rank2 = 2 * (higher + 1) + w2 * same_others
        out[sid] = {"rank": Decimal(rank2) / 2, "grade": grade_of_rank2(rank2, n, cum, cut)}
    return out


# ---------- 학기 성적표 ----------

def _score_map(data: dict, exam_id: str) -> dict:
    return {s["student_id"]: s for s in data["scores"] if s["exam_id"] == exam_id}


def performance_map(data: dict, semester: int) -> dict:
    return {p["student_id"]: p for p in data.get("performance", []) if int(p["semester"]) == semester}


def transcript(data: dict, rules: dict, sem: dict) -> dict | None:
    """한 학기 성적표. 중간·기말·수행이 모두 있어야 만든다."""
    exam_ids = {e["exam_id"] for e in data["exams"]}
    if sem.get("final") not in exam_ids or sem.get("midterm") not in exam_ids:
        return None
    perf = performance_map(data, sem["semester"])
    if not perf:
        return None
    mid, fin = _score_map(data, sem["midterm"]), _score_map(data, sem["final"])
    places = int(rules["total_rounding"]["places"])
    totals, raws, excluded = {}, {}, []
    for st in data["students"]:
        sid = st["student_id"]
        parts = {"중간": mid.get(sid), "기말": fin.get(sid)}
        p = perf.get(sid)
        why = [k for k, s in parts.items() if s is None or s["status"] == "결시" or s["raw"] is None]
        if p is None or p["status"] == "결시" or p["score"] is None:
            why.append("수행")
        if why:
            excluded.append({"student_id": sid, "reason": "·".join(why) + " 결시/빈칸 → 학교 규정의 인정점 필요"})
            continue
        raw, total = semester_total(parts["중간"]["raw"], parts["기말"]["raw"], p["score"], p["max_score"],
                                    sem["weights"], places)
        raws[sid], totals[sid] = raw, total
    if not totals:
        return None
    ranks = rank_grades(totals, rules)
    cut = sem["achievement"]["cutoffs"]
    n = len(totals)
    ach = {sid: achievement(t, cut) for sid, t in totals.items()}
    dist = {L: round_half_up(D(100) * sum(1 for a in ach.values() if a == L) / n, 1) for L in LETTERS}
    mean = round_half_up(sum(totals.values()) / n, 1)
    grade_counts = {g: sum(1 for r in ranks.values() if r["grade"] == g) for g in range(1, 6)}
    rows = {sid: {"raw": raws[sid], "total": totals[sid], "achievement": ach[sid],
                  "rank": ranks[sid]["rank"], "grade": ranks[sid]["grade"]} for sid in totals}
    return {"semester": sem["semester"], "subject": sem["subject"], "credits": sem["credits"],
            "n": n, "mean": mean, "dist": dist, "grade_counts": grade_counts,
            "rows": rows, "excluded": excluded}


# ---------- 필요한 점수 ----------

def needed_final(mid, perf, perf_max, weights: dict, places: int, target_total,
                 step=1, max_score=100) -> Decimal | None:
    """반올림한 원점수가 target_total 이상이 되는 가장 낮은 기말 점수(step 단위).
    0점이어도 되면 0, 만점이어도 안 되면 None."""
    step, target = D(step), D(target_total)
    unit = Decimal(1).scaleb(-places)
    # 반올림해서 target 이상 ⇔ 반올림 전 합계 >= target - unit/2 (사사오입)
    need_raw = target - unit / 2
    rest = D(mid) * D(weights["midterm"]) / 100 + D(perf) / D(perf_max) * D(weights["performance"])
    wf = D(weights["final"])
    if wf == 0:
        return Decimal(0) if semester_total(mid, 0, perf, perf_max, weights, places)[1] >= target else None
    f = ((need_raw - rest) * 100 / wf / step).to_integral_value(rounding=ROUND_CEILING) * step
    f = max(Decimal(0), f)
    # 십진 계산 경계를 한 번 더 확인한다.
    while f > 0 and semester_total(mid, f - step, perf, perf_max, weights, places)[1] >= target:
        f -= step
    while f <= D(max_score) and semester_total(mid, f, perf, perf_max, weights, places)[1] < target:
        f += step
    return f if f <= D(max_score) else None
