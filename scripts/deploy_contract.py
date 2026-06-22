#!/usr/bin/env python3
"""Compile and deploy contracts/Splitter.sol to Arc Testnet.

Reuses the agent's patterns: CA-pinned Arc RPC (agents/arc_ca.pem), PRIVATE_KEY
from .env, and EIP-1559 (type 0x2) txs. On success the contract address is saved
to .env as SPLITTER_ADDRESS.

Usage:
    uv run python scripts/deploy_contract.py
"""

import json
import os
import sys

RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002
SOLC_VERSION = "0.8.26"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, ".env")
CONTRACT_FILE = os.path.join(ROOT, "contracts", "Splitter.sol")
# Pin Arc RPC to Let's Encrypt roots (same bundle the agent uses).
ARC_CA_BUNDLE = os.path.join(ROOT, "agents", "arc_ca.pem")


def _web3():
    from web3 import Web3
    from web3.providers.rpc import HTTPProvider

    return Web3(HTTPProvider(RPC_URL, request_kwargs={"verify": ARC_CA_BUNDLE}))


def _read_env_value(name: str) -> str | None:
    try:
        for line in open(ENV_FILE):
            s = line.strip()
            if s.startswith(f"{name}="):
                return s.split("=", 1)[1]
    except FileNotFoundError:
        pass
    return None


def _write_env_value(name: str, value: str) -> None:
    """Set name=value in .env, preserving all other lines."""
    try:
        with open(ENV_FILE) as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    out, found = [], False
    for line in lines:
        if line.strip().startswith(f"{name}="):
            out.append(f"{name}={value}\n")
            found = True
        else:
            out.append(line)
    if not found:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append(f"{name}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(out)


def compile_contract() -> tuple[list, str]:
    """Compile Splitter.sol, returning (abi, bytecode)."""
    from solcx import compile_standard, install_solc, set_solc_version

    print(f"🛠  Installing solc {SOLC_VERSION} (cached after first run)...")
    install_solc(SOLC_VERSION)
    set_solc_version(SOLC_VERSION)

    source = open(CONTRACT_FILE).read()
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"Splitter.sol": {"content": source}},
            "settings": {
                "optimizer": {"enabled": True, "runs": 200},
                "outputSelection": {
                    "*": {"*": ["abi", "evm.bytecode.object"]}
                },
            },
        },
        solc_version=SOLC_VERSION,
    )
    contract = compiled["contracts"]["Splitter.sol"]["Splitter"]
    abi = contract["abi"]
    bytecode = contract["evm"]["bytecode"]["object"]
    return abi, bytecode


def main():
    try:
        from web3 import Web3
    except ImportError:
        print("❌ web3.py not installed. Install: uv pip install web3 py-solc-x")
        sys.exit(1)

    pk = os.environ.get("PRIVATE_KEY") or _read_env_value("PRIVATE_KEY")
    if not pk:
        print("❌ No PRIVATE_KEY in env or .env. Run the agent once with --execute to create one.")
        sys.exit(1)

    abi, bytecode = compile_contract()

    w3 = _web3()
    acct = w3.eth.account.from_key(pk)
    print(f"\n🚀 Deploying Splitter to Arc Testnet ({CHAIN_ID})")
    print(f"   Deployer: {acct.address}")

    balance = w3.from_wei(w3.eth.get_balance(acct.address), "ether")
    print(f"   Balance:  {float(balance):.4f} USDC")
    if balance == 0:
        print("⚠️  Deployer has 0 USDC — fund it at https://faucet.circle.com/ (Arc Testnet)")
        sys.exit(1)

    Splitter = w3.eth.contract(abi=abi, bytecode=bytecode)
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    nonce = w3.eth.get_transaction_count(acct.address)

    deploy_tx = {
        "from": acct.address,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "maxFeePerGas": base_fee * 2,
        "maxPriorityFeePerGas": base_fee // 2,
        "type": "0x2",
    }
    try:
        gas_est = w3.eth.estimate_gas({"from": acct.address, "data": "0x" + bytecode})
        deploy_tx["gas"] = int(gas_est * 1.25)
    except Exception as e:
        print(f"   (gas estimate failed: {e}; using fallback 600000)")
        deploy_tx["gas"] = 600000

    built = Splitter.constructor().build_transaction(deploy_tx)
    signed = acct.sign_transaction(built)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"\n📝 Deploy tx: {tx_hash.hex()}")
    print("   Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] not in (1, "0x1", b"\x01"):
        print("❌ Deployment failed on chain (status 0). Check the tx on arcscan.")
        sys.exit(1)

    address = receipt["contractAddress"]
    _write_env_value("SPLITTER_ADDRESS", address)

    print("\n✅ Splitter deployed!")
    print("━" * 60)
    print(f"  Address:   {address}")
    print(f"  Gas used:  {receipt['gasUsed']}")
    print(f"  Explorer:  https://testnet.arcscan.app/address/{address}")
    print(f"  Saved to:  .env (SPLITTER_ADDRESS)")
    print("━" * 60)

    # Save ABI alongside the contract for reference / external tools.
    abi_path = os.path.join(ROOT, "contracts", "Splitter.abi.json")
    with open(abi_path, "w") as f:
        json.dump(abi, f, indent=2)
    print(f"  ABI saved: {abi_path}")

    print("\n🔎 Verify source on arcscan (manual, best-effort):")
    print(f"   1. Open https://testnet.arcscan.app/address/{address}#code")
    print(f"   2. 'Verify & Publish' → Solidity (single file), compiler v{SOLC_VERSION}")
    print(f"   3. Optimization: Yes (200 runs); paste contracts/Splitter.sol")


if __name__ == "__main__":
    main()
