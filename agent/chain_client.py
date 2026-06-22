"""
Thin wrapper around pycspr (the Casper Python SDK) for signing and
submitting `submit_reading` transactions to the WeatherOracle contract.

NOTE ON pycspr VERSIONS: pycspr's API for calling a *stored* contract
entry point (as opposed to a native transfer) has shifted across
releases. The pattern below follows the documented `create_deploy_parameters`
+ `NodeClient` flow from the Casper Python SDK docs. Before your first
real testnet call, run `python -c "import pycspr; help(pycspr)"` against
whatever version `pip` resolves and confirm the exact helper name for a
stored-contract-by-hash deploy (commonly named something like
`create_deploy` with a `StoredContractByHash` session target, or
`create_contract_call` depending on version) — the buildathon mentors'
support channel is also worth a ping here since this is the single most
version-fragile part of the stack.
"""
from dataclasses import dataclass
import pathlib

import pycspr
from pycspr.client import NodeClient, NodeConnectionInfo
from pycspr.types import PrivateKey

from .config import AgentConfig


# Payment amount in motes for a submit_reading call. Start generous for
# testnet (cheap) and tighten once you've measured real gas cost.
SUBMIT_READING_PAYMENT_MOTES = 3_000_000_000  # 3 CSPR


@dataclass
class ChainClient:
    config: AgentConfig
    node_client: NodeClient
    signer: PrivateKey

    @classmethod
    def from_config(cls, config: AgentConfig) -> "ChainClient":
        key_path = pathlib.Path(config.agent_secret_key_path)
        if not key_path.exists():
            raise FileNotFoundError(
                f"Agent secret key not found at {key_path}. Generate one with "
                f"`casper-client keygen ./keys` before running the agent."
            )

        # NodeConnectionInfo expects host/port separately in the documented
        # API; if you're pointed at a full RPC URL instead, parse it here.
        node_client = NodeClient(
            NodeConnectionInfo(host=_extract_host(config.casper_node_url), port_rpc=7777)
        )
        signer = PrivateKey.from_pem_file(str(key_path))
        return cls(config=config, node_client=node_client, signer=signer)

    def submit_reading(
        self,
        metric: int,
        value_fp: int,
        timestamp: int,
        source_confidence_bps: int,
    ) -> str:
        """
        Builds, signs, and sends a deploy calling `submit_reading` on the
        WeatherOracle contract. Returns the deploy hash as a hex string.
        """
        deploy_params = pycspr.create_deploy_parameters(
            account=self.signer,
            chain_name=self.config.chain_name,
        )

        # See module docstring: confirm this constructor name/shape against
        # your installed pycspr version before first real use. Conceptually
        # this needs to produce a deploy whose session is
        # "call entry point `submit_reading` on stored contract
        # `self.config.contract_hash` with the four named+typed args below."
        deploy = pycspr.create_stored_contract_call_deploy(
            params=deploy_params,
            contract_hash=self.config.contract_hash,
            entry_point="submit_reading",
            args={
                "metric": ("u8", metric),
                "value_fp": ("i64", value_fp),
                "timestamp": ("u64", timestamp),
                "source_confidence_bps": ("u32", source_confidence_bps),
            },
            payment_amount=SUBMIT_READING_PAYMENT_MOTES,
        )

        deploy.approve(self.signer)
        self.node_client.deploys.send(deploy)
        return deploy.hash.hex()


def _extract_host(node_url: str) -> str:
    """Strips scheme/path from a full RPC URL, leaving just the host."""
    stripped = node_url.replace("https://", "").replace("http://", "")
    return stripped.split("/")[0]
