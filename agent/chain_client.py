"""
Chain client for the WeatherOracle agent.

Instead of using pycspr directly (which has version-fragile API surface),
this module shells out to the Odra CLI binary which we know works correctly
on Casper testnet protocol 2.2.2 with the PaymentLimited pricing mode fix
in Odra 2.8.2.

The CLI command that gets run per reading:
    cargo run --bin weather_oracle_new_cli --features livenet --
        contract WeatherOracle submit_reading
        --metric <0|1|2>
        --value_fp <int>
        --timestamp <unix_seconds>
        --source_confidence_bps <int>
        --gas 3cspr

Transaction hash is parsed from stdout and returned.
"""
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass

from .config import AgentConfig

log = logging.getLogger("weather-oracle-agent.chain")

# Regex to extract transaction hash from Odra CLI stdout
# Matches: 💁  INFO : Transaction "abc123..." successfully executed.
TX_HASH_RE = re.compile(r'Transaction\s+"([0-9a-f]{64})"')

# How long to wait for CLI to compile + submit + confirm (seconds)
CLI_TIMEOUT_SECONDS = 180


@dataclass
class ChainClient:
    config: AgentConfig

    @classmethod
    def from_config(cls, config: AgentConfig) -> "ChainClient":
        # Verify the CLI project directory exists
        if not os.path.isdir(config.cli_project_dir):
            raise FileNotFoundError(
                f"Odra CLI project directory not found: {config.cli_project_dir}\n"
                f"Set CLI_PROJECT_DIR in your .env to the contracts/weather_oracle_new path."
            )
        return cls(config=config)

    def submit_reading(
        self,
        metric: int,
        value_fp: int,
        timestamp: int,
        source_confidence_bps: int,
    ) -> str:
        """
        Calls the Odra CLI to submit a reading on-chain.
        Returns the transaction hash as a hex string.
        Raises RuntimeError if submission fails.
        """
        cmd = [
            "cargo", "run",
            "--bin", "weather_oracle_new_cli",
            "--features", "livenet",
            "--",
            "contract", "WeatherOracle", "submit_reading",
            "--metric", str(metric),
            "--value_fp", str(value_fp),
            "--timestamp", str(timestamp),
            "--source_confidence_bps", str(source_confidence_bps),
            "--gas", self.config.gas_per_call,
        ]

        log.info("submitting reading via CLI: metric=%d value_fp=%d conf=%d bps",
                 metric, value_fp, source_confidence_bps)
        log.debug("command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                cwd=self.config.cli_project_dir,
                capture_output=True,
                text=True,
                timeout=CLI_TIMEOUT_SECONDS,
                env={**os.environ, "RUST_BACKTRACE": "0"},
            )
        except subprocess.TimeoutExpired:
            # SSE timeout — transaction may still have landed on-chain.
            # Check the explorer manually if you see this frequently.
            raise RuntimeError(
                f"CLI timed out after {CLI_TIMEOUT_SECONDS}s. "
                "Transaction may still be on-chain — check CSPR.live."
            )

        output = result.stdout + result.stderr
        log.debug("CLI output:\n%s", output)

        # Check for successful execution
        if "successfully executed" in output:
            match = TX_HASH_RE.search(output)
            if match:
                tx_hash = match.group(1)
                log.info("transaction confirmed: %s", tx_hash)
                return tx_hash
            # Succeeded but hash not parsed — extract from LINK line instead
            link_match = re.search(r'/transaction/([0-9a-f]{64})', output)
            if link_match:
                return link_match.group(1)
            return "confirmed-hash-not-parsed"

        # Handle SSE timeout — transaction likely landed, just not confirmed
        if "Timeout waiting for transaction" in output:
            log.warning(
                "SSE timeout (ISP blocks streaming). "
                "Transaction likely landed — check CSPR.live for confirmation."
            )
            # Return a placeholder so the agent doesn't crash and retry
            raise RuntimeError("SSE timeout — transaction unconfirmed but likely on-chain")

        # Actual failure
        raise RuntimeError(
            f"CLI submission failed.\nOutput:\n{output[-500:]}"
        )
