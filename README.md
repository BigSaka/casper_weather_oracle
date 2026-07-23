# Weather Oracle Agent — Casper Agentic Buildathon 2026

A trust-minimized RWA oracle: an autonomous AI agent tracks rainfall, wind speed, and temperature for a region, posts verified readings on-chain to the Casper Network, and earns a public accuracy score over time as those readings are checked against ground truth. The accuracy score is the trust signal a parametric insurance product — or any downstream consumer — can build on.

## Why this exists

Global weather oracles exist, but what's missing is a small, auditable, fully transparent primitive: an agent that fetches real-world data, scores its own confidence, signs a transaction, and is graded in public afterward. This repo is that primitive — built for the Casper Agentic Buildathon 2026.

## How it works

1. The **Python agent** fetches live weather readings (rainfall mm, wind speed km/h, temperature °C) from a public weather API on a scheduled interval
2. It scores its own **confidence** by cross-checking against a secondary source
3. If confidence clears the threshold, it signs and posts the reading on-chain via a **Casper testnet transaction**
4. The **WeatherOracle contract** stores the reading and fires a `TriggerFired` event if a parametric threshold is crossed
5. A slower **reconciliation job** compares posted readings against official ground-truth data and updates the agent's **on-chain accuracy score**
6. A public **dashboard** shows live readings, trigger history, and the agent's trust score

## Architecture

## Buildathon Requirements

- **Working prototype on Casper Testnet with a transaction-producing on-chain component** — every scheduler tick that clears the confidence bar is a real signed deploy calling `submit_reading` on the deployed `WeatherOracle` contract
- **Open-source GitHub repo with README** — this file
- **Demo video** — shows the agent fetching and scoring a live reading, the resulting deploy hash on a Casper testnet explorer, and the dashboard displaying reading history and accuracy score

## Quickstart

### Prerequisites

- Python 3.10+
- Rust + cargo (https://rustup.rs)
- WSL2 or Linux recommended for contract development

### Contracts

```bash
cd contracts/weather_oracle_new
rustup target add wasm32-unknown-unknown
cargo install cargo-odra --locked
cargo odra test
cargo odra build
```

Deploy to testnet using casper-client put-deploy with the generated .wasm files in wasm/. Save the resulting contract hashes into .env.

### Agent

```bash
./scripts/setup.sh
source .venv/bin/activate
casper-client keygen ./keys
python -m agent.run_agent
```

## Smart Contract Surface

**WeatherOracle**
- submit_reading(metric, value_fp, timestamp, confidence_bps) — agent only
- get_latest_reading(metric) — public view
- get_reading_at(index) — public view, for dashboard history
- TriggerFired event — emitted when a reading crosses the parametric threshold

**Reputation**
- record_outcome(reading_index, posted_value_fp, official_value_fp) — reconciler only
- get_accuracy_bps() — public view, returns accuracy as basis points (e.g. 9500 = 95%)
- get_current_streak() — public view

## Tech Stack

- **Casper Network** — smart contract deployment target (testnet)
- **Odra Framework** — Rust smart contract framework for Casper
- **Python** — agent runtime (fetch, score, sign, post)
- **pycspr** — Casper Python SDK for transaction signing
- **Open-Meteo** — free weather API (no key required for basic usage)

## License

MIT
# Updated Tue Jul 21 12:54:41 WAT 2026

## Architecture

- **Agent**: Autonomous Python agent fetching weather via Open-Meteo, scoring confidence
- **Contract**: Casper smart contract storing readings on-chain immutably
- **x402 Payments**: Agents pay per API request with Ed25519 payment proof
- **MCP Server**: Exposes readings via `/mcp/readings`, `/mcp/reading/{metric}`, `/mcp/confidence`
- **Dashboard**: Multi-region UI (Miami, Lagos, Accra) with real confidence scores

## Features

- ✅ Real weather data from autonomous agent
- ✅ x402 micropayment protocol for data access
- ✅ Confidence scoring via multi-source validation
- ✅ Model Context Protocol (MCP) server for AI agents
- ✅ Multi-region support (expandable)
- ✅ On-chain verification with Casper testnet

## Quick Start

```bash
# Start agent
./.venv/bin/python -m agent.run_agent

# Start MCP server
./.venv/bin/python mcp_server.py 9000

# Access readings
curl http://localhost:9000/mcp/readings
```
