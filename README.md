# Weather oracle agent — Casper Agentic Buildathon 2026

A trust-minimized RWA oracle: an autonomous agent tracks rainfall, wind
speed, and temperature for a region, posts readings on-chain to the Casper
testnet, and earns a public, verifiable accuracy score over time as those
readings are checked against ground truth. The accuracy score is the
trust signal a parametric insurance product (or any downstream consumer)
would build on.

## Why this exists

Global commodity and weather oracles are common; what's missing is a
small, auditable, fully transparent example of the core primitive — an
agent that fetches real-world data, scores its own confidence, signs a
transaction, and is graded in public afterward. This repo is that
primitive, built for the qualification round's "RWA Oracle Agent"
archetype.

## Quickstart in VS Code

1. Unzip and open the `casper-weather-oracle/` folder in VS Code (`File -> Open Folder`).
2. VS Code will prompt to install recommended extensions (Python, rust-analyzer) — accept.
3. Open a terminal in VS Code and run:
   ```bash
   ./scripts/setup.sh
   ```
   This creates `.venv`, installs Python dependencies, and copies `.env.example` to `.env`.
4. Select the interpreter: `Cmd/Ctrl+Shift+P` -> "Python: Select Interpreter" -> `.venv/bin/python` (VS Code usually picks this up automatically from `.vscode/settings.json`).
5. Fill in `.env` (weather API keys, contract hash once deployed, key path).
6. For the contract side, you'll need the Rust toolchain installed separately (not covered by `setup.sh`):
   ```bash
   rustup target add wasm32-unknown-unknown
   cargo install cargo-odra --locked
   cd contracts/weather_oracle && cargo odra test
   ```

## Architecture

```
agent/                  Python agent (off-chain)
  config.py              Region, thresholds, fixed-point scaling
  weather_source.py       Fetches live readings (Open-Meteo by default)
  confidence.py           Scores agreement between sources
  chain_client.py         Signs and submits deploys via pycspr
  run_agent.py             Main scheduler loop
  reconcile.py             Slower job: grades past readings, updates reputation

contracts/weather_oracle/  Odra smart contracts (on-chain)
  src/weather_oracle.rs     Stores readings, fires threshold-trigger events
  src/reputation.rs         Tracks accuracy score from reconciled outcomes
  tests/integration.rs      cargo-odra test suite
```

See the agent loop and contract surface diagrams in `docs/` for the full
data flow.

## How it satisfies the qualification round requirements

- **Working prototype on Casper Testnet with a transaction-producing
  on-chain component**: every scheduler tick that clears the confidence
  bar is a real signed deploy calling `submit_reading` on the deployed
  `WeatherOracle` contract.
- **Open-source GitHub repo with README**: this file.
- **Demo video**: record a run showing (1) the agent fetching and scoring
  a live reading, (2) the resulting deploy hash on a Casper testnet
  explorer, (3) the dashboard showing reading history and accuracy score.

## Setup

### Contracts

```bash
cd contracts/weather_oracle
cargo install cargo-odra --locked
rustup target add wasm32-unknown-unknown
cargo odra test
cargo odra build --backend casper
```

Deploy to testnet with `casper-client put-deploy` using the generated
`.wasm` in `wasm/`, or via Odra's livenet integration — see
`odra.dev/docs/tutorials/deploying-on-casper`. Save the resulting
contract hash into `.env` as `ORACLE_CONTRACT_HASH`.

### Agent

```bash
cd agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in contract hash, key path, etc.
casper-client keygen ./keys  # generates agent_secret_key.pem
python -m agent.run_agent
```

## Known gaps to close before the demo (tracked honestly, not hidden)

- `chain_client.py` flags one open question: confirm the exact `pycspr`
  stored-contract-call constructor name against whatever version `pip`
  resolves — the Casper docs show the CLI flow clearly but the Python
  helper name has shifted across SDK releases.
- `reconcile.py`'s `fetch_official_value` is a stub — needs a real
  archival weather data source wired in before reconciliation can run
  for real (intentionally kept separate from the live agent's source so
  grading is against an independent source, not the same API grading
  itself).
- Secondary cross-check source in `weather_source.py` is currently a
  stub returning `None` (moderate default confidence) — add a second
  free weather API for genuine two-source agreement scoring.

## License

MIT — see LICENSE.
