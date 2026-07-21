import { useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const POLL_INTERVAL_MS = 30000;

// Payment config
const PAYMENT_ADDRESS = '012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8';
const PAYMENT_AMOUNT_MOTES = "1224910000";

function getMockData() {
  return {
    readings: {
      rainfall:    { value: 0.0,  confidence: 95, timestamp: Date.now(), source: 'mock' },
      windSpeed:   { value: 10.7, confidence: 94, timestamp: Date.now(), source: 'mock' },
      temperature: { value: 27.3, confidence: 95, timestamp: Date.now(), source: 'mock' },
    },
    accuracy: 94.2,
    totalReadings: 0,
    streak: 0,
    history: [],
    isLive: false,
    lastFetched: null,
    error: null,
  };
}

export function useOracleData() {
  const [state, setState] = useState(getMockData());
  const [paymentRequired, setPaymentRequired] = useState(false);

  const fetchAllWithPayment = useCallback(async (retryCount = 0) => {
    try {
      // First request: no payment
      let res = await fetch(`${API_URL}/api/readings`);

      // If 402, request payment
      if (res.status === 402) {
        setPaymentRequired(true);
        const paymentReq = await res.json();
        console.log('Payment required:', paymentReq);

        // TODO: In production, sign payment with wallet
        // For MVP, we'll create a mock signature
        const mockSignature = 'mock_ed25519_signature_placeholder';
        const paymentHeader = `casper:${PAYMENT_ADDRESS}:${PAYMENT_AMOUNT_MOTES}:${mockSignature}`;

        // Retry with payment
        res = await fetch(`${API_URL}/api/readings`, {
          headers: {
            'X-Payment': paymentHeader,
          },
        });

        if (!res.ok) throw new Error('Payment verification failed');
        setPaymentRequired(false);
      }

      if (!res.ok) throw new Error('API error');

      const readingsData = await res.json();

      setState({
        readings: {
          rainfall: {
            value: readingsData.rainfall_mm.value,
            confidence: readingsData.rainfall_mm.confidence_pct,
            timestamp: Date.now(),
            source: readingsData.source,
          },
          windSpeed: {
            value: readingsData.wind_speed_kmh.value,
            confidence: readingsData.wind_speed_kmh.confidence_pct,
            timestamp: Date.now(),
            source: readingsData.source,
          },
          temperature: {
            value: readingsData.temperature_c.value,
            confidence: readingsData.temperature_c.confidence_pct,
            timestamp: Date.now(),
            source: readingsData.source,
          },
        },
        accuracy: 94.2,
        totalReadings: 0,
        streak: 0,
        history: [],
        isLive: true,
        lastFetched: new Date(),
        error: null,
      });
    } catch (err) {
      console.warn('Fetch failed:', err.message);
      setState(prev => ({
        ...prev,
        isLive: false,
        error: err.message,
      }));
    }
  }, []);

  useEffect(() => {
    fetchAllWithPayment();
    const interval = setInterval(() => fetchAllWithPayment(), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAllWithPayment]);

  return { ...state, paymentRequired };
}
