# SOLE submission draft

## Purpose

SOLE is a reusable GenLayer Intelligent Contract primitive for semantic exclusivity reservations. It prevents a canonical issuer book from granting a new exclusive right when the new right materially overlaps an already-granted right in time and semantic scope, even when the two grants use different natural-language wording.

## Why GenLayer

Deterministic code can compare dates, exact IDs and hashes, but it cannot reliably decide whether terms such as "online distribution" and "e-commerce resale", "West Africa" and "Nigeria", or "retail customers" and "consumer buyers" materially intersect under a frozen commercial charter.

SOLE uses GenLayer consensus only for that bounded overlap relation.

## What consensus decides

For each time-overlapping incumbent, independent validators classify five dimensions:

- right
- product
- territory
- channel
- audience

Each dimension is one of `EQUIVALENT`, `CONTAINS`, `CONTAINED_BY`, `OVERLAPS`, `DISJOINT`, `AMBIGUOUS`.

The contract then derives the pair outcome deterministically.

## What deterministic code decides

- book ownership/sealing
- one canonical book per owner/domain key
- holder consent
- immutable reservation hashes
- interval overlap
- incumbent selection
- conflict/ambiguity derivation
- READY/BLOCKED/AMBIGUOUS state
- epoch-based stale-assessment rejection
- final grant
- holder-only release
- exact-hash consumer verification
- replay prevention in the sample consumer

## Why the epoch matters

If another right is granted or released after a candidate was assessed, the book epoch changes. The candidate cannot use the old assessment and must be reassessed against the new incumbent set. This closes the race between semantic assessment and final grant.

## Reusability

`is_granted(reservation_id, expected_reservation_hash, expected_book_hash)` is the consumer surface.

`contracts/sole_consumer.py` proves a second IC can rely on the grant while binding the exact holder, book and reservation hash.

## Scope

No frontend. No custody. No legal opinion. No claim that a SOLE reservation has legal force outside systems that choose this canonical registry.

SOLE's claim is narrower: **inside a canonical SOLE book, two materially overlapping exclusive reservations cannot both be granted unless the earlier right is released or the semantic scopes/time windows are actually disjoint.**

## Required network

Studionet **61999** only, RPC `https://studio.genlayer.com/api`, GenLayer CLI **0.39.1**.

## Live evidence

- SOLE: `0xc3eDFC2624498Df0539dc1c05926981Cb57bE614`
- SoleConsumer: `0xd3F89786CC5af4b82AdBeDa3b02307565a47427A`
- immutable book `1`: `580db256cea77b0aa1c5b9659f25b2130acbd05ce960835437147fe0845d4bc4`
- reservation `2`: `14cd8d36041bee553e728f1310c608350ac29988833c93dbcbf90b830e5948a2`
- green deployed-source CI: `https://github.com/lolaaa00/Sole-/actions/runs/37667620785`

The finalized transaction trail, negative authorization checks, and exact
deployed-source hashes are in `deployments/studionet.json`.
