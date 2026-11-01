"""성적 계산. AI는 쓰지 않는다. 모든 계산은 이 파일 안에서 끝난다.

원칙
- 내신과 모의고사는 섞지 않는다(합산·평균하지 않는다).
- 결시는 통계에서 빼고 따로 센다. 응시했는데 필요한 칸이 비면 '누락'으로 따로 센다.
- 비교는 같은 항목끼리만 한다. 값이 없으면 '비교 불가'와 그 이유를 남긴다.
- 표준편차는 모집단 표준편차(n으로 나눔)를 쓴다.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

# 시험 종류별로 '응시했다면 반드시 있어야 하는 칸'
REQUIRED = {
    "내신": ["raw"],
    "전국연합": ["raw", "grade"],
    "평가원": ["grade"],
}
NUMERIC_FIELDS = ["raw", "std", "percentile", "grade"]
FIELD_LABEL = {"raw": "원점수", "std": "표준점수", "percentile": "백분위", "grade": "등급"}


# ---------- 읽기 ----------

def _read(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _num(v: str):
    v = (v or "").strip()
    if v == "":
        return None
    return float(v) if "." in v else int(v)


def load(data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    students = _read(data_dir / "students.csv")
    exams = _read(data_dir / "exams.csv")
    scores = _read(data_dir / "scores.csv")
    for s in scores:
        for f in NUMERIC_FIELDS:
            s[f] = _num(s.get(f, ""))
        s["status"] = (s.get("status") or "").strip()
    exams.sort(key=lambda e: e["date"])
    items, responses = [], []
    if (data_dir / "items.csv").exists() and (data_dir / "responses.csv").exists():
        items = _read(data_dir / "items.csv")
        for it in items:
            it["item_no"] = int(it["item_no"])
            it["points"] = int(it["points"])
            it["band"] = it["band"].strip().upper()
        responses = _read(data_dir / "responses.csv")
        for r in responses:
            r["item_no"] = int(r["item_no"])
            r["correct"] = int(r["correct"])
    performance = []
    if (data_dir / "performance.csv").exists():
        performance = _read(data_dir / "performance.csv")
        for p in performance:
            p["status"] = (p.get("status") or "").strip()
            p["score"] = _num(p.get("score", ""))
            p["max_score"] = _num(p.get("max_score", ""))
    return {"students": students, "exams": exams, "scores": scores, "items": items, "responses": responses,
            "performance": performance}


# ---------- 기본 통계 (직접 구현; 테스트에서 statistics 모듈과 대조) ----------

def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def pstdev(xs):
    if not xs:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


# ---------- 상태 판정 ----------

def classify(score: dict, kind: str) -> str:
    """'응시' / '결시' / '누락' 중 하나."""
    if score["status"] == "결시":
        return "결시"
    if any(score.get(f) is None for f in REQUIRED.get(kind, [])):
        return "누락"
    return "응시"


# ---------- 시험별 요약 ----------

def exam_summary(exam: dict, scores: list[dict]) -> dict:
    rows = [s for s in scores if s["exam_id"] == exam["exam_id"]]
    states = [classify(s, exam["kind"]) for s in rows]
    out = {
        "exam_id": exam["exam_id"], "kind": exam["kind"], "label": exam["label"], "date": exam["date"],
        "n_total": len(rows),
        "n_taken": states.count("응시") + states.count("누락"),
        "n_absent": states.count("결시"),
        "n_missing": states.count("누락"),
        "fields": {},
        "grade_dist": None,
    }
    for f in NUMERIC_FIELDS:
        vals = [s[f] for s, st in zip(rows, states) if st != "결시" and s[f] is not None]
        if not vals:
            continue  # 이 시험에서 제공되지 않는 항목(예: 평가원 영어 원점수)
        out["fields"][f] = {
            "n": len(vals), "mean": mean(vals), "median": median(vals),
            "sd": pstdev(vals), "min": min(vals), "max": max(vals),
        }
    if "grade" in out["fields"]:
        dist = {g: 0 for g in range(1, 10)}
        for s, st in zip(rows, states):
            if st != "결시" and s["grade"] is not None:
                dist[int(s["grade"])] += 1
        out["grade_dist"] = dist
    return out


# ---------- 학생별 변화 ----------

# 비교 묶음: 같은 항목이 있는 시험끼리만 잇는다.
SERIES = [
    {"key": "naesin_raw", "title": "내신 원점수", "kinds": ["내신"], "field": "raw", "lower_is_better": False},
    {"key": "jeonguk_raw", "title": "전국연합 원점수", "kinds": ["전국연합"], "field": "raw", "lower_is_better": False},
    {"key": "mock_grade", "title": "모의고사 등급 (전국연합·평가원)", "kinds": ["전국연합", "평가원"], "field": "grade", "lower_is_better": True},
]


def student_series(student_id: str, data: dict) -> list[dict]:
    by_exam = {s["exam_id"]: s for s in data["scores"] if s["student_id"] == student_id}
    result = []
    for spec in SERIES:
        points = []
        for e in data["exams"]:
            if e["kind"] not in spec["kinds"]:
                continue
            s = by_exam.get(e["exam_id"])
            if s is None:
                points.append({"exam_id": e["exam_id"], "label": e["label"], "value": None, "note": "자료 없음"})
                continue
            st = classify(s, e["kind"])
            v = s.get(spec["field"]) if st != "결시" else None
            note = "결시" if st == "결시" else ("누락" if v is None else "")
            points.append({"exam_id": e["exam_id"], "label": e["label"], "value": v, "note": note})
        changes = []
        for a, b in zip(points, points[1:]):
            if a["value"] is None or b["value"] is None:
                why = a["note"] or b["note"] or "값 없음"
                changes.append({"from": a["label"], "to": b["label"], "diff": None, "text": f"비교 불가({why})"})
                continue
            diff = b["value"] - a["value"]
            changes.append({"from": a["label"], "to": b["label"], "diff": diff,
                            "text": describe_change(diff, spec["lower_is_better"], spec["field"])})
        result.append({**spec, "points": points, "changes": changes})
    return result


def describe_change(diff, lower_is_better: bool, field: str) -> str:
    if diff == 0:
        return "변화 없음"
    unit = "등급" if field == "grade" else "점"
    better = diff < 0 if lower_is_better else diff > 0
    return f"{abs(diff):g}{unit} {'상승' if better else '하락'}"


# ---------- 전국연합 문항 분석 ----------

# 전국 정답률 구간. A가 가장 쉬움. 하한 포함(예: 80%는 A)으로 가정.
BAND_RANGE = {"A": (80, 100), "B": (60, 80), "C": (40, 60), "D": (20, 40), "E": (0, 20)}
BAND_ORDER = "ABCDE"


def band_of(rate: float) -> str:
    for b in "ABCD":
        if rate >= BAND_RANGE[b][0]:
            return b
    return "E"


def compare_to_band(class_rate: float, national_band: str) -> str:
    """우리 반 정답률이 전국 구간보다 '높음' / '범위 안' / '낮음'."""
    diff = BAND_ORDER.index(national_band) - BAND_ORDER.index(band_of(class_rate))
    return "높음" if diff > 0 else ("낮음" if diff < 0 else "범위 안")


def item_analysis(exam_id: str, data: dict) -> dict | None:
    items = sorted((i for i in data["items"] if i["exam_id"] == exam_id), key=lambda i: i["item_no"])
    if not items:
        return None
    resp = [r for r in data["responses"] if r["exam_id"] == exam_id]
    by_item: dict[int, list[int]] = {}
    for r in resp:
        by_item.setdefault(r["item_no"], []).append(r["correct"])

    rows = []
    for it in items:
        marks = by_item.get(it["item_no"], [])
        rate = 100 * sum(marks) / len(marks) if marks else None
        rows.append({
            "item_no": it["item_no"], "area": it["area"], "type": it["type"], "points": it["points"],
            "band": it["band"], "band_range": BAND_RANGE[it["band"]],
            "n": len(marks), "n_correct": sum(marks), "class_rate": rate,
            "position": compare_to_band(rate, it["band"]) if rate is not None else "응답 없음",
        })

    # 유형별 정답률(문항을 묶어 맞힌 수 / 응답 수)
    types: dict[str, list[int]] = {}
    order: list[str] = []
    for row in rows:
        if row["type"] not in types:
            types[row["type"]] = [0, 0]
            order.append(row["type"])
        types[row["type"]][0] += row["n_correct"]
        types[row["type"]][1] += row["n"]
    type_rows = [{"type": t, "n_items": sum(1 for r in rows if r["type"] == t),
                  "rate": 100 * types[t][0] / types[t][1] if types[t][1] else None} for t in order]

    # 자료 점검: 원점수 = 맞힌 문항 배점의 합 인가?
    points = {it["item_no"]: it["points"] for it in items}
    per_student: dict[str, list[dict]] = {}
    for r in resp:
        per_student.setdefault(r["student_id"], []).append(r)
    raw_of = {s["student_id"]: s["raw"] for s in data["scores"] if s["exam_id"] == exam_id}
    problems = []
    for sid, rs in per_student.items():
        total = sum(points[r["item_no"]] * r["correct"] for r in rs)
        if len(rs) != len(items):
            problems.append(f"{sid}: 응답 {len(rs)}개 (문항 {len(items)}개)")
        if raw_of.get(sid) is not None and raw_of[sid] != total:
            problems.append(f"{sid}: 원점수 {raw_of[sid]} ≠ 문항 합계 {total}")

    return {"exam_id": exam_id, "items": rows, "types": type_rows,
            "max_points": sum(points.values()), "check_problems": problems}


def student_items(student_id: str, exam_id: str, data: dict) -> dict | None:
    items = {i["item_no"]: i for i in data["items"] if i["exam_id"] == exam_id}
    rs = [r for r in data["responses"] if r["exam_id"] == exam_id and r["student_id"] == student_id]
    if not items or not rs:
        return None
    area = {}
    for a in ("듣기", "읽기"):
        nos = [n for n, i in items.items() if i["area"] == a]
        got = sum(items[r["item_no"]]["points"] for r in rs if r["correct"] and r["item_no"] in nos)
        area[a] = {"got": got, "max": sum(items[n]["points"] for n in nos)}
    wrong = sorted((r["item_no"] for r in rs if not r["correct"]))
    wrong_rows = [{"item_no": n, "type": items[n]["type"], "points": items[n]["points"], "band": items[n]["band"]}
                  for n in wrong]
    return {"exam_id": exam_id, "area": area, "wrong": wrong_rows,
            "wrong_easy": sum(1 for w in wrong_rows if w["band"] in ("A", "B"))}


def analyze(data: dict) -> dict:
    item_exams = [e["exam_id"] for e in data["exams"] if any(i["exam_id"] == e["exam_id"] for i in data["items"])]
    return {
        "exams": [exam_summary(e, data["scores"]) for e in data["exams"]],
        "items": {eid: item_analysis(eid, data) for eid in item_exams},
        "students": [
            {**s, "series": student_series(s["student_id"], data),
             "items": {eid: student_items(s["student_id"], eid, data) for eid in item_exams}}
            for s in data["students"]
        ],
    }
