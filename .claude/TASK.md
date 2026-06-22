# ScrobblePay — Project Context for Coding Agents

## Technical Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Agent (main)** | **Python** | 3.14 | 🤖 AI agent logic |
| Server | TypeScript | 5.x / Node 26 | Express REST API + x402 |
| Blockchain | Arc (Circle L1) | Testnet (chain 5042002) | Settlement |
| Stablecoin | USDC | 18 decimals on Arc | Nanopayment unit |
| Web3 | web3.py | 7.x | Arc RPC interactions |
| CLI Tools | Circle CLI, arc-canteen | latest | Wallet, faucet |
| Data Source | Last.fm API | v2.0 | Scrobble history |
| Package mgmt | uv / pip | latest | Python deps |

## Project Architecture

```
User's music listening (Spotify, all month)
       ↓ scrobbles accumulate
  Last.fm API
       ↓
  scrobble_agent.py  ←  🤖 AI Agent (runs end-of-period)
       │
       ├── fetch all recent scrobbles for the period
       ├── aggregate by artist
       ├── calculate per-artist splits (formula: plays/total × budget)
       └── [--execute] send nanopayments on Arc via web3.py
              ↓
         Arc Testnet RPC → sequential USDC transfers (batch)
              ↓
         Each artist gets their fair share — no pool, no middleman
```

## File Map

| Path | Language | Purpose |
|------|----------|---------|
| `agents/scrobble_agent.py` | 🐍 Python | **Core AI Agent** — main file you edit |
| `scripts/send_nanopayment.py` | 🐍 Python | Arc RPC helper for sending payments |
| `pyproject.toml` | — | Python dependencies |
| `src/server.ts` | 🟦 TS | Express server with API + x402 (stable, rarely change) |
| `src/lastfm.ts` | 🟦 TS | Last.fm API client (TS, stable) |
| `src/splitter.ts` | 🟦 TS | Split calculator (TS, stable) |
| `public/index.html` | HTML | Demo page |
| `docs/circle-usage.md` | — | Circle CLI / Arc docs |

## Key Concepts

### Model: Monthly Batch Settlement
- **Not per-play real-time payments.** Scrobbles accumulate all month, then the agent runs once to calculate splits and send all payments in one batch.
- Budget is fixed (e.g. $5/month), split proportionally by actual plays.
- This avoids: (a) running out of budget mid-month, (b) excessive gas costs from thousands of micro-transactions.

### Why Nanopayments
- A single batch of 24 micro-payments ($0.01–$0.50 each) costs ~$0.01 in Arc fees.
- Traditional rails would charge $0.30+/tx, making sub-cent payouts uneconomical.

### Nanopayment on Arc
- Native token is USDC (18 decimals, use `w3.to_wei(amount, "ether")`)
- Gas paid in USDC
- Chain ID: `5042002`, RPC: `https://rpc.testnet.arc.network`
- Explorer: `https://testnet.arcscan.app`
- Faucet: `https://faucet.circle.com/`

### Wallet Setup
- **Self-custodial**: on the first `--execute` run the agent auto-generates a wallet, saves the key to `.env` as `PRIVATE_KEY=`, prints the address + faucet link, and exits for funding. Subsequent runs reuse it.
- **Override (optional)**: set `PRIVATE_KEY` (env var or `--private-key`) to use an existing wallet instead — it is not overwritten.
- **Manual create**: `uv run --with web3 python -c "from eth_account import Account; acct=Account.create(); print(acct.address); print(acct.key.hex())"`
- **Fund wallet**: https://faucet.circle.com/ → paste address → Arc Testnet
- **Check balance**: `python scripts/send_nanopayment.py <address> 0` (fails but shows balance)

### x402 Protocol (TS server only)
- HTTP 402 "Payment Required"
- Circle Gateway middleware: `@circle-fin/x402-batching/server`
- Reference: `circle-agent/server.ts` (external, not part of this project)

## Coding Conventions

| Rule | Detail |
|------|--------|
| **Agent language** | Python 3.14 |
| **Server language** | TypeScript ESM (stable, don't refactor) |
| **Arc amounts** | `w3.to_wei(dollars, "ether")` — Arc uses 18 decimals |
| **Env vars** | `LASTFM_API_KEY`, `PRIVATE_KEY` |
| **Data models** | Pydantic v2 (`BaseModel`) |
| **Error handling** | typed exceptions, catch at main() |
| **Dependencies** | `pip install web3` via uv |

## Status

| ID | Status | Summary |
|----|--------|---------|
| SCR-001 | ✅ Done | Self-custodial wallet + batch send on Arc |
| SCR-002 | ✅ Done | Deploy via ngrok (public URL) |

## Next Up

| Priority | Task | Key File |
|----------|------|----------|
| 🔴 P1 | Scheduled monthly agent run (cron) | cron + `agents/scrobble_agent.py` |
| 🔴 P1 | On-chain splitter contract | `contracts/Splitter.sol` |
| 🟡 P2 | Dashboard UI | `public/dashboard.html` |

## Avoid

- ~~LLM payment decisions~~ — formula is fair, no real problem
- ~~x402 paywalled endpoint~~ — no one pays for listening data
- ~~Agent-to-agent payments~~ — depends on discarded x402

**Core model:** Monthly batch settlement — scrobbles accumulate, then the agent runs end-of-period to calculate fair splits and send all payments in one batch on Arc. Not per-play real-time payments.

## Common Commands

```bash
# Run agent (dry run)
python agents/scrobble_agent.py --user elias_fisch --budget 5.0

# Run agent with real payments
PRIVATE_KEY=*** python agents/scrobble_agent.py --user elias_fisch --budget 5.0 --execute

# Send one nanopayment
PRIVATE_KEY=*** python scripts/send_nanopayment.py 0x933a...9682 0.000001

# Start server
npm start

# Check Arc balance
curl -s -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["<address>","latest"],"id":1}'

# Install web3.py
uv pip install web3
```
