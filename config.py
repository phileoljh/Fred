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
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4},

    # 衰退期指標 (Recession)
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 4},
    
    # 復甦期指標 (Recovery)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "lin", "format": "{value}", "points": 14},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "IMPGS", "name": "進口金額年增率 (Imports)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 4},

    # Daily (1 Month = ~22-30 points)
    {"id": "T10Y2Y", "name": "10年期減2年期公債利差 (10Y-2Y Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "T10Y3M", "name": "10年期減3個月期公債利差 (10Y-3M Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "IORB", "name": "準備金餘額利率 (IORB)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "SOFR", "name": "擔保隔夜融資利率 (SOFR)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "BAMLH0A0HYM2", "name": "美國高收益債券利差 (US High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "BAMLH0A3HYC", "name": "CCC級及以下高收益債券利差 (CCC High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "T10YIE", "name": "10年期平準通膨率 (10-Year Breakeven Inflation Rate)", "freq": "Daily", "category": "Monetary & Inflation", "units": "lin", "format": "{value}%", "points": 30},
    {"id": "VIXCLS", "name": "VIX恐慌指數 (CBOE Volatility Index)", "freq": "Daily", "category": "Consumption & Sentiment", "units": "lin", "format": "{value} pts", "points": 30},
    
    # Weekly (3 Months = ~13-14 points)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Weekly", "category": "Labor Market", "units": "lin", "format": "{value}", "points": 14},
    
    # Monthly (1 Year = 12 points)
    {"id": "PAYEMS", "name": "非農就業人數 (Nonfarm Payrolls)", "freq": "Monthly", "category": "Labor Market", "units": "chg", "format": "{value}K MoM", "points": 12},
    {"id": "ADPMNUSNERSA", "name": "ADP小非農就業人數 (ADP Employment)", "freq": "Monthly", "category": "Labor Market", "units": "chg", "format": "{value}K MoM", "points": 12},
    {"id": "UEMPLT5", "name": "短期失業人數 (Unemployed <5 Weeks)", "freq": "Monthly", "category": "Labor Market", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "SAHMREALTIME", "name": "薩姆規則衰退指標 (Sahm Rule Indicator)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value} pts", "points": 12},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "UMCSENT", "name": "密西根大學消費者信心指數 (U.S. Consumer Sentiment)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "lin", "format": "{value} pts", "points": 12},
    {"id": "INDPRO", "name": "工業生產指數 (Industrial Production)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "FEDFUNDS", "name": "聯邦基金有效利率 (Federal Funds Rate)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "lin", "format": "{value}%", "points": 12},
    {"id": "CPIAUCSL", "name": "消費者物價指數 (CPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "PCEPILFE", "name": "核心個人消費支出物價指數 (Core PCE Price Index)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "PPIACO", "name": "生產者物價指數 (PPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pc1", "format": "{value}% YoY", "points": 12},
    {"id": "JTSJOL", "name": "JOLTS 職缺數 (Job Openings)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}M", "points": 12},
    {"id": "CIVPART", "name": "勞動參與率 (Labor Force Participation Rate)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}%", "points": 12},
    {"id": "CES0500000003", "name": "平均每小時薪資 (Average Hourly Earnings)", "freq": "Monthly", "category": "Labor Market", "units": "pch", "format": "{value}% MoM", "points": 12},
    {"id": "HOUST", "name": "新屋開工 (Housing Starts)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}K", "points": 12},
    {"id": "PERMIT", "name": "營建許可 (Building Permits)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}K", "points": 12},
    {"id": "EXHOSLUSM495S", "name": "成屋銷售 (Existing Home Sales)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}M", "points": 12},
    
    # Quarterly (1 Year = 4 points)
    {"id": "GDPC1", "name": "實質國內生產毛額 (Real GDP)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "PRFI", "name": "私人住宅固定投資 (Private Residential Fixed Investment)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Quarterly", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Quarterly", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 4},
    {"id": "IMPGS", "name": "進口金額年增率 (Imports)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4},
]

# ==========================================
# INDICATOR EXPLANATIONS (Documentation)
# ==========================================
# < Daily >
# T10Y2Y / T10Y3M: 10年期減2年/3個月期公債利差，被稱為殖利率曲線倒掛與否的關鍵指標，通常領先衰退1年左右。
# IORB: 準備金餘額利率。影響銀行拆款的關鍵利率下限。
# SOFR: 擔保隔夜融資利率。市場上真實的短期無風險借貸成本。
# BAMLH0A0HYM2 / BAMLH0A3HYC: 高收益債與CCC級債利差，用來衡量市場恐慌情緒與企業違約風險的信用風險擴張。
# T10YIE: 10年期平準通膨率，反映債券市場(TIPS)對未來十年平均通膨的市場預期。
# VIXCLS: 恐慌指數，反映市場對未來 30 天 S&P 500 波動率的預期。
#
# < Weekly >
# ICSA: 初領失業救濟金人數。最即時反映就業市場榮枯的高頻數據。
#
# < Monthly >
# PAYEMS / ADPMNUSNERSA: (大/小)非農就業人數，觀察就業市場新增動能的核心指標 (MoM 月增減)。
# UEMPLT5: 短期失業人數，當經濟剛轉弱時，這數據會率先攀升。
# SAHMREALTIME: 薩姆規則衰退指標，當失業率三個月移動平均比過去12個月低點高出 0.5% 時，通常代表經濟已進入衰退。
# RSXFS / PCEC96 / PCEDGC96: 零售銷售與其實質/耐久財消費支出，由於美國是消費大國，反映民眾最真實的消費狀況。
# UMCSENT: 密大消費者信心，先行反映消費者未來的消費意願與通膨預期。
# INDPRO / NEWORDER / BUSINV: 涵蓋工業生產、核心資本財訂單(企業投資意願)與商業庫存的水位。
# FEDFUNDS: 美國聯邦基金利率(聯準會基準利率)。
# CPIAUCSL / PCEPILFE / PPIACO: 觀察美國消費者物價及聯準會最看重的核心PCE(月增率MoM)，與生產端出廠物價的變化。
# JTSJOL: 職缺數。勞動力市場的「需求面」，以百萬(M)人計。
# CIVPART: 勞動參與率。就業市場結構健康的指標，影響失業率解讀。
# CES0500000003: 平均每小時薪資月增率 (MoM)。觀察有無「薪資-物價螺旋上升」的關鍵指標，也是服務業通膨的重點。
# HOUST / PERMIT: 新屋開工與營建許可。房市的先行指標，帶動後續的一連串住宅相關消費跟銀行貸款。
# EXHOSLUSM495S: 成屋銷售。佔據房地產市場大宗交易，了解整體房價熱度與庫存去化速度。
#
# < Quarterly >
# GDPC1: 實質GDP，代表國家整體生產力與經濟成長最終結果。
# FPI / PRFI / SLCEC1: 分別代表固定私人投資、住宅投資與地方政府支出，為 GDP 組成的重要區塊。
# DRBLACBS / DRCCLACBS: 信用卡與商業貸款違約發生率，延遲反映消費與企業的財務健康體質惡化程度。
# IMPGS: 進口實質年增率。國內經濟過熱時進口需求通常強勁，衰退時萎靡。
