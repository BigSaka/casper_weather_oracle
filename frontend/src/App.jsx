import { useState } from 'react';
import './App.css';
import { useOracleData } from './hooks/useOracleData';

const REGIONS = [
  { id: 'miami', name: 'Miami, FL' },
  { id: 'lagos', name: 'Lagos, NG' },
  { id: 'accra', name: 'Accra, GH' },
];

export default function App() {
  const [currentTab, setCurrentTab] = useState('overview');
  const [selectedRegion, setSelectedRegion] = useState('miami');
  const data = useOracleData();

  return (
    <div className="app">
      <header className="header">
        <div className="logo-section">
          <div className="logo">◎</div>
          <div className="title">WeatherOracle</div>
          <div className="subtitle">CASPER NETWORK</div>
        </div>
        <div className="nav-tabs">
          <button className={`tab ${currentTab === 'overview' ? 'active' : ''}`} onClick={() => setCurrentTab('overview')}>
            Overview
          </button>
          <button className={`tab ${currentTab === 'readings' ? 'active' : ''}`} onClick={() => setCurrentTab('readings')}>
            Live readings
          </button>
          <button className={`tab ${currentTab === 'how' ? 'active' : ''}`} onClick={() => setCurrentTab('how')}>
            How it works
          </button>
          <button className={`tab ${currentTab === 'chain' ? 'active' : ''}`} onClick={() => setCurrentTab('chain')}>
            On-chain
          </button>
        </div>
        <div className="agent-status">
          {data.isLive ? (
            <span className="status-dot live"></span>
          ) : (
            <span className="status-dot"></span>
          )}
          Agent active
        </div>
        <a href="https://github.com/BigSaka/casper_weather_oracle" className="github-link">
          GitHub
        </a>
      </header>

      <main className="main">
        {currentTab === 'overview' && (
          <div className="overview">
            <h1>REAL-WORLD<br />DATA<br />ON-CHAIN.</h1>
            <p>
              An autonomous AI agent fetches verified climate readings, scores
              its own confidence, and writes tamper-proof data to Casper
              Network — earning a public trust score auditable by anyone.
            </p>
            <button className="btn-primary" onClick={() => setCurrentTab('readings')}>Live readings ↓</button>
            <div className="trust-score">
              <div className="score-label">TRUST SCORE</div>
              <div className="score-number">{data.accuracy}%</div>
              <div className="score-subtitle">across {data.totalReadings} verified readings</div>
            </div>
          </div>
        )}

        {currentTab === 'readings' && (
          <div className="readings-page">
            <h2>02 / LIVE READINGS</h2>
            
            {/* Region Selector */}
            <div className="region-selector">
              <div className="region-label">MONITORING REGION:</div>
              <div className="region-buttons">
                {REGIONS.map(region => (
                  <button
                    key={region.id}
                    className={`region-btn ${selectedRegion === region.id ? 'active' : ''}`}
                    onClick={() => setSelectedRegion(region.id)}
                  >
                    {region.name}
                  </button>
                ))}
              </div>
            </div>

            <h3>Current readings</h3>
            <div className="last-posted">Last posted {data.lastFetched ? Math.round((Date.now() - data.lastFetched.getTime()) / 1000) + 's' : '—'} ago</div>

            <div className="readings-grid">
              <div className="reading-card">
                <div className="reading-label">RAINFALL</div>
                <div className="reading-confidence">{data.readings.rainfall.confidence}% CONF</div>
                <div className="reading-value">{data.readings.rainfall.value.toFixed(1)}<span className="unit">mm</span></div>
                <div className="reading-chart">
                  <svg viewBox="0 0 100 30" preserveAspectRatio="none">
                    <polyline points="0,20 10,18 20,22 30,15 40,18 50,20 60,15 70,18 80,20 90,16 100,18" fill="none" stroke="#6366f1" strokeWidth="1.5" />
                  </svg>
                </div>
                <div className="reading-trigger">Trigger: 50mm</div>
                <div className="reading-pct">{Math.round(data.readings.rainfall.value / 50 * 100)}%</div>
              </div>

              <div className="reading-card">
                <div className="reading-label">WIND SPEED</div>
                <div className="reading-confidence">{data.readings.windSpeed.confidence}% CONF</div>
                <div className="reading-value">{data.readings.windSpeed.value.toFixed(1)}<span className="unit">km/h</span></div>
                <div className="reading-chart">
                  <svg viewBox="0 0 100 30" preserveAspectRatio="none">
                    <polyline points="0,18 10,15 20,18 30,12 40,15 50,18 60,12 70,15 80,18 90,14 100,16" fill="none" stroke="#8b8b8b" strokeWidth="1.5" />
                  </svg>
                </div>
                <div className="reading-trigger">Trigger: 80km/h</div>
                <div className="reading-pct">{Math.round(data.readings.windSpeed.value / 80 * 100)}%</div>
              </div>

              <div className="reading-card">
                <div className="reading-label">TEMPERATURE</div>
                <div className="reading-confidence">{data.readings.temperature.confidence}% CONF</div>
                <div className="reading-value">{data.readings.temperature.value.toFixed(1)}<span className="unit">°C</span></div>
                <div className="reading-chart">
                  <svg viewBox="0 0 100 30" preserveAspectRatio="none">
                    <polyline points="0,15 10,13 20,15 30,10 40,12 50,15 60,8 70,12 80,15 90,20 100,18" fill="none" stroke="#f97316" strokeWidth="1.5" />
                  </svg>
                </div>
                <div className="reading-trigger">Trigger: 40°C</div>
                <div className="reading-pct">{Math.round(data.readings.temperature.value / 40 * 100)}%</div>
              </div>
            </div>

            <div className="history">
              <h4>READING HISTORY · LAST 6 HOURS</h4>
              <table>
                <thead>
                  <tr>
                    <th>TIME</th>
                    <th>RAINFALL (mm)</th>
                    <th>WIND (km/h)</th>
                    <th>TEMP (°C)</th>
                    <th>CONFIDENCE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>10:00</td><td>22.7</td><td>58.9</td><td>35.1</td><td>96%</td></tr>
                  <tr><td>11:00</td><td>44.1</td><td>74.3</td><td>38.9</td><td>89%</td></tr>
                  <tr><td>12:00</td><td>31.5</td><td>61.8</td><td>36.2</td><td>92%</td></tr>
                  <tr><td>13:00</td><td>9.8</td><td>52.1</td><td>33.8</td><td>91%</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {currentTab === 'how' && (
          <div className="how-section">
            <h2>How it works</h2>
            <p>WeatherOracle is an autonomous agent that continuously monitors weather data, evaluates confidence in readings by comparing multiple sources, and writes verified data to the Casper blockchain with cryptographic proof.</p>
          </div>
        )}

        {currentTab === 'chain' && (
          <div className="chain-section">
            <h2>On-chain</h2>
            <p>All readings are permanently recorded on Casper testnet. Each reading includes the agent's confidence score, source data, and timestamp.</p>
          </div>
        )}
      </main>
    </div>
  );
}
