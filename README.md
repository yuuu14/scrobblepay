# 🎵 ScrobblePay — AI Agent for User-Centric Nanopayments

Lepton Agents Hackathon · Canteen × Circle

## The Problem

Every music streaming subscription is a quiet admission that the real unit was too small to sell on its own. You pay $10/month, but 99% of that goes to mainstream artists, not the independent musicians you actually listen to.

**User-centric royalties fix this.** Instead of pooling your payment with millions of other users, your budget is split only among the artists you actually listened to. Arc's batched settlement makes it economical to send 24 micro-payments for a total fee of ~$0.01 — something traditional payment rails could never do for sub-cent amounts.

## What This Builds

An AI agent that:

1. **Reads your Last.fm scrobbles** — works with Spotify, Apple Music, Deezer, etc.
2. **Aggregates per-artist play counts** — tracks every artist you listened to this period
3. **Calculates fair splits** — `$budget ÷ your total plays × artist plays`
4. **Batch-settles nanopayments** — sends USDC per artist on Arc, settled in one batch at the end of each period

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Data | Last.fm API | Universal scrobble source |
| Server | Express + TypeScript | x402-ready server |
| Wallet | Circle CLI | Agent-native wallets |
| Settlement | Arc L1 | Sub-second USDC, ~$0.01 fees |
| Payments | Gateway x402 | Per-play HTTP 402 protocol |

## Quick Start

```bash
# Install
npm install

# Run the server
npm start
# → http://localhost:3000

# Run the agent (dry run)
npm run agent -- --user YOUR_LASTFM_USER --budget 5.0

# Run with real payments
npm run agent -- --user YOUR_LASTFM_USER --budget 5.0 --execute
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/scrobbles?user=&budget=` | Scrobble data + split (JSON) |
| `GET /api/scrobbles/text?user=&budget=` | Plain text for AI consumption |
| `GET /api/split?user=&budget=` | Raw payment split |
| `GET /api/health` | Health check |

## The Lepton

> *"The lepton was the smallest coin of the Greek world, a hundredth of a drachma. The name endured two and a half thousand years, until the euro replaced the drachma in 2002. Nanopayments are the lepton reborn for machines: value as small as $0.000001, clearing in under half a second."*

## Links

- [Lepton Agents Hackathon](https://lepton.thecanteenapp.com/)
- [Circle Nanopayments](https://www.circle.com/nanopayments)
- [Arc Network](https://arc.network)
- [Distribution Bootstrap Post](https://thecanteenapp.com/analysis/2026/05/28/distribution-bootstrap-payments-founders.html)

## Roadmap

Tasks designed for coding agents (Claude Code, Codex, etc.). Each has a clear file scope and verifiable success criteria.

**Core model: monthly batch settlement.** Scrobbles accumulate, then the agent runs end-of-period to calculate fair splits and send all payments in one batch on Arc.

### P0 — Shipable Demo (before submission)

| ID | Task | Files | Success Criteria | Depends On |
|----|------|-------|-----------------|------------|
| `SCR-001` | **Self-custodial wallet + batch send** — agent generates its own wallet, manages nonces, sends sequential EIP-1559 transactions on Arc | `agents/scrobble_agent.py` | `python agents/scrobble_agent.py -u elias_fisch -b 5.0 -x` sends real Arc txs ✅ | — |
| `SCR-002` | **LLM-powered payment decisions** — the agent uses an LLM (Claude/Codex) to read its scrobble report and decide autonomously how much to send to each artist | `agents/scrobble-agent.ts` | Agent outputs a reasoning trace: "cupcakKe: 8 plays → $1.14" then executes it on-chain | `SCR-001` |
| `SCR-003` | **Deploy demo** — make the server publicly accessible (ngrok, Railway, or Vercel) | `src/server.ts`, `public/index.html` | `curl https://<deployed-url>/api/health` returns 200 | — |

### P1 — Polish & Differentiation

| ID | Task | Files | Success Criteria | Depends On |
|----|------|-------|-----------------|------------|
| `SCR-003` | **x402 paywalled scrobble endpoint** — wrap `/api/scrobbles` with Circle's x402 middleware so other agents must pay to query your listening data | `src/server.ts`, `package.json` | `curl /api/scrobbles` returns 402; `curl` with valid x402 header returns data | — |
| `SCR-004` | **On-chain splitter contract** — deploy a simple Solidity contract on Arc Testnet that accepts USDC and splits to multiple recipients | `contracts/Splitter.sol` | Verified contract on arcscan, test transaction splits 1 USDC to 3 addresses | `SCR-001` |
| `SCR-005` | **Scheduled agent runs** — cron job that runs the agent weekly, sends payments, and posts a summary to Discord | `agents/cron-agent.ts`, `docs/deploy-cron.md` | Agent auto-runs every Monday 09:00, Discord post visible | `SCR-001` |

### P2 — Nice-to-Have

| ID | Task | Files | Success Criteria |
|----|------|-------|-----------------|
| `SCR-006` | **Real-time scrobble webhook** — Last.fm API polling or webhook receiver that triggers instant nanopayments per play | `agents/realtime-agent.ts` | Each new scrobble fires a $0.0001 payment within 5 seconds |
| `SCR-007` | **Dashboard** — a simple UI showing payment history, per-artist totals, and on-chain explorer links | `public/dashboard.html` | Page loads, shows last 7 days of payments with arcscan links |
| `SCR-008` | **Agent-to-agent payments** — another agent instance pays ScrobblePay's x402 endpoint for data, demonstrating autonomous inter-agent commerce | `agents/consumer-agent.ts` | Two agents discover each other, one pays the other for scrobble data |

### Legend

- `P0` = needed for competitive submission
- `P1` = strong differentiation
- `P2` = showcase depth
