#!/usr/bin/env python3
"""ScrobblePay Agent — AI agent for user-centric nanopayments on Arc.

Usage:
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0
    python agents/scrobble_agent.py --user elias_fisch --budget 5.0 --execute
"""

import asyncio
import json
import os
from typing import Optional
import httpx

import typer
from pydantic import BaseModel

app = typer.Typer()
LASTFM_API = "https://ws.audioscrobbler.com/2.0/"
RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002

import ssl as _ssl
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE


def _web3() -> "Web3":
    from web3 import Web3
    from web3.providers.rpc import HTTPProvider
    import urllib3
    urllib3.disable_warnings()
    return Web3(HTTPProvider(RPC_URL, request_kwargs={"verify": False}))
ENV_FILE = ".env"
FAUCET_URL = "https://faucet.circle.com/"


class Scrobble(BaseModel):
    artist: str
    track: str
    album: str
    timestamp: int = 0
    url: str = ""


class ArtistSplit(BaseModel):
    name: str
    play_count: int
    share_pct: float
    amount_dollars: float


class LastFmClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_recent_tracks(self, user: str, limit: int = 200):
        params = {
            "method": "user.getRecentTracks",
            "user": user,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        resp = httpx.get(LASTFM_API, params=params, timeout=15)
        data = resp.json()

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
    def aggregate(tracks: list[Scrobble]) -> list[dict]:
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
        lines.append(
            f"  {s.name:<28} {s.play_count:>3} plays "
            f"{s.share_pct:>5.1f}% → ${s.amount_dollars:>6.3f} {bar}"
        )
    lines += ["━" * 55, f"  Total artists: {len(splits)} | Sample: {plays} | Total: {scrobbles}"]
    return "\n".join(lines)


async def send_payment(to_address: str, amount_usdc: float, private_key: Optional[str]) -> Optional[str]:
    if not private_key:
        return None

    def _send():
        try:
            from web3 import Web3
            w3 = _web3()
            acct = w3.eth.account.from_key(private_key)
            wei = w3.to_wei(amount_usdc, "ether")
            tx = {
                "to": w3.to_checksum_address(to_address),
                "value": wei,
                "gas": 30000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(acct.address),
                "chainId": CHAIN_ID,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            return tx_hash.hex() if receipt["status"] in (1, "0x1") else None
        except Exception as e:
            return f"error: {e}"

    return await asyncio.get_running_loop().run_in_executor(None, _send)


def _read_env_value(name: str) -> Optional[str]:
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


def load_or_create_wallet(explicit_key: Optional[str]) -> tuple[str, str, bool]:
    """Return (private_key, address, newly_created).

    Precedence: explicit flag/env var → key stored in .env → freshly generated.
    A generated key is persisted to .env; the key itself is never printed.
    """
    from web3 import Web3

    pk = explicit_key or os.environ.get("PRIVATE_KEY") or _read_env_value("PRIVATE_KEY")
    if pk:
        return pk, Web3().eth.account.from_key(pk).address, False

    acct = Web3().eth.account.create()
    pk = acct.key.hex()
    if not pk.startswith("0x"):  # normalize across eth_account versions
        pk = "0x" + pk
    _write_env_value("PRIVATE_KEY", pk)
    return pk, acct.address, True


def get_balance(address: str) -> float:
    from web3 import Web3

    w3 = _web3()
    return float(w3.from_wei(w3.eth.get_balance(Web3.to_checksum_address(address)), "ether"))


def _read_private_key() -> tuple[Optional[str], Optional[str]]:
    """Read private key from env/.env and return (key, address)."""
    pk = os.environ.get("PRIVATE_KEY") or _read_env_value("PRIVATE_KEY")
    if not pk:
        return None, None
    try:
        from web3 import Web3
        acct = Web3().eth.account.from_key(pk)
        return pk, acct.address
    except Exception:
        return None, None


def load_api_key() -> str:
    key = os.environ.get("LASTFM_API_KEY") or _read_env_value("LASTFM_API_KEY")
    if key:
        return key
    typer.echo("❌ LASTFM_API_KEY not set. Set env var or create .env file.", err=True)
    raise typer.Exit(1)


@app.command()
def run(
    show_wallet: bool = typer.Option(False, "--show-wallet", "-w", help="Print agent wallet address and exit"),
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
    api_key = load_api_key()
    pk = private_key or os.environ.get("PRIVATE_KEY")

    if show_wallet:
        pk, address = _read_private_key()
        if not pk:
            typer.echo("❌ No PRIVATE_KEY found. Run --execute once to generate one.", err=True)
            raise typer.Exit(1)
        typer.echo(f"")
        typer.echo(f"🔑 Agent Wallet")
        typer.echo(f"━" * 30)
        typer.echo(f"  Address:  {address}")
        typer.echo(f"  Explorer: https://testnet.arcscan.app/address/{address}")
        typer.echo(f"━" * 30)
        raise typer.Exit() or _read_env_value("PRIVATE_KEY")

    typer.echo(f"""
🤖 ScrobblePay Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  User:    {user}
  Budget:  ${budget:.2f}
  Execute: {'✅ ON' if execute else '❌ OFF (dry run)'}
  Wallet:  {'✅ configured' if pk else '❌ no key'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    typer.echo("📡 Fetching scrobbles...")
    client = LastFmClient(api_key)
    tracks, total = client.get_recent_tracks(user)
    typer.echo(f"   {len(tracks)} tracks ({total} total)")

    if not tracks:
        typer.echo("   ⚠️  No scrobbles. Connect Spotify at https://www.last.fm/settings/applications")
        raise typer.Exit()

    artists = client.aggregate(tracks)
    splits = calculate_splits(artists, budget)
    typer.echo(f"\n📊 {len(artists)} unique artists\n")
    typer.echo(format_splits(splits, len(tracks), total, budget))

    if execute and splits:
        pk, address, created = load_or_create_wallet(private_key)
        if created:
            typer.echo("\n🔑 Generated a new agent wallet (saved to .env):")
            typer.echo(f"   Address: {address}")
            typer.echo(f"   Fund it: {FAUCET_URL}  (Arc Testnet)")
            typer.echo("   Then re-run with --execute to send payments.")
            raise typer.Exit()

        if get_balance(address) == 0:
            typer.echo(f"\n⚠️  Wallet {address} has 0 USDC — fund it: {FAUCET_URL}")
            raise typer.Exit()

        limit = max_payments if max_payments > 0 else len(splits)
        targets = splits[:limit]
        typer.echo(f"\n💸 Sending {len(targets)} nanopayments on Arc...")
        typer.echo(f"   From: {address}")

        async def pay_all():
            """Send payments sequentially with proper nonce management."""
            from web3 import Web3
            w3 = _web3()
            acct = w3.eth.account.from_key(pk)
            base_nonce = w3.eth.get_transaction_count(acct.address)

            for i, s in enumerate(targets):
                wei = w3.to_wei(s.amount_dollars, "ether")
                base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
                tx = {
                    "to": w3.to_checksum_address(to_address),
                    "value": wei,
                    "gas": 30000,
                    "maxFeePerGas": base_fee * 2,
                    "maxPriorityFeePerGas": base_fee // 2,
                    "nonce": base_nonce + i,
                    "chainId": CHAIN_ID,
                    "type": "0x2",
                }
                try:
                    signed = acct.sign_transaction(tx)
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                    if receipt["status"] in (1, "0x1", b"\x01"):
                        typer.echo(f"   ✅ {s.name:<22} ${s.amount_dollars:.4f} → {tx_hash.hex()[:10]}...")
                    else:
                        typer.echo(f"   ❌ {s.name:<22} ${s.amount_dollars:.4f} → failed on chain")
                except Exception as e:
                    typer.echo(f"   ❌ {s.name:<22} ${s.amount_dollars:.4f} → {e}")

        asyncio.run(pay_all())
    elif not execute:
        typer.echo("\n💡 Pass --execute (-x) to send real payments on Arc")
        typer.echo("   The agent auto-generates & funds its own wallet on first --execute run.")

    typer.echo("\n✅ Done!")


if __name__ == "__main__":
    app()
