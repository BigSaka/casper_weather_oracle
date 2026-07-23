# WeatherOracle

Autonomous AI agent posting verified weather data on-chain with x402 micropayments and MCP server integration.

## Architecture

- **Agent**: Autonomous Python agent fetching weather via Open-Meteo, scoring confidence
- **Contract**: Casper smart contract storing readings on-chain immutably
- **x402 Payments**: Agents pay per API request with Ed25519 payment proof
- **MCP Server**: Exposes readings via `/mcp/readings`, `/mcp/reading/{metric}`, `/mcp/confidence`
- **Dashboard**: Live readings display with confidence scores and historical data

## Features

- ✅ Real weather data from autonomous agent
- ✅ x402 micropayment protocol for data access
- ✅ Confidence scoring via multi-source validation
- ✅ Model Context Protocol (MCP) server for AI agents
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

## Live Demo

- **Dashboard**: https://casper-weather-oracle-1vc0gln2z-bigsakas-projects.vercel.app/
- **GitHub**: https://github.com/BigSaka/casper_weather_oracle
- **MCP Endpoints**: `http://localhost:9000/mcp/*`

## Buildathon Requirements

- ✅ Working prototype on Casper Testnet with transaction-producing on-chain component
- ✅ Open-source GitHub repo with README
- ✅ Demo video showing agent fetching, scoring, and dashboard
