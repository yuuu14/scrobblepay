#!/usr/bin/env python3
"""Send a nanopayment on Arc Testnet.

Usage:
    PRIVATE_KEY=*** python scripts/send_nanopayment.py 0x933a...9682 0.000001
"""

import os
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: PRIVATE_KEY=*** python scripts/send_nanopayment.py <to_address> [amount_usdc]")
        sys.exit(1)

    to_address = sys.argv[1]
    amount = float(sys.argv[2]) if len(sys.argv) > 2 else 0.000001
    private_key = os.environ.get("PRIVATE_KEY")

    if not private_key:
        print("❌ PRIVATE_KEY env var not set")
        sys.exit(1)

    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network"))
        account = w3.eth.account.from_key(private_key)
        wei_amount = w3.to_wei(amount, "ether")

        print(f"\n💸 ScrobblePay Nanopayment")
        print(f"━" * 40)
        print(f"  From:   {account.address}")
        print(f"  To:     {to_address}")
        print(f"  Amount: ${amount:.6f} USDC")
        print(f"  Chain:  Arc Testnet (5042002)")
        print(f"━" * 40)

        tx = {
            "to": w3.to_checksum_address(to_address),
            "value": wei_amount,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": 5042002,
        }

        print("\n📝 Signing and sending...")
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        status = "✅ Success" if receipt["status"] == 1 else "❌ Failed"
        print(f"\n{status}")
        print(f"  Tx Hash:   {tx_hash.hex()}")
        print(f"  Block:     {receipt['blockNumber']}")
        print(f"  Gas Used:  {receipt['gasUsed']}")
        print(f"  Explorer:  https://testnet.arcscan.app/tx/{tx_hash.hex()}")

    except ImportError:
        print("❌ web3.py not installed. Install: uv pip install web3")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
