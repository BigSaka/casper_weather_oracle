#!/usr/bin/env bash
# Sets up the Python virtual environment and installs agent dependencies.
# Run from the project root: ./scripts/setup.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing agent dependencies..."
pip install --upgrade pip -q
pip install -r agent/requirements.txt -q

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "  -> fill in CASPER_NODE_URL, ORACLE_CONTRACT_HASH, AGENT_SECRET_KEY_PATH, etc."
fi

mkdir -p keys

echo ""
echo "Done. Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. edit .env with your contract hash and weather API keys"
echo "  3. casper-client keygen ./keys   (generates agent_secret_key.pem)"
echo "  4. python -m agent.run_agent"
echo ""
echo "For the contracts side (requires Rust toolchain, not installed by this script):"
echo "  cd contracts/weather_oracle && cargo install cargo-odra --locked && cargo odra test"
