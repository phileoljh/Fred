import sqlite3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from datetime import datetime
from config import FRED_API_KEY, DB_PATH, INDICATORS
from init_db import init_db, fetch_historical_observations

def update_data():
    conn = init_db()
    c = conn.cursor()
    
    fetched_ids = set()
    
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=1.0,
                    status_forcelist=[ 429, 500, 502, 503, 504 ])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    with session:
        failed_items = []

        def process_item(item):
            series_id = item['id']
            if series_id in fetched_ids:
                print(f"Skipping duplicate fetch for {series_id}...")
                return True
                
            # Fetch Window Limit (API)
            fetch_limit = item.get('points', 30)
            
            print(f"Fetching history for {series_id} (Limit: {fetch_limit})...")
            observations = fetch_historical_observations(series_id, item['units'], fetch_limit, session=session)
            if observations is None:
                return False
            if not observations:
                return True
                
            fetched_ids.add(series_id)
                
            # Query official FRED series last_updated
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
                if val != '.':
                    c.execute('''INSERT INTO observations (series_id, value, date, updated_at) 
                                 VALUES (?, ?, ?, ?)
                                 ON CONFLICT(series_id, date) DO UPDATE SET 
                                 value=excluded.value
                                 WHERE observations.value != excluded.value''', 
                                 (item['id'], val, date, updated_at))
            return True

        for item in INDICATORS:
            if not process_item(item):
                failed_items.append(item)
                
        if failed_items:
            print(f"\n--- Retrying {len(failed_items)} failed items ---")
            for item in failed_items:
                process_item(item)
                
        conn.commit()
    
    # Calculate SOFR - IORB spread historically based on recent intersecting dates
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
                c.execute('''INSERT INTO observations (series_id, value, date, updated_at) 
                             VALUES (?, ?, ?, ?)
                             ON CONFLICT(series_id, date) DO UPDATE SET 
                             value=excluded.value
                             WHERE observations.value != excluded.value''', 
                             ('SOFR_IORB_SPREAD', f"{spread:.4f}", date, updated_at))
            except ValueError:
                pass
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Triggering 18-month initial fetch...")
        from init_db import initialize_database
        initialize_database()
        print("Initial database setup complete.")
    else:
        print("Initiating FRED data sync with history...")
        update_data()
        print("Fetch complete! Data saved to sqlite database.")
