import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from config import DB_PATH, INDICATORS, CHART_GROUPS, MACRO_SCORE_MODEL

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

def get_composite_index():
    """
    計算綜合指標 (雙層權重架構)，分數區間落在 +10 到 -10 之間。
    - 第一層：大類板塊權重 (如 0.30, 0.25)
    - 第二層：板塊內部子權重 (如 4, 3, 2, 0 為不計分)
    """
    conn = sqlite3.connect(DB_PATH)
    
    # 建構 meta_lookup
    meta_lookup = {item['id']: item for item in INDICATORS}
    
    total_final_score = 0
    details = []

    for cat_key, cat_data in MACRO_SCORE_MODEL.items():
        cat_name = cat_data.get("name", cat_key)
        cat_weight = cat_data.get("weight", 0)
        
        cat_earned_score = 0
        cat_max_weight = 0
        
        cat_details = []
        for ind_id, ind_info in cat_data["indicators"].items():
            meta = meta_lookup.get(ind_id, {})
            c = conn.cursor()
            c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 2", (ind_id,))
            rows = c.fetchall()
            
            if len(rows) < 2:
                continue
                
            latest_val = float(rows[0][0])
            latest_date = rows[0][1]
            prev_val = float(rows[1][0])
            prev_date = rows[1][1]
            
            delta = latest_val - prev_val
            polarity = ind_info.get("polarity", "neutral")
            sub_weight = ind_info.get("sub_weight", 0)
            
            if sub_weight <= 0 or polarity == 'neutral':
                status = 'neutral'
                score_change = 0
            else:
                cat_max_weight += sub_weight
                if delta > 0:
                    if polarity == 'positive':
                        status = 'favorable'
                        score_change = sub_weight
                    else: # negative
                        status = 'unfavorable'
                        score_change = -sub_weight
                elif delta < 0:
                    if polarity == 'positive':
                        status = 'unfavorable'
                        score_change = -sub_weight
                    else: # negative
                        status = 'favorable'
                        score_change = sub_weight
                else:
                    # delta == 0
                    status = 'no_change'
                    score_change = 0
                    
                cat_earned_score += score_change
                
            cat_details.append({
                'category': cat_name,
                'cat_weight': cat_weight,
                'id': ind_id,
                'name': meta.get('name', ind_id),
                'latest_val': latest_val,
                'latest_date': latest_date,
                'prev_val': prev_val,
                'prev_date': prev_date,
                'delta': delta,
                'polarity': polarity,
                'status': status,
                'sub_weight': sub_weight,
                'score_change': score_change,
                'format': meta.get('format', '{value}')
            })
            
        if cat_max_weight > 0:
            cat_score_ratio = cat_earned_score / cat_max_weight
        else:
            cat_score_ratio = 0
            
        for d in cat_details:
            if cat_max_weight > 0:
                d['abs_points'] = (d['score_change'] / cat_max_weight) * cat_weight * 10
            else:
                d['abs_points'] = 0
            details.append(d)
            
        total_final_score += (cat_score_ratio * cat_weight) * 10

    conn.close()
    
    return {
        'score': total_final_score,
        'details': details
    }

def generate_combined_html(grouped_data, composite_data=None):
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
            .composite-card {{
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 30px;
            }}
            .score-display {{
                font-size: 4rem;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
            }}
            .score-positive {{ color: #3fb950; }}
            .score-negative {{ color: #f85149; }}
            .score-neutral {{ color: #c9d1d9; }}
            .comp-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9rem; }}
            .comp-table th, .comp-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid var(--border-color); }}
            .comp-table th {{ color: var(--text-muted); }}
            .status-favorable {{ color: #3fb950; }}
            .status-unfavorable {{ color: #f85149; }}
            .status-neutral {{ color: var(--text-muted); }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>FRED 綜合對比分析</h1>
                <p style="color: var(--text-muted);">最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </header>
    """

    if composite_data:
        score_val = composite_data['score']
        if score_val > 0:
            s_class = "score-positive"
        elif score_val < 0:
            s_class = "score-negative"
        else:
            s_class = "score-neutral"
            
        comp_html = f"""
            <div class="composite-card">
                <div class="card-title">經濟綜合指標 (Composite Index)</div>
                <div style="text-align: center; color: var(--text-muted);">
                    目前評分：+10 (完全樂觀) ~ -10 (完全悲觀) <br/>
                    (基於四大經濟要素兩回合疊加模型)
                </div>
                <div class="score-display {s_class}">
                    {score_val:+.2f}
                </div>
                
                <details>
                    <summary style="cursor: pointer; color: var(--accent); margin-bottom: 10px;">展開詳細判定清單</summary>
                    <table class="comp-table">
                        <thead>
                            <tr>
                                <th>板塊分類</th>
                                <th>指標名稱</th>
                                <th>極性</th>
                                <th>前次數值</th>
                                <th>最新數值</th>
                                <th>變化</th>
                                <th>判定狀態</th>
                                <th>貢獻滿分10分</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        for row in composite_data['details']:
            f_prev = row['format'].replace('{value}', f"{row['prev_val']:.2f}") if row['prev_val'] is not None else 'N/A'
            f_latest = row['format'].replace('{value}', f"{row['latest_val']:.2f}") if row['latest_val'] is not None else 'N/A'
            f_delta = f"{row['delta']:+.2f}"
            
            if row['status'] == 'favorable':
                st_text = '🟢 有利'
                st_class = 'status-favorable'
            elif row['status'] == 'unfavorable':
                st_text = '🔴 不利'
                st_class = 'status-unfavorable'
            elif row['status'] == 'neutral':
                st_text = '⚪ 不計分'
                st_class = 'status-neutral'
            else:
                st_text = '➖ 無變化'
                st_class = 'status-neutral'
                
            if row['status'] == 'no_change' or row['sub_weight'] <= 0:
                wt_text = "-"
            else:
                wt_text = f"<b style='color:var(--accent)'>{row['abs_points']:+.2f} 分</b><br/><small style='color:var(--text-muted)'>(板塊佔 {row['sub_weight']*100:.0f}%)</small>"
                
            comp_html += f"""
                            <tr>
                                <td><b style="color:var(--accent)">{row['category']}</b><br/><small style="color:var(--text-muted)">({int(row['cat_weight']*100)}%)</small></td>
                                <td>{row['name']}</td>
                                <td>{row['polarity']}</td>
                                <td>{f_prev} <br/><small style="color:var(--text-muted)">{row['prev_date']}</small></td>
                                <td>{f_latest} <br/><small style="color:var(--text-muted)">{row['latest_date']}</small></td>
                                <td>{f_delta}</td>
                                <td class="{st_class}">{st_text}</td>
                                <td class="{st_class}">{wt_text}</td>
                            </tr>
            """
            
        comp_html += """
                        </tbody>
                    </table>
                </details>
            </div>
        """
        html_template += comp_html

    html_template += """
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
        print("Calculating composite index...")
        comp_data = get_composite_index()
        print(f"Generating {OUTPUT_PATH}...")
        generate_combined_html(data, comp_data)
        print("Done!")
