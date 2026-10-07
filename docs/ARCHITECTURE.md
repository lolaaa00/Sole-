# SOLE architecture

## Trust boundary

SOLE is a registry-level exclusivity mechanism, not a court.

It proves only what happened inside one canonical SOLE deployment/book:

- immutable rights were proposed;
- the holder accepted;
- contract-selected time-overlapping incumbents were compared;
- GenLayer validators agreed on the semantic state consequence;
- the assessment was fresh at the moment of grant;
- no conflicting/ambiguous incumbent remained;
- the grant/release transition occurred.

Consumers must bind the intended SOLE deployment, book id and book hash.

## Book model

An issuer may create one book for a given `(owner, domain_key)` pair.

The sealed book hash commits to:

- protocol version
- owner
- name
- canonical domain key
- semantic charter

The charter is issuer-specific interpretation context for scope language. Once sealed, it is immutable.

## Reservation model

A reservation commits to:

- id
- book id/hash
- grantor
- holder
- right scope
- product scope
- territory
- channel
- audience
- `[start_at,end_at)` interval

Holder acceptance occurs only after this hash exists.

## Deterministic prefilter

Only reservations in the same book with status `GRANTED` and overlapping half-open intervals are incumbents.

The leader cannot hide or insert incumbents.

The comparison-set digest commits to:

- candidate hash
- book epoch
- ordered incumbent ids/hashes

## Semantic consensus

For each incumbent, the model classifies exactly five dimensions into a fixed six-label vocabulary.

SOLE derives pair state itself:

```text
ANY DISJOINT   -> CLEAR
else ANY AMBIGUOUS -> AMBIGUOUS
else -> CONFLICT
```

This rule is important: models cannot output "overall conflict".

## Validation

The validator re-runs the same comparison.

Leader and follower must agree on the exact partition:

- conflict ids
- ambiguous ids
- clear ids

They need not agree on explanatory relation labels when those labels yield the same partition.

This keeps equivalence focused on the on-chain state consequence.

## TOCTOU closure

`book.epoch` changes on each `GRANTED` and `RELEASED` transition.

Assessment stores:

- `assessed_epoch`
- `comparison_set_hash`

`finalize_grant` recomputes the comparison set and refuses a stale epoch/hash.

Therefore two candidates assessed against the same old book cannot both finalize if the first grant changes the incumbent set.

## Release

The issuer cannot unilaterally revoke a granted exclusive right.

Only the holder can call `release_reservation`.

Release increments the epoch and makes blocked/stale proposals eligible for fresh assessment.

## Scaling bound

One semantic assessment handles at most `MAX_COMPARISON_SET` time-overlapping incumbents. The repository intentionally fails closed above that bound rather than silently truncating evidence.

Use narrower canonical domain books for high-volume deployments. The `(owner, domain_key)` uniqueness guard prevents duplicate books for the same declared domain inside this SOLE deployment.
