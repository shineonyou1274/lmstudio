"""가상 성적 자료를 만든다. 실제 학생 정보는 하나도 들어가지 않는다.

실행:  python grade_lab/generate_sample.py
결과:  grade_lab/data/sample/ 아래 CSV 3개 (엑셀에서 한글이 깨지지 않도록 UTF-8 BOM)

같은 seed면 언제나 같은 자료가 나온다(검증을 다시 할 수 있게).
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 20261101
N_STUDENTS = 30
OUT_DIR = Path(__file__).parent / "data" / "sample"

# 고3 영어 기준 가상 시험 일정.
# kind: 내신 / 전국연합(교육청) / 평가원
EXAMS = [
    ("M03", "전국연합", "3월 전국연합", "2026-03-26"),
    ("N1", "내신", "1학기 중간고사", "2026-04-28"),
    ("M06", "평가원", "6월 모의평가", "2026-06-04"),
    ("N2", "내신", "1학기 기말고사", "2026-07-03"),
    ("M07", "전국연합", "7월 전국연합", "2026-07-09"),
]

# 영어 절대평가 등급 기준(원점수 90점 이상 1등급, 이후 10점 간격).
ENGLISH_CUTS = [90, 80, 70, 60, 50, 40, 30, 20]


def english_grade(raw: int) -> int:
    for i, cut in enumerate(ENGLISH_CUTS):
        if raw >= cut:
            return i + 1
    return 9


def clip(x: float) -> int:
    return max(0, min(100, round(x)))


def main() -> None:
    rng = random.Random(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    students = [
        {"student_id": f"S{i:02d}", "class": "3-1", "number": i, "name": f"가상학생{i:02d}"}
        for i in range(1, N_STUDENTS + 1)
    ]

    # 일부러 넣는 결시와 누락(검증용).
    absent = {("S07", "N1"), ("S19", "M06"), ("S23", "M07"), ("S23", "N2")}
    missing = {("S11", "M03", "grade")}  # 응시했지만 등급 칸이 비어 있는 경우

    scores = []
    for s in students:
        ability = rng.gauss(66, 14)
        drift = rng.gauss(0, 4)  # 학기 중 조금씩 오르거나 내리는 경향
        for idx, (exam_id, kind, _label, _date) in enumerate(EXAMS):
            row = {
                "student_id": s["student_id"], "exam_id": exam_id, "status": "응시",
                "raw": "", "std": "", "percentile": "", "grade": "",
            }
            if (s["student_id"], exam_id) in absent:
                row["status"] = "결시"
                scores.append(row)
                continue
            latent = clip(ability + drift * idx / 2 + rng.gauss(0, 6))
            if kind == "내신":
                row["raw"] = latent
            elif kind == "전국연합":
                row["raw"] = latent
                row["grade"] = english_grade(latent)
            elif kind == "평가원":
                # 평가원 영어는 원점수를 주지 않는다. 등급만 기록한다.
                row["grade"] = english_grade(latent)
            for (sid, eid, field) in missing:
                if sid == s["student_id"] and eid == exam_id:
                    row[field] = ""
            scores.append(row)

    def write(name: str, rows: list[dict], fields: list[str]) -> None:
        with open(OUT_DIR / name, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write("students.csv", students, ["student_id", "class", "number", "name"])
    write(
        "exams.csv",
        [{"exam_id": e, "kind": k, "label": l, "date": d} for e, k, l, d in EXAMS],
        ["exam_id", "kind", "label", "date"],
    )
    write("scores.csv", scores, ["student_id", "exam_id", "status", "raw", "std", "percentile", "grade"])
    print(f"가상 자료를 만들었습니다: {OUT_DIR}")


if __name__ == "__main__":
    main()
