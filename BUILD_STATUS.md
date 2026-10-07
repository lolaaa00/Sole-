# SOLE build status

## Locally verified on 2026-10-07

- contract architecture and state machine
- immutable book and reservation hashing
- holder acceptance flow
- deterministic half-open time-overlap rule
- GenLayer semantic overlap consensus
- strict validator agreement at the state-consequence boundary
- retryable non-decision handling
- epoch-based TOCTOU protection
- holder-only release
- minimal second-contract consumer
- deterministic pure-Python reference model
- 11 deterministic unit tests passing on Python 3.12
- 34 adversarial main-contract Direct Mode tests plus 5 consumer/source
  compatibility checks passing with `genlayer-test` 0.29.2 (39 tests in the direct suite)
- GenVM lint and SDK validation passing for both contracts against the cached
  `v0.3.0-rc7` bundle containing the pinned stable-Studionet dependency
- repository preflight passing
- CLI 0.39.1 verified
- stable Studionet RPC independently verified as chain ID 61999
- Direct Mode explicitly pinned to GenVM `v0.2.16`, which contains the declared
  stable-Studionet SDK dependency and avoids CI drift to incompatible prereleases
- Two live deployment proposals returned `invalid_contract`; their addresses are
  excluded. The runtime declaration is now first-line as required by the loader.
- input bounds reject oversize values instead of silently truncating them
- finalization, release and `is_granted` re-check immutable definitions
- consumer rejects zero SOLE addresses and malformed hash bindings
- consumer contract syntax/static checks; full cross-contract dispatch reserved for live 61999 because genlayer-test v0.29.2 loads one Contract subclass per process
- network/CLI guard scripts
- CI definition
- deployment/lifecycle documentation
- reviewer-facing submission draft
- Codex master handoff

## Intentionally not claimed

This working tree does **not** claim:

- a live deployment
- a 61999 contract address
- a live transaction hash
- a complete 61999 lifecycle proof
- a git commit or CI run; `lolaaa00/sole` did not exist when last checked

Those must be produced by the finishing agent from the extracted repository and recorded honestly.

## Required final state before submission

1. The user creates `lolaaa00/sole`; this exact folder is initialized and
   checkpointed there.
2. Core and consumer are freshly deployed from the final committed source.
3. Lifecycle cases in `docs/LIVE_TEST_PLAN.md` are executed and finalized.
4. `deployments/studionet.json` contains only real addresses/tx hashes.
5. `python scripts/preflight.py --final` passes.
6. GitHub Actions is green on the final pushed commit.
