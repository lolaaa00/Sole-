# SOLE

**Consensus-backed semantic exclusivity reservations for GenLayer.**

SOLE is a standalone GenLayer Intelligent Contract primitive. It prevents one canonical issuer book from granting two materially overlapping exclusive rights merely because the rights were phrased differently.

There is **no frontend**. That is deliberate. SOLE belongs in the standalone Intelligent Contract category, not Projects.

## The primitive in one picture

```text
Existing grant
Product X
West Africa
online sales
retail customers
[Jan, Jun)
        │
        │ semantic overlap?
        ▼
Candidate
Product X Pro
Nigeria
e-commerce
consumer buyers
[Mar, May)
        │
        ▼
GenLayer consensus
        │
        ├─ any semantic dimension DISJOINT → CLEAR
        ├─ no DISJOINT + any AMBIGUOUS    → AMBIGUOUS
        └─ all dimensions overlap         → CONFLICT
        │
        ▼
deterministic book state

CLEAR      → READY → owner may GRANT
CONFLICT   → BLOCKED
AMBIGUOUS  → AMBIGUOUS, no grant
```

Time overlap is deterministic. The model never decides dates, authorization, consent, book ownership, grant finalization, release, replay, or stale-assessment handling.

## Why this primitive exists

A numerical-capacity contract can prevent overbooking a finite resource. It cannot detect that:

- "exclusive online distribution in West Africa"
- and "exclusive e-commerce resale in Nigeria"

may describe overlapping long-lived rights.

Likewise, exact hash/string checks cannot tell whether:

- "online"
- "e-commerce"
- "web shop"

materially intersect under an issuer's frozen commercial charter.

SOLE uses GenLayer only at that semantic boundary.

## Hard protocol invariants

### 1. One canonical book per issuer + domain key

An issuer cannot create two SOLE books with the same `domain_key` inside this deployment. Consumers should bind the canonical SOLE address, `book_id`, and immutable `book_hash`.

### 2. Rights are immutable proposals

A proposal binds:

- grantor
- holder
- right scope
- product scope
- territory
- channel
- audience
- half-open `[start_at,end_at)` interval
- book hash

Any material change requires a new reservation.

### 3. Holder consent is explicit

The issuer cannot assess/finalize a right until the named holder accepts the exact immutable reservation.

### 4. One disjoint dimension is enough to clear a pair

Two reservations do not collide if any one of the five semantic dimensions is definitely disjoint.

With no disjoint dimension, ambiguity fails closed.

### 5. TOCTOU is closed by the book epoch

Every grant or release increments the book epoch.

A candidate assessed at epoch `N` cannot be granted at epoch `N+1`. It must be reassessed against the new incumbent set.

This prevents:

```text
Candidate A assessed CLEAR
Candidate B granted
Candidate A uses stale CLEAR receipt
```

### 6. The issuer cannot revoke a granted exclusivity

Once granted, only the holder can release it in SOLE. Pausing the book stops new proposals/assessments/grants but does not silently erase existing grants.

### 7. Model/infra failure is never a verdict

`MODEL_OUTPUT_INVALID` and `SOURCE_UNAVAILABLE` are retryable non-decisions. They never become `CLEAR`.

## Semantic dimensions

Every time-overlapping incumbent is compared against the candidate on:

1. `right`
2. `product`
3. `territory`
4. `channel`
5. `audience`

Allowed relations are fixed:

- `EQUIVALENT`
- `CONTAINS`
- `CONTAINED_BY`
- `OVERLAPS`
- `DISJOINT`
- `AMBIGUOUS`

Deterministic derivation:

```text
if ANY dimension == DISJOINT:
    pair = CLEAR
elif ANY dimension == AMBIGUOUS:
    pair = AMBIGUOUS
else:
    pair = CONFLICT
```

Overall candidate result:

```text
any CONFLICT  → BLOCKED
else any AMBIGUOUS → AMBIGUOUS
else → READY
```

The model cannot override that rule.

## Consensus validator

`assess_reservation()` uses `gl.vm.run_nondet_unsafe(observe, validate)`.

The leader and validator independently interpret the exact same immutable candidate and incumbent set.

Validation requires exact agreement on the **state consequence**:

- same overall result
- exact same `conflict_ids`
- exact same `ambiguous_ids`
- exact same `clear_ids`

The models may use different explanatory relation labels if those differences do not change a pair's deterministic outcome.

The incumbent set itself is chosen by contract code, not by the leader.

## Reusability

`contracts/sole_consumer.py` is a deliberately tiny second Intelligent Contract.

It binds one SOLE book and only allows the recorded holder of a `GRANTED` reservation to activate it once. It demonstrates that another IC can depend on SOLE without duplicating SOLE's semantic logic.

Production consumers should also enforce whatever interval semantics their use case needs. SOLE's `GRANTED` status means the canonical registry issued the immutable reservation covering its declared `[start_at,end_at)` interval; it is not a wall-clock oracle.

## Network lock

SOLE is built only for:

- network: **Studionet**
- chain ID: **61999**
- RPC: `https://studio.genlayer.com/api`
- GenLayer CLI: **0.39.1**

Do **not** migrate this repository to 61997 / Studio Next / Studionet-dev / Bradbury.

## Repository map

- `contracts/sole.py` — main primitive
- `contracts/sole_consumer.py` — minimal consuming IC
- `reference/sole_model.py` — deterministic reference model
- `tests/unit/` — pure-Python invariant tests
- `tests/direct/` — adversarial Direct Mode tests
- `scripts/preflight.py` — frontend/network/static guard
- `scripts/check_cli.py` — enforces CLI 0.39.1
- `scripts/verify_studionet.py` — verifies chain ID 61999
- `scripts/deploy_studionet.py` — stable-Studionet core deployment helper
- `docs/ARCHITECTURE.md` — protocol design
- `docs/SECURITY_MODEL.md` — attack surfaces/invariants
- `docs/LIVE_TEST_PLAN.md` — finalized lifecycle proof plan
- `docs/DEPLOYMENT.md` — 61999 deployment instructions
- `SUBMISSION.md` — reviewer-facing submission draft
- `SOLE_CODEX_MASTER_HANDOFF.txt` — exact continuation instructions

## Local verification

```bash
python -m unittest discover -s tests/unit -p 'test_*.py'
python scripts/preflight.py
```

Direct Mode:

```bash
python -m pip install -r requirements-test.txt
pytest -q tests/direct
```

The Direct Mode harness is explicitly pinned to GenVM `v0.2.16`; the contract
dependency itself remains the stable-Studionet `py-genlayer` hash declared in
each contract header.

Submission result (2026-10-07): 11 deterministic tests and 40 Direct Mode/source
compatibility tests pass; GenVM lint/validation passes for both contracts. SOLE
and SoleConsumer are finalized on stable Studionet 61999, their deployed sources
exactly match this repository after newline normalization, and the complete
multi-account lifecycle is recorded in `deployments/studionet.json`.
