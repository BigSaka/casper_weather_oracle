import { useState, useEffect, useRef } from 'react';
import { useOracleData } from './hooks/useOracleData';

// ─── DATA ──────────────────────────────────────────────────────────────────────
const RAIN_HIST  = [22.7, 44.1, 31.5, 9.8, 18.2, 12.4, 15.3];
const WIND_HIST  = [58.9, 74.3, 61.8, 52.1, 45.2, 38.7, 43.2];
const TEMP_HIST  = [35.1, 38.9, 36.2, 33.8, 31.4, 29.1, 32.6];
const HOURS      = ['09:00','10:00','11:00','12:00','13:00','14:00','15:00'];

const TXNS = [
  { hash: 'b53563...2fa62', label: 'submit_reading · rainfall',    age: 'Jun 26 2026', ok: true },
  { hash: '5a646d...2a804', label: 'submit_reading · wind speed',  age: 'Jun 26 2026', ok: true },
  { hash: 'f6fa0a...c15f',  label: 'submit_reading · temperature', age: 'Jun 26 2026', ok: true },
  { hash: '945c35...64dae', label: 'WeatherOracle deploy',         age: 'Jun 26 2026', ok: true },
];

const HISTORY = [
  { time: '10:00', rain: 22.7, wind: 58.9, temp: 35.1, conf: 96 },
  { time: '11:00', rain: 44.1, wind: 74.3, temp: 38.9, conf: 89 },
  { time: '12:00', rain: 31.5, wind: 61.8, temp: 36.2, conf: 92 },
  { time: '13:00', rain: 9.8,  wind: 52.1, temp: 33.8, conf: 97 },
  { time: '14:00', rain: 18.2, wind: 45.2, temp: 31.4, conf: 95 },
  { time: '15:00', rain: 12.4, wind: 38.7, temp: 29.1, conf: 98 },
];

// ─── ICONS ──────────────────────────────────────────────────────────────────────
const GithubIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
  </svg>
);

const ExternalIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
    <path d="M5 2H2C1.4 2 1 2.4 1 3V10C1 10.6 1.4 11 2 11H9C9.6 11 10 10.6 10 10V7M7 1H11M11 1V5M11 1L5 7"
          stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ─── SPARKLINE ──────────────────────────────────────────────────────────────────
function Sparkline({ data, color, width = 240, height = 40 }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const lastX = width;
  const lastY = height - ((data[data.length - 1] - min) / range) * (height - 6) - 3;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round" opacity="0.7"/>
      <circle cx={lastX} cy={lastY} r="3" fill={color}/>
    </svg>
  );
}

// ─── METRIC CARD ────────────────────────────────────────────────────────────────
function MetricCard({ label, value, unit, confidence, sparkData, color, threshold, thresholdLabel }) {
  const pct = Math.min((value / threshold) * 100, 100);
  const confColor = confidence >= 95 ? '#22C55E' : confidence >= 85 ? '#EAB308' : '#F97316';
  return (
    <div style={{
      background: '#111111',
      border: '1px solid #1E1E1E',
      borderRadius: 20,
      padding: '36px 32px 28px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
        <p style={{ fontSize: 11, color: '#555555', letterSpacing: '0.08em' }}>{label}</p>
        <span style={{
          fontSize: 10, padding: '3px 10px',
          background: confidence >= 90 ? '#0D2B0D' : '#2B1500',
          color: confColor,
          borderRadius: 20, letterSpacing: '0.04em', fontFamily: 'var(--font-mono)',
        }}>{confidence}% CONF</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, margin: '16px 0 24px' }}>
        <span className="mono" style={{ fontSize: 54, fontWeight: 500, lineHeight: 1, letterSpacing: '-0.03em', color: '#FFFFFF' }}>
          {value.toFixed(1)}
        </span>
        <span style={{ fontSize: 17, color: '#444444' }}>{unit}</span>
      </div>
      <Sparkline data={sparkData} color={color} width={240} height={40}/>
      <div style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: '#444444' }}>Trigger: {thresholdLabel}</span>
          <span style={{ fontSize: 11, color, fontFamily: 'var(--font-mono)' }}>{pct.toFixed(0)}%</span>
        </div>
        <div style={{ height: 2, background: '#1A1A1A', borderRadius: 1 }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: color, borderRadius: 1,
            transition: 'width 0.8s ease',
          }}/>
        </div>
      </div>
    </div>
  );
}

// ─── MAIN APP ───────────────────────────────────────────────────────────────────
export default function App() {
  const { readings, accuracy, totalReadings, streak, isLive, lastFetched } = useOracleData();
  const timerLabel = lastFetched 
  ? `${Math.floor((Date.now() - lastFetched) / 1000)}s ago`
  : 'waiting...';
  const [scrolled, setScrolled]         = useState(false);
  const [activeSection, setActiveSection] = useState('overview');

  const refs = {
    overview: useRef(null),
    readings: useRef(null),
    how:      useRef(null),
    chain:    useRef(null),
  };

  // Scroll border on nav
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);


  // Intersection observer for active nav section
  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) setActiveSection(e.target.id); });
    }, { threshold: 0.4 });
    Object.values(refs).forEach(r => r.current && observer.observe(r.current));
    return () => observer.disconnect();
  }, []);

  const scrollTo = (id) => {
    refs[id].current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Animated readings
// Live readings from API
const rain = readings.rainfall.value;
const wind = readings.windSpeed.value;
const temp = readings.temperature.value;

  // Nav link
  const NavLink = ({ id, label }) => (
    <button onClick={() => scrollTo(id)} style={{
      background: 'none', border: 'none', cursor: 'pointer',
      fontSize: 13, fontWeight: 500, fontFamily: 'inherit',
      color: activeSection === id ? '#FFFFFF' : '#555555',
      borderBottom: `1px solid ${activeSection === id ? '#FFFFFF' : 'transparent'}`,
      paddingBottom: 2,
      transition: 'color 0.2s, border-color 0.2s',
    }}>{label}</button>
  );

  return (
    <>
      {/* ── NAV ──────────────────────────────────────────────────────────── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        padding: '0 48px',
        height: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: scrolled ? 'rgba(10,10,10,0.94)' : 'transparent',
        borderBottom: `1px solid ${scrolled ? '#1E1E1E' : 'transparent'}`,
        backdropFilter: scrolled ? 'blur(14px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(14px)' : 'none',
        transition: 'background 0.3s, border-color 0.3s, backdrop-filter 0.3s',
      }}>
        {/* Logo — swap src to your actual exported file from Gemini/Claude Design */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img src="/logo.svg" alt="WeatherOracle logo" width={36} height={36}
               style={{ filter: 'invert(1)' }}/>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              WeatherOracle
            </div>
            <div style={{ fontSize: 10, color: '#444444', letterSpacing: '0.06em' }}>
              CASPER NETWORK
            </div>
          </div>
        </div>

        {/* Nav links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <NavLink id="overview" label="Overview"/>
          <NavLink id="readings" label="Live readings"/>
          <NavLink id="how"      label="How it works"/>
          <NavLink id="chain"    label="On-chain"/>
        </div>

        {/* Right side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="live-dot"/>
            <span style={{ fontSize: 12, color: '#555555' }}>Agent active</span>
          </div>
          <a href="https://github.com/BigSaka/casper_weather_oracle"
             target="_blank" rel="noreferrer"
             title="View source on GitHub"
             style={{
               display: 'flex', alignItems: 'center', justifyContent: 'center',
               width: 36, height: 36,
               background: '#1A1A1A', border: '1px solid #2A2A2A', borderRadius: 8,
               color: '#FFFFFF', transition: 'background 0.2s, border-color 0.2s',
             }}
             onMouseEnter={e => { e.currentTarget.style.background = '#222'; e.currentTarget.style.borderColor = '#444'; }}
             onMouseLeave={e => { e.currentTarget.style.background = '#1A1A1A'; e.currentTarget.style.borderColor = '#2A2A2A'; }}
          >
            <GithubIcon/>
          </a>
        </div>
      </nav>

      {/* ── SECTION 1: OVERVIEW ──────────────────────────────────────────── */}
      <section id="overview" ref={refs.overview}
               style={{ padding: '140px 48px 80px', maxWidth: 1200, margin: '0 auto' }}>

        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between',
                      marginBottom: 64, flexWrap: 'wrap', gap: 48 }}>
          <div style={{ maxWidth: 660 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 22 }}>
              <span className="live-dot"/>
              <span style={{ fontSize: 11, color: '#555555', letterSpacing: '0.1em' }}>
                CASPER TESTNET · CONTRACTS DEPLOYED · READINGS ON-CHAIN
              </span>
            </div>
            <h1 style={{
              fontSize: 'clamp(52px, 7vw, 92px)',
              fontWeight: 600, lineHeight: 0.93,
              letterSpacing: '-0.04em', color: '#FFFFFF',
            }}>
              REAL-WORLD<br/>
              <span style={{ color: '#2A2A2A' }}>DATA</span><br/>
              ON-CHAIN.
            </h1>
            <p style={{ fontSize: 15, color: '#555555', marginTop: 28, lineHeight: 1.75, maxWidth: 460 }}>
              An autonomous AI agent fetches verified climate readings, scores
              its own confidence, and writes tamper-proof data to Casper Network
              — earning a public trust score auditable by anyone.
            </p>
            <div style={{ display: 'flex', gap: 12, marginTop: 32 }}>
              <a href="https://github.com/BigSaka/casper_weather_oracle"
                 target="_blank" rel="noreferrer"
                 style={{
                   display: 'flex', alignItems: 'center', gap: 8,
                   padding: '10px 20px',
                   background: '#FFFFFF', color: '#0A0A0A',
                   borderRadius: 8, fontSize: 13, fontWeight: 600,
                   transition: 'opacity 0.2s',
                 }}
                 onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
                 onMouseLeave={e => e.currentTarget.style.opacity = '1'}
              >
                <GithubIcon/> View on GitHub
              </a>
              <button onClick={() => scrollTo('readings')} style={{
                padding: '10px 20px',
                background: 'transparent', color: '#FFFFFF',
                border: '1px solid #2A2A2A', borderRadius: 8,
                fontSize: 13, fontWeight: 500,
                transition: 'border-color 0.2s',
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#555'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#2A2A2A'}
              >
                Live readings ↓
              </button>
            </div>
          </div>

          {/* Trust score card */}
          <div style={{
            background: '#FFFFFF', borderRadius: 20,
            padding: '40px 44px', textAlign: 'center', minWidth: 220, flexShrink: 0,
          }}>
            <p style={{ fontSize: 10, color: '#AAAAAA', letterSpacing: '0.1em', marginBottom: 10 }}>TRUST SCORE</p>
            <p className="mono" style={{
              fontSize: 72, fontWeight: 500,
              color: '#1F293A', lineHeight: 1, letterSpacing: '-0.04em',
            }}>94.2<span style={{ fontSize: 30, color: '#AAAAAA' }}>%</span></p>
            <div style={{ height: 3, background: '#F0F0F0', borderRadius: 2, margin: '18px 0 10px' }}>
              <div style={{ width: '94.2%', height: '100%', background: '#1F293A', borderRadius: 2 }}/>
            </div>
            <p style={{ fontSize: 11, color: '#AAAAAA' }}>across 312 verified readings</p>
          </div>
        </div>

        {/* Stats strip */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 1, background: '#1A1A1A', borderRadius: 16, overflow: 'hidden',
        }}>
          {[
            { label: 'TOTAL READINGS', value: '312',        mono: true  },
            { label: 'ACCURATE',       value: '294',        mono: true  },
            { label: 'STREAK',         value: '14 hits',    mono: false },
            { label: 'REGION',         value: 'Miami, FL',  mono: false },
          ].map(s => (
            <div key={s.label} style={{ background: '#0A0A0A', padding: '28px 32px' }}>
              <p style={{ fontSize: 10, color: '#444444', letterSpacing: '0.1em', marginBottom: 10 }}>{s.label}</p>
              <p className={s.mono ? 'mono' : ''} style={{
                fontSize: 26, fontWeight: 500, color: '#FFFFFF',
                letterSpacing: s.mono ? '-0.02em' : '-0.01em',
              }}>{s.value}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── SECTION 2: LIVE READINGS ─────────────────────────────────────── */}
      <section id="readings" ref={refs.readings}
               style={{ padding: '80px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 40 }}>
          <div>
            <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.1em', marginBottom: 8 }}>02 / LIVE READINGS</p>
            <h2 style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.03em' }}>Current readings</h2>
          </div>
          <span style={{ fontSize: 12, color: '#444444' }}>Last posted {timerLabel}</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          <MetricCard label="RAINFALL"   value={rain} unit="mm" confidence={readings.rainfall.confidence}
                      sparkData={RAIN_HIST} color="#5B9CF6"
                      threshold={50}  thresholdLabel="50mm"/>
          <MetricCard label="WIND SPEED" value={wind} unit="km/h" confidence={readings.windSpeed.confidence}
                      sparkData={WIND_HIST} color="#9CA3AF"
                      threshold={80}  thresholdLabel="80km/h"/>
          <MetricCard label="TEMPERATURE" value={temp} unit="°C"  confidence={readings.temperature.confidence}
                      sparkData={TEMP_HIST} color="#F97316"
                      threshold={40}  thresholdLabel="40°C"/>
        </div>

        {/* History table */}
        <div style={{
          background: '#111111', border: '1px solid #1E1E1E',
          borderRadius: 20, padding: '28px 32px', marginTop: 16,
        }}>
          <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.1em', marginBottom: 20 }}>
            READING HISTORY · LAST 6 HOURS
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr>
                {['TIME','RAINFALL (mm)','WIND (km/h)','TEMP (°C)','CONFIDENCE'].map(h => (
                  <th key={h} style={{
                    fontSize: 10, color: '#333333', letterSpacing: '0.08em',
                    textAlign: 'left', paddingBottom: 12,
                    borderBottom: '1px solid #1A1A1A', fontWeight: 400,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {HISTORY.map((row, i) => (
                <tr key={i}>
                  <td style={{ padding: '14px 0', borderBottom: i < HISTORY.length - 1 ? '1px solid #111' : 'none', color: '#555555', fontSize: 13 }}>{row.time}</td>
                  <td style={{ padding: '14px 0', borderBottom: i < HISTORY.length - 1 ? '1px solid #111' : 'none', color: '#5B9CF6', fontSize: 14 }}>{row.rain}</td>
                  <td style={{ padding: '14px 0', borderBottom: i < HISTORY.length - 1 ? '1px solid #111' : 'none', color: '#9CA3AF', fontSize: 14 }}>{row.wind}</td>
                  <td style={{ padding: '14px 0', borderBottom: i < HISTORY.length - 1 ? '1px solid #111' : 'none', color: '#F97316', fontSize: 14 }}>{row.temp}</td>
                  <td style={{ padding: '14px 0', borderBottom: i < HISTORY.length - 1 ? '1px solid #111' : 'none', fontSize: 14,
                                color: row.conf >= 95 ? '#22C55E' : row.conf >= 90 ? '#EAB308' : '#F97316' }}>
                    {row.conf}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── SECTION 3: HOW IT WORKS ──────────────────────────────────────── */}
      <section id="how" ref={refs.how}
               style={{ padding: '80px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.1em', marginBottom: 8 }}>03 / HOW IT WORKS</p>
          <h2 style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.03em' }}>The agent loop</h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Steps */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {[
              { n: '01', title: 'Fetch', body: 'Pulls live readings from Open-Meteo and a secondary source on an hourly schedule. Both sources must agree within tolerance for the reading to proceed.' },
              { n: '02', title: 'Score confidence', body: 'Cross-checks values from both sources. If agreement falls below 70%, the reading is skipped entirely — better to miss a tick than post bad data.' },
              { n: '03', title: 'Sign & submit', body: 'Agent wallet signs a Casper transaction containing the reading, timestamp, and confidence score, then submits to the WeatherOracle smart contract.' },
            ].map(s => (
              <div key={s.n} style={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: 20, padding: '28px 32px' }}>
                <div style={{ display: 'flex', gap: 20 }}>
                  <span className="mono" style={{ fontSize: 11, color: '#2A2A2A', paddingTop: 3, minWidth: 20 }}>{s.n}</span>
                  <div>
                    <p style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, letterSpacing: '-0.01em' }}>{s.title}</p>
                    <p style={{ fontSize: 14, color: '#555555', lineHeight: 1.7 }}>{s.body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {[
              { n: '04', title: 'Contract stores reading', body: 'WeatherOracle contract stores the reading on-chain and checks it against a configurable threshold. A TriggerFired event is emitted when the threshold is crossed — this is what a parametric insurance payout listens to.' },
              { n: '05', title: 'Grade & update trust score', body: 'A reconciliation job compares posted readings against authoritative ground-truth data. Each comparison updates the Reputation contract, incrementing the agent\'s public accuracy score and streak.' },
            ].map(s => (
              <div key={s.n} style={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: 20, padding: '28px 32px' }}>
                <div style={{ display: 'flex', gap: 20 }}>
                  <span className="mono" style={{ fontSize: 11, color: '#2A2A2A', paddingTop: 3, minWidth: 20 }}>{s.n}</span>
                  <div>
                    <p style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, letterSpacing: '-0.01em' }}>{s.title}</p>
                    <p style={{ fontSize: 14, color: '#555555', lineHeight: 1.7 }}>{s.body}</p>
                  </div>
                </div>
              </div>
            ))}
            {/* Tech stack */}
            <div style={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: 20, padding: '28px 32px' }}>
              <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.08em', marginBottom: 16 }}>BUILT WITH</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {['Casper Network', 'Odra 2.8', 'Rust / WASM', 'Python Agent', 'Open-Meteo', 'pycspr'].map(t => (
                  <span key={t} style={{
                    fontSize: 12, padding: '5px 12px',
                    background: '#1A1A1A', border: '1px solid #2A2A2A',
                    borderRadius: 20, color: '#666666',
                  }}>{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 4: ON-CHAIN ──────────────────────────────────────────── */}
      <section id="chain" ref={refs.chain}
               style={{ padding: '80px 48px 120px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 40 }}>
          <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.1em', marginBottom: 8 }}>04 / ON-CHAIN ACTIVITY</p>
          <h2 style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.03em' }}>Casper testnet</h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Accuracy */}
          <div style={{ background: '#FFFFFF', borderRadius: 20, padding: '44px 44px' }}>
            <p style={{ fontSize: 10, color: '#AAAAAA', letterSpacing: '0.1em', marginBottom: 16 }}>ON-CHAIN ACCURACY SCORE</p>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 20 }}>
              <span className="mono" style={{ fontSize: 80, fontWeight: 500, color: '#1F293A', lineHeight: 1, letterSpacing: '-0.04em' }}>94.2</span>
              <span style={{ fontSize: 28, color: '#CCCCCC' }}>%</span>
            </div>
            <div style={{ height: 3, background: '#F0F0F0', borderRadius: 2, marginBottom: 28 }}>
              <div style={{ width: '94.2%', height: '100%', background: '#1F293A', borderRadius: 2 }}/>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              {[
                { label: 'Accurate', value: '294' },
                { label: 'Missed',   value: '18'  },
                { label: 'Streak',   value: '14'  },
              ].map(s => (
                <div key={s.label}>
                  <p className="mono" style={{ fontSize: 28, fontWeight: 500, color: '#1F293A', letterSpacing: '-0.02em' }}>{s.value}</p>
                  <p style={{ fontSize: 11, color: '#AAAAAA', marginTop: 4 }}>{s.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Transactions */}
          <div style={{ background: '#111111', border: '1px solid #1E1E1E', borderRadius: 20, padding: '32px 32px' }}>
            <p style={{ fontSize: 11, color: '#444444', letterSpacing: '0.1em', marginBottom: 20 }}>RECENT TRANSACTIONS</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {TXNS.map((t, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 16px', background: '#0F0F0F', borderRadius: 10,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                      background: t.ok ? '#22C55E' : '#EAB308',
                    }}/>
                    <div>
                      <p className="mono" style={{ fontSize: 13, color: '#5B9CF6' }}>{t.hash}</p>
                      <p style={{ fontSize: 11, color: '#333333', marginTop: 2 }}>{t.label}</p>
                    </div>
                  </div>
                  <p style={{ fontSize: 11, color: '#333333' }}>{t.age}</p>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #1A1A1A' }}>
              <a href="https://testnet.cspr.live/account/012def50b8112e8974bc49a48a389b92d92b3e48bbfc48ec3cbab97a91bad5c8f8/transactions"
                 target="_blank" rel="noreferrer"
                 style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#5B9CF6', fontWeight: 500 }}>
                View all on CSPR.live <ExternalIcon/>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: '1px solid #1A1A1A', padding: '28px 48px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img src="/logo.svg" alt="" width={20} height={20} style={{ filter: 'invert(1)', opacity: 0.4 }}/>
          <span style={{ fontSize: 12, color: '#333333' }}>WeatherOracle · Casper Agentic Buildathon 2026</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <span style={{ fontSize: 12, color: '#2A2A2A' }}>Odra 2.8 · Python · Open Source</span>
          <a href="https://github.com/BigSaka/casper_weather_oracle"
             target="_blank" rel="noreferrer"
             style={{ color: '#333333', display: 'flex' }} title="GitHub">
            <GithubIcon/>
          </a>
        </div>
      </footer>
    </>
  );
}
