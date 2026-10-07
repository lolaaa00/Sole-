"""Pure-Python deterministic SOLE reference model.

No GenLayer dependency. This module exists so the conflict rule, interval rule,
and state consequence can be tested independently of Direct Mode.
"""
from __future__ import annotations

RELATIONS = {
    "EQUIVALENT",
    "CONTAINS",
    "CONTAINED_BY",
    "OVERLAPS",
    "DISJOINT",
    "AMBIGUOUS",
}
DIMENSIONS = ("right", "product", "territory", "channel", "audience")


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return int(a_start) < int(b_end) and int(b_start) < int(a_end)


def pair_outcome(relations: dict[str, str]) -> str:
    if set(relations) != set(DIMENSIONS):
        raise ValueError("all five dimensions are required")
    for value in relations.values():
        if value not in RELATIONS:
            raise ValueError(f"invalid relation {value}")
    if any(relations[d] == "DISJOINT" for d in DIMENSIONS):
        return "CLEAR"
    if any(relations[d] == "AMBIGUOUS" for d in DIMENSIONS):
        return "AMBIGUOUS"
    return "CONFLICT"


def overall_outcome(pair_outcomes: list[str]) -> str:
    if any(v == "CONFLICT" for v in pair_outcomes):
        return "CONFLICT"
    if any(v == "AMBIGUOUS" for v in pair_outcomes):
        return "AMBIGUOUS"
    return "CLEAR"


def stale(assessed_epoch: int, current_epoch: int) -> bool:
    return int(assessed_epoch) != int(current_epoch)
