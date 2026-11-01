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
    return {"students": students, "exams": exams, "scores": scores}


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


def analyze(data: dict) -> dict:
    return {
        "exams": [exam_summary(e, data["scores"]) for e in data["exams"]],
        "students": [
            {**s, "series": student_series(s["student_id"], data)} for s in data["students"]
        ],
    }
