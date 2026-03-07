import sqlite3
import json
import os
import sys
from datetime import datetime
from config import DB_PATH, HTML_PATH, AI_HTML_PATH, INDICATORS

def get_data_for_ui():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ui_data = []
    
    # Custom SOFR_IORB_SPREAD indicator info
    spread_info = {
        "id": "SOFR_IORB_SPREAD", 
        "name": "流動性利差 (SOFR - IORB Spread)", 
        "freq": "Daily", 
        "category": "Rates & Spreads",
        "units": "lin",
        "format": "{value}%",
        "points": 30
    }
    all_indicators = INDICATORS.copy()
    all_indicators.insert(3, spread_info) # Insert after SOFR
    
    for idx, item in enumerate(all_indicators):
        try:
            # Query exactly 18 months of history from database context
            c.execute("SELECT value, date FROM observations WHERE series_id=? AND date >= date('now', '-18 months') ORDER BY date DESC", (item['id'],))
            rows = c.fetchall()
        except sqlite3.OperationalError:
            rows = []
        
        history = []
        history_baseline = []
        baseline_display = ""
        display_val = "N/A"
        date_val = "N/A"
        val_float = None
        
        if rows:
            # Most recent for the big card
            latest_val, latest_date = rows[0]
            try:
                val_float = float(latest_val)
                if item['id'] == 'ICSA':
                    display_val = f"{val_float / 1000:.1f}K"
                else:
                    display_val = item['format'].format(value=f"{val_float:.2f}")
            except ValueError:
                display_val = latest_val
            date_val = latest_date
            
            # Format history for chart (oldest to newest)
            for row in reversed(rows):
                try:
                    history.append({'x': row[1], 'y': float(row[0])})
                except:
                    pass
            
            # Calculate baseline (0-axis or 18-mo avg)
            baseline_val = None
            if history:
                y_vals = [h['y'] for h in history]
                min_y, max_y = min(y_vals), max(y_vals)
                
                # Only apply the forced 0.0 baseline to the three specific yield spread indicators 
                # requested by the user. Everything else falls back to the 18-month moving average.
                zero_axis_indicators = ["SOFR_IORB_SPREAD", "T10Y2Y", "T10Y3M"]
                
                if item['id'] in zero_axis_indicators:
                    baseline_val = 0.0
                else:
                    baseline_val = sum(y_vals) / len(y_vals)
                    
            history_baseline = [{'x': h['x'], 'y': baseline_val} for h in history] if baseline_val is not None else []
            
            baseline_display = ""
            if baseline_val is not None:
                if baseline_val == 0.0:
                    baseline_display = "0.00"
                else:
                    if item['id'] == 'ICSA':
                        baseline_display = f"{baseline_val / 1000:.1f}K"
                    else:
                        baseline_display = f"{baseline_val:.2f}"
                baseline_display = item['format'].format(value=baseline_display)
        
        # Split English and Chinese for cleaner UI
        full_name = item['name']
        name_zh = full_name
        name_en = ""
        
        # Determine frequency for label display
        freq_label = item['freq'].lower()
        if freq_label in ["priority", "recession", "recovery"]:
            # Deduce frequency based on points or id
            if item['points'] == 30:
                freq_label = "daily"
            elif item['points'] == 14:
                freq_label = "weekly"
            elif item['points'] == 12:
                freq_label = "monthly"
            elif item['points'] == 4:
                freq_label = "quarterly"

        if " (" in full_name and full_name.endswith(")"):
            parts = full_name.split(" (")
            name_zh = parts[0]
            name_en = parts[1].replace(")", "")
            name_en = f"{name_en} ({freq_label})"
            
        ui_data.append({
            **item, 
            'name_zh': name_zh,
            'name_en': name_en,
            'display_val': display_val, 
            'date': date_val, 
            'raw_val': val_float,
            'history': history,
            'history_baseline': history_baseline,
            'baseline_display_val': baseline_display,
            'chart_id': f"chart_{idx}_{item['id'].replace('-', '_')}"
        })
        
    conn.close()
    return ui_data


def generate_html(data):
    categories = [
        "榮景期指標 (Priority)",
        "衰退期指標 (Recession)",
        "復甦期指標 (Recovery)",
        "Labor Market",
        "Rates & Spreads",
        "Credit Risk",
        "Credit Delinquency",
        "Consumption & Sentiment",
        "Production & Manufacturing",
        "Monetary & Inflation",
        "GDP Output",
        "Investment & Gov",
        "Trade"
    ]
    
    cat_zh = {
        "榮景期指標 (Priority)": "🌟 榮景期指標",
        "衰退期指標 (Recession)": "📉 衰退期指標",
        "復甦期指標 (Recovery)": "🌱 復甦期指標",
        "Labor Market": "就業與勞動市場 (Labor Market)",
        "Rates & Spreads": "殖利率與利差 (Rates & Spreads)",
        "Consumption & Sentiment": "消費與信心 (Consumption & Sentiment)",
        "Production & Manufacturing": "生產與庫存製造 (Production & Manufacturing)",
        "Monetary & Inflation": "貨幣與通膨 (Monetary & Inflation)",
        "GDP Output": "國內生產毛額 (GDP Output)",
        "Investment & Gov": "投資與政府支出 (Investment & Gov)",
        "Credit Risk": "信用風險 (Credit Risk)",
        "Credit Delinquency": "違約率 (Credit Delinquency)",
        "Trade": "進出口貿易 (Trade)"
    }
    
    grouped = {cat: [] for cat in categories}
    
    for item in data:
        cat = item['category']
        grouped[cat].append(item)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FRED 總體經濟數據儀表板 (Macroeconomic Dashboard)</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
        <!-- Include Chart.js -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg-color: #0d1117;
                --surface-color: #161b22;
                --border-color: #30363d;
                --text-main: #c9d1d9;
                --text-muted: #8b949e;
                --accent: #58a6ff;
                --positive: #3fb950;
                --negative: #f85149;
                --card-bg: rgba(22, 27, 34, 0.7);
            }}
            
            body {{
                font-family: 'Inter', 'Noto Sans TC', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 40px 20px;
                line-height: 1.6;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            header {{
                text-align: center;
                margin-bottom: 60px;
            }}
            
            h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                background: -webkit-linear-gradient(45deg, #58a6ff, #a371f7);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            p.subtitle {{
                color: var(--text-muted);
                font-size: 1.1rem;
            }}
            
            .frequency-section {{
                margin-bottom: 60px;
            }}
            
            .frequency-title {{
                font-size: 1.8rem;
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 10px;
                margin-bottom: 30px;
                color: #fff;
            }}
            
            .category-title {{
                font-size: 1.2rem;
                color: var(--accent);
                margin-bottom: 20px;
                margin-top: 40px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                gap: 25px;
            }}
            
            .card {{
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 24px;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}
            
            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 400%;
                height: 3px;
                background: linear-gradient(90deg, #58a6ff, #a371f7, #58a6ff);
                opacity: 0;
                transition: opacity 0.3s ease;
            }}
            
            .card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border-color: var(--accent);
            }}
            
            .card:hover::before {{
                opacity: 1;
                animation: flow 2s linear infinite;
            }}
            
            @keyframes flow {{
                0% {{ transform: translateX(-50%); }}
                100% {{ transform: translateX(0); }}
            }}
            
            .card-header-flex {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
            }}

            .card-title-container {{
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}

            .card-title-zh {{
                font-size: 1.05rem;
                font-weight: 500;
                color: #fff;
                line-height: 1.3;
            }}
            
            .card-title-en {{
                font-size: 0.82rem;
                font-weight: 400;
                color: var(--text-muted);
                line-height: 1.2;
            }}
            
            .card-value-container {{
                display: flex;
                align-items: baseline;
                gap: 10px;
                margin-bottom: 20px;
            }}

            .card-value {{
                font-size: 2.3rem;
                font-weight: 700;
                color: #fff;
            }}
            
            .card-date {{
                font-size: 0.85rem;
                color: var(--text-muted);
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            
            .badge {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 0.75rem;
                background: rgba(139, 148, 158, 0.15);
                color: var(--accent);
                font-weight: 600;
                white-space: nowrap;
                margin-left: 10px;
            }}
            
            .chart-container {{
                flex: 1;
                min-height: 120px;
                width: 100%;
                position: relative;
                margin-top: auto;
            }}

            a {{ text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>FRED 總體經濟數據儀表板</h1>
                <p class="subtitle">追蹤關鍵市場指標與趨勢 (Real-time Macroeconomic Trends)</p>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 10px;">最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </header>
    """

    charts_config_json = []

    for cat in categories:
        items = grouped[cat]
        if not items: continue
        
        html_content += f'<div class="frequency-section"><h2 class="frequency-title">{cat_zh[cat]}</h2>'
        html_content += f'<div class="grid">'
        
        for item in items:
            link = f"https://fred.stlouisfed.org/series/{item['id']}" if item['id'] != 'SOFR_IORB_SPREAD' else '#'
            
            val_color = ""
            if item.get('raw_val') is not None:
                if item['id'] == 'SAHMREALTIME' and item['raw_val'] >= 0.5:
                    val_color = "color: var(--negative);"
            
            if item['history']:
                charts_config_json.append({
                    "id": item['chart_id'],
                    "data": item['history'],
                    "baseline": item['history_baseline'],
                    "is_negative": (item['id'] == 'SAHMREALTIME' and item['raw_val'] >= 0.5)
                })
            
            baseline_html = ""
            if item.get('baseline_display_val'):
                is_zero = item['baseline_display_val'].startswith("0.00") or item['baseline_display_val'] == "0.00%"
                baseline_label = "0 軸" if is_zero else "18月平均"
                baseline_html = f'<div class="baseline-badge" style="font-size: 0.75rem; color: var(--text-muted); margin-left: auto; display: flex; align-items: center; gap: 4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4 4"><line x1="2" y1="12" x2="22" y2="12"></line></svg>{baseline_label} {item["baseline_display_val"]}</div>'

            html_content += f"""
            <a href="{link}" target="_blank" class="card">
                <div class="card-header-flex">
                    <div class="card-title-container">
                        <div class="card-title-zh">{item['name_zh']}</div>
                        <div class="card-title-en">{item['name_en']}</div>
                    </div>
                    <div class="badge">{item['id']}</div>
                </div>
                <div class="card-value-container">
                    <div class="card-value" style="{val_color}">{item['display_val']}</div>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <div class="card-date">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            {item['date']}
                        </div>
                        {baseline_html}
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="{item['chart_id']}"></canvas>
                </div>
            </a>
            """
        html_content += '</div></div>'

    html_content += """
        </div>
        
        <script>
            // Chart configuration and rendering
            const chartConfigs = """ + json.dumps(charts_config_json) + """;
            
            Chart.defaults.color = '#8b949e';
            Chart.defaults.font.family = "'Inter', sans-serif";
            
            chartConfigs.forEach(conf => {
                const ctx = document.getElementById(conf.id);
                if (!ctx) return;
                
                const data = conf.data;
                const baselineData = conf.baseline || [];
                const labels = data.map(d => d.x);
                const values = data.map(d => d.y);
                const baselineValues = baselineData.map(d => d.y);
                
                let lineColor = '#58a6ff';
                let gradientStart = 'rgba(88, 166, 255, 0.2)';
                let gradientEnd = 'rgba(88, 166, 255, 0)';
                
                if (conf.is_negative) {
                    lineColor = '#f85149';
                    gradientStart = 'rgba(248, 81, 73, 0.2)';
                    gradientEnd = 'rgba(248, 81, 73, 0)';
                }
                
                const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 120);
                gradient.addColorStop(0, gradientStart);
                gradient.addColorStop(1, gradientEnd);
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                data: baselineValues,
                                borderColor: 'rgba(139, 148, 158, 0.5)',
                                borderWidth: 1.5,
                                borderDash: [5, 5],
                                pointRadius: 0,
                                pointHoverRadius: 0,
                                fill: false,
                                tension: 0,
                                tooltip: {
                                    callbacks: {
                                        label: function() { return null; }
                                    }
                                }
                            },
                            {
                                data: values,
                                borderColor: lineColor,
                                backgroundColor: gradient,
                                borderWidth: 2,
                                pointRadius: 0,
                                pointHoverRadius: 4,
                                fill: true,
                                tension: 0.4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                intersect: false,
                                mode: 'index',
                                backgroundColor: 'rgba(22, 27, 34, 0.9)',
                                titleColor: '#fff',
                                bodyColor: '#c9d1d9',
                                borderColor: '#30363d',
                                borderWidth: 1,
                                padding: 10,
                                displayColors: false,
                                callbacks: {
                                    label: function(context) {
                                        return context.parsed.y;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                display: false
                            },
                            y: {
                                display: false,
                                grace: '10%' 
                            }
                        },
                        interaction: {
                            mode: 'nearest',
                            axis: 'x',
                            intersect: false
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Index HTML generated at {HTML_PATH}")


def generate_ai_html(data):
    """
    Generates a simplified, text/semantic-heavy HTML for LLM consumption.
    Ignores styling, JavaScript, or charts completely.
    """
    categories = [
        "榮景期指標 (Priority)",
        "衰退期指標 (Recession)",
        "復甦期指標 (Recovery)",
        "Labor Market",
        "Rates & Spreads",
        "Consumption & Sentiment",
        "Production & Manufacturing",
        "Monetary & Inflation",
        "GDP Output",
        "Investment & Gov",
        "Credit Risk",
        "Credit Delinquency",
        "Trade"
    ]
    grouped = {cat: [] for cat in categories}
    
    for item in data:
        cat = item['category']
        grouped[cat].append(item)
        
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FRED 總體經濟數據 - AI Parsing Version</title>
</head>
<body>
    <h1>FRED Macroeconomic Data (For AI Analysis)</h1>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
"""

    # Start the table directly since categories will be mixed into rows if we just want a flat list
    html_content += """
<table border="1" cellpadding="5" cellspacing="0">
  <thead>
    <tr>
      <th>Name</th>
      <th>Value (Released)</th>
      <th>Frequency</th>
    </tr>
  </thead>
  <tbody>
"""
    for cat in categories:
        items = grouped[cat]
        if not items: continue
        
        for item in items:
            link = f"https://fred.stlouisfed.org/series/{item['id']}" if item['id'] != 'SOFR_IORB_SPREAD' else '#'
            html_content += f"    <tr>\n"
            html_content += f"      <td><a href=\"{link}\">{item['name']}</a></td>\n"
            html_content += f"      <td>{item['display_val']} (Released: {item['date']})</td>\n"
            html_content += f"      <td>{cat}</td>\n"
            html_content += f"    </tr>\n"

    html_content += """
  </tbody>
</table>
</body>
</html>
"""
    with open(AI_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"AI simplified view generated at {AI_HTML_PATH}")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"[警告] 找不到資料庫檔案 '{DB_PATH}'！請先執行 'python init_db.py' 去抓取歷史資料後再嘗試產生網頁。")
        sys.exit(1)
        
    print("Generating HTML dashboards...")
    ui_data = get_data_for_ui()
    generate_html(ui_data)
    generate_ai_html(ui_data)
    print("Generation complete!")
