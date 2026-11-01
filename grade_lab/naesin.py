"""고1·2 내신 학기 성적 계산 (5등급 상대평가 + 성취도 A~E). AI는 쓰지 않는다.

학교마다 다른 규칙(반영 비율, 성취도 기준, 동점자 처리, 반올림)은 코드에 박지 않고
자료 폴더의 rules.json에서 읽는다. 규칙마다 확인 상태를 적어 화면에 보여 준다.
  확인됨      학교 규정까지 확인
  교육청 지침  교육청 시행지침에서 확인(학교 규정은 아직)
  가정        아직 확인하지 못함

기본값은 광주광역시교육청 「2025학년도 고등학교 학업성적관리 시행지침」의 내용을 따른다.
정확한 계산을 위해 점수는 Decimal(십진수)로 다룬다. 반올림은 '사사오입'(0.5는 올림)이다.
파이썬 기본 round()는 0.5를 짝수 쪽으로 보내므로 쓰지 않는다.
"""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path

LETTERS = "ABCDE"
GUIDE = "광주광역시교육청 2025학년도 고등학교 학업성적관리 시행지침"
GUIDE_URL = "https://www.gen.go.kr/flexer/html/www/356/2025/20250320_151807_067017800.files/Sections1.html"

DEFAULT_RULES = {
    "_설명": "학교·교과마다 다른 성적 규칙. 학교 학업성적관리규정을 확인한 뒤 status를 '확인됨'으로 바꾼다.",
    "guide": {"title": GUIDE, "url": GUIDE_URL},
    "grade_ratio": {
        "cumulative": [10, 34, 66, 90, 100],
        "status": "교육청 지침",
        "source": "2022 개정 교육과정 학년: 누적 10/34/66/90/100%",
    },
    "cut_method": {
        "value": "지침",
        "choices": {
            "지침": "누적 인원 = 수강자 수 × 누적 비율을 반올림. 동점자가 등급 경계에 걸치면 중간석차 백분율로 등급을 줌",
            "백분율": "(동점자 처리한) 석차 ÷ 수강자 수 × 100 이 누적 비율 이하이면 그 등급",
            "인원반올림": "(동점자 처리한) 석차가 수강자 수 × 누적 비율을 반올림한 인원 안에 들면 그 등급",
        },
        "status": "교육청 지침",
        "source": "중간석차 = 석차 + (동석차 수 − 1) ÷ 2. 등급 범위 안의 동점자에게는 적용하지 않음",
    },
    "tie_method": {
        "value": "중간석차",
        "choices": {"중간석차": "동점자 석차의 가운데 값 (예: 6·7·8등 동점 → 7)",
                    "최고석차": "동점자 모두 가장 높은 석차 (예: 6·7·8등 동점 → 6)"},
        "status": "교육청 지침",
        "source": "cut_method가 '백분율'·'인원반올림'일 때만 쓰임",
    },
    "total_rounding": {
        "sum_places": 2,
        "places": 0,
        "status": "교육청 지침",
        "source": "환산 점수 합계는 소수 셋째 자리에서 반올림(둘째 자리까지), 원점수는 그 합계를 소수 첫째 자리에서 반올림해 정수",
    },
    "rank_basis": {
        "value": "원점수",
        "choices": {"원점수": "정수 원점수로 석차를 매김", "환산합계": "소수 둘째 자리 합계로 석차를 매김"},
        "status": "가정",
        "source": "석차를 어느 점수로 매기는지는 아직 확인하지 못함",
    },
    "min_level": {"value": 40, "status": "교육청 지침",
                  "source": "성취율 40% 미만은 최소 성취수준 보장지도 대상(이수 시 E)"},
    "semesters": [
        {
            "semester": 1, "subject": "공통영어1", "credits": 4,
            "midterm": "N1M", "final": "N1F",
            "weights": {"midterm": 30, "final": 30, "performance": 40},
            "performance_max": 40,
            "weights_status": "가정",
            "achievement": {"mode": "고정분할", "cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60}, "status": "교육청 지침"},
        },
        {
            "semester": 2, "subject": "공통영어2", "credits": 4,
            "midterm": "N2M", "final": "N2F",
            "weights": {"midterm": 30, "final": 30, "performance": 40},
            "performance_max": 40,
            "weights_status": "가정",
            "achievement": {"mode": "고정분할", "cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60}, "status": "교육청 지침"},
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


def semester_values(mid, fin, perf, perf_max, weights: dict, rounding: dict) -> dict:
    """반올림 전 합계(raw), 환산 점수 합계(sum, 보통 소수 둘째 자리), 원점수(total, 보통 정수).
    지필은 100점 만점으로 본다. 원점수는 '환산 합계'를 반올림한다(지침의 순서 그대로)."""
    raw = (D(mid) * D(weights["midterm"]) / 100
           + D(fin) * D(weights["final"]) / 100
           + D(perf) / D(perf_max) * D(weights["performance"]))
    s = round_half_up(raw, int(rounding.get("sum_places", 2)))
    return {"raw": raw, "sum": s, "total": round_half_up(s, int(rounding["places"]))}


def basis_key(rules: dict) -> str:
    return "sum" if rules.get("rank_basis", {}).get("value") == "환산합계" else "total"


def basis_places(rules: dict) -> int:
    r = rules["total_rounding"]
    return int(r.get("sum_places", 2)) if basis_key(rules) == "sum" else int(r["places"])


def achievement(total, cutoffs: dict) -> str:
    t = D(total)
    for letter in "ABCD":
        if t >= D(cutoffs[letter]):
            return letter
    return "E"


# ---------- 석차와 석차등급 ----------

def grade_from_position(top: int, k: int, n: int, rules: dict) -> int:
    """top: 동점자 중 가장 높은 석차(1부터), k: 나를 포함한 동점자 수, n: 수강자 수."""
    return _grade_cached(top, k, n, tuple(rules["grade_ratio"]["cumulative"]),
                         rules["cut_method"]["value"], rules["tie_method"]["value"])


@lru_cache(maxsize=200_000)
def _grade_cached(top: int, k: int, n: int, cum: tuple, method: str, tie: str) -> int:
    counts = [round_half_up(D(n) * D(c) / 100) for c in cum]

    def by_count(rank):            # rank는 Decimal(0.5 단위 가능)
        return next((g for g, c in enumerate(counts, 1) if rank <= c), len(cum))

    def by_percent(rank):
        return next((g for g, c in enumerate(cum, 1) if rank * 100 <= D(n) * D(c)), len(cum))

    mid = D(top) + D(k - 1) / 2
    if method == "지침":
        g_top, g_bottom = by_count(D(top)), by_count(D(top + k - 1))
        return g_top if g_top == g_bottom else by_percent(mid)
    if tie == "중간석차":
        rank = mid
    elif tie == "최고석차":
        rank = D(top)
    else:
        raise ValueError(f"알 수 없는 동점자 처리: {tie}")
    if method == "백분율":
        return by_percent(rank)
    if method == "인원반올림":
        return by_count(rank)
    raise ValueError(f"알 수 없는 등급 경계 방식: {method}")


def rank_grades(totals: dict, rules: dict) -> dict:
    """{학생: 점수} → {학생: {"rank": 석차, "ties": 동석차 수, "grade": 석차등급}}. 높은 점수가 1등."""
    vals = list(totals.values())
    n = len(vals)
    out = {}
    for sid, t in totals.items():
        top = sum(1 for v in vals if v > t) + 1
        k = sum(1 for v in vals if v == t)
        out[sid] = {"rank": top, "ties": k, "grade": grade_from_position(top, k, n, rules)}
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
    vals, excluded = {}, []
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
        vals[sid] = semester_values(parts["중간"]["raw"], parts["기말"]["raw"], p["score"], p["max_score"],
                                    sem["weights"], rules["total_rounding"])
    if not vals:
        return None
    bk = basis_key(rules)
    ranks = rank_grades({sid: v[bk] for sid, v in vals.items()}, rules)
    cut = sem["achievement"]["cutoffs"]
    n = len(vals)
    ach = {sid: achievement(v["total"], cut) for sid, v in vals.items()}
    dist = {L: round_half_up(D(100) * sum(1 for a in ach.values() if a == L) / n, 1) for L in LETTERS}
    mean = round_half_up(sum(v["total"] for v in vals.values()) / n, 1)  # 과목평균은 원점수로
    grade_counts = {g: sum(1 for r in ranks.values() if r["grade"] == g) for g in range(1, 6)}
    min_level = D(rules.get("min_level", {}).get("value", 0))
    rows = {sid: {"raw": v["raw"], "sum": v["sum"], "total": v["total"], "achievement": ach[sid],
                  "below_min": v["total"] < min_level,
                  "rank": ranks[sid]["rank"], "ties": ranks[sid]["ties"], "grade": ranks[sid]["grade"]}
            for sid, v in vals.items()}
    return {"semester": sem["semester"], "subject": sem["subject"], "credits": sem["credits"],
            "n": n, "mean": mean, "dist": dist, "grade_counts": grade_counts,
            "rows": rows, "excluded": excluded}


# ---------- 필요한 점수 ----------

def needed_final(mid, perf, perf_max, weights: dict, rounding: dict, target,
                 step=1, max_score=100, key: str = "total") -> Decimal | None:
    """semester_values(...)[key]가 target 이상이 되는 가장 낮은 기말 점수(step 단위).
    0점이어도 되면 0, 만점이어도 안 되면 None."""
    step, target = D(step), D(target)

    def ok(f):
        return semester_values(mid, f, perf, perf_max, weights, rounding)[key] >= target

    wf = D(weights["final"])
    if wf == 0:
        return Decimal(0) if ok(0) else None
    # 대략 위치를 계산한 뒤, 앞뒤로 한 칸씩 확인해 정확히 맞춘다(합계는 기말 점수가 오르면 줄지 않음).
    rest = D(mid) * D(weights["midterm"]) / 100 + D(perf) / D(perf_max) * D(weights["performance"])
    f = ((target - 1 - rest) * 100 / wf / step).to_integral_value(rounding=ROUND_CEILING) * step
    f = min(D(max_score), max(Decimal(0), f))
    while f > 0 and ok(f - step):
        f -= step
    while f <= D(max_score) and not ok(f):
        f += step
    return f if f <= D(max_score) else None
