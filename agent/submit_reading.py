"""
Submit readings to WeatherOracle backend API.
Called by agent after posting to Casper contract.
"""
import requests
import os

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')


def submit_reading(metric_name: str, value: float, confidence_pct: int, timestamp: int) -> bool:
    """POST reading to backend."""
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
            print(f'✅ Submitted {metric_name}={value} to backend')
            return True
        else:
            print(f'❌ Backend submit failed: {res.status_code}')
            return False
    except Exception as e:
        print(f'❌ Submit error: {e}')
        return False
