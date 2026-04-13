import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from config import DB_PATH, INDICATORS, CHART_GROUPS

# ==========================================
# 綜合對比分析腳本 (Standalone Comparative Analysis)
# ==========================================

OUTPUT_PATH = 'combined.html'

def get_grouped_data():
    conn = sqlite3.connect(DB_PATH)
    grouped_data = []
    
    # Create a lookup for indicator metadata
    meta = {item['id']: item for item in INDICATORS}
    
    for g_idx, group in enumerate(CHART_GROUPS):
        members = group['members']
        combined_history = {} # date -> {series_id: value}
        
        for mid in members:
            c = conn.cursor()
            # Fetch 24 months to ensure enough overlap
            c.execute("SELECT value, date FROM observations WHERE series_id=? AND date >= date('now', '-24 months') ORDER BY date ASC", (mid,))
            for val, date in c.fetchall():
                if date not in combined_history:
                    combined_history[date] = {}
                try:
                    combined_history[date][mid] = float(val) / meta.get(mid, {}).get('scale', 1)
                except:
                    pass
        
        # Sort dates
        sorted_dates = sorted(combined_history.keys())
        # Filter to 18 points for UI clarity
        if len(sorted_dates) > 18:
            sorted_dates = sorted_dates[-18:]
            
        datasets = []
        colors = ['#58a6ff', '#3fb950', '#a371f7', '#d29922', '#f85149']
        
        for m_idx, mid in enumerate(members):
            data_points = []
            m_meta = meta.get(mid, {})
            name = m_meta.get('name', mid).split(' (')[0] # Get zh name
            
            for d in sorted_dates:
                val = combined_history[d].get(mid)
                data_points.append(val) # Just the y-value for Chart.js flat labels
            
            datasets.append({
                'label': name,
                'data': data_points,
                'borderColor': colors[m_idx % len(colors)],
                'format': m_meta.get('format', '{value}'),
                'decimals': m_meta.get('decimals', 2)
            })
            
        grouped_data.append({
            'name': group['name'],
            'chart_id': f"combined_chart_{g_idx}",
            'datasets': datasets,
            'labels': sorted_dates
        })
        
    conn.close()
    return grouped_data

def generate_combined_html(grouped_data):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FRED 綜合對比分析 (Comparative Analysis)</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg-color: #0d1117;
                --surface-color: #161b22;
                --border-color: #30363d;
                --text-main: #c9d1d9;
                --text-muted: #8b949e;
                --accent: #58a6ff;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            header {{ text-align: center; margin-bottom: 50px; }}
            h1 {{ color: #fff; margin-bottom: 10px; }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(550px, 1fr));
                gap: 25px;
            }}
            .card {{
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 24px;
                display: flex;
                flex-direction: column;
            }}
            .card-title {{
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 20px;
                color: var(--accent);
            }}
            .chart-container {{ min-height: 300px; position: relative; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>FRED 綜合對比分析</h1>
                <p style="color: var(--text-muted);">最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </header>
            <div class="grid">
    """
    
    for g in grouped_data:
        html_template += f"""
                <div class="card">
                    <div class="card-title">{g['name']}</div>
                    <div class="chart-container">
                        <canvas id="{g['chart_id']}"></canvas>
                    </div>
                </div>
        """
        
    html_template += """
            </div>
        </div>
        <script>
            const config = """ + json.dumps(grouped_data) + """;
            config.forEach(group => {
                const ctx = document.getElementById(group.chart_id);
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: group.labels,
                        datasets: group.datasets.map(ds => ({
                            label: ds.label,
                            data: ds.data,
                            borderColor: ds.borderColor,
                            backgroundColor: 'transparent',
                            borderWidth: 3,
                            pointRadius: 2,
                            tension: 0.3,
                            spanGaps: true
                        }))
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        plugins: {
                            legend: { labels: { color: '#c9d1d9' } },
                            tooltip: {
                                backgroundColor: 'rgba(22, 27, 34, 0.9)',
                                bodyColor: '#c9d1d9',
                                callbacks: {
                                    label: function(context) {
                                        const ds = group.datasets[context.datasetIndex];
                                        const val = context.parsed.y;
                                        if (val === null) return ds.label + ': N/A';
                                        return ds.label + ': ' + ds.format.replace('{value}', val.toFixed(ds.decimals));
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { ticks: { color: '#8b949e' }, grid: { display: false } },
                            y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } }
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Combined analysis board generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
    else:
        print("Fetching grouped data...")
        data = get_grouped_data()
        print(f"Generating {OUTPUT_PATH}...")
        generate_combined_html(data)
        print("Done!")
