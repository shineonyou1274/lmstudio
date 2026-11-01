"""계산 검증. 실행:  python -m unittest discover -s grade_lab/tests -v

두 가지로 대조한다.
1. 손으로 계산해 둔 작은 자료(정답을 미리 알고 있음)
2. 가상 자료 전체를 파이썬 표준 statistics 모듈로 따로 계산한 값
"""
import csv
import statistics
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analysis  # noqa: E402
import generate_sample  # noqa: E402


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


class HandFixture(unittest.TestCase):
    """학생 4명, 시험 3개. 답을 손으로 계산해 둔 자료."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        write_csv(d / "students.csv", ["student_id", "class", "number", "name"],
                  [{"student_id": f"T{i}", "class": "3-1", "number": i, "name": f"t{i}"} for i in range(1, 5)])
        write_csv(d / "exams.csv", ["exam_id", "kind", "label", "date"], [
            {"exam_id": "A", "kind": "내신", "label": "중간", "date": "2026-04-01"},
            {"exam_id": "B", "kind": "내신", "label": "기말", "date": "2026-07-01"},
            {"exam_id": "C", "kind": "평가원", "label": "6월", "date": "2026-06-04"},
        ])
        f = ["student_id", "exam_id", "status", "raw", "std", "percentile", "grade"]
        rows = [
            # 중간: 80, 70, 90, 결시  → 평균 80, 중앙값 80, 모표준편차 sqrt(200/3)
            {"student_id": "T1", "exam_id": "A", "status": "응시", "raw": 80},
            {"student_id": "T2", "exam_id": "A", "status": "응시", "raw": 70},
            {"student_id": "T3", "exam_id": "A", "status": "응시", "raw": 90},
            {"student_id": "T4", "exam_id": "A", "status": "결시"},
            # 기말: 85, 70, 누락(빈칸), 60 → 평균 215/3, 중앙값 70
            {"student_id": "T1", "exam_id": "B", "status": "응시", "raw": 85},
            {"student_id": "T2", "exam_id": "B", "status": "응시", "raw": 70},
            {"student_id": "T3", "exam_id": "B", "status": "응시", "raw": ""},
            {"student_id": "T4", "exam_id": "B", "status": "응시", "raw": 60},
            # 평가원: 등급만 2, 3, 3, 1
            {"student_id": "T1", "exam_id": "C", "status": "응시", "grade": 2},
            {"student_id": "T2", "exam_id": "C", "status": "응시", "grade": 3},
            {"student_id": "T3", "exam_id": "C", "status": "응시", "grade": 3},
            {"student_id": "T4", "exam_id": "C", "status": "응시", "grade": 1},
        ]
        write_csv(d / "scores.csv", f, rows)
        self.data = analysis.load(d)
        self.result = analysis.analyze(self.data)
        self.ex = {e["exam_id"]: e for e in self.result["exams"]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_midterm_stats(self):
        a = self.ex["A"]
        self.assertEqual((a["n_total"], a["n_taken"], a["n_absent"], a["n_missing"]), (4, 3, 1, 0))
        r = a["fields"]["raw"]
        self.assertAlmostEqual(r["mean"], 80)
        self.assertAlmostEqual(r["median"], 80)
        self.assertAlmostEqual(r["sd"], (200 / 3) ** 0.5)
        self.assertEqual((r["min"], r["max"]), (70, 90))

    def test_final_with_missing(self):
        b = self.ex["B"]
        self.assertEqual((b["n_taken"], b["n_absent"], b["n_missing"]), (4, 0, 1))
        r = b["fields"]["raw"]
        self.assertEqual(r["n"], 3)
        self.assertAlmostEqual(r["mean"], 215 / 3)
        self.assertAlmostEqual(r["median"], 70)

    def test_pyeongga_has_no_raw(self):
        c = self.ex["C"]
        self.assertNotIn("raw", c["fields"])
        self.assertEqual(c["grade_dist"][1], 1)
        self.assertEqual(c["grade_dist"][2], 1)
        self.assertEqual(c["grade_dist"][3], 2)

    def test_student_changes(self):
        st = {s["student_id"]: s for s in self.result["students"]}
        t1 = {x["key"]: x for x in st["T1"]["series"]}
        self.assertEqual(t1["naesin_raw"]["changes"][0]["diff"], 5)
        self.assertEqual(t1["naesin_raw"]["changes"][0]["text"], "5점 상승")
        t3 = {x["key"]: x for x in st["T3"]["series"]}
        self.assertIsNone(t3["naesin_raw"]["changes"][0]["diff"])
        self.assertIn("누락", t3["naesin_raw"]["changes"][0]["text"])
        t4 = {x["key"]: x for x in st["T4"]["series"]}
        self.assertIn("결시", t4["naesin_raw"]["changes"][0]["text"])

    def test_grade_direction(self):
        # 등급은 숫자가 작을수록 좋다: 3 → 1 은 '2등급 상승'
        self.assertEqual(analysis.describe_change(-2, True, "grade"), "2등급 상승")
        self.assertEqual(analysis.describe_change(1, True, "grade"), "1등급 하락")

    def test_naesin_and_mock_never_mixed(self):
        for spec in analysis.SERIES:
            kinds = set(spec["kinds"])
            self.assertFalse("내신" in kinds and len(kinds) > 1, spec["key"])


class ItemFixture(unittest.TestCase):
    """전국연합 문항 3개, 학생 4명(1명 결시). 답을 손으로 계산해 둔 자료."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        write_csv(d / "students.csv", ["student_id", "class", "number", "name"],
                  [{"student_id": f"T{i}", "class": "3-1", "number": i, "name": f"t{i}"} for i in range(1, 5)])
        write_csv(d / "exams.csv", ["exam_id", "kind", "label", "date"],
                  [{"exam_id": "M", "kind": "전국연합", "label": "3월", "date": "2026-03-26"}])
        # 1번 듣기 2점 A, 2번 읽기 3점 C, 3번 읽기 2점 E  (만점 7)
        write_csv(d / "items.csv", ["exam_id", "item_no", "area", "type", "points", "band"], [
            {"exam_id": "M", "item_no": 1, "area": "듣기", "type": "듣기", "points": 2, "band": "A"},
            {"exam_id": "M", "item_no": 2, "area": "읽기", "type": "빈칸", "points": 3, "band": "C"},
            {"exam_id": "M", "item_no": 3, "area": "읽기", "type": "빈칸", "points": 2, "band": "E"},
        ])
        marks = {"T1": (1, 1, 0), "T2": (1, 0, 0), "T3": (0, 1, 1)}  # T4 결시
        write_csv(d / "responses.csv", ["student_id", "exam_id", "item_no", "correct"],
                  [{"student_id": s, "exam_id": "M", "item_no": i + 1, "correct": c}
                   for s, cs in marks.items() for i, c in enumerate(cs)])
        # T3 원점수를 일부러 틀리게(실제 합계 5인데 6) 넣어 자료 점검이 잡는지 본다.
        write_csv(d / "scores.csv", ["student_id", "exam_id", "status", "raw", "std", "percentile", "grade"], [
            {"student_id": "T1", "exam_id": "M", "status": "응시", "raw": 5, "grade": 9},
            {"student_id": "T2", "exam_id": "M", "status": "응시", "raw": 2, "grade": 9},
            {"student_id": "T3", "exam_id": "M", "status": "응시", "raw": 6, "grade": 9},
            {"student_id": "T4", "exam_id": "M", "status": "결시"},
        ])
        self.data = analysis.load(d)
        self.result = analysis.analyze(self.data)
        self.ia = self.result["items"]["M"]

    def tearDown(self):
        self.tmp.cleanup()

    def test_class_rates_and_position(self):
        rows = {r["item_no"]: r for r in self.ia["items"]}
        # 1번: 2/3 = 66.7% → B 구간, 전국 A보다 '낮음'
        self.assertAlmostEqual(rows[1]["class_rate"], 200 / 3)
        self.assertEqual(rows[1]["position"], "낮음")
        # 2번: 2/3 = 66.7% → B, 전국 C보다 '높음'
        self.assertEqual(rows[2]["position"], "높음")
        # 3번: 1/3 = 33.3% → D, 전국 E보다 '높음'
        self.assertEqual(rows[3]["position"], "높음")
        self.assertEqual(rows[1]["n"], 3)  # 결시자는 분모에 없음

    def test_type_rate(self):
        t = {r["type"]: r for r in self.ia["types"]}
        # 빈칸: 2번 맞힌 2 + 3번 맞힌 1 = 3 / 응답 6
        self.assertAlmostEqual(t["빈칸"]["rate"], 50)
        self.assertEqual(t["빈칸"]["n_items"], 2)

    def test_raw_consistency_check(self):
        self.assertEqual(self.ia["max_points"], 7)
        self.assertEqual(len(self.ia["check_problems"]), 1)
        self.assertIn("T3", self.ia["check_problems"][0])

    def test_student_area_and_wrong(self):
        st = {s["student_id"]: s for s in self.result["students"]}
        t2 = st["T2"]["items"]["M"]
        self.assertEqual(t2["area"]["듣기"], {"got": 2, "max": 2})
        self.assertEqual(t2["area"]["읽기"], {"got": 0, "max": 5})
        self.assertEqual([w["item_no"] for w in t2["wrong"]], [2, 3])
        self.assertEqual(st["T3"]["items"]["M"]["wrong_easy"], 1)  # A 문항(1번)을 틀림
        self.assertIsNone(st["T4"]["items"]["M"])  # 결시

    def test_band_boundaries(self):
        b = analysis.band_of
        self.assertEqual([b(100), b(80), b(79.9), b(60), b(40), b(20), b(19.9), b(0)],
                         ["A", "A", "B", "B", "C", "D", "E", "E"])


class SampleCrossCheck(unittest.TestCase):
    """가상 자료 전체를 statistics 모듈로 따로 계산해 대조한다."""

    @classmethod
    def setUpClass(cls):
        generate_sample.main()
        cls.dir = generate_sample.OUT_DIR
        cls.data = analysis.load(cls.dir)
        cls.result = analysis.analyze(cls.data)

    def test_every_exam_every_field(self):
        with open(self.dir / "scores.csv", encoding="utf-8-sig") as f:
            raw = list(csv.DictReader(f))
        for ex in self.result["exams"]:
            rows = [r for r in raw if r["exam_id"] == ex["exam_id"]]
            self.assertEqual(ex["n_absent"], sum(r["status"] == "결시" for r in rows))
            for field, got in ex["fields"].items():
                vals = [float(r[field]) for r in rows if r["status"] != "결시" and r[field].strip() != ""]
                self.assertEqual(got["n"], len(vals))
                self.assertAlmostEqual(got["mean"], statistics.fmean(vals))
                self.assertAlmostEqual(got["median"], statistics.median(vals))
                self.assertAlmostEqual(got["sd"], statistics.pstdev(vals))

    def test_planted_absences_and_missing(self):
        ex = {e["exam_id"]: e for e in self.result["exams"]}
        self.assertEqual(ex["N1"]["n_absent"], 1)
        self.assertEqual(ex["M06"]["n_absent"], 1)
        self.assertEqual(ex["M03"]["n_missing"], 1)
        self.assertNotIn("raw", ex["M06"]["fields"])

    def test_sample_items_consistent(self):
        for eid, ia in self.result["items"].items():
            self.assertEqual(ia["max_points"], 100, eid)
            self.assertEqual(len(ia["items"]), 45, eid)
            self.assertEqual(ia["check_problems"], [], eid)

    def test_sample_item_rates_independent(self):
        with open(self.dir / "responses.csv", encoding="utf-8-sig") as f:
            resp = list(csv.DictReader(f))
        for eid, ia in self.result["items"].items():
            for row in ia["items"]:
                marks = [int(r["correct"]) for r in resp if r["exam_id"] == eid and int(r["item_no"]) == row["item_no"]]
                self.assertAlmostEqual(row["class_rate"], 100 * statistics.fmean(marks))

    def test_generator_and_analysis_bands_agree(self):
        for rate in (0, 19.99, 20, 39.9, 40, 59.9, 60, 79.9, 80, 100):
            self.assertEqual(generate_sample.band_of(rate), analysis.band_of(rate))

    def test_english_grade_cutoffs(self):
        g = generate_sample.english_grade
        self.assertEqual([g(100), g(90), g(89), g(80), g(20), g(19), g(0)], [1, 1, 2, 2, 8, 9, 9])


if __name__ == "__main__":
    unittest.main()
