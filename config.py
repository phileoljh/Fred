import os
from dotenv import load_dotenv

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
load_dotenv()
FRED_API_KEY = os.getenv('FRED_API_KEY')
DB_PATH = 'fred_data.db'
HTML_PATH = 'index.html'
AI_HTML_PATH = 'ai_view.html'

# Update INDICATORS to include Chinese names and chart config
INDICATORS = [
    # 榮景期指標 (Priority)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}", "points": 14}, # 3mo (13 weeks)
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "UMCSENT", "name": "密西根大學消費者信心指數 (U.S. Consumer Sentiment)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value} pts", "points": 12},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4},

    # 衰退期指標 (Recession)
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    
    # 復甦期指標 (Recovery)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "lin", "format": "{value}", "points": 14},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "IMPGS", "name": "進口金額年增率 (Imports)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 4},

    # Daily (1 Month = ~22-30 points)
    {"id": "T10Y2Y", "name": "10年期減2年期公債利差 (10Y-2Y Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "T10Y3M", "name": "10年期減3個月期公債利差 (10Y-3M Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "IORB", "name": "準備金餘額利率 (IORB)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "SOFR", "name": "擔保隔夜融資利率 (SOFR)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "BAMLH0A0HYM2", "name": "美國高收益債券利差 (US High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "BAMLH0A3HYC", "name": "CCC級及以下高收益債券利差 (CCC High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30},
    
    # Weekly (3 Months = ~13-14 points)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Weekly", "category": "Labor Market", "units": "lin", "format": "{value}", "points": 14},
    
    # Monthly (1 Year = 12 points)
    {"id": "PAYEMS", "name": "非農就業人數 (Nonfarm Payrolls)", "freq": "Monthly", "category": "Labor Market", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "ADPMNUSNERSA", "name": "ADP小非農就業人數 (ADP Employment)", "freq": "Monthly", "category": "Labor Market", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "UEMPLT5", "name": "短期失業人數 (Unemployed <5 Weeks)", "freq": "Monthly", "category": "Labor Market", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "SAHMREALTIME", "name": "薩姆規則衰退指標 (Sahm Rule Indicator)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value} pts", "points": 12},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "UMCSENT", "name": "密西根大學消費者信心指數 (U.S. Consumer Sentiment)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "lin", "format": "{value} pts", "points": 12},
    {"id": "INDPRO", "name": "工業生產指數 (Industrial Production)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "FEDFUNDS", "name": "聯邦基金有效利率 (Federal Funds Rate)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "lin", "format": "{value}%", "points": 12},
    {"id": "CPIAUCSL", "name": "消費者物價指數 (CPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "PCEPILFE", "name": "核心個人消費支出物價指數 (Core PCE Price Index)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "JTSJOL", "name": "JOLTS 職缺數 (Job Openings)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}K", "points": 12},
    
    # Quarterly (1 Year = 4 points)
    {"id": "GDPC1", "name": "實質國內生產毛額 (Real GDP)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Quarterly", "category": "Investment & Gov", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "PRFI", "name": "私人住宅固定投資 (Private Residential Fixed Investment)", "freq": "Quarterly", "category": "Investment & Gov", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Quarterly", "category": "Investment & Gov", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Quarterly", "category": "Credit Delinquency", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Quarterly", "category": "Credit Delinquency", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "IMPGS", "name": "進口金額年增率 (Imports)", "freq": "Quarterly", "category": "Trade", "units": "pc1", "format": "{value}% YoY", "points": 4},
]
