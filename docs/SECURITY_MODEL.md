# SOLE security model

## Invariants

1. **No mutable grant text**: a reservation hash binds every material field.
2. **Explicit holder consent**: no assessment/final grant before acceptance.
3. **Deterministic incumbent set**: leader cannot choose which granted rights are compared.
4. **Fail-closed ambiguity**: ambiguity never becomes READY.
5. **No model-selected grant**: consensus classifies overlap; code grants.
6. **No stale assessment**: book epoch and comparison-set hash must still match.
7. **No issuer revocation after grant**: only holder release is supported.
8. **No model/infrastructure failure as CLEAR**.
9. **No frontend/backend authority**: the contract is the authority.
10. **No 61997 path**: operational files are locked to 61999.

## Threats and responses

### Malicious leader omits an incumbent

Impossible at the input boundary. Contract code derives the incumbent list before `run_nondet_unsafe`.

### Malicious leader returns a convenient relation

Validator independently reassesses the same frozen comparison set and must agree on the exact conflict/ambiguous/clear partition.

### Two candidates both assessed CLEAR, then both granted

The first grant increments the epoch. The second candidate's assessment becomes stale and cannot finalize.

### Issuer changes terms after holder accepts

No mutator exists. Any changed terms require a fresh reservation id/hash and fresh holder acceptance.

### Issuer pauses the book after granting

Pause blocks new proposals/assessments/grants. It does not erase already-granted reservations.

### Issuer revokes a holder's right

Unsupported. Only the holder can release a granted reservation.

### LLM is unavailable/malformed

Recorded as non-decision, reservation falls back to ACCEPTED, and never becomes grantable. Repeated non-decisions eventually exhaust.

### Ambiguous territory/channel wording

Fails closed as `AMBIGUOUS`. Narrow the wording in a new immutable reservation.

### Different books/deployments

SOLE cannot magically police rights issued outside the canonical deployment/book. Consumers must pin the intended SOLE address and book hash. This is an explicit trust boundary, not hidden.

### Private/off-chain rights

SOLE does not discover undisclosed external agreements. It prevents conflicting grants *within the canonical registry*.

## What SOLE does not claim

- legal enforceability
- ownership of the underlying asset
- truth of off-chain representations
- wall-clock activation in the sample consumer
- exclusivity outside the canonical book
