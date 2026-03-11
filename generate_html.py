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
            c.execute("SELECT value, date, updated_at FROM observations WHERE series_id=? AND date >= date('now', '-18 months') ORDER BY date DESC", (item['id'],))
            rows = c.fetchall()
        except sqlite3.OperationalError:
            rows = []
        
        history = []
        history_baseline = []
        baseline_display = ""
        display_val = "N/A"
        date_val = "N/A"
        latest_updated_at = None
        val_float = None
        
        if rows:
            # Most recent for the big card
            latest_val, latest_date, latest_updated_at = rows[0]
            try:
                val_float = float(latest_val)
                if item['id'] == 'ICSA':
                    display_val = f"{val_float / 1000:.1f}K"
                elif item['id'] == 'ADPMNUSNERSA':
                    display_val = item['format'].format(value=f"{val_float / 1000:.1f}")
                elif item['id'] == 'JTSJOL':
                    display_val = item['format'].format(value=f"{val_float / 1000:.2f}")
                elif item['id'] == 'EXHOSLUSM495S':
                    display_val = item['format'].format(value=f"{val_float / 1000000:.2f}")
                elif item['id'] in ['HOUST', 'PERMIT']:
                    display_val = item['format'].format(value=f"{val_float:.0f}")
                elif item['id'] == 'PAYEMS':
                    display_val = item['format'].format(value=f"{val_float:.1f}")
                else:
                    display_val = item['format'].format(value=f"{val_float:.2f}")
            except ValueError:
                display_val = latest_val
            date_val = latest_date
            
            # Format history for chart (oldest to newest)
            for row in reversed(rows):
                try:
                    raw_y = float(row[0])
                    if item['id'] == 'ICSA':
                        raw_y /= 1000
                    elif item['id'] == 'ADPMNUSNERSA':
                        raw_y /= 1000
                    elif item['id'] == 'JTSJOL':
                        raw_y /= 1000
                    elif item['id'] == 'EXHOSLUSM495S':
                        raw_y /= 1000000
                        
                    history.append({'x': row[1], 'y': raw_y})
                except Exception:
                    pass
            
            # Calculate baseline (0-axis or 18-mo avg)
            baseline_val = None
            if history:
                y_vals = [h['y'] for h in history]
                
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
                    if item['id'] == 'ICSA' or item['id'] == 'ADPMNUSNERSA' or item['id'] == 'PAYEMS':
                        baseline_display = f"{baseline_val:.1f}"
                    elif item['id'] in ['HOUST', 'PERMIT']:
                        baseline_display = f"{baseline_val:.0f}"
                    else:
                        baseline_display = f"{baseline_val:.2f}"
                
                # ICSA is a special case as config doesn't add the suffix
                if item['id'] == 'ICSA':
                    baseline_display = f"{baseline_display}K"
                else:
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
            
        is_new_update = False
        new_badge_html = ""
        if latest_updated_at:
            try:
                # Strip out any timezone info or fractional seconds to make it compatible with older Python fromisoformat
                clean_updated = str(latest_updated_at)
                if '+' in clean_updated:
                    clean_updated = clean_updated.rsplit('+', 1)[0]
                # Sometimes timezone is represented as "-06" at the end of the string
                # ISO format ends with HH:MM:SS or HH:MM:SS.ffffff. If there's another "-" after the time, that's timezone
                if clean_updated.count('-') > 2 and ' ' in clean_updated:
                    time_part = clean_updated.split(' ')[1]
                    if '-' in time_part:
                        clean_updated = clean_updated.rsplit('-', 1)[0]
                elif clean_updated.count('-') > 2 and 'T' in clean_updated:
                    time_part = clean_updated.split('T')[1]
                    if '-' in time_part:
                        clean_updated = clean_updated.rsplit('-', 1)[0]
                
                if clean_updated.endswith('Z'):
                    clean_updated = clean_updated[:-1]

                updated_at_dt = datetime.fromisoformat(clean_updated.strip())
                days_diff = (datetime.now() - updated_at_dt).days
                if days_diff <= 7 and freq_label not in ["daily", "weekly"]:
                    is_new_update = True
                    if days_diff <= 1:
                        new_badge_html = '<span class="badge-new-1d">NEW (1d)</span>'
                    elif days_diff <= 3:
                        new_badge_html = '<span class="badge-new-3d">NEW (3d)</span>'
                    else:
                        new_badge_html = '<span class="badge-new-7d">NEW</span>'
            except (ValueError, TypeError):
                pass

        ui_data.append({
            **item, 
            'name_zh': name_zh,
            'name_en': name_en,
            'is_new_update': is_new_update,
            'new_badge_html': new_badge_html,
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
        "Investment & Gov",
        "GDP Output"
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
        "Investment & Gov": "投資與政府支出 (Investment & Gov)",
        "Credit Risk": "信用風險 (Credit Risk)",
        "Credit Delinquency": "違約率 (Credit Delinquency)",
        "GDP Output": "國內生產毛額與貿易 (GDP Output & Trade)"
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

            .badge-new-1d {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                background: linear-gradient(45deg, #ff4500, #ff8c00);
                color: white;
                font-weight: 800;
                white-space: nowrap;
                margin-left: 10px;
                box-shadow: 0 0 12px rgba(255, 69, 0, 0.6);
                animation: pulse-1d 1.2s infinite;
            }}
            .badge-new-3d {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                background: linear-gradient(45deg, #f85149, #a371f7);
                color: white;
                font-weight: 700;
                white-space: nowrap;
                margin-left: 10px;
                box-shadow: 0 0 10px rgba(248, 81, 73, 0.4);
                animation: pulse-3d 2s infinite;
            }}
            .badge-new-7d {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                background: linear-gradient(45deg, #1f6feb, #388bfd);
                color: white;
                font-weight: 700;
                white-space: nowrap;
                margin-left: 10px;
                box-shadow: 0 0 8px rgba(31, 111, 235, 0.3);
                animation: pulse-7d 3s infinite;
            }}
            
            @keyframes pulse-1d {{
                0%, 100% {{ box-shadow: 0 0 16px rgba(255, 69, 0, 0.9); transform: scale(1); opacity: 1; }}
                50% {{ box-shadow: 0 0 4px rgba(255, 69, 0, 0.3); transform: scale(0.97); opacity: 0.85; }}
            }}
            @keyframes pulse-3d {{
                0%, 100% {{ box-shadow: 0 0 14px rgba(248, 81, 73, 0.7); opacity: 1; }}
                50% {{ box-shadow: 0 0 4px rgba(248, 81, 73, 0.2); opacity: 0.85; }}
            }}
            @keyframes pulse-7d {{
                0%, 100% {{ box-shadow: 0 0 12px rgba(31, 111, 235, 0.6); opacity: 1; }}
                50% {{ box-shadow: 0 0 2px rgba(31, 111, 235, 0.1); opacity: 0.85; }}
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
        if not items:
            continue
        
        html_content += f'<div class="frequency-section"><h2 class="frequency-title">{cat_zh[cat]}</h2>'
        html_content += '<div class="grid">'
        
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
                    "is_negative": (item['id'] == 'SAHMREALTIME' and item['raw_val'] >= 0.5),
                    "is_zero_baseline": (item['id'] in ["SOFR_IORB_SPREAD", "T10Y2Y", "T10Y3M"])
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
                            { item.get('new_badge_html', '') }
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
                
                let baseColor = 'rgba(139, 148, 158, 0.5)';
                let baseDash = [5, 5];
                let baseWidth = 1.5;
                if (conf.is_zero_baseline) {
                    baseColor = '#f85149';
                    baseDash = [];
                    baseWidth = 2;
                }
                
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
                                borderColor: baseColor,
                                borderWidth: baseWidth,
                                borderDash: baseDash,
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
        "Credit Risk",
        "Credit Delinquency",
        "Investment & Gov",
        "GDP Output"
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
        if not items:
            continue
        
        for item in items:
            link = f"https://fred.stlouisfed.org/series/{item['id']}" if item['id'] != 'SOFR_IORB_SPREAD' else '#'
            html_content += "    <tr>\n"
            html_content += f"      <td><a href=\"{link}\">{item['name']}</a></td>\n"
            html_content += f"      <td>{item['display_val']} (Released: {item['date']})</td>\n"
            html_content += f"      <td>{cat}</td>\n"
            html_content += "    </tr>\n"

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
