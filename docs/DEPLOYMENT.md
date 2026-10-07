# Deployment lock

SOLE is for **stable Studionet only**:

- network: `studionet`
- chain ID: **61999**
- RPC: `https://studio.genlayer.com/api`
- GenLayer CLI: **0.39.1**

Do not use 61997, Studio Next, Studionet-dev or Bradbury.

## Core

```bash
python scripts/preflight.py
python scripts/check_cli.py
python scripts/verify_studionet.py

genlayer deploy \
  --contract contracts/sole.py \
  --rpc https://studio.genlayer.com/api
```

Wait for finalization. Record the exact address and deployment transaction.

## Consumer

After the core address is finalized:

1. Create and seal the demo SOLE book.
2. Record its `book_id` and immutable `book_hash`.
3. Deploy `contracts/sole_consumer.py` with:
   - `sole_address`
   - `book_id`
   - `book_hash`

Using CLI 0.39.1 syntax:

```bash
genlayer deploy \
  --contract contracts/sole_consumer.py \
  --rpc https://studio.genlayer.com/api \
  --args <SOLE_ADDRESS> <BOOK_ID> <BOOK_HASH>
```

If CLI constructor syntax differs, use the syntax actually supported by 0.39.1. Do not upgrade the CLI to make deployment easier.

## Source changes

Any change to either contract invalidates older addresses as proof for the new source.

Fresh source -> fresh deployment -> fresh lifecycle proof.

## Evidence

Populate `deployments/studionet.json` only after real execution.

Generate a truthful local-only manifest before deployment with:

```bash
python scripts/make_manifest.py --predeployment
```

After real deployment evidence exists, generate the final manifest with:

```bash
python scripts/make_manifest.py
```

Then run:

```bash
python scripts/preflight.py --final
```
