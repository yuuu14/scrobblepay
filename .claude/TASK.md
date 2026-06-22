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
User's music listening (Spotify)
       ↓ scrobble
  Last.fm API
       ↓
  scrobble_agent.py  ←  🤖 AI Agent (Python, your main code)
       │
       ├── fetch recent scrobbles
       ├── aggregate by artist
       ├── calculate per-artist splits
       └── [--execute] send nanopayments on Arc via web3.py
              ↓
         Arc Testnet RPC → USDC transfer
              ↓
         Artists receive nanopayments
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

### Nanopayment on Arc
- Native token is USDC (18 decimals, use `w3.to_wei(amount, "ether")`)
- Gas paid in USDC
- Chain ID: `5042002`, RPC: `https://rpc.testnet.arc.network`
- Explorer: `https://testnet.arcscan.app`
- Faucet: `https://faucet.circle.com/`

### Wallet Setup
- **For agent**: raw EVM private key (env var `PRIVATE_KEY`)
- **Create wallet**: `uv run --with web3 python -c "from eth_account import Account; acct=Account.create(); print(acct.address); print(acct.key.hex())"`
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

## Roadmap Priorities

| ID | Priority | Summary | Key File | 
|----|----------|---------|----------|
| SCR-001 | 🔴 P0 | Agent holds private key, sends Arc tx autonomously | `agents/scrobble_agent.py` |
| SCR-002 | 🔴 P0 | LLM-powered payment decisions with reasoning trace | `agents/scrobble_agent.py` |
| SCR-003 | 🔴 P0 | Deploy server to public URL | `src/server.ts` |
| SCR-004 | 🟡 P1 | x402 paywalled scrobble endpoint | `src/server.ts` |
| SCR-005 | 🟡 P1 | On-chain splitter contract | `contracts/Splitter.sol` |
| SCR-006 | 🟡 P1 | Scheduled weekly agent runs | cron + agent script |
| SCR-007 | 🟢 P2 | Real-time scrobble → instant payment | `agents/realtime_agent.py` |
| SCR-008 | 🟢 P2 | Payment history dashboard | `public/dashboard.html` |
| SCR-009 | 🟢 P2 | Agent-to-agent autonomous payments | `agents/consumer_agent.py` |

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
