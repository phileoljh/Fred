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

def fetch_historical_observations(series_id, units, limit=540, session=None):
    if not FRED_API_KEY or FRED_API_KEY == 'your_fred_api_key_here':
        print(f"Skipping API fetch for {series_id}: No valid API key provided.")
        return []
    
    requester = session or requests
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': limit,
        'sort_order': 'desc',
        'units': units
    }
    try:
        response = requester.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if 'observations' in data:
            return [(obs['value'], obs['date']) for obs in data['observations']]
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return None
    return []

def initialize_database():
    conn = init_db()
    c = conn.cursor()
    fetched_ids = set()
    
    with requests.Session() as session:
        failed_items = []

        def process_item(item):
            series_id = item['id']
            if series_id in fetched_ids:
                print(f"Skipping duplicate init fetch for {series_id}...")
                return True
                
            # Base time param: how many months of history to initialize
            period = 18
            
            # Calculate how many data points cover 18 months, based on the true publication frequency.
            true_freq = item.get('true_freq', 'monthly')
            if true_freq == 'daily':
                init_limit = int(period * 22)    # ~22 trading days per month
            elif true_freq == 'weekly':
                init_limit = int(period * 4.345) # ~4.345 weeks per month
            elif true_freq == 'quarterly':
                init_limit = int(period / 3.0)   # 1 quarter every 3 months
            else:                                # monthly (default)
                init_limit = period
            
            print(f"Initializing 18-month history for {series_id} (Limit: {init_limit})...")
            observations = fetch_historical_observations(series_id, item['units'], init_limit, session=session)
            if observations is None:
                return False
            if not observations:
                return True
                
            fetched_ids.add(series_id)
                
            # Query official FRED series last_updated to prevent all indicators from appearing NEW
            series_url = "https://api.stlouisfed.org/fred/series"
            series_params = {
                'series_id': series_id,
                'api_key': FRED_API_KEY,
                'file_type': 'json'
            }
            updated_at = datetime.now().isoformat()
            try:
                r_info = session.get(series_url, params=series_params)
                if r_info.status_code == 200:
                    d_info = r_info.json()
                    if 'seriess' in d_info and len(d_info['seriess']) > 0:
                        updated_at = d_info['seriess'][0].get('last_updated', updated_at)
            except Exception as e:
                print(f"Error fetching metadata for {series_id}: {e}")

            for val, date in observations:
                if val != '.': # Ignore missing dots
                    c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                                 VALUES (?, ?, ?, ?)''', (series_id, val, date, updated_at))
            return True

        for item in INDICATORS:
            if not process_item(item):
                failed_items.append(item)
                
        if failed_items:
            print(f"\n--- Retrying {len(failed_items)} failed items ---")
            for item in failed_items:
                process_item(item)
                
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
