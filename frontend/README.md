# WeatherOracle — Dashboard Frontend

React + Vite dashboard for the WeatherOracle agent.

## Setup

```bash
npm install
cp .env.example .env.local   # fill in contract hashes
npm run dev                   # http://localhost:5173
```

## Deploy to Vercel

```bash
npm install -g vercel
vercel
```

## Environment Variables

| Variable | Description |
|---|---|
| `VITE_NODE_URL` | Casper node RPC URL |
| `VITE_ORACLE_CONTRACT_HASH` | WeatherOracle package hash |
| `VITE_REPUTATION_CONTRACT_HASH` | Reputation package hash |
| `VITE_CSPR_CLOUD_KEY` | CSPR.cloud API key (optional) |

## Contract Hashes (Casper Testnet)

- WeatherOracle: `945c3519301534820fd3eb5691462e89f3439783f13ed9f2b1910d2d84664dae`
- Reputation: `5334342652c03b03dcd5d838c58849375543047fd6cd5fe7abcc1811a0f7538f`
