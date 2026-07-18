/**
 * useOracleData.js
 * Fetches live WeatherOracle data from the FastAPI backend server.
 * Falls back to mock data if the server is unreachable.
 */
import { useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const POLL_INTERVAL_MS = 30000;

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

function parseReadings(data) {
  const map = { rainfall: null, windSpeed: null, temperature: null };
  const nameMap = {
    'rainfall_mm':    'rainfall',
    'wind_speed_kmh': 'windSpeed',
    'temperature_c':  'temperature',
  };
  for (const r of data) {
    const key = nameMap[r.metric_name];
    if (key) {
      map[key] = {
        value:      r.value,
        valueFp:    r.value_fp,
        confidence: r.confidence_pct,
        timestamp:  r.timestamp * 1000,
        source:     r.source,
      };
    }
  }
  if (!map.rainfall)    map.rainfall    = { value: 0, confidence: 0, timestamp: Date.now(), source: 'none' };
  if (!map.windSpeed)   map.windSpeed   = { value: 0, confidence: 0, timestamp: Date.now(), source: 'none' };
  if (!map.temperature) map.temperature = { value: 0, confidence: 0, timestamp: Date.now(), source: 'none' };
  return map;
}

export function useOracleData() {
  const [state, setState] = useState(getMockData());

  const fetchAll = useCallback(async () => {
    try {
      const [readingsRes, accuracyRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/readings`),
        fetch(`${API_URL}/accuracy`),
        fetch(`${API_URL}/history?limit=10`),
      ]);

      if (!readingsRes.ok || !accuracyRes.ok) throw new Error('API error');

      const readingsData = await readingsRes.json();
      const accuracyData = await accuracyRes.json();
      const historyData  = historyRes.ok ? await historyRes.json() : [];

      setState({
        readings:      parseReadings(readingsData),
        accuracy:      accuracyData.accuracy_pct,
        totalReadings: accuracyData.total_readings,
        streak:        accuracyData.streak,
        history:       historyData,
        isLive:        true,
        lastFetched:   new Date(),
        error:         null,
      });
    } catch (err) {
      console.warn('API unreachable, using mock data:', err.message);
      setState(prev => ({
        ...getMockData(),
        error: err.message,
        ...(prev.isLive ? {
          readings: prev.readings,
          accuracy: prev.accuracy,
          totalReadings: prev.totalReadings,
          streak: prev.streak,
          history: prev.history,
          isLive: true,
          lastFetched: prev.lastFetched,
        } : {}),
      }));
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return state;
}
