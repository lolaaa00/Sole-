import unittest

from reference.sole_model import (
    intervals_overlap,
    pair_outcome,
    overall_outcome,
    stale,
)


def all_overlap(**overrides):
    value = {
        "right": "OVERLAPS",
        "product": "EQUIVALENT",
        "territory": "CONTAINED_BY",
        "channel": "OVERLAPS",
        "audience": "CONTAINS",
    }
    value.update(overrides)
    return value


class SoleModelTests(unittest.TestCase):
    def test_half_open_intervals_touch_without_overlap(self):
        self.assertFalse(intervals_overlap(0, 10, 10, 20))

    def test_intervals_overlap_when_they_intersect(self):
        self.assertTrue(intervals_overlap(0, 11, 10, 20))

    def test_conflict_requires_no_disjoint_or_ambiguous_dimension(self):
        self.assertEqual(pair_outcome(all_overlap()), "CONFLICT")

    def test_one_disjoint_dimension_clears_pair(self):
        self.assertEqual(
            pair_outcome(all_overlap(territory="DISJOINT")),
            "CLEAR",
        )

    def test_disjoint_beats_ambiguity_because_intersection_is_impossible(self):
        self.assertEqual(
            pair_outcome(all_overlap(territory="DISJOINT", audience="AMBIGUOUS")),
            "CLEAR",
        )

    def test_ambiguity_fails_closed_when_no_dimension_is_disjoint(self):
        self.assertEqual(
            pair_outcome(all_overlap(channel="AMBIGUOUS")),
            "AMBIGUOUS",
        )

    def test_overall_conflict_dominates(self):
        self.assertEqual(overall_outcome(["CLEAR", "CONFLICT", "AMBIGUOUS"]), "CONFLICT")

    def test_overall_ambiguity_when_no_conflict(self):
        self.assertEqual(overall_outcome(["CLEAR", "AMBIGUOUS"]), "AMBIGUOUS")

    def test_overall_clear(self):
        self.assertEqual(overall_outcome(["CLEAR", "CLEAR"]), "CLEAR")

    def test_epoch_staleness(self):
        self.assertTrue(stale(2, 3))
        self.assertFalse(stale(3, 3))

    def test_invalid_relation_rejected(self):
        with self.assertRaises(ValueError):
            pair_outcome(all_overlap(channel="SIMILAR"))


if __name__ == "__main__":
    unittest.main()
