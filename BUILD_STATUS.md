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
- 34 adversarial main-contract Direct Mode tests plus 6 consumer/source
  compatibility checks passing with `genlayer-test` 0.29.2 (40 tests in the direct suite)
- GenVM lint and SDK validation passing for both contracts against the cached
  `v0.3.0-rc7` bundle containing the pinned stable-Studionet dependency
- repository preflight passing
- CLI 0.39.1 verified
- stable Studionet RPC independently verified as chain ID 61999
- Direct Mode explicitly pinned to GenVM `v0.2.16`, which contains the declared
  stable-Studionet SDK dependency and avoids CI drift to incompatible prereleases
- Three live deployment proposals returned `invalid_contract`; their addresses are
  excluded. Hosted diagnostics identified and corrected the required version/dependency header sequence.
- Hosted schema extraction now accepts the compact 42 KB source; a 44 KB regression
  guard keeps future releases below the stable loader limit.
- input bounds reject oversize values instead of silently truncating them
- finalization, release and `is_granted` re-check immutable definitions
- consumer rejects zero SOLE addresses and malformed hash bindings
- consumer contract syntax/static checks; full cross-contract dispatch reserved for live 61999 because genlayer-test v0.29.2 loads one Contract subclass per process
- network/CLI guard scripts
- CI definition
- deployment/lifecycle documentation
- reviewer-facing submission draft
- Codex master handoff

## Live Studionet verification

- SOLE: `0xc3eDFC2624498Df0539dc1c05926981Cb57bE614`
- SoleConsumer: `0xd3F89786CC5af4b82AdBeDa3b02307565a47427A`
- both deployments finalized with successful execution on chain 61999
- exact normalized deployed-source parity proved for both contracts
- distinct grantor and holder accounts exercised
- create, seal, propose, accept, assess READY, grant, consumer activation,
  holder release, and post-release revocation finalized successfully
- unauthorized release and unrelated withdrawal produced the expected errors
- deployed-source CI run `37667620785` passed

Full evidence is in `deployments/studionet.json` and
`deployments/final_manifest.json`.
