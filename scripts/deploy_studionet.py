#!/usr/bin/env python3
"""Deploy SOLE core to stable Studionet 61999 only."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RPC = "https://studio.genlayer.com/api"
CONTRACT = ROOT / "contracts" / "sole.py"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "preflight.py")])
    run([sys.executable, str(ROOT / "scripts" / "check_cli.py")])
    run([sys.executable, str(ROOT / "scripts" / "verify_studionet.py")])
    cli = shutil.which("genlayer")
    if cli is None:
        print("ERROR: genlayer CLI not found")
        return 2
    run([cli, "account", "show"])
    run([cli, "deploy", "--contract", str(CONTRACT), "--rpc", RPC])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
