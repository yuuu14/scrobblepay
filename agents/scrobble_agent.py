#!/usr/bin/env python3
"""ScrobblePay Agent — AI agent for user-centric nanopayments on Arc.

Usage:
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0 --execute
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional
from urllib.request import Request, urlopen
from urllib.parse import urlencode

import typer

app = typer.Typer()
LASTFM_API = "https://ws.audioscrobbler.com/2.0/"


@dataclass
class Scrobble:
    artist: str
    track: str
    album: str
    timestamp: int = 0
    url: str = ""


@dataclass
class ArtistSplit:
    name: str
    play_count: int
    share_pct: float
    amount_dollars: float


class LastFmClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_recent_tracks(self, user: str, limit: int = 200):
        params = urlencode({
            "method": "user.getRecentTracks",
            "user": user,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        })
        req = Request(f"{LASTFM_API}?{params}", headers={"User-Agent": "ScrobblePay/1.0"})
        with urlopen(req) as resp:
            data = json.loads(resp.read())

        if "error" in data:
            raise RuntimeError(f"Last.fm API error: {data['message']}")

        tracks_raw = data.get("recenttracks", {}).get("track", [])
        attr = data.get("recenttracks", {}).get("@attr", {})

        tracks = [
            Scrobble(
                artist=t["artist"]["#text"],
                track=t["name"],
                album=t["album"]["#text"],
                timestamp=int(t.get("date", {}).get("uts", 0)),
                url=t["url"],
            )
            for t in tracks_raw
            if not t.get("@attr", {}).get("nowplaying")
        ]
        return tracks, int(attr.get("total", 0))

    @staticmethod
    def aggregate(tracks: list[Scrobble]):
        counts: dict[str, dict] = {}
        for t in tracks:
            key = t.artist.lower()
            if key in counts:
                counts[key]["count"] += 1
            else:
                counts[key] = {"name": t.artist, "count": 1}
        return sorted(counts.values(), key=lambda x: -x["count"])


def calculate_splits(artists: list[dict], total_usd: float) -> list[ArtistSplit]:
    total = sum(a["count"] for a in artists)
    if total == 0:
        return []
    return [
        ArtistSplit(
            name=a["name"],
            play_count=a["count"],
            share_pct=round(a["count"] / total * 100, 2),
            amount_dollars=round(a["count"] / total * total_usd, 4),
        )
        for a in artists
    ]


def format_splits(splits: list[ArtistSplit], plays: int, scrobbles: int, budget: float) -> str:
    lines = [f"📊 Payment Split (${budget:.2f} total)", "━" * 55]
    for s in splits:
        bar = "█" * max(1, int(s.share_pct / 2))
        lines.append(f"  {s.name:<28} {s.play_count:>3} plays {s.share_pct:>5.1f}% → ${s.amount_dollars:>6.3f} {bar}")
    lines += ["━" * 55, f"  Total artists: {len(splits)} | Sample: {plays} | Total: {scrobbles}"]
    return "\n".join(lines)


async def send_payment(to_address: str, amount_usdc: float, private_key: Optional[str]) -> Optional[str]:
    """Send one nanopayment. Uses web3.py — runs asynchronously via executor."""
    if not private_key:
        return None

    loop = asyncio.get_running_loop()

    def _send():
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network"))
            acct = w3.eth.account.from_key(private_key)
            wei = w3.to_wei(amount_usdc, "ether")
            tx = {
                "to": w3.to_checksum_address(to_address),
                "value": wei,
                "gas": 21000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": 5042002,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return tx_hash.hex() if receipt["status"] == 1 else None
        except Exception as e:
            return f"error: {e}"

    return await loop.run_in_executor(None, _send)


def load_api_key() -> str:
    """Load Last.fm API key from env var or .env file."""
    key = os.environ.get("LASTFM_API_KEY")
    if key:
        return key
    try:
        for line in open(".env"):
            if line.startswith("LASTFM_API_KEY="):
                return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    typer.echo("❌ LASTFM_API_KEY not set. Set env var or create .env file.", err=True)
    raise typer.Exit(1)


@app.command()
def run(
    user: str = typer.Option("elias_fisch", "--user", "-u", help="Last.fm username"),
    budget: float = typer.Option(5.0, "--budget", "-b", help="Monthly budget in USD"),
    execute: bool = typer.Option(False, "--execute", "-x", help="Actually send payments on Arc"),
    private_key: Optional[str] = typer.Option(None, "--private-key", "-k", help="Arc wallet private key"),
    to_address: str = typer.Option(
        "0x933a2405f84c224be1ef373ba16e992e1f459682",
        "--to", help="Recipient address for payments",
    ),
    max_payments: int = typer.Option(5, "--max", help="Max artists to pay (0 = all)"),
):
    """🤖 ScrobblePay Agent: fetch scrobbles, calculate splits, send nanopayments."""
    api_key = load_api_key()
    pk = private_key or os.environ.get("PRIVATE_KEY")

    typer.echo(f"""
🤖 ScrobblePay Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  User:    {user}
  Budget:  ${budget:.2f}
  Execute: {'✅ ON' if execute else '❌ OFF (dry run)'}
  Wallet:  {'✅ configured' if pk else '❌ no key'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    # Step 1: Fetch
    typer.echo("📡 Fetching scrobbles...")
    client = LastFmClient(api_key)
    tracks, total = client.get_recent_tracks(user)
    typer.echo(f"   {len(tracks)} tracks ({total} total)")

    if not tracks:
        typer.echo("   ⚠️  No scrobbles. Connect Spotify at https://www.last.fm/settings/applications")
        raise typer.Exit()

    # Step 2: Aggregate + split
    artists = client.aggregate(tracks)
    splits = calculate_splits(artists, budget)
    typer.echo(f"\n📊 {len(artists)} unique artists\n")
    typer.echo(format_splits(splits, len(tracks), total, budget))

    # Step 3: Execute (async)
    if execute and splits and pk:
        limit = max_payments if max_payments > 0 else len(splits)
        targets = splits[:limit]

        typer.echo(f"\n💸 Sending {len(targets)} nanopayments on Arc...")

        async def pay_all():
            results = await asyncio.gather(*[
                send_payment(to_address, s.amount_dollars, pk)
                for s in targets
            ], return_exceptions=True)

            for s, result in zip(targets, results):
                if isinstance(result, str) and result.startswith("0x"):
                    typer.echo(f"   ✅ {s.name:<22} ${s.amount_dollars:.4f} → {result[:10]}...")
                elif result is None:
                    typer.echo(f"   ⚠️  {s.name:<22} ${s.amount_dollars:.4f} → skipped (no key)")
                else:
                    typer.echo(f"   ❌ {s.name:<22} ${s.amount_dollars:.4f} → {result}")

        asyncio.run(pay_all())
    elif not execute:
        typer.echo("\n💡 Pass --execute (-x) to send real payments on Arc")
        typer.echo("   Set PRIVATE_KEY env var for the source wallet.")

    typer.echo("\n✅ Done!")


if __name__ == "__main__":
    app()
