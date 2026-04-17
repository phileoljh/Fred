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
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}K", "points": 14, "true_freq": "weekly", "scale": 1000, "decimals": 1},
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "UMCSENT", "name": "密西根大學消費者信心指數 (U.S. Consumer Sentiment)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value} pts", "points": 12, "true_freq": "monthly"},
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4, "true_freq": "quarterly"},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Priority", "category": "榮景期指標 (Priority)", "units": "lin", "format": "{value}%", "points": 4, "true_freq": "quarterly"},

    # 衰退期指標 (Recession)
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Recession", "category": "衰退期指標 (Recession)", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    
    # 復甦期指標 (Recovery)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "lin", "format": "{value}K", "points": 14, "true_freq": "weekly", "scale": 1000, "decimals": 1},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders Excl. Aircraft)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "IMPGS", "name": "商品與服務進口 (Imports of Goods & Services)", "freq": "Recovery", "category": "復甦期指標 (Recovery)", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},

    # Daily (1 Month = ~22-30 points)
    {"id": "T10Y3M", "name": "10年期減3個月期公債利差 (10Y-3M Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "T10Y2Y", "name": "10年期減2年期公債利差 (10Y-2Y Spread)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "IORB", "name": "準備金餘額利率 (IORB)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "SOFR", "name": "擔保隔夜融資利率 (SOFR)", "freq": "Daily", "category": "Rates & Spreads", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "BAMLC0A4CBBB", "name": "美國 BBB 級企業債選擇權調整利差 (US BBB Corporate OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "BAMLH0A0HYM2", "name": "美國高收益債券利差 (US High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "BAMLH0A3HYC", "name": "CCC級及以下高收益債券利差 (CCC High Yield OAS)", "freq": "Daily", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "T10YIE", "name": "10年期平準通膨率 (10-Year Breakeven Inflation Rate)", "freq": "Daily", "category": "Monetary & Inflation", "units": "lin", "format": "{value}%", "points": 30, "true_freq": "daily"},
    {"id": "VIXCLS", "name": "VIX恐慌指數 (CBOE Volatility Index)", "freq": "Daily", "category": "Consumption & Sentiment", "units": "lin", "format": "{value} pts", "points": 30, "true_freq": "daily"},
    
    # Weekly (3 Months = ~13-14 points)
    {"id": "ICSA", "name": "初領失業金人數 (Initial Claims)", "freq": "Weekly", "category": "Labor Market", "units": "lin", "format": "{value}K", "points": 14, "true_freq": "weekly", "scale": 1000, "decimals": 1},
    
    # Monthly (1 Year = 12 points)
    {"id": "PAYEMS", "name": "非農就業人數 (Nonfarm Payrolls)", "freq": "Monthly", "category": "Labor Market", "units": "chg", "format": "{value}K MoM", "points": 12, "true_freq": "monthly", "decimals": 1},
    {"id": "UNRATE", "name": "失業率 (Unemployment Rate)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}%", "points": 12, "true_freq": "monthly"},
    {"id": "ADPMNUSNERSA", "name": "ADP小非農就業人數 (ADP Employment)", "freq": "Monthly", "category": "Labor Market", "units": "chg", "format": "{value}K MoM", "points": 12, "true_freq": "monthly", "scale": 1000, "decimals": 1},
    {"id": "UEMPLT5", "name": "短期失業人數 (Unemployed <5 Weeks)", "freq": "Monthly", "category": "Labor Market", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "JTSJOL", "name": "JOLTS 職缺數 (Job Openings)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}M", "points": 12, "true_freq": "monthly", "scale": 1000, "decimals": 2},
    {"id": "CIVPART", "name": "勞動參與率 (Labor Force Participation Rate)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value}%", "points": 12, "true_freq": "monthly"},
    {"id": "SAHMREALTIME", "name": "薩姆規則衰退指標 (Sahm Rule Indicator)", "freq": "Monthly", "category": "Labor Market", "units": "lin", "format": "{value} pts", "points": 12, "true_freq": "monthly"},
    {"id": "UMCSENT", "name": "密西根大學消費者信心指數 (U.S. Consumer Sentiment)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "lin", "format": "{value} pts", "points": 12, "true_freq": "monthly"},
    {"id": "RSXFS", "name": "零售銷售 (Retail Sales)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "DSPIC96", "name": "實質可支配個人所得 (Real Disposable Personal Income)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "PCEC96", "name": "實質個人消費支出 (Real PCE)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "PCEDGC96", "name": "實質耐久財消費支出 (Real PCE: Durable Goods)", "freq": "Monthly", "category": "Consumption & Sentiment", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "NEWORDER", "name": "核心資本財訂單 (Nondefense Capital Goods Orders Excl. Aircraft)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "INDPRO", "name": "工業生產指數 (Industrial Production)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "BUSINV", "name": "商業庫存 (Business Inventories)", "freq": "Monthly", "category": "Production & Manufacturing", "units": "pc1", "format": "{value}% YoY", "points": 12, "true_freq": "monthly"},
    {"id": "FEDFUNDS", "name": "聯邦基金有效利率 (Federal Funds Rate)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "lin", "format": "{value}%", "points": 12, "true_freq": "monthly"},
    {"id": "CPIAUCSL", "name": "消費者物價指數 (CPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "PCEPILFE", "name": "核心個人消費支出物價指數 (Core PCE Price Index)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "PPIACO", "name": "生產者物價指數 (PPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "PPIFES", "name": "核心生產者物價指數 (Core PPI)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "CES0500000003", "name": "平均每小時薪資 (Average Hourly Earnings)", "freq": "Monthly", "category": "Labor Market", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly"},
    {"id": "RTWEXBGS", "name": "實質廣義美元指數 (Real Broad Dollar Index)", "freq": "Monthly", "category": "Monetary & Inflation", "units": "lin", "format": "{value} pts", "points": 12, "true_freq": "monthly"},
    {"id": "PERMIT", "name": "營建許可 (Building Permits)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}K", "points": 12, "true_freq": "monthly", "decimals": 0},
    {"id": "HOUST", "name": "新屋開工 (Housing Starts)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}K", "points": 12, "true_freq": "monthly", "decimals": 0},
    {"id": "EXHOSLUSM495S", "name": "成屋銷售 (Existing Home Sales)", "freq": "Monthly", "category": "GDP Output", "units": "lin", "format": "{value}M", "points": 12, "true_freq": "monthly", "scale": 1000000, "decimals": 2},
    
    # Quarterly (1 Year = 4 points)
    {"id": "GDPC1", "name": "實質國內生產毛額 (Real GDP)", "freq": "Quarterly", "category": "GDP Output", "units": "pca", "format": "{value}% SAAR", "points": 4, "true_freq": "quarterly"},
    {"id": "FPI", "name": "固定私人投資 (Fixed Private Investment)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    {"id": "PRFI", "name": "私人住宅固定投資 (Private Residential Fixed Investment)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    {"id": "SLCEC1", "name": "州和地方政府消費支出 (State & Local Gov Consumption)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},
    {"id": "DRBLACBS", "name": "商業貸款違約率 (Delinquency Rate: Business Loans)", "freq": "Quarterly", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 4, "true_freq": "quarterly"},
    {"id": "DRCCLACBS", "name": "信用卡違約率 (Delinquency Rate: Credit Card Loans)", "freq": "Quarterly", "category": "Credit Risk", "units": "lin", "format": "{value}%", "points": 4, "true_freq": "quarterly"},
    {"id": "IMPGS", "name": "商品與服務進口 (Imports of Goods & Services)", "freq": "Quarterly", "category": "GDP Output", "units": "pc1", "format": "{value}% YoY", "points": 4, "true_freq": "quarterly"},

    # Liquidity & Money Supply
    {"id": "WALCL", "name": "聯準會總資產 (Fed Balance Sheet)", "freq": "Weekly", "category": "Liquidity & Money Supply", "units": "lin", "format": "{value}T", "points": 14, "true_freq": "weekly", "scale": 1000000, "decimals": 2},
    {"id": "M2SL", "name": "M2 貨幣供給量 (M2 Money Supply)", "freq": "Monthly", "category": "Liquidity & Money Supply", "units": "pch", "format": "{value}% MoM", "points": 12, "true_freq": "monthly", "decimals": 2},
]

# ==========================================
# CHART GROUPS (Multi-series Comparative Analysis)
# ==========================================
CHART_GROUPS = [
    {"name": "實質收入與支出 (Real Income vs. PCE)", "members": ["DSPIC96", "PCEC96"]},
    {"name": "就業市場動能 (Labor Market Dynamics)", "members": ["PAYEMS", "ADPMNUSNERSA"]},
    {"name": "信用利差對比 (Credit Spreads Comparison)", "members": ["BAMLC0A4CBBB", "BAMLH0A0HYM2", "BAMLH0A3HYC"]},
    {"name": "違約風險對比 (Delinquency Rates)", "members": ["DRCCLACBS", "DRBLACBS"]},
    {"name": "通膨指標對比 (Inflation: CPI vs. PPI)", "members": ["CPIAUCSL", "PPIACO"]},
    {"name": "核心通膨對比 (Core Inflation: PCE vs. PPI)", "members": ["PCEPILFE", "PPIFES"]},
    {"name": "殖利率曲線對比 (Yield Curve Comparison)", "members": ["T10Y2Y", "T10Y3M"]},
    {"name": "生產流水線動能 (Manufacturing Pipeline)", "members": ["NEWORDER", "INDPRO", "BUSINV"]},
    {"name": "房地產熱度對比 (Housing Market Activity)", "members": ["HOUST", "EXHOSLUSM495S"]},
]

# ==========================================
# MACRO SCORE MODEL (Two-Tier Weighting System)
# ==========================================
# Defines the multi-tiered scoring system for building the Composite Index.
MACRO_SCORE_MODEL = {
    "Liquidity_and_Credit": {
        "name": "流動性與信用風險",
        "weight": 0.30,
        "indicators": {
            "WALCL": {"polarity": "positive", "sub_weight": 0.4},         # Fed資產負債表
            "M2SL": {"polarity": "positive", "sub_weight": 0.4},          # M2貨幣供給
            "DRCCLACBS": {"polarity": "negative", "sub_weight": 0.1},     # 信用卡違約率
            "DRBLACBS": {"polarity": "negative", "sub_weight": 0.1},      # 商業貸款違約率
        }
    },
    "Inflation_and_Rates": {
        "name": "通膨與利率",
        "weight": 0.25,
        "indicators": {
            "PCEPILFE": {"polarity": "negative", "sub_weight": 0.5},      # 核心PCE (Fed最青睞)
            "CPIAUCSL": {"polarity": "negative", "sub_weight": 0.3},      # CPI (市場情緒最快)
            "PPIFES": {"polarity": "negative", "sub_weight": 0.2},        # 核心PPI (保留核心剔除雜訊)
            "PPIACO": {"polarity": "negative", "sub_weight": 0.0},        # PPI (留查不計分)
            "FEDFUNDS": {"polarity": "negative", "sub_weight": 0.0},      # 聯邦基金利率 (屬落後結果結果, 留查不計分)
            "RTWEXBGS": {"polarity": "negative", "sub_weight": 0.0},      # 廣義美元指數 (留查不計分)
        }
    },
    "Labor_Market": {
        "name": "勞動力市場",
        "weight": 0.25,
        "indicators": {
            "ICSA": {"polarity": "negative", "sub_weight": 0.4},          # 初領失業金
            "PAYEMS": {"polarity": "positive", "sub_weight": 0.3},        # 非農就業
            "UNRATE": {"polarity": "negative", "sub_weight": 0.2},        # 失業率
            "SAHMREALTIME": {"polarity": "negative", "sub_weight": 0.1},  # 薩姆規則
            "CES0500000003": {"polarity": "negative", "sub_weight": 0.0}, # 平均時薪 (留查不計分)
            "ADPMNUSNERSA": {"polarity": "positive", "sub_weight": 0.0},  # ADP就業 (留查不計分)
            "JTSJOL": {"polarity": "positive", "sub_weight": 0.0},        # JOLTS職缺 (留查不計分)
            "CIVPART": {"polarity": "positive", "sub_weight": 0.0},       # 勞動參與率 (留查不計分)
            "UEMPLT5": {"polarity": "negative", "sub_weight": 0.0},       # 短期失業 (留查不計分)
        }
    },
    "GDP_and_Consumption": {
        "name": "經濟產出與消費",
        "weight": 0.20,
        "indicators": {
            "RSXFS": {"polarity": "positive", "sub_weight": 0.4},         # 零售銷售
            "GDPC1": {"polarity": "positive", "sub_weight": 0.2},         # 實質GDP
            "PCEC96": {"polarity": "positive", "sub_weight": 0.2},        # 實質PCE
            "INDPRO": {"polarity": "positive", "sub_weight": 0.1},        # 工業生產
            "NEWORDER": {"polarity": "positive", "sub_weight": 0.1},      # 核心資本財訂單
            "DSPIC96": {"polarity": "positive", "sub_weight": 0.0},       # 實質可支配所得 (留查不計分)
            "PCEDGC96": {"polarity": "positive", "sub_weight": 0.0},      # 耐久財消費 (留查不計分)
            "UMCSENT": {"polarity": "positive", "sub_weight": 0.0},       # 消費者信心 (留查不計分)
            "BUSINV": {"polarity": "neutral", "sub_weight": 0.0},         # 商業庫存 (留查不計分)
            "PERMIT": {"polarity": "positive", "sub_weight": 0.0},        # 營建許可 (留查不計分)
            "HOUST": {"polarity": "positive", "sub_weight": 0.0},         # 新屋開工 (留查不計分)
            "EXHOSLUSM495S": {"polarity": "positive", "sub_weight": 0.0}, # 成屋銷售 (留查不計分)
            "FPI": {"polarity": "positive", "sub_weight": 0.0},           # 固定私人投資 (留查不計分)
            "PRFI": {"polarity": "positive", "sub_weight": 0.0},          # 私人住宅投資 (留查不計分)
            "SLCEC1": {"polarity": "positive", "sub_weight": 0.0},        # 州地方政府支出 (留查不計分)
            "IMPGS": {"polarity": "neutral", "sub_weight": 0.0},          # 進口 (留查不計分)
        }
    }
}

# ==========================================
# INDICATOR EXPLANATIONS (Documentation)
# ==========================================
# < Daily >
# T10Y2Y / T10Y3M: 10年期減2年/3個月期公債利差，被稱為殖利率曲線倒掛與否的關鍵指標，通常領先衰退1年左右。
# IORB: 準備金餘額利率。影響銀行拆款的關鍵利率下限。
# SOFR: 擔保隔夜融資利率。市場上真實的短期無風險借貸成本。
# BAMLH0A0HYM2 / BAMLH0A3HYC / BAMLC0A4CBBB: 高收益債與各級企業債利差，衡量市場恐慌與企業違約風險的信用擴張程度，BBB級為觀察「墮落天使」的重要切入點。
# T10YIE: 10年期平準通膨率，反映債券市場(TIPS)對未來十年平均通膨的市場預期。
# VIXCLS: 恐慌指數，反映市場對未來 30 天 S&P 500 波動率的預期。
#
# < Weekly >
# ICSA: 初領失業救濟金人數。最即時反映就業市場榮枯的高頻數據。
# WALCL: 聯準會總資產（資產負債表規模）。QE/QT 操作的直接觀察指標，數字縮減代表聯準會正在收緊流動性。
#
# < Monthly >
# PAYEMS / ADPMNUSNERSA: (大/小)非農就業人數，觀察就業市場新增動能的核心指標 (MoM 月增減)。
# UNRATE: 失業率。勞動市場最核心的落後指標，但也最容易被一般大眾理解，上升代表景氣放緩。
# UEMPLT5: 短期失業人數，當經濟剛轉弱時，這數據會率先攀升。
# SAHMREALTIME: 薩姆規則衰退指標，當失業率三個月移動平均比過去12個月低點高出 0.5% 時，通常代表經濟已進入衰退。
# CES0500000003: 平均每小時薪資月增率 (MoM)。觀察有無「薪資-物價螺旋上升」的關鍵指標，也是服務業通膨的重點。
# JTSJOL: 職缺數。勞動力市場的「需求面」，以百萬(M)人計。
# CIVPART: 勞動參與率。就業市場結構健康的指標，影響失業率解讀。
# RSXFS / PCEC96 / PCEDGC96 / DSPIC96: 零售銷售、實質/耐久財消費支出及實質可支配所得，由於美國是消費大國，反映民眾最真實的收入與消費狀況。
# UMCSENT: 密大消費者信心，先行反映消費者未來的消費意願與通膨預期。
# NEWORDER / INDPRO / BUSINV: 涵蓋生產流水線：下單(NEWORDER) -> 製造(INDPRO) -> 堆貨庫存(BUSINV)。
# FEDFUNDS: 美國聯邦基金利率(聯準會基準利率)。
# CPIAUCSL / PCEPILFE / PPIACO / PPIFES: 觀察美國消費者物價及聯準會最看重的核心PCE(月增率MoM)，與生產端出廠物價的變化。
# RTWEXBGS: 實質廣義美元指數。衡量美元相對主要貿易夥伴貨幣的強弱，美元走強通常壓制大宗商品與新興市場。
# M2SL: M2 貨幣供給量。廣義貨幣總量，觀察貨幣寬鬆或緊縮的長期趨勢。
# HOUST / PERMIT: 新屋開工與營建許可。房市的先行指標，帶動後續的一連串住宅相關消費跟銀行貸款。
# EXHOSLUSM495S: 成屋銷售。佔據房地產市場大宗交易，了解整體房價熱度與庫存去化速度。
#
# < Quarterly >
# GDPC1: 實質GDP，代表國家整體生產力與經濟成長最終結果。
# FPI / PRFI / SLCEC1: 分別代表固定私人投資、住宅投資與地方政府支出，為 GDP 組成的重要區塊。
# DRBLACBS / DRCCLACBS: 信用卡與商業貸款違約發生率，延遲反映消費與企業的財務健康體質惡化程度。
# IMPGS: 進口實質年增率。國內經濟過熱時進口需求通常強勁，衰退時萎靡。
