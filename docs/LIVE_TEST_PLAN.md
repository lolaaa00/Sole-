# SOLE 61999 live lifecycle plan

Network lock:

- Studionet
- chain ID 61999
- RPC `https://studio.genlayer.com/api`
- CLI 0.39.1

Do not substitute 61997.

## 1. Preflight

```bash
python scripts/preflight.py
python scripts/check_cli.py
python scripts/verify_studionet.py
```

Expected:

- preflight PASS
- CLI 0.39.1
- chain ID 61999

## 2. Deploy

Deploy fresh final-source:

- `contracts/sole.py`
- `contracts/sole_consumer.py` after the book exists

Verify schemas.

## 3. Create canonical book

Example:

- name: `SOLE Demo Distribution Rights`
- domain key: `SOLE_DEMO_PRODUCT_X`
- charter: ordinary commercial interpretation; ambiguity fails closed

Seal it and record `book_hash`.

## 4. Case A — first grant

Propose reservation A:

- holder: wallet A
- right: `exclusive distribution and resale`
- product: `Product X`
- territory: `Nigeria`
- channel: `online and e-commerce sales`
- audience: `retail customers`
- interval: a clearly declared demo interval

Holder accepts.

Assess. With no incumbent, expect deterministic `READY`.

Finalize.

Verify:

- status `GRANTED`
- epoch incremented
- `is_granted(...correct hashes...) == true`

## 5. Case B — material conflict

Propose reservation B for a different holder with materially overlapping wording, e.g.:

- right: `exclusive e-commerce resale`
- product: `Product X`
- territory: `Nigeria`
- channel: `web shops and online marketplaces`
- audience: `consumer buyers`
- overlapping interval

Holder accepts.

Assess.

Expected: consensus finds reservation A conflicting and B becomes `BLOCKED`.

Attempt `finalize_grant(B)` and verify rejection.

## 6. Case C — semantic disjointness

Propose reservation C with same time/product but a clearly disjoint territory or channel.

Expected: `READY`.

Finalize.

Verify epoch increment.

## 7. Case D — stale assessment race

Create D and E so both can be assessed at the same epoch.

Assess D -> READY.

Assess E -> READY.

Finalize E first.

Attempt to finalize D using its old assessment.

Expected: deterministic stale-epoch rejection.

Reassess D against the new incumbent set and record the fresh result.

This is a mandatory reviewer proof because it demonstrates TOCTOU closure.

## 8. Case E — holder release

Have the holder of a granted reservation release it.

Verify:

- status `RELEASED`
- book epoch increments
- `is_granted` becomes false

Reassess a previously blocked/stale candidate if applicable and show the released right no longer blocks it.

## 9. Case F — book pause

Pause the book.

Verify new proposal/assessment/grant operations reject.

Verify previously granted reservations remain recorded as granted.

Reactivate.

## 10. Case G — consumer

Deploy `SoleConsumer` bound to the exact canonical `book_id` and `book_hash`.

The granted holder activates once.

Verify:

- activation count increments exactly once
- non-holder rejected
- wrong reservation hash rejected
- replay rejected
- released reservation cannot activate

## 11. Case H — non-decision

Direct Mode only unless naturally encountered live.

Mock malformed model output and model exception.

Verify:

- never becomes READY
- stays ACCEPTED/retryable
- consecutive non-decision counter increments
- no fake semantic verdict is stored

Do not falsely label mocked evidence as live.

## 12. Record

Populate `deployments/studionet.json` with:

- commit SHA
- source hashes
- core address
- consumer address
- every deployment tx
- every lifecycle tx
- final readbacks
- explorer links
- Direct Mode counts
- any honest blocker

Then:

```bash
python scripts/preflight.py --final
```
