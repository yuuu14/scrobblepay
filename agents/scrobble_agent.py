#!/usr/bin/env python3
"""ScrobblePay Agent — AI agent for user-centric nanopayments on Arc.

Usage:
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0 --execute
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from urllib.request import urlopen, Request
from urllib.parse import urlencode

LASTFM_API = "https://ws.audioscrobbler.com/2.0/"


@dataclass
class Scrobble:
    artist: str
    track: str
    album: str
    timestamp: int
    url: str


@dataclass
class ArtistSplit:
    name: str
    play_count: int
    share_pct: float
    amount_dollars: float


class LastFmClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_recent_tracks(self, user: str, limit: int = 200) -> tuple[list[Scrobble], int]:
        params = urlencode({
            "method": "user.getRecentTracks",
            "user": user,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        })
        url = f"{LASTFM_API}?{params}"
        req = Request(url, headers={"User-Agent": "ScrobblePay/1.0"})
        with urlopen(req) as resp:
            data = json.loads(resp.read())

        if "error" in data:
            raise RuntimeError(f"Last.fm API error: {data['message']}")

        tracks_raw = data.get("recenttracks", {}).get("track", [])
        attr = data.get("recenttracks", {}).get("@attr", {})

        tracks = []
        for t in tracks_raw:
            if t.get("@attr", {}).get("nowplaying"):
                continue  # skip currently playing
            tracks.append(Scrobble(
                artist=t["artist"]["#text"],
                track=t["name"],
                album=t["album"]["#text"],
                timestamp=int(t.get("date", {}).get("uts", 0)),
                url=t["url"],
            ))

        return tracks, int(attr.get("total", 0))

    @staticmethod
    def aggregate_by_artist(tracks: list[Scrobble]) -> list[dict]:
        counts: dict[str, dict] = {}
        for t in tracks:
            key = t.artist.lower()
            if key in counts:
                counts[key]["count"] += 1
            else:
                counts[key] = {"name": t.artist, "count": 1, "url": t.url}
        result = sorted(counts.values(), key=lambda x: -x["count"])
        return result


class PaymentSplitter:
    @staticmethod
    def calculate(artists: list[dict], total_usd: float) -> list[ArtistSplit]:
        total_plays = sum(a["count"] for a in artists)
        if total_plays == 0:
            return []

        splits = []
        for a in artists:
            share = (a["count"] / total_plays) * 100
            amount = round((a["count"] / total_plays) * total_usd, 4)
            splits.append(ArtistSplit(
                name=a["name"],
                play_count=a["count"],
                share_pct=round(share, 2),
                amount_dollars=amount,
            ))
        return splits

    @staticmethod
    def format_splits(splits: list[ArtistSplit], total_plays: int, total_scrobbles: int, budget: float) -> str:
        lines = [f"📊 Payment Split (${budget:.2f} total)", "━" * 55]
        for s in splits:
            bar = "█" * max(1, int(s.share_pct / 2))
            lines.append(
                f"  {s.name:<28} {s.play_count:>3} plays "
                f"{s.share_pct:>5.1f}% → ${s.amount_dollars:>6.3f} {bar}"
            )
        lines.append("━" * 55)
        lines.append(f"  Total artists: {len(splits)} | Plays in sample: {total_plays} | Total scrobbles: {total_scrobbles}")
        return "\n".join(lines)


def send_nanopayment(to_address: str, amount_usdc: float, private_key: str | None = None):
    """Send a nanopayment on Arc Testnet via RPC.

    Requires PRIVATE_KEY env var or --private-key argument.
    Uses web3.py for the actual transaction.
    """
    if private_key is None:
        private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        print("   ⚠️  No PRIVATE_KEY set. Skipping real transaction.")
        print("   💡 Set PRIVATE_KEY env var to send real payments.")
        return False

    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network"))
        account = w3.eth.account.from_key(private_key)
        wei_amount = w3.to_wei(amount_usdc, "ether")  # Arc uses 18 decimals

        tx = {
            "to": w3.to_checksum_address(to_address),
            "value": wei_amount,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": 5042002,
        }
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"   ✅ Sent ${amount_usdc:.6f} → {to_address[:10]}...")
        print(f"      Tx: https://testnet.arcscan.app/tx/{tx_hash.hex()}")
        return True
    except ImportError:
        print("   ⚠️  web3.py not installed. Install with: uv pip install web3")
        return False
    except Exception as e:
        print(f"   ❌ Transaction failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="ScrobblePay Agent")
    parser.add_argument("--user", default="elias_fisch", help="Last.fm username")
    parser.add_argument("--budget", type=float, default=5.0, help="Monthly budget in USD")
    parser.add_argument("--execute", action="store_true", help="Actually send payments")
    parser.add_argument("--private-key", help="Private key for Arc Testnet (or set PRIVATE_KEY env)")
    args = parser.parse_args()

    
    api_key = os.environ.get("LASTFM_API_KEY", "") or open(".env").read().split("LASTFM_API_KEY=")[1].split("\n")[0].strip()
    if not api_key:
        print("❌ LASTFM_API_KEY not set. Create .env file or set env var.")
        sys.exit(1)

    print(f"""
🤖 ScrobblePay Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  User:    {args.user}
  Budget:  ${args.budget:.2f}
  Execute: {'✅ ON' if args.execute else '❌ OFF (dry run)'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    # Step 1: Fetch scrobbles
    print("📡 Fetching scrobbles from Last.fm...")
    client = LastFmClient(api_key)
    tracks, total = client.get_recent_tracks(args.user)
    print(f"   Found {len(tracks)} tracks ({total} total scrobbles)")

    if not tracks:
        print("   ⚠️  No scrobbles found. Connect Spotify at https://www.last.fm/settings/applications")
        return

    # Step 2: Aggregate
    artists = client.aggregate_by_artist(tracks)
    print(f"\n📊 {len(artists)} unique artists")

    # Step 3: Calculate splits
    splitter = PaymentSplitter()
    splits = splitter.calculate(artists, args.budget)
    print("\n" + splitter.format_splits(splits, len(tracks), total, args.budget))

    # Step 4: Execute
    if args.execute and splits:
        print("\n💸 Sending nanopayments on Arc Testnet...")
        for s in splits[:5]:  # top 5 for demo
            print(f"\n   → {s.name}: ${s.amount_dollars:.4f}")
            send_nanopayment("0x933a2405f84c224be1ef373ba16e992e1f459682", s.amount_dollars, args.private_key)

    if not args.execute:
        print("\n💡 Run with --execute to send real payments on Arc")
        print("   Set PRIVATE_KEY env var first.")


if __name__ == "__main__":
    main()
