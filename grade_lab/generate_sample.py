"""가상 성적 자료를 만든다. 실제 학생 정보는 하나도 들어가지 않는다.

실행:  python grade_lab/generate_sample.py
결과:  grade_lab/data/sample/ 아래 CSV와 rules.json (엑셀에서 한글이 깨지지 않도록 UTF-8 BOM)

가상 상황: 고1 영어(1학기 공통영어1, 2학기 공통영어2), 4개 반 100명.
오늘은 2학기 중간고사가 끝난 뒤다. 2학기 기말과 2학기 수행평가는 아직 없다.

같은 seed면 언제나 같은 자료가 나온다(검증을 다시 할 수 있게).
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

SEED = 20261101
CLASSES = ["1-1", "1-2", "1-3", "1-4"]
PER_CLASS = 25
OUT_DIR = Path(__file__).parent / "data" / "sample"

# 고1 영어 기준 가상 시험 일정. kind: 내신 / 전국연합(교육청) / 평가원(고3만, 여기엔 없음)
EXAMS = [
    ("M03", "전국연합", "3월 전국연합", "2026-03-26"),
    ("N1M", "내신", "1학기 중간고사", "2026-04-28"),
    ("M06", "전국연합", "6월 전국연합", "2026-06-04"),
    ("N1F", "내신", "1학기 기말고사", "2026-07-03"),
    ("M09", "전국연합", "9월 전국연합", "2026-09-03"),
    ("N2M", "내신", "2학기 중간고사", "2026-10-14"),
]
PERF_MAX = 40  # 수행평가 만점(가상). 반영 비율 40%와 같게 둔다.

# 영어 절대평가 등급 기준(원점수 90점 이상 1등급, 이후 10점 간격).
ENGLISH_CUTS = [90, 80, 70, 60, 50, 40, 30, 20]


def english_grade(raw: int) -> int:
    for i, cut in enumerate(ENGLISH_CUTS):
        if raw >= cut:
            return i + 1
    return 9


def clip(x: float) -> int:
    return max(0, min(100, round(x)))


# 전국연합 영어 45문항 (가상 배치). 1~17 듣기, 18~45 읽기.
# 유형 이름은 흔히 쓰는 배치를 따른 가상 값이다. 실제 회차는 정오표 기준으로 바꾼다.
READING_TYPES = {
    18: "목적", 19: "심경", 20: "주장", 21: "함축 의미", 22: "요지", 23: "주제", 24: "제목",
    25: "도표", 26: "내용 일치", 27: "안내문", 28: "안내문", 29: "어법", 30: "어휘",
    31: "빈칸", 32: "빈칸", 33: "빈칸", 34: "빈칸", 35: "무관한 문장", 36: "순서", 37: "순서",
    38: "삽입", 39: "삽입", 40: "요약", 41: "장문", 42: "장문", 43: "장문", 44: "장문", 45: "장문",
}
THREE_POINT = {12, 16, 21, 29, 32, 33, 34, 37, 39, 42}  # 3점 10문항 + 2점 35문항 = 100점


def band_of(rate: float) -> str:
    """전국 정답률(%) → A~E. A가 가장 쉬움(80~100). 하한 포함으로 가정."""
    for cut, b in ((80, "A"), (60, "B"), (40, "C"), (20, "D")):
        if rate >= cut:
            return b
    return "E"


def make_items(rng: random.Random, exam_id: str) -> list[dict]:
    items = []
    for no in range(1, 46):
        listening = no <= 17
        # 문항 난이도(전국 정답률). 빈칸·순서·삽입 등은 대체로 어렵게.
        base = 82 if listening else 68
        if READING_TYPES.get(no) in {"빈칸", "순서", "삽입", "함축 의미", "어법"}:
            base -= 25
        if no in THREE_POINT:
            base -= 8
        national = max(5.0, min(97.0, rng.gauss(base, 9)))
        items.append({
            "exam_id": exam_id, "item_no": no,
            "area": "듣기" if listening else "읽기",
            "type": "듣기" if listening else READING_TYPES[no],
            "points": 3 if no in THREE_POINT else 2,
            "band": band_of(national),
            "_national": national,
        })
    return items


def main() -> None:
    rng = random.Random(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    students = []
    for ci, cls in enumerate(CLASSES):
        for no in range(1, PER_CLASS + 1):
            i = ci * PER_CLASS + no
            students.append({"student_id": f"S{i:03d}", "class": cls, "number": no, "name": f"가상학생{i:03d}"})

    # 일부러 넣는 결시와 누락(검증용).
    absent = {("S007", "N1M"), ("S019", "M06"), ("S023", "M09"), ("S052", "N2M")}
    missing = {("S011", "M03", "grade")}  # 응시했지만 등급 칸이 비어 있는 경우
    absent_perf = {("S088", 1)}

    items_by_exam = {e[0]: make_items(rng, e[0]) for e in EXAMS if e[1] == "전국연합"}
    responses = []

    scores = []
    performance = []
    for s in students:
        ability = rng.gauss(66, 14)
        drift = rng.gauss(0, 4)  # 학기 중 조금씩 오르거나 내리는 경향
        if (s["student_id"], 1) in absent_perf:
            performance.append({"student_id": s["student_id"], "semester": 1, "status": "결시",
                                "score": "", "max_score": PERF_MAX})
        else:
            ratio = max(0.4, min(1.0, 0.82 + (ability - 66) / 250 + rng.gauss(0, 0.06)))
            performance.append({"student_id": s["student_id"], "semester": 1, "status": "응시",
                                "score": round(PERF_MAX * ratio), "max_score": PERF_MAX})
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
                # 내신은 학교 시험이라 점수가 더 넓게 퍼지도록 만든다.
                row["raw"] = clip(66 + (latent - 66) * 1.25 + rng.gauss(0, 4))
            elif kind == "전국연합":
                # 문항마다 맞힘/틀림을 정하고, 원점수는 맞힌 문항 배점의 합으로 만든다.
                raw = 0
                for it in items_by_exam[exam_id]:
                    p = it["_national"] / 100 + (latent - 66) / 100
                    ok = 1 if rng.random() < max(0.02, min(0.99, p)) else 0
                    raw += it["points"] * ok
                    responses.append({"student_id": s["student_id"], "exam_id": exam_id,
                                      "item_no": it["item_no"], "correct": ok})
                row["raw"] = raw
                row["grade"] = english_grade(raw)
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
    write(
        "items.csv",
        [{k: v for k, v in it.items() if not k.startswith("_")} for its in items_by_exam.values() for it in its],
        ["exam_id", "item_no", "area", "type", "points", "band"],
    )
    write("responses.csv", responses, ["student_id", "exam_id", "item_no", "correct"])
    write("performance.csv", performance, ["student_id", "semester", "status", "score", "max_score"])
    import naesin  # 같은 폴더
    with open(OUT_DIR / "rules.json", "w", encoding="utf-8") as f:
        json.dump(naesin.DEFAULT_RULES, f, ensure_ascii=False, indent=2)
    print(f"가상 자료를 만들었습니다: {OUT_DIR}")


if __name__ == "__main__":
    main()
