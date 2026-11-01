"""학생용 한 장에 다른 학생 정보가 들어가지 않는지 확인한다.
실행:  python -m unittest discover -s grade_lab/tests -v
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import generate_sample  # noqa: E402
import student_sheet  # noqa: E402


class StudentSheetPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generate_sample.main()
        cls.full = student_sheet.compute(generate_sample.OUT_DIR)
        cls.students = cls.full["result"]["students"]

    def sheet(self, sid):
        return student_sheet.render(student_sheet.student_payload(self.full, sid))

    def test_no_other_student_ids_or_names(self):
        # 보통 학생, 학기 성적 제외 학생(S007), 시뮬레이션 제외 학생(S052)
        for sid in ("S014", "S007", "S052", "S100"):
            html = self.sheet(sid)
            me = next(s for s in self.students if s["student_id"] == sid)
            ids = set(re.findall(r"S\d{3}", html))
            self.assertLessEqual(ids, set(), f"{sid}: 학생 번호가 들어 있음 {ids}")
            names = set(re.findall(r"가상학생\d{3}", html))
            self.assertEqual(names, {me["name"]}, sid)

    def test_payload_keys_are_only_mine(self):
        p = student_sheet.student_payload(self.full, "S014")
        self.assertEqual(set(p), {"student", "series", "transcripts", "items", "sim", "rules_note", "storage_key"})
        self.assertNotIn("students", p["sim"])
        self.assertNotIn("excluded", p["sim"])
        for t in p["transcripts"]:
            self.assertNotIn("rows", t)
            self.assertNotIn("rank", t["row"] or {})  # 석차는 학생 성적표에 없다

    def test_numbers_match_teacher_side(self):
        p = student_sheet.student_payload(self.full, "S014")
        teacher_sim = self.full["sim"]["students"]["S014"]
        self.assertEqual(p["sim"]["me"]["grade"], teacher_sim["grade"])
        t = self.full["transcripts"][0]["rows"]["S014"]
        self.assertEqual(p["transcripts"][0]["row"]["grade"], t["grade"])

    def test_excluded_students_still_get_a_sheet(self):
        p = student_sheet.student_payload(self.full, "S052")
        self.assertIsNone(p["sim"]["me"])
        p = student_sheet.student_payload(self.full, "S007")
        self.assertTrue(p["transcripts"][0]["excluded"])


if __name__ == "__main__":
    unittest.main()
