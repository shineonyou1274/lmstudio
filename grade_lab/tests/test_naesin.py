"""학기 성적(5등급)과 기말 시뮬레이션 검증. 실행:  python -m unittest discover -s grade_lab/tests -v

1. 손으로 계산해 둔 작은 자료
2. 빠른 계산(시뮬레이션 안의 지름길)을 느리지만 확실한 방법(하나씩 다 해 보기)과 대조
"""
import random
import sys
import unittest
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analysis  # noqa: E402
import generate_sample  # noqa: E402
import naesin  # noqa: E402
import simulate  # noqa: E402
from naesin import D  # noqa: E402

W = {"midterm": 30, "final": 30, "performance": 40}


RND = {"sum_places": 2, "places": 0}


def rules_with(tie="중간석차", cut="지침", places=0):
    r = deepcopy(naesin.DEFAULT_RULES)
    r["tie_method"]["value"] = tie
    r["cut_method"]["value"] = cut
    r["total_rounding"]["places"] = places
    return r


def total(mid, fin, perf, w=W, rnd=RND, perf_max=40):
    return naesin.semester_values(mid, fin, perf, perf_max, w, rnd)["total"]


class Basics(unittest.TestCase):
    def test_round_half_up(self):
        r = naesin.round_half_up
        self.assertEqual([r("2.5"), r("3.5"), r("89.49"), r("89.5")], [3, 4, 89, 90])
        self.assertEqual(r("84.45", 1), Decimal("84.5"))  # 파이썬 round()라면 84.4가 될 수 있음

    def test_semester_total(self):
        # 중간 80×0.3=24, 기말 90×0.3=27, 수행 36/40×40=36 → 87
        v = naesin.semester_values(80, 90, 36, 40, W, RND)
        self.assertEqual((v["raw"], v["sum"], v["total"]), (87, 87, 87))
        # 중간 77×0.3=23.1, 기말 81×0.3=24.3, 수행 33/40×40=33 → 80.4 → 80
        self.assertEqual(total(77, 81, 33), 80)

    def test_guide_rounding_order(self):
        # 지침: 합계를 먼저 소수 둘째 자리로(셋째 자리에서 반올림), 그다음 정수로.
        # 수행 33.98/40×40 = 33.98, 중간 85 → 25.5, 기말 100 → 30 : 89.48 → 89
        self.assertEqual(total(85, 100, "33.98"), 89)
        # 89.495 → 89.50 → 90 (한 번에 정수로 반올림하면 89)
        w = {"midterm": 0, "final": 0, "performance": 100}
        v = naesin.semester_values(0, 0, "89.495", 100, w, RND)
        self.assertEqual((v["sum"], v["total"]), (Decimal("89.50"), 90))
        self.assertEqual(naesin.round_half_up("89.495"), 89)

    def test_achievement_fixed_and_custom(self):
        fixed = {"A": 90, "B": 80, "C": 70, "D": 60}
        a = naesin.achievement
        self.assertEqual([a(100, fixed), a(90, fixed), a(89, fixed), a(60, fixed), a(59, fixed)],
                         ["A", "A", "B", "D", "E"])
        varied = {"A": "87.5", "B": 76, "C": 64, "D": 51}  # 변동분할처럼 학교가 정한 기준
        self.assertEqual([a(88, varied), a(87, varied), a(50, varied)], ["A", "B", "E"])


class RankFixture(unittest.TestCase):
    """10명. 누적 비율 10/34/66/90/100 → 누적 인원(반올림) 1, 3, 7, 9, 10명."""
    totals = {"a": 100, "b": 95, "c": 95, "d": 90, "e": 85, "f": 80, "g": 80, "h": 80, "i": 70, "j": 60}

    def grades(self, **kw):
        r = naesin.rank_grades({k: D(v) for k, v in self.totals.items()}, rules_with(**kw))
        return {k: (v["rank"], v["ties"], v["grade"]) for k, v in r.items()}

    def test_guide_rule(self):
        g = self.grades()
        self.assertEqual(g["a"], (1, 1, 1))
        self.assertEqual(g["b"], (2, 2, 2))  # 2·3등 동점: 둘 다 2등급 범위(≤3명) 안 → 그대로 2등급
        self.assertEqual(g["d"], (4, 1, 3))
        # 6·7·8등 동점: 6·7등은 3등급(≤7명), 8등은 4등급 → 경계에 걸침
        # → 중간석차 7, 7/10 = 70% > 66% → 모두 4등급
        self.assertEqual(g["f"], (6, 3, 4))
        self.assertEqual(g["i"], (9, 1, 4))
        self.assertEqual(g["j"], (10, 1, 5))

    def test_guide_examples(self):
        # 지침 예시 1: 수강자 96명, 1등 동점자 19명 → 중간석차 10, 10.42% → 19명 모두 2등급
        tot = {f"t{i}": D(100) for i in range(19)} | {f"o{i}": D(90 - i % 50) for i in range(77)}
        r = naesin.rank_grades(tot, rules_with())
        self.assertEqual({r[f"t{i}"]["grade"] for i in range(19)}, {2})
        # 지침 예시 2: 수강자 120명, 1등 1명·2등 동점자 15명 → 중간석차 9, 7.5% → 16명 모두 1등급
        tot = {"top": D(100)} | {f"t{i}": D(99) for i in range(15)} | {f"o{i}": D(50 + i % 40) for i in range(104)}
        r = naesin.rank_grades(tot, rules_with())
        self.assertEqual(sum(1 for v in r.values() if v["grade"] == 1), 16)

    def test_rule_choice_changes_result(self):
        # 같은 점수라도 규칙에 따라 등급이 바뀐다 → 학교 규정 확인이 꼭 필요한 이유
        self.assertEqual(self.grades(cut="인원반올림")["f"][2], 3)               # 중간석차 7 ≤ 7명
        self.assertEqual(self.grades(cut="백분율", tie="최고석차")["f"][2], 3)    # 6/10 = 60% ≤ 66%
        self.assertEqual(self.grades(cut="백분율")["f"][2], 4)                   # 7/10 = 70%

    def test_count_vs_percent_without_ties(self):
        # 98명이면 1등급 누적 인원 = 9.8 → 10명. 10등은 지침으로 1등급, 단순 백분율(10.2%)로는 2등급
        tot = {f"s{i}": D(200 - i) for i in range(98)}
        self.assertEqual(naesin.rank_grades(tot, rules_with())["s9"]["grade"], 1)
        self.assertEqual(naesin.rank_grades(tot, rules_with(cut="백분율"))["s9"]["grade"], 2)

    def test_transcript_hand(self):
        data = {
            "students": [{"student_id": k} for k in "pqrs"],
            "exams": [{"exam_id": "M"}, {"exam_id": "F"}],
            "scores": [
                {"student_id": "p", "exam_id": "M", "status": "응시", "raw": 80},
                {"student_id": "p", "exam_id": "F", "status": "응시", "raw": 90},
                {"student_id": "q", "exam_id": "M", "status": "응시", "raw": 60},
                {"student_id": "q", "exam_id": "F", "status": "응시", "raw": 70},
                {"student_id": "r", "exam_id": "M", "status": "결시", "raw": None},
                {"student_id": "r", "exam_id": "F", "status": "응시", "raw": 99},
                {"student_id": "s", "exam_id": "M", "status": "응시", "raw": 100},
                {"student_id": "s", "exam_id": "F", "status": "응시", "raw": 100},
            ],
            "performance": [{"student_id": k, "semester": 1, "status": "응시", "score": sc, "max_score": 40}
                            for k, sc in (("p", 36), ("q", 30), ("r", 40), ("s", 40))],
        }
        sem = {"semester": 1, "subject": "x", "credits": 4, "midterm": "M", "final": "F",
               "weights": W, "achievement": {"cutoffs": {"A": 90, "B": 80, "C": 70, "D": 60}}}
        t = naesin.transcript(data, rules_with(), sem)
        self.assertFalse(t["rows"]["q"]["below_min"])
        # p: 24+27+36=87(B), q: 18+21+30=69(D), s: 100(A). r는 중간 결시로 제외
        self.assertEqual(t["n"], 3)
        self.assertEqual([t["rows"][k]["total"] for k in "pqs"], [87, 69, 100])
        self.assertEqual([t["rows"][k]["achievement"] for k in "pqs"], ["B", "D", "A"])
        self.assertEqual(t["mean"], Decimal("85.3"))   # 256/3 = 85.33…
        self.assertEqual(t["dist"]["A"], Decimal("33.3"))
        self.assertEqual(t["excluded"][0]["student_id"], "r")


class NeededFinal(unittest.TestCase):
    def test_hand(self):
        # 중간 80, 수행 36/40: 합계 = 60 + 0.3×기말. 반올림해 90 이상 → 89.5 이상 → 기말 98.33… → 99
        self.assertEqual(naesin.needed_final(80, 36, 40, W, RND, 90), 99)
        self.assertIsNone(naesin.needed_final(50, 20, 40, W, RND, 90))     # 만점이어도 안 됨
        self.assertEqual(naesin.needed_final(100, 40, 40, W, RND, 60), 0)  # 0점이어도 됨

    def test_against_brute_force(self):
        rng = random.Random(7)
        for _ in range(400):
            mid, perf, target = rng.randint(0, 100), rng.randint(0, 40), rng.randint(40, 100)
            rnd = rng.choice([RND, {"sum_places": 2, "places": 1}, {"sum_places": 1, "places": 0}])
            key = rng.choice(["total", "sum"])
            w = rng.choice([W, {"midterm": 35, "final": 35, "performance": 30},
                            {"midterm": 25, "final": 40, "performance": 35}])
            brute = next((f for f in range(101)
                          if naesin.semester_values(mid, f, perf, 40, w, rnd)[key] >= target), None)
            got = naesin.needed_final(mid, perf, 40, w, rnd, target, key=key)
            self.assertEqual(got, None if brute is None else brute, (mid, perf, target, rnd, w, key))


class ThresholdShortcut(unittest.TestCase):
    """시뮬레이션의 빠른 경계 계산(이분 탐색)이, 내 점수를 0점부터 하나씩 넣고
    석차를 다 매겨 보는 방법과 같은지. 동점이 많이 생기도록 좁은 점수 범위를 쓴다."""

    def test_against_full_ranking(self):
        rng = random.Random(11)
        for trial in range(200):
            tie, cut = rng.choice(["중간석차", "최고석차"]), rng.choice(["지침", "지침", "백분율", "인원반올림"])
            rules = rules_with(tie=tie, cut=cut)
            others = [rng.randint(40, 60) for _ in range(rng.randint(4, 40))]
            v_self = rng.randint(30, 70)
            srt = sorted(others + [v_self])
            for g in range(1, 5):
                fast = simulate.min_units_for_grade(srt, v_self, g, rules, 100)

                def grade_if(T):
                    tot = {f"o{i}": D(x) for i, x in enumerate(others)}
                    tot["me"] = D(T)
                    return naesin.rank_grades(tot, rules)["me"]["grade"]
                slow = [grade_if(T) <= g for T in range(101)]
                expect = slow.index(True) if True in slow else 101
                self.assertEqual(fast, expect, (trial, tie, cut, g, others, v_self))
                # 이분 탐색의 전제: 한 번 목표 등급에 들면 점수가 더 올라도 계속 든다
                self.assertTrue(all(slow[expect:]), (trial, tie, cut, g))


class SampleSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generate_sample.main()
        cls.data = analysis.load(generate_sample.OUT_DIR)
        cls.rules = naesin.load_rules(generate_sample.OUT_DIR)
        s1, s2 = cls.rules["semesters"]
        cls.t1 = naesin.transcript(cls.data, cls.rules, s1)
        cls.sim = simulate.simulate(cls.data, cls.rules, s2, s1)

    def test_transcript_counts(self):
        self.assertEqual(self.t1["n"], 98)  # 100명 - 중간 결시 1 - 수행 결시 1
        self.assertEqual({e["student_id"] for e in self.t1["excluded"]}, {"S007", "S088"})
        self.assertEqual(sum(self.t1["grade_counts"].values()), 98)
        # 2학기 기말이 아직 없으므로 2학기 성적표는 만들지 않는다
        self.assertIsNone(naesin.transcript(self.data, self.rules, self.rules["semesters"][1]))

    def test_transcript_matches_independent_ranking(self):
        rows = self.t1["rows"]
        totals = sorted((r["total"] for r in rows.values()), reverse=True)
        for sid, r in rows.items():
            first = totals.index(r["total"]) + 1
            last = len(totals) - totals[::-1].index(r["total"])
            self.assertEqual(r["rank"], first)
            self.assertEqual(r["ties"], last - first + 1)

    def test_simulation_shape_and_order(self):
        sim = self.sim
        self.assertEqual(sim["n"], 99)
        self.assertEqual(sim["excluded"][0]["student_id"], "S052")
        for sid, st in sim["students"].items():
            for scen, by_perf in st["grade"].items():
                for pk, per_g in by_perf.items():
                    self.assertAlmostEqual(sum(st["predict"][scen][pk]), 1.0)
                    prev = Decimal(-1)
                    for g in (4, 3, 2, 1):  # 높은 등급일수록 필요한 점수는 같거나 높다
                        v = per_g[g]
                        if v["p80"] is not None and v["p50"] is not None:
                            self.assertLessEqual(v["p50"], v["p80"])
                        cur = v["p80"] if v["p80"] is not None else Decimal(1000)
                        self.assertGreaterEqual(cur, prev, (sid, scen, pk, g))
                        prev = cur

    def test_harder_exam_needs_no_more(self):
        # 다른 학생들이 더 못 보는 시나리오에서 같은 등급에 필요한 점수가 더 높을 수는 없다
        big = Decimal(1000)
        for st in self.sim["students"].values():
            for pk in st["grade"]["base"]:
                for g in range(1, 5):
                    h = st["grade"]["hard"][pk][g]["p50"]
                    b = st["grade"]["base"][pk][g]["p50"]
                    e = st["grade"]["easy"][pk][g]["p50"]
                    h, b, e = (x if x is not None else big for x in (h, b, e))
                    self.assertLessEqual(h, b)
                    self.assertLessEqual(b, e)

    def test_achievement_need_is_exact(self):
        s2 = self.rules["semesters"][1]
        rnd = self.rules["total_rounding"]
        for st in self.sim["students"].values():
            for lv in st["perf_levels"]:
                for L, f in st["achievement"][lv["key"]].items():
                    cut = s2["achievement"]["cutoffs"][L]
                    t = lambda x: naesin.semester_values(st["mid"], x, lv["score"], 40, s2["weights"], rnd)["total"]
                    if f is None:
                        self.assertLess(t(100), cut)
                        continue
                    self.assertGreaterEqual(t(f), cut)
                    if f > 0:
                        self.assertLess(t(f - 1), cut)

    def test_reproducible(self):
        again = simulate.simulate(self.data, self.rules, self.rules["semesters"][1], self.rules["semesters"][0])
        self.assertEqual(again["students"]["S001"]["grade"], self.sim["students"]["S001"]["grade"])


if __name__ == "__main__":
    unittest.main()
