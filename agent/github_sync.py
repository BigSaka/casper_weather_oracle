import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READINGS_FILE = os.path.join(PROJECT_ROOT, "readings.json")

def save_reading(metric_name, value, confidence_pct):
    """Save reading to JSON file."""
    print(f"DEBUG: Saving to {READINGS_FILE}")
    try:
        with open(READINGS_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"DEBUG: File not found, creating new")
        data = {}
    except Exception as e:
        print(f"DEBUG: Error reading file: {e}")
        data = {}
    
    data[metric_name] = {
        'value': value,
        'confidence_pct': confidence_pct,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        with open(READINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ SUCCESS: Saved {metric_name}={value} to {READINGS_FILE}")
    except Exception as e:
        print(f"❌ ERROR saving to file: {e}")
