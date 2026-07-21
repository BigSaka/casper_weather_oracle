"""
Submit readings to WeatherOracle Railway backend API.
Called by agent after posting to Casper contract.
"""
import requests
import os
import logging

log = logging.getLogger("weather-oracle-agent.api-submit")

# Use Railway backend URL or localhost for dev
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')


def submit_reading_to_backend(
    metric_name: str,
    value: float,
    confidence_pct: int,
    timestamp: int,
) -> bool:
    """POST reading to Railway backend."""
    try:
        res = requests.post(
            f'{BACKEND_URL}/api/submit-reading',
            json={
                'metric_name': metric_name,
                'value': value,
                'confidence_pct': confidence_pct,
                'timestamp': timestamp,
            },
            timeout=5,
        )
        if res.status_code == 200:
            log.info(f'✅ Submitted {metric_name}={value} to backend')
            return True
        else:
            log.warning(f'Backend submit returned {res.status_code}: {res.text}')
            return False
    except Exception as e:
        log.warning(f'Failed to submit to backend: {e}')
        return False
