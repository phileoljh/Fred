import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from config import DB_PATH, INDICATORS, CHART_GROUPS, MACRO_SCORE_MODEL, FAST_MACRO_SCORE_MODEL, COMBINED_HTML_PATH, FAST_SCORE_TIERS, MACRO_SCORE_TIERS

# ==========================================
# 綜合對比分析腳本 (Standalone Comparative Analysis)
# ==========================================

OUTPUT_PATH = COMBINED_HTML_PATH

def get_grouped_data():
    conn = sqlite3.connect(DB_PATH)
    grouped_data = []
    
    # Create a lookup for indicator metadata
    meta = {item['id']: item for item in INDICATORS}
    
    for g_idx, group in enumerate(CHART_GROUPS):
        members = group['members']
        combined_history = {} # date -> {series_id: value}
        
        for mid in members:
            # Special handling for NET_LIQUIDITY synthesis
            if mid == 'NET_LIQUIDITY':
                # Net Liquidity = WALCL - TGA - RRP
                components = ['WALCL', 'WTREGEN', 'RRPONTSYD']
                comp_vals = {}
                for cid in components:
                    c = conn.cursor()
                    c.execute("SELECT value, date FROM observations WHERE series_id=? AND date >= date('now', '-24 months') ORDER BY date ASC", (cid,))
                    comp_vals[cid] = {r[1]: float(r[0]) for r in c.fetchall()}
                
                # Use WALCL dates as base
                for d in comp_vals.get('WALCL', {}).keys():
                    try:
                        v_assets = comp_vals['WALCL'][d]
                        # Find nearest TGA/RRP
                        v_tga = comp_vals.get('WTREGEN', {}).get(d)
                        v_rrp = comp_vals.get('RRPONTSYD', {}).get(d)
                        
                        if v_tga is None:
                            d_list = [dt for dt in comp_vals.get('WTREGEN', {}).keys() if dt <= d]
                            if d_list: v_tga = comp_vals['WTREGEN'][max(d_list)]
                        if v_rrp is None:
                            d_list = [dt for dt in comp_vals.get('RRPONTSYD', {}).keys() if dt <= d]
                            if d_list: v_rrp = comp_vals['RRPONTSYD'][max(d_list)]
                        
                        if v_assets and v_tga is not None and v_rrp is not None:
                            if d not in combined_history: combined_history[d] = {}
                            # Formula (T) = A(M)/1M - T(M)/1M - R(B)/1K
                            combined_history[d][mid] = (v_assets / 1000000.0) - (v_tga / 1000000.0) - (v_rrp / 1000.0)
                    except:
                        pass
                continue

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
            
        # Check for magnitude consistency (e.g., mixing K and M)
        formats = [meta.get(mid, {}).get('format', '') for mid in members]
        has_k = any('K' in f for f in formats)
        has_m = any('M' in f for f in formats)
        unify_to_m = has_k and has_m # If mixed, unify all K to M for this chart
        
        datasets = []
        colors = ['#58a6ff', '#3fb950', '#a371f7', '#d29922', '#f85149']
        
        for m_idx, mid in enumerate(members):
            data_points = []
            m_meta = meta.get(mid, {})
            
            # Base metadata
            name = m_meta.get('name', mid).split(' (')[0]
            fmt = m_meta.get('format', '{value}')
            decimals = m_meta.get('decimals', 2)
            scale_adjust = 1.0
            
            # Apply dynamic conversion if needed
            if unify_to_m and 'K' in fmt:
                scale_adjust = 1000.0
                fmt = fmt.replace('K', 'M')
                decimals = 2
                name += " (M)" # Add unit suffix to legend to be clear
            
            for d in sorted_dates:
                val = combined_history[d].get(mid)
                if val is not None:
                    data_points.append(val / scale_adjust)
                else:
                    data_points.append(None)
            
            datasets.append({
                'label': name,
                'data': data_points,
                'borderColor': colors[m_idx % len(colors)],
                'format': fmt,
                'decimals': decimals
            })
            
        grouped_data.append({
            'name': group['name'],
            'chart_id': f"combined_chart_{g_idx}",
            'datasets': datasets,
            'labels': sorted_dates
        })
        
    conn.close()
    return grouped_data

# ==========================================
# CORE SCORING LOGIC (Tiered Impact)
# ==========================================

def get_tiered_impact(delta, baseline_val, tiers, is_rate_or_spread=False):
    """
    根據變動幅度百分比或絕對值計算評分乘數與強度標籤。
    
    參數:
    - delta: 最新值與基準值的差額
    - baseline_val: 用於計算比例的基準值 (通常為前次值或均值)
    - tiers: config.py 中定義的階梯清單
    - is_rate_or_spread: 若為 True，則比較 limit_abs；否則比較 limit_pct
    
    回傳: (multiplier, label)
    """
    if not tiers:
        return 1.0, "顯著 (Significant)" if delta != 0 else "平穩 (Stable)"
    
    # 計算變動百分比 (絕對值) 防呆
    pct_change = (abs(delta) / abs(baseline_val)) * 100 if baseline_val else 0
    
    target_multiplier = 0.0
    target_label = "平穩 (Stable)"
    
    # 遍歷階梯找出符合的最高門檻
    # tiers 需預先按 limit 由小到大排序
    for tier in tiers:
        if is_rate_or_spread:
            meets_threshold = (abs(delta) >= tier.get('limit_abs', tier['limit_pct']))
        else:
            meets_threshold = (pct_change >= tier['limit_pct'])
            
        if meets_threshold:
            target_multiplier = tier['multiplier']
            target_label = tier['label']
        else:
            break
            
    return target_multiplier, target_label

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
            
            # Virtual Indicator Handling: NET_LIQUIDITY
            if ind_id == 'NET_LIQUIDITY':
                # Synthesize from WALCL, WTREGEN, RRPONTSYD
                c = conn.cursor()
                results = {}
                for cid in ['WALCL', 'WTREGEN', 'RRPONTSYD']:
                    c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 2", (cid,))
                    rows = c.fetchall()
                    if rows: results[cid] = rows
                
                if len(results.get('WALCL', [])) < 2: continue
                
                # Get latest and prev for all
                def get_net_liq(idx):
                    try:
                        v_a = float(results['WALCL'][idx][0])
                        v_t = float(results['WTREGEN'][idx][0]) if len(results.get('WTREGEN', [])) > idx else float(results['WTREGEN'][0][0])
                        v_r = float(results['RRPONTSYD'][idx][0]) if len(results.get('RRPONTSYD', [])) > idx else float(results['RRPONTSYD'][0][0])
                        # Net Liq (T) = Assets(M)/1M - TGA(M)/1M - RRP(B)/1K
                        return (v_a / 1000000.0) - (v_t / 1000000.0) - (v_r / 1000.0)
                    except: return None
                
                latest_val = get_net_liq(0)
                prev_val = get_net_liq(1)
                latest_date = results['WALCL'][0][1]
                prev_date = results['WALCL'][1][1]
                
                if latest_val is None or prev_val is None: continue
                meta = {"name": "市場淨流動性 (Net Liquidity)", "format": "{value}T"}
            else:
                c = conn.cursor()
                c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 2", (ind_id,))
                rows = c.fetchall()
                
                if len(rows) < 2:
                    continue
                    
                scale = meta.get('scale', 1)
                latest_val = float(rows[0][0]) / scale
                latest_date = rows[0][1]
                prev_val = float(rows[1][0]) / scale
                prev_date = rows[1][1]
            
            delta = latest_val - prev_val
            polarity = ind_info.get("polarity", "neutral")
            sub_weight = ind_info.get("sub_weight", 0)
            
            # 【自動化判定】：根據頻率自動切換階梯
            # 1. 預設使用宏觀階梯 (MACRO)
            # 2. 若為日/週報或淨流動性合成指標，套用高頻階梯 (FAST)
            tiers = MACRO_SCORE_TIERS
            if meta.get('true_freq') in ['daily', 'weekly'] or ind_id == 'NET_LIQUIDITY':
                tiers = FAST_SCORE_TIERS

            # 判定是否為率/利差/變動量指標 (使用絕對基點評估，避免趨近於 0 時的數學發散)
            is_rate_or_spread = (meta.get('units') in ['pch', 'pca']) or ('%' in meta.get('format', ''))
            
            # 獲取階梯乘數與標籤
            multiplier, intensity = get_tiered_impact(delta, prev_val, tiers, is_rate_or_spread)
            
            if sub_weight <= 0 or polarity == 'neutral' or multiplier == 0:
                status = 'no_change' if multiplier == 0 else 'neutral'
                score_change = 0
            else:
                cat_max_weight += sub_weight
                # 最終得分 = 子權重 * 階梯乘數 * 方向
                direction = 1 if (delta > 0 and polarity == 'positive') or (delta < 0 and polarity == 'negative') else -1
                score_change = sub_weight * multiplier * direction
                
                if direction == 1:
                    status = 'favorable'
                else:
                    status = 'unfavorable'
                    
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
                'intensity': intensity,
                'multiplier': multiplier,
                'sub_weight': sub_weight,
                'score_change': score_change,
                'format': meta.get('format', '{value}'),
                'decimals': meta.get('decimals', 2)
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

def get_fast_composite_index():
    """
    針對高頻指標（日報、週報）的快速評分模型。
    - 週報 (Weekly): 對比「前一次」數值。
    - 日報 (Daily): 對比「前三次有效數值之算術平均」。
    """
    conn = sqlite3.connect(DB_PATH)
    meta_lookup = {item['id']: item for item in INDICATORS}
    
    total_final_score = 0
    details = []

    for cat_key, cat_data in FAST_MACRO_SCORE_MODEL.items():
        cat_name = cat_data.get("name", cat_key)
        cat_weight = cat_data.get("weight", 0)
        
        cat_earned_score = 0
        cat_max_weight = 0
        cat_details = []
        
        for ind_id, ind_info in cat_data["indicators"].items():
            meta = meta_lookup.get(ind_id, {})
            c = conn.cursor()
            
            # 1. 處理虛擬合成指標: NET_LIQUIDITY (市場淨流動性)
            if ind_id == 'NET_LIQUIDITY':
                results = {}
                for cid in ['WALCL', 'WTREGEN', 'RRPONTSYD']:
                    c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 5", (cid,))
                    results[cid] = c.fetchall()
                
                if len(results.get('WALCL', [])) < 2: continue
                
                # 合成運算: 兆 (T) = Assets(M)/1M - TGA(M)/1M - RRP(B)/1K
                def get_net_liq_val(idx):
                    try:
                        v_a = float(results['WALCL'][idx][0])
                        v_t = float(results['WTREGEN'][idx][0]) if len(results.get('WTREGEN', [])) > idx else float(results['WTREGEN'][0][0])
                        v_r = float(results['RRPONTSYD'][idx][0]) if len(results.get('RRPONTSYD', [])) > idx else float(results['RRPONTSYD'][0][0])
                        return (v_a / 1000000.0) - (v_t / 1000000.0) - (v_r / 1000.0)
                    except: return None

                latest_val = get_net_liq_val(0)
                latest_date = results['WALCL'][0][1]
                baseline_val = get_net_liq_val(1) # 週更邏輯：對比前週值
                compare_label = "前次值"
                # 強制使用手動元數據以匹配合成結果
                meta = {"name": "市場淨流動性 (Net Liquidity)", "format": "{value}T", "decimals": 2}
                
            else:
                # 2. 處理一般指標：區分頻率並執行數值縮放 (Scale)
                true_freq = meta.get('true_freq', 'weekly')
                scale = meta.get('scale', 1)
                
                if true_freq == 'daily':
                    # 日報指標：抓取 4 筆觀察值，以計算「前 3 日均值」作為基準
                    c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 4", (ind_id,))
                    rows = c.fetchall()
                    if len(rows) < 4: continue
                    latest_val = float(rows[0][0]) / scale
                    latest_date = rows[0][1]
                    baseline_val = sum(float(r[0]) for r in rows[1:]) / (3 * scale)
                    compare_label = "3日均值"
                else:
                    # 週報指標：抓取 2 筆，對比前次值
                    c.execute("SELECT value, date FROM observations WHERE series_id=? ORDER BY date DESC LIMIT 2", (ind_id,))
                    rows = c.fetchall()
                    if len(rows) < 2: continue
                    latest_val = float(rows[0][0]) / scale
                    latest_date = rows[0][1]
                    baseline_val = float(rows[1][0]) / scale
                    compare_label = "前次值"
            
            polarity = ind_info.get("polarity", "neutral")
            sub_weight = ind_info.get("sub_weight", 0)
            delta = latest_val - baseline_val
            
            # 【自動化判定】：根據頻率自動切換階梯
            tiers = MACRO_SCORE_TIERS
            if meta.get('true_freq') in ['daily', 'weekly'] or ind_id == 'NET_LIQUIDITY':
                tiers = FAST_SCORE_TIERS
            
            # 判定是否為率/利差/變動量指標 (使用絕對基點評估，避免趨近於 0 時的數學發散)
            is_rate_or_spread = (meta.get('units') in ['pch', 'pca', 'chg']) or ('%' in meta.get('format', ''))
            
            # 獲取階梯乘數與標籤
            multiplier, intensity = get_tiered_impact(delta, baseline_val, tiers, is_rate_or_spread)
            
            if sub_weight <= 0 or polarity == 'neutral' or multiplier == 0:
                status = 'no_change' if multiplier == 0 else 'neutral'
                score_change = 0
            else:
                cat_max_weight += sub_weight
                # 最終得分 = 子權重 * 階梯乘數 * 方向
                direction = 1 if (delta > 0 and polarity == 'positive') or (delta < 0 and polarity == 'negative') else -1
                score_change = sub_weight * multiplier * direction
                
                if direction == 1:
                    status = 'favorable'
                else:
                    status = 'unfavorable'
            
            cat_earned_score += score_change
            
            cat_details.append({
                'category': cat_name,
                'cat_weight': cat_weight,
                'id': ind_id,
                'name': meta.get('name', ind_id),
                'latest_val': latest_val,
                'latest_date': latest_date,
                'baseline_val': baseline_val,
                'delta': delta,
                'compare_label': compare_label,
                'polarity': polarity,
                'status': status,
                'intensity': intensity, # 新增強度
                'multiplier': multiplier, # 新增乘數
                'sub_weight': sub_weight,
                'score_change': score_change,
                'format': meta.get('format', '{value}'),
                'decimals': meta.get('decimals', 2) # 傳遞小數位數
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

def generate_combined_html(grouped_data, composite_data=None, fast_composite_data=None):
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

    def render_index_card(data, title, description):
        if not data: return ""
        score_val = data['score']
        if score_val > 0:
            s_class = "score-positive"
        elif score_val < 0:
            s_class = "score-negative"
        else:
            s_class = "score-neutral"
            
        html = f"""
            <div class="composite-card">
                <div class="card-title">{title}</div>
                <div style="text-align: center; color: var(--text-muted);">
                    {description}
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
                                <th>基準與對比</th>
                                <th>最新數值</th>
                                <th>變化</th>
                                <th>判定狀態</th>
                                <th>貢獻分數</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        for row in data['details']:
            latest_date_str = row.get('latest_date', 'N/A')
            decimals = row.get('decimals', 2)
            f_latest = row['format'].replace('{value}', f"{row['latest_val']:.{decimals}f}") if row['latest_val'] is not None else 'N/A'
            f_delta = f"{row['delta']:+.{decimals}f}"
            
            # 兼容 Fast 指標與標準指標的基準顯示
            if 'compare_label' in row:
                base_val = row['baseline_val']
                label = row['compare_label']
            else:
                base_val = row.get('prev_val')
                label = "前次值"
            
            f_base = row['format'].replace('{value}', f"{base_val:.{decimals}f}") if base_val is not None else 'N/A'
            
            # 處理強度標籤
            intensity_str = f"({row['intensity'].split(' ')[0]}) " if row.get('intensity') and row['status'] in ['favorable', 'unfavorable'] else ""
            
            if row['status'] == 'favorable':
                st_text = f'🟢 {intensity_str}有利'; st_class = 'status-favorable'
            elif row['status'] == 'unfavorable':
                st_text = f'🔴 {intensity_str}不利'; st_class = 'status-unfavorable'
            elif row['status'] == 'neutral':
                st_text = '⚪ 不計分'; st_class = 'status-neutral'
            else:
                st_text = '➖ 無變化'; st_class = 'status-neutral'
                
            if row['status'] == 'no_change' or row['sub_weight'] <= 0:
                wt_text = "-"
            else:
                wt_text = f"<b style='color:var(--accent)'>{row['abs_points']:+.2f} 分</b><br/><small style='color:var(--text-muted)'>(板塊佔 {row['sub_weight']*100:.0f}%)</small>"
                
            html += f"""
                            <tr>
                                <td><b style="color:var(--accent)">{row['category']}</b><br/><small style="color:var(--text-muted)">({int(row['cat_weight']*100)}%)</small></td>
                                <td>{row['name']}</td>
                                <td>{f_base} <br/><small style="color:var(--text-muted)">({label})</small></td>
                                <td>{f_latest} <br/><small style="color:var(--text-muted)">{latest_date_str}</small></td>
                                <td>{f_delta}</td>
                                <td class="{st_class}">{st_text}</td>
                                <td class="{st_class}">{wt_text}</td>
                            </tr>
            """
        html += """
                        </tbody>
                    </table>
                </details>
            </div>
        """
        return html

    # 先渲染快速指標，再渲染標準指標
    html_template += render_index_card(
        fast_composite_data, 
        "快速經濟指標 (Fast Index)", 
        "目前評分：+10 (完全樂觀) ~ -10 (完全悲觀) <br/> 基於日報(三日均線)與週報指標之即時反饋"
    )
    
    html_template += render_index_card(
        composite_data, 
        "經濟綜合指標 (Macro Index)", 
        "目前評分：+10 (完全樂觀) ~ -10 (完全悲觀) <br/> 基於四大經濟板塊之月報/季報趨勢分析"
    )

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
        comp_macro = get_composite_index()
        print("Calculating fast index...")
        comp_fast = get_fast_composite_index()
        print(f"Generating {OUTPUT_PATH}...")
        generate_combined_html(data, composite_data=comp_macro, fast_composite_data=comp_fast)
        print("Done!")
