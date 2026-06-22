# 🎵 ScrobblePay — AI Agent for User-Centric Nanopayments

Lepton Agents Hackathon · Canteen × Circle

## The Problem

Every music streaming subscription is a quiet admission that the real unit was too small to sell on its own. You pay $10/month, but 99% of that goes to mainstream artists, not the independent musicians you actually listen to.

**Nanopayments fix this.** Each play can now cost $0.0001, settled in under half a second on Arc for ~$0.01 in USDC fees.

## What This Builds

An AI agent that:

1. **Reads your Last.fm scrobbles** — works with Spotify, Apple Music, Deezer, etc.
2. **Aggregates per-artist play counts** — tracks every artist you listened to
3. **Calculates fair splits** — `$X ÷ your plays × artist plays`
4. **Executes nanopayments** — sends USDC per artist via Circle CLI on Arc L1

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
