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

**Model:** Monthly batch settlement. Scrobbles accumulate, then agent runs at end of period to split a fixed budget proportionally by plays and send all payments on Arc.

Status icons: ✅ completed  🔜 next  💡 idea

### ✅ Completed

| ID | Task | Status |
|----|------|--------|
| `SCR-001` | Self-custodial wallet + batch send — agent generates wallet, manages nonces, sends sequential EIP-1559 txs on Arc | ✅ Live on Arc testnet |
| `SCR-002` | Deploy to public URL — ngrok tunnel with health polling | ✅ `https://craftily-obedient-campfire.ngrok-free.dev` |

### 🔜 Next

| ID | Task | Why |
|----|------|-----|
| `SCR-003` | **Scheduled monthly agent run** — cron job runs agent on the 1st of each month, sends payments, posts summary to Discord | Only missing piece for "set and forget" |
| `SCR-004` | **On-chain splitter contract** — deploy a simple Solidity contract on Arc that accepts USDC and splits to multiple recipients in one tx | Reduces gas from N × 25891 to 1 tx |
| `SCR-005` | **Dashboard** — simple UI showing current month's split, payment history, arcscan links | Better than CLI for demo |

### 💡 Post-Hackathon Ideas

| ID | Idea | Notes |
|----|------|-------|
| `SCR-006` | Agent-to-agent data querying with x402 | If someone builds a service worth paying per-request for, x402 is the right protocol. ScrobblePay itself doesn't need it. |
| `SCR-007` | Real-time scrobble webhook | Per-play nanopayments raise the budget-overrun problem — only makes sense with a replenishable wallet |

### Discarded

| ID | Reason |
|----|--------|
| ~~LLM payment decisions~~ | No real problem to solve — formula (plays/total × budget) is fair, transparent, auditable. "AI for AI's sake". |
| ~~x402 paywalled scrobble endpoint~~ | No one will pay to see someone else's listening data. x402 is a tool for paid APIs, not a feature for ScrobblePay. |
| ~~Agent-to-agent payments~~ | Relies on the discarded x402 endpoint. If x402 doesn't solve a real problem for this project, neither does agent-to-agent. |
