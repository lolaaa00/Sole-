"""Adversarial Direct Mode tests for SOLE.

Designed for the stable 61999-era GenLayer testing stack:
genlayer-test v0.29.2.

The tests exercise the real contract shape, holder consent, semantic overlap
consensus, non-decisions, stale-epoch TOCTOU protection, releases, and the
minimal consumer contract.
"""
import json
import pytest

CONTRACT = "contracts/sole.py"
CONSUMER = "contracts/sole_consumer.py"

ZERO = "0x0000000000000000000000000000000000000000"


def addr(value):
    from genlayer.py.types import Address
    if isinstance(value, str):
        return Address(value)
    return Address(bytes(value))


def charter():
    return (
        "Reservations in this book concern commercial exclusivity. "
        "Interpret product, territory, channel, audience and right scope by "
        "their ordinary commercial meaning. Do not infer exclusions that are "
        "not written. Ambiguity must fail closed."
    )


def make_book(contract):
    book_id = contract.create_book("ACME Product X Rights", "ACME_PRODUCT_X", charter())
    book_hash = contract.seal_book(book_id)
    return book_id, book_hash


def proposal(
    contract,
    book_id,
    holder,
    *,
    right="exclusive distribution and resale",
    product="Product X and Product X Pro",
    territory="Nigeria",
    channel="online and e-commerce sales",
    audience="retail customers",
    start=1000,
    end=2000,
):
    return contract.propose_reservation(
        book_id,
        addr(holder),
        right,
        product,
        territory,
        channel,
        audience,
        start,
        end,
    )


def comparison(
    incumbent_id,
    *,
    right="OVERLAPS",
    product="EQUIVALENT",
    territory="OVERLAPS",
    channel="OVERLAPS",
    audience="OVERLAPS",
):
    return {
        "incumbent_id": incumbent_id,
        "right": right,
        "product": product,
        "territory": territory,
        "channel": channel,
        "audience": audience,
        "reason_code": "TEST",
    }


def response(*items):
    return json.dumps({"comparisons": list(items)})


def grant_first(direct_vm, contract, owner, holder, book_id):
    direct_vm.sender = owner
    rid = proposal(contract, book_id, holder)
    direct_vm.sender = holder
    contract.accept_reservation(rid)
    direct_vm.sender = owner
    contract.assess_reservation(rid)
    assert contract.get_reservation(rid)["status_name"] == "READY"
    contract.finalize_grant(rid)
    return rid


def test_only_one_canonical_book_per_owner_domain(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    make_book(c)
    with direct_vm.expect_revert("canonical book"):
        c.create_book("Duplicate", "ACME_PRODUCT_X", charter())


def test_book_is_immutable_after_seal(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, bh = make_book(c)
    b = c.get_book(bid)
    assert b["definition_hash"] == bh
    with direct_vm.expect_revert("already sealed"):
        c.seal_book(bid)


def test_pause_blocks_new_proposal(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    c.set_book_active(bid, False)
    with direct_vm.expect_revert("not active"):
        proposal(c, bid, direct_bob)


def test_zero_holder_rejected(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    with direct_vm.expect_revert("zero address"):
        proposal(c, bid, ZERO)


def test_only_owner_can_propose(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only book owner"):
        proposal(c, bid, direct_bob)


def test_holder_must_accept_exact_proposal(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = proposal(c, bid, direct_bob)
    with direct_vm.expect_revert("holder has not accepted"):
        c.assess_reservation(rid)
    direct_vm.sender = direct_bob
    c.accept_reservation(rid)
    assert c.get_reservation(rid)["holder_accepted"] is True


def test_non_holder_cannot_accept(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = proposal(c, bid, direct_bob)
    with direct_vm.expect_revert("only proposed holder"):
        c.accept_reservation(rid)


def test_first_right_is_deterministically_ready_without_llm(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = proposal(c, bid, direct_bob)
    direct_vm.sender = direct_bob
    c.accept_reservation(rid)
    direct_vm.sender = direct_alice
    c.assess_reservation(rid)
    item = c.get_reservation(rid)
    assert item["status_name"] == "READY"
    assert item["conflict_ids"] == []
    assert item["ambiguous_ids"] == []


def test_conflicting_scope_is_blocked(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)

    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    direct_vm.mock_llm("SOLE semantic exclusivity overlap assessor", response(comparison(incumbent)))
    c.assess_reservation(candidate)

    item = c.get_reservation(candidate)
    assert item["status_name"] == "BLOCKED"
    assert item["conflict_ids"] == [incumbent]


def test_one_disjoint_dimension_makes_pair_clear(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)

    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie, territory="Kenya")
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, territory="DISJOINT")),
    )
    c.assess_reservation(candidate)
    assert c.get_reservation(candidate)["status_name"] == "READY"


def test_ambiguity_fails_closed(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)

    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie, channel="digital channels")
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, channel="AMBIGUOUS")),
    )
    c.assess_reservation(candidate)
    item = c.get_reservation(candidate)
    assert item["status_name"] == "AMBIGUOUS"
    assert item["ambiguous_ids"] == [incumbent]


def test_time_disjoint_rights_never_call_semantic_consensus(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    grant_first(direct_vm, c, direct_alice, direct_bob, bid)

    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie, start=2000, end=3000)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    c.assess_reservation(candidate)
    assert c.get_reservation(candidate)["status_name"] == "READY"


def test_validator_rejects_different_state_consequence(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice

    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, territory="DISJOINT")),
    )
    c.assess_reservation(candidate)
    assert c.get_reservation(candidate)["status_name"] == "READY"

    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent)),
    )
    assert direct_vm.run_validator() is False


def test_validator_accepts_different_labels_when_pair_outcome_is_same(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice

    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, right="OVERLAPS", product="EQUIVALENT")),
    )
    c.assess_reservation(candidate)

    direct_vm.clear_mocks()
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, right="CONTAINS", product="CONTAINED_BY")),
    )
    assert direct_vm.run_validator() is True


def test_malformed_model_output_is_retryable_nondecision(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    direct_vm.mock_llm("SOLE semantic exclusivity overlap assessor", "not json")
    c.assess_reservation(candidate)
    item = c.get_reservation(candidate)
    assert item["status_name"] == "ACCEPTED"
    assert item["last_assessment_result"] == "MODEL_OUTPUT_INVALID"
    assert item["consecutive_nondecisions"] == 1


def test_ready_candidate_becomes_stale_if_another_right_is_granted(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)

    # Candidate A is assessed READY in empty epoch 0 but not granted yet.
    a = proposal(c, bid, direct_bob, territory="Nigeria")
    direct_vm.sender = direct_bob
    c.accept_reservation(a)
    direct_vm.sender = direct_alice
    c.assess_reservation(a)
    assert c.get_reservation(a)["status_name"] == "READY"

    # Candidate B, disjoint in time, can also be assessed and granted, moving epoch.
    b = proposal(c, bid, direct_charlie, territory="Kenya", start=3000, end=4000)
    direct_vm.sender = direct_charlie
    c.accept_reservation(b)
    direct_vm.sender = direct_alice
    c.assess_reservation(b)
    c.finalize_grant(b)

    with direct_vm.expect_revert("assessment is stale"):
        c.finalize_grant(a)


def test_reassessment_after_epoch_change_can_detect_new_conflict(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)

    a = proposal(c, bid, direct_bob)
    direct_vm.sender = direct_bob
    c.accept_reservation(a)
    direct_vm.sender = direct_alice
    c.assess_reservation(a)  # READY epoch 0

    b = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(b)
    direct_vm.sender = direct_alice
    c.assess_reservation(b)  # READY epoch 0 too
    c.finalize_grant(b)      # epoch 1

    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(b)),
    )
    c.assess_reservation(a)
    assert c.get_reservation(a)["status_name"] == "BLOCKED"


def test_only_holder_can_release_and_release_moves_epoch(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    epoch_before = c.get_book(bid)["epoch"]
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("only holder"):
        c.release_reservation(rid)
    direct_vm.sender = direct_bob
    c.release_reservation(rid)
    assert c.get_reservation(rid)["status_name"] == "RELEASED"
    assert c.get_book(bid)["epoch"] == epoch_before + 1


def test_release_allows_future_reassessment_to_clear(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)

    direct_vm.sender = direct_alice
    candidate = proposal(c, bid, direct_charlie)
    direct_vm.sender = direct_charlie
    c.accept_reservation(candidate)
    direct_vm.sender = direct_alice
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent)),
    )
    c.assess_reservation(candidate)
    assert c.get_reservation(candidate)["status_name"] == "BLOCKED"

    direct_vm.sender = direct_bob
    c.release_reservation(incumbent)
    direct_vm.sender = direct_alice
    direct_vm.clear_mocks()
    c.assess_reservation(candidate)  # no incumbent -> deterministic CLEAR
    assert c.get_reservation(candidate)["status_name"] == "READY"


def test_is_granted_binds_exact_hashes(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, bh = make_book(c)
    rid = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    item = c.get_reservation(rid)
    assert c.is_granted(rid, item["reservation_hash"], bh) is True
    assert c.is_granted(rid, "00" * 32, bh) is False
    assert c.is_granted(rid, item["reservation_hash"], "11" * 32) is False

# ---------------------------------------------------------------------------
# Consumer contract note
#
# genlayer-test v0.29.2 Direct Mode permits at most one gl.Contract subclass
# per Python process. Loading SOLE and SoleConsumer in the same Direct Mode
# process therefore cannot prove true IC-to-IC dispatch. This is a testing
# harness limitation, not an application shortcut. Full composability is a
# mandatory live 61999 case in docs/LIVE_TEST_PLAN.md.
# ---------------------------------------------------------------------------

def test_protocol_dictionary_exposes_fixed_conflict_rule(
    direct_vm, direct_deploy, direct_alice
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    dictionary = c.get_protocol_dictionary()
    assert dictionary["protocol"] == "SOLE/1"
    assert "DISJOINT" in dictionary["relations"]
    assert "AMBIGUOUS" in dictionary["relations"]
    assert dictionary["max_comparison_set"] == 12


def accepted_candidate(direct_vm, contract, owner, holder, book_id, **kwargs):
    direct_vm.sender = owner
    rid = proposal(contract, book_id, holder, **kwargs)
    direct_vm.sender = holder
    contract.accept_reservation(rid)
    direct_vm.sender = owner
    return rid


def test_zero_address_book_owner_cannot_be_impersonated(
    direct_vm, direct_deploy, direct_alice
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    direct_vm.sender = addr(ZERO)
    with direct_vm.expect_revert("only book owner"):
        c.set_book_active(bid, False)


def test_issuer_cannot_impersonate_holder_acceptance(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = proposal(c, bid, direct_bob)
    with direct_vm.expect_revert("only proposed holder"):
        c.accept_reservation(rid)


def test_granted_reservation_cannot_be_withdrawn(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    rid = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    with direct_vm.expect_revert("cannot be withdrawn"):
        c.withdraw_reservation(rid)


def test_pause_blocks_assessment_and_finalization_without_erasing_grant(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, bh = make_book(c)
    granted = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    granted_hash = c.get_reservation(granted)["reservation_hash"]
    candidate = accepted_candidate(
        direct_vm, c, direct_alice, direct_charlie, bid, start=3000, end=4000
    )
    c.assess_reservation(candidate)
    c.set_book_active(bid, False)
    with direct_vm.expect_revert("book is not active"):
        c.finalize_grant(candidate)
    assert c.is_granted(granted, granted_hash, bh) is True


def test_oversized_and_empty_inputs_are_rejected_not_truncated(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("name exceeds"):
        c.create_book("x" * 97, "DOMAIN", charter())
    bid, _ = make_book(c)
    with direct_vm.expect_revert("right_scope exceeds"):
        proposal(c, bid, direct_bob, right="x" * 421)
    with direct_vm.expect_revert("audience_scope is required"):
        proposal(c, bid, direct_bob, audience="   ")


def test_invalid_intervals_are_rejected(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    with direct_vm.expect_revert("invalid reservation interval"):
        proposal(c, bid, direct_bob, start=1000, end=1000)
    with direct_vm.expect_revert("protocol maximum"):
        proposal(c, bid, direct_bob, start=1, end=315360002)


@pytest.mark.parametrize("case", ("missing", "duplicate", "extra"))
def test_missing_duplicate_and_extra_incumbents_are_nondecisions(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie, case
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    candidate = accepted_candidate(direct_vm, c, direct_alice, direct_charlie, bid)
    if case == "missing":
        raw = response()
    elif case == "duplicate":
        raw = response(comparison(incumbent), comparison(incumbent))
    else:
        raw = response(comparison(incumbent), comparison(999))
    direct_vm.mock_llm("SOLE semantic exclusivity overlap assessor", raw)
    c.assess_reservation(candidate)
    item = c.get_reservation(candidate)
    assert item["status_name"] == "ACCEPTED"
    assert item["last_assessment_result"] == "MODEL_OUTPUT_INVALID"


def test_unsupported_relation_is_nondecision(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    candidate = accepted_candidate(direct_vm, c, direct_alice, direct_charlie, bid)
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor",
        response(comparison(incumbent, channel="SIMILAR")),
    )
    c.assess_reservation(candidate)
    assert c.get_reservation(candidate)["status_name"] == "ACCEPTED"


def test_validator_rejects_malformed_leader_wrapper_and_payload(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    candidate = accepted_candidate(direct_vm, c, direct_alice, direct_charlie, bid)
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor", response(comparison(incumbent))
    )
    c.assess_reservation(candidate)
    assert direct_vm.run_validator(leader_result="not a dict") is False
    assert direct_vm.run_validator(leader_error=RuntimeError("boom")) is False


def test_validator_rejects_fabricated_partitions(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, _ = make_book(c)
    incumbent = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    candidate = accepted_candidate(direct_vm, c, direct_alice, direct_charlie, bid)
    direct_vm.mock_llm(
        "SOLE semantic exclusivity overlap assessor", response(comparison(incumbent))
    )
    c.assess_reservation(candidate)
    stored = c.get_reservation(candidate)
    fabricated = {
        "outcome": "SUBSTANTIVE",
        "comparison_set_hash": stored["comparison_set_hash"],
        "incumbent_ids": [incumbent],
        "conflict_ids": [],
        "ambiguous_ids": [],
        "clear_ids": [incumbent, incumbent],
        "overall": "CLEAR",
    }
    assert direct_vm.run_validator(leader_result=fabricated) is False


def test_serialization_sensitive_state_round_trip(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.check_pickling = True
    direct_vm.sender = direct_alice
    c = direct_deploy(CONTRACT)
    bid, bh = make_book(c)
    rid = grant_first(direct_vm, c, direct_alice, direct_bob, bid)
    item = c.get_reservation(rid)
    assert c.is_granted(rid, item["reservation_hash"], bh) is True
