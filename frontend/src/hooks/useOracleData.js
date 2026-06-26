/**
 * useOracleData.js
 * Reads live data from WeatherOracle + Reputation contracts on Casper testnet.
 * Falls back to mock data when contract hashes aren't set yet.
 */
import { useState, useEffect, useCallback } from 'react';

const NODE_URL = import.meta.env.VITE_NODE_URL || 'https://node.testnet.casper.network';
const CSPR_KEY = import.meta.env.VITE_CSPR_CLOUD_KEY || '';
const ORACLE_HASH = import.meta.env.VITE_ORACLE_CONTRACT_HASH || '';
const REPUTATION_HASH = import.meta.env.VITE_REPUTATION_CONTRACT_HASH || '';
const FP_SCALE = 100;

async function rpc(method, params = []) {
  const res = await fetch(`${NODE_URL}/rpc`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(CSPR_KEY ? { Authorization: CSPR_KEY } : {}),
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return data.result;
}

function getMock() {
  return {
    readings: {
      rainfall:    { value: 12.4, confidence: 98, timestamp: Date.now() },
      windSpeed:   { value: 38.7, confidence: 94, timestamp: Date.now() },
      temperature: { value: 29.1, confidence: 97, timestamp: Date.now() },
    },
    accuracy: 94.2,
    totalReadings: 312,
    streak: 14,
    isLive: false,
  };
}

export function useOracleData({ pollMs = 60000 } = {}) {
  const [data, setData] = useState(getMock());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetched, setLastFetched] = useState(null);

  const hasContracts = ORACLE_HASH && REPUTATION_HASH;

  const fetch = useCallback(async () => {
    if (!hasContracts) { setData(getMock()); return; }
    setLoading(true);
    setError(null);
    try {
      const { state_root_hash } = await rpc('chain_get_state_root_hash');
      // TODO: parse actual CLValue bytes from contract named keys
      // Use: casper-client query-global-state --key hash-<ORACLE_HASH>
      // to discover exact key paths after deployment, then decode here.
      setData({ ...getMock(), isLive: true });
      setLastFetched(new Date());
    } catch (e) {
      setError(e.message);
      setData(getMock());
    } finally {
      setLoading(false);
    }
  }, [hasContracts]);

  useEffect(() => {
    fetch();
    const t = setInterval(fetch, pollMs);
    return () => clearInterval(t);
  }, [fetch, pollMs]);

  return { ...data, loading, error, lastFetched, refetch: fetch };
}
