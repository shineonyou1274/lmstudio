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

    def test_english_grade_cutoffs(self):
        g = generate_sample.english_grade
        self.assertEqual([g(100), g(90), g(89), g(80), g(20), g(19), g(0)], [1, 1, 2, 2, 8, 9, 9])


if __name__ == "__main__":
    unittest.main()
