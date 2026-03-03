import sqlite3
import requests
from datetime import datetime
from config import FRED_API_KEY, DB_PATH, INDICATORS

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS observations
                 (series_id TEXT, value TEXT, date TEXT, updated_at TEXT, 
                  PRIMARY KEY (series_id, date))''')
    conn.commit()
    return conn

def fetch_historical_observations(series_id, units, limit=30):
    if not FRED_API_KEY or FRED_API_KEY == 'your_fred_api_key_here':
        print(f"Skipping API fetch for {series_id}: No valid API key provided.")
        return []
    
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': limit,
        'sort_order': 'desc',
        'units': units
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'observations' in data:
            return [(obs['value'], obs['date']) for obs in data['observations']]
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
    return []

def update_data():
    conn = init_db()
    c = conn.cursor()
    
    fetched_ids = set()
    
    for item in INDICATORS:
        series_id = item['id']
        if series_id in fetched_ids:
            print(f"Skipping duplicate fetch for {series_id}...")
            continue
            
        print(f"Fetching history for {series_id}...")
        observations = fetch_historical_observations(series_id, item['units'], item['points'])
        if not observations:
            continue
            
        fetched_ids.add(series_id)
            
        updated_at = datetime.now().isoformat()
        
        for val, date in observations:
            if val != '.': # Ignore missing dots
                c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                             VALUES (?, ?, ?, ?)''', (item['id'], val, date, updated_at))
        conn.commit()
    
    # Calculate SOFR - IORB spread historically based on recent intersecting dates
    c.execute("SELECT date, value FROM observations WHERE series_id='SOFR' ORDER BY date DESC LIMIT 30")
    sofr_data = {row[0]: row[1] for row in c.fetchall()}
    
    c.execute("SELECT date, value FROM observations WHERE series_id='IORB' ORDER BY date DESC LIMIT 30")
    iorb_data = {row[0]: row[1] for row in c.fetchall()}
    
    updated_at = datetime.now().isoformat()
    for date in sofr_data:
        if date in iorb_data:
            try:
                s_val = float(sofr_data[date])
                i_val = float(iorb_data[date])
                spread = s_val - i_val
                c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                             VALUES (?, ?, ?, ?)''', ('SOFR_IORB_SPREAD', f"{spread:.4f}", date, updated_at))
            except ValueError:
                pass
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Initiating FRED data sync with history...")
    update_data()
    print("Fetch complete! Data saved to sqlite database.")
