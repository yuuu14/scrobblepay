# On-Chain Splitter Contract

## Why

Currently, the agent sends multi---transactions to distribute rewards to artists:

```python
for artist in splits:
    send_one_tx(artist.address, artist.amount)  # 25 txs / month
```

Each transaction costs ~25891 gas. For 25 artists, that's ~647275 gas just for distribution.

A splitter contract fixes this:

```solidity
function split(address[] calldata recipients, uint256[] calldata amounts)
    external payable
{
    uint256 total;
    for (uint i = 0; i < recipients.length; i++) {
        total += amounts[i];
    }
    require(msg.value == total, "value != total");
    for (uint i = 0; i < recipients.length; i++) {
        (bool ok,) = recipients[i].call{value: amounts[i]}("");
        require(ok, "transfer failed");
    }
}
```

One transaction deploys the logic; one `split()` call distributes to all recipients. Gas cost drops from N × 25891 to roughly 1 tx + N × ~5000 (transfer overhead).

## Transparency

With the agent sending individual txs, the link "I paid artist X from my wallet" is visible on chain but unstructured. With a contract:

- Anyone can query `getHistory()` and see every monthly distribution
- The formula (plays/total × budget) can be verified on-chain
- Auditors (or other agents) don't need access to the agent's log files

## Decentralization

Right now, if the agent's machine is offline, no payments happen. With the contract:

- Agent computes the split (off-chain)
- Anyone can submit the split data to the contract
- Distribution is guaranteed by the contract execution, not by the agent's uptime

## Architecture

```
Agent (runs monthly)
  │
  ├── fetch scrobbles from Last.fm
  ├── compute per-artist splits
  ├── call splitter.split([addresses], [amounts])
  │       │
  │       ▼
  │   Splitter contract on Arc
  │       │
  │       ├── transfer USDC → artist A
  │       ├── transfer USDC → artist B
  │       └── transfer USDC → ...
  │
  └── done
```

## Next Step

Deploy the contract to Arc Testnet, then update `scrobble_agent.py` to call `split()` instead of sending individual txs.
