import sqlite3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
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

def update_fear_greed(conn, days_back=30, session=None):
    """
    Fetch Fear & Greed Index from CNN internal API for a given number of days
    and write/update the records in the SQLite database.
    
    Args:
        conn (sqlite3.Connection): SQLite connection object.
        days_back (int): Number of days to look back. Default is 30.
        session (requests.Session): Optional requests session for retry mechanisms.
    """
    c = conn.cursor()
    today = datetime.now()
    start_date = today - timedelta(days=days_back)
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    print(f"=== Syncing Fear & Greed Index ===")
    print(f"Current time: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Start date (back {days_back} days): {start_date_str}")
    
    url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start_date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    requester = session or requests
    try:
        response = requester.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Error: Failed to fetch data from CNN API. Status code: {response.status_code}")
            return False
            
        data = response.json()
        fng_historical = data.get("fear_and_greed_historical")
        
        if not fng_historical or not isinstance(fng_historical.get("data"), list):
            print("Error: Could not find 'fear_and_greed_historical' data points in JSON response.")
            return False
            
        points = fng_historical["data"]
        updated_at = datetime.now().isoformat()
        db_success = 0
        
        for pt in points:
            ts = pt.get("x")
            score = pt.get("y")
            if ts is not None and score is not None:
                date_str = datetime.fromtimestamp(ts / 1000.0).strftime("%Y-%m-%d")
                score_val = f"{float(score):.2f}"
                c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                             VALUES (?, ?, ?, ?)''', ('FEAR_GREED_INDEX', score_val, date_str, updated_at))
                db_success += 1
                
        conn.commit()
        print(f"Successfully wrote/updated database observations count: {db_success}")
        return True
    except Exception as e:
        print(f"Exception occurred while fetching history: {e}")
        return False

def initialize_database():
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
                
    # Calculate Federal Interest to Receipts ratio historically
    c.execute("SELECT date, value FROM observations WHERE series_id='A091RC1Q027SBEA' ORDER BY date DESC LIMIT 400")
    interest_data = {row[0]: row[1] for row in c.fetchall()}
    
    c.execute("SELECT date, value FROM observations WHERE series_id='FGRECPT' ORDER BY date DESC LIMIT 400")
    receipts_data = {row[0]: row[1] for row in c.fetchall()}
    
    for date in interest_data:
        if date in receipts_data:
            try:
                i_val = float(interest_data[date])
                r_val = float(receipts_data[date])
                if r_val != 0:
                    ratio = (i_val / r_val) * 100
                    c.execute('''INSERT OR REPLACE INTO observations (series_id, value, date, updated_at) 
                                 VALUES (?, ?, ?, ?)''', ('FED_INTEREST_TO_RECEIPTS_RATIO', f"{ratio:.4f}", date, updated_at))
            except ValueError:
                pass
                
    conn.commit()
    
    # 初始化載入 600 天的貪婪指數歷史數據以與圖表完全對齊
    print("Initializing Fear & Greed Index history (Limit: 600 days)...")
    update_fear_greed(conn, days_back=600, session=session)
    
    conn.close()


if __name__ == "__main__":
    print("Initializing Database with 18 months of history...")
    initialize_database()
    print("Database initialization complete!")
