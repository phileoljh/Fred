import sqlite3
import requests
from datetime import datetime
from config import FRED_API_KEY, DB_PATH, INDICATORS
from fetch_data import init_db

def fetch_historical_observations(series_id, units, limit=540):
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

def initialize_database():
    conn = init_db()
    c = conn.cursor()
    fetched_ids = set()
    
    for item in INDICATORS:
        series_id = item['id']
        if series_id in fetched_ids:
            print(f"Skipping duplicate init fetch for {series_id}...")
            continue
            
        freq = item['freq']
        
        # Calculate ~18 months equivalent points
        if freq == "Daily":
            init_limit = 18 * 22 # ~396 trading days
        elif freq == "Weekly":
            init_limit = 18 * 4 # ~72 weeks
        elif freq == "Quarterly":
            init_limit = 6 # 6 quarters = 18 months
        else:
            # Monthly, Priority, Recession, Recovery
            init_limit = 18
            
        print(f"Initializing 18-month history for {series_id} (Limit: {init_limit})...")
        observations = fetch_historical_observations(series_id, item['units'], init_limit)
        if not observations:
            continue
            
        fetched_ids.add(series_id)
            
        updated_at = datetime.now().isoformat()
        for val, date in observations:
            if val != '.': # Ignore missing dots
                c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                             VALUES (?, ?, ?, ?)''', (series_id, val, date, updated_at))
        conn.commit()
    
    # Calculate SOFR - IORB spread historically
    c.execute("SELECT date, value FROM observations WHERE series_id='SOFR' ORDER BY date DESC LIMIT 400")
    sofr_data = {row[0]: row[1] for row in c.fetchall()}
    
    c.execute("SELECT date, value FROM observations WHERE series_id='IORB' ORDER BY date DESC LIMIT 400")
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
    print("Initializing Database with 18 months of history...")
    initialize_database()
    print("Database initialization complete!")
