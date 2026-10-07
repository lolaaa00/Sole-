#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import py_compile
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "SUBMISSION.md",
    "BUILD_STATUS.md",
    "NETWORK_LOCK.json",
    "SOLE_CODEX_MASTER_HANDOFF.txt",
    "contracts/sole.py",
    "contracts/sole_consumer.py",
    "reference/sole_model.py",
    "tests/direct/test_sole.py",
    "tests/unit/test_sole_model.py",
    "docs/ARCHITECTURE.md",
    "docs/SECURITY_MODEL.md",
    "docs/LIVE_TEST_PLAN.md",
    "docs/DEPLOYMENT.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--final",
        action="store_true",
        help="also require real deployment/lifecycle evidence",
    )
    args = parser.parse_args()

    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    lock = json.loads((ROOT / "NETWORK_LOCK.json").read_text())
    if lock.get("chain_id") != 61999:
        fail("NETWORK_LOCK chain_id must be 61999")
    if lock.get("rpc") != "https://studio.genlayer.com/api":
        fail("NETWORK_LOCK RPC is not stable Studionet")
    if lock.get("genlayer_cli") != "0.39.1":
        fail("CLI lock must be 0.39.1")
    if 61997 not in lock.get("forbidden_chain_ids", []):
        fail("NETWORK_LOCK must explicitly forbid chain 61997")

    operational = [
        ROOT / "contracts" / "sole.py",
        ROOT / "contracts" / "sole_consumer.py",
        ROOT / "gltest.config.yaml",
        ROOT / "scripts" / "deploy_studionet.py",
        ROOT / "scripts" / "verify_studionet.py",
    ]
    for path in operational:
        text = path.read_text()
        if "61997" in text or "studio-next.genlayer.com" in text:
            fail(
                "forbidden 61997/studio-next reference in operational file "
                f"{path.relative_to(ROOT)}"
            )

    # SOLE is deliberately frontend-free.
    for forbidden in (
        "package.json",
        "vite.config.js",
        "next.config.js",
        "next.config.mjs",
    ):
        if (ROOT / forbidden).exists():
            fail(f"frontend artifact present: {forbidden}")
    for forbidden_dir in ("src", "app", "frontend", "web", "pages"):
        if (ROOT / forbidden_dir).is_dir():
            fail(f"frontend directory present: {forbidden_dir}")

    for rel in (
        "contracts/sole.py",
        "contracts/sole_consumer.py",
        "reference/sole_model.py",
    ):
        try:
            with tempfile.TemporaryDirectory(prefix="sole-preflight-") as tmp:
                target = pathlib.Path(tmp) / (pathlib.Path(rel).name + "c")
                py_compile.compile(str(ROOT / rel), cfile=str(target), doraise=True)
        except Exception as error:
            fail(f"syntax compile failed for {rel}: {error}")

    contract = (ROOT / "contracts" / "sole.py").read_text()
    for needle in (
        "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6",
        "gl.vm.run_nondet_unsafe",
        "def finalize_grant",
        "def release_reservation",
        "def is_granted",
        "assessment is stale; book epoch changed",
        "only holder may release exclusivity",
    ):
        if needle not in contract:
            fail(f"main contract missing invariant marker: {needle}")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/unit",
            "-p",
            "test_*.py",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        fail("deterministic unit tests failed")

    if args.final:
        deployment = ROOT / "deployments" / "studionet.json"
        if not deployment.is_file():
            fail("final mode requires deployments/studionet.json")
        data = json.loads(deployment.read_text())
        if data.get("network") != "studionet" or data.get("chain_id") != 61999:
            fail("deployment evidence must be stable Studionet 61999")
        addr = re.compile(r"^0x[0-9a-fA-F]{40}$")
        for key in ("sole_address", "consumer_address"):
            if not addr.match(str(data.get(key, ""))):
                fail(f"deployment evidence missing valid {key}")
        transactions = data.get("lifecycle_transactions", [])
        if not transactions:
            fail("final deployment evidence has no lifecycle transactions")
        required_steps = {
            "create_book", "seal_book", "propose_reservation", "holder_accept",
            "assess_clear", "finalize_grant", "consumer_activate", "holder_release",
        }
        steps = {item.get("step") for item in transactions}
        if not required_steps.issubset(steps):
            fail("final deployment evidence is missing lifecycle steps")
        for item in transactions:
            if item.get("status") != "FINALIZED" or item.get("execution") != "SUCCESS":
                fail(f"lifecycle step is not a finalized success: {item.get('step')}")
        parity = data.get("source_parity", {})
        if parity.get("normalized_exact_match") is not True:
            fail("final deployment evidence does not prove source parity")

    print("PASS: SOLE preflight")
    if not args.final:
        print(
            "NOTE: live deployment evidence is intentionally not required "
            "without --final"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
