# ScrobblePay — Project Context for Coding Agents

## Technical Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Runtime | Node.js | v26.2 | Server + scripts |
| Language | TypeScript | 5.x | All source code |
| Server | Express | 5.x | REST API |
| Blockchain | Arc (Circle L1) | Testnet (chain 5042002) | Settlement |
| Stablecoin | USDC | 18 decimals on Arc | Nanopayment unit |
| CLI Tools | Circle CLI, arc-canteen | latest | Wallet, RPC, faucet |
| Data Source | Last.fm API | v2.0 | Scrobble history |

## Project Architecture

```
User's music listening
       ↓ (scrobbles via Spotify → Last.fm)
  scrobble-agent.ts  ←  AI Agent (the core)
       ↓
  GET scrobble data → splitter.ts → per-artist amounts
       ↓
  Circle CLI / Arc RPC → USDC transfer on Arc L1
       ↓
  Artists receive nanopayments
```

## File Map

| Path | Purpose | Key Exports |
|------|---------|-------------|
| `src/lastfm.ts` | Last.fm API client | `LastFmClient` class |
| `src/splitter.ts` | Payment split calculator | `PaymentSplitter`, `PaymentSplit` |
| `src/server.ts` | Express API server | Runs on `:3000` |
| `agents/scrobble-agent.ts` | 🤖 AI Agent | CLI entry point |
| `scripts/send-nanopayment.ts` | Arc RPC payment helper | |
| `public/index.html` | Demo page | |
| `docs/circle-usage.md` | Circle CLI / Arc docs | |

## Key Concepts

### Nanopayment on Arc
- Native token is USDC (18 decimals, not 6 like ERC-20 USDC)
- Gas paid in USDC, not a separate token
- Chain ID: `5042002`, RPC: `https://rpc.testnet.arc.network`
- Explorer: `https://testnet.arcscan.app`
- Faucet: `https://faucet.circle.com/`

### Wallet Setup
- **Circle Agent Wallet**: managed wallet, needs OTP login each session
  - `CIRCLE_ACCEPT_TERMS=1 npx circle wallet login <email> --type agent --init`
  - Does NOT support direct Arc transfers from agent wallets ❌
- **Local wallet**: raw private key, direct Arc RPC calls ✅
  - Generated via Python `eth_account` or any Ethereum tool

### x402 Protocol
- HTTP 402 "Payment Required" — pay-per-request
- Circle Gateway middleware: `@circle-fin/x402-batching/server`
- Buyer signs EIP-712, merchant submits to facilitator
- Reference: `circle-agent/server.ts`

## Coding Conventions

1. **TypeScript ESM** — `"type": "module"` in package.json, use `import`/`export`
2. **No unused dependencies** — keep `package.json` minimal
3. **Async/await** — no raw promises or callbacks
4. **Errors** — throw typed errors, catch at top-level
5. **Testing** — manual for now, `console.log` based

## Roadmap Priorities

Current tasks in priority order (see README.md for full table):

| ID | Priority | Summary | Key File |
|----|----------|---------|----------|
| SCR-001 | 🔴 P0 | Agent holds private key, sends Arc tx autonomously | `agents/scrobble-agent.ts` |
| SCR-002 | 🔴 P0 | LLM-powered payment decisions with reasoning trace | `agents/scrobble-agent.ts` |
| SCR-003 | 🔴 P0 | Deploy server to public URL | `src/server.ts` |
| SCR-004 | 🟡 P1 | x402 paywalled scrobble endpoint | `src/server.ts` |
| SCR-005 | 🟡 P1 | On-chain splitter contract | `contracts/Splitter.sol` |
| SCR-006 | 🟡 P1 | Scheduled weekly agent runs | `agents/cron-agent.ts` |
| SCR-007 | 🟢 P2 | Real-time scrobble → instant payment | `agents/realtime-agent.ts` |
| SCR-008 | 🟢 P2 | Payment history dashboard | `public/dashboard.html` |
| SCR-009 | 🟢 P2 | Agent-to-agent autonomous payments | `agents/consumer-agent.ts` |

## Helpful Commands

```bash
# Run the agent
npm run agent -- --user elias_fisch --budget 5.0

# Run with execution
npm run agent -- --user elias_fisch --budget 5.0 --execute

# Start server
npm start

# Check Arc wallet balance
curl -s -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["<address>","latest"],"id":1}'

# Arc explorer
open https://testnet.arcscan.app/address/<address>
```
