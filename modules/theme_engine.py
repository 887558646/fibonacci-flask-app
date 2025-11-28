"""
族群判斷與熱度計算模組
負責將股票對應到族群，並計算各族群的熱度指標。
"""

import re
from typing import Dict, List, Set, Tuple

import pandas as pd


def extract_stock_code_from_company_name(company_str: str) -> Set[str]:
    """
    從「代表公司」字串中提取股票代碼。

    例如：
    - "南亞 (1303)" -> {"1303"}
    - "台積電 (2330)" -> {"2330"}
    - "英偉達 NVIDIA(美股)" -> set()（無台股代碼）

    Args:
        company_str: 代表公司字串

    Returns:
        股票代碼的集合（可能為空）
    """
    # 匹配括號內的 4 位數字
    pattern = r"\((\d{4})\)"
    matches = re.findall(pattern, company_str)
    return set(matches)


def map_stock_to_themes(
    stocks_df: pd.DataFrame, themes_data: Dict
) -> Dict[str, List[str]]:
    """
    將股票列表對應到其所屬的族群（一檔股票可能屬於多個族群）。

    支援兩種 JSON 格式：
    1. 舊格式：{"族群清單": [{"族群名稱": "...", "上游": {"代表公司": [...]}, ...}]}
    2. 新格式：{"popular_sectors": [{"sector_name": "...", "upstream": [{"stocks": [...]}], ...}]}

    Args:
        stocks_df: 股票 DataFrame，需包含 code 欄位
        themes_data: 從 load_supply_chain_json() 載入的族群資料

    Returns:
        字典，key 為股票代碼，value 為該股票所屬的族群名稱列表
    """
    stock_to_themes: Dict[str, List[str]] = {}

    # 建立「股票代碼 -> 族群名稱」的對應表
    theme_to_stocks: Dict[str, Set[str]] = {}

    # 判斷是新格式還是舊格式
    # 支援四種格式：
    # 1. themes_new.json 格式（物件，有 themes 鍵，每個主題有 theme 欄位）
    # 2. 新格式（物件，有 popular_sectors 鍵）
    # 3. 直接陣列格式（陣列，每個元素是族群物件）
    # 4. 舊格式（物件，有 族群清單 鍵）
    
    sectors_list = None
    if isinstance(themes_data, list):
        # 直接陣列格式
        sectors_list = themes_data
    elif "themes" in themes_data:
        # themes_new.json 格式（物件，有 themes 鍵）
        themes_list = themes_data.get("themes", [])
        # 轉換格式：將 theme 欄位轉為 sector_name，intro 轉為 description
        sectors_list = []
        for theme_info in themes_list:
            if not isinstance(theme_info, dict):
                continue
            sector_info = {
                "sector_name": theme_info.get("theme", ""),
                "description": theme_info.get("description", ""),
                "stocks": []
            }
            # 轉換 stocks：將 intro 轉為 description
            stocks = theme_info.get("stocks", [])
            if isinstance(stocks, list):
                for stock in stocks:
                    if isinstance(stock, dict):
                        sector_info["stocks"].append({
                            "ticker": stock.get("ticker", ""),
                            "name": stock.get("name", ""),
                            "description": stock.get("intro", "")  # intro 轉為 description
                        })
            sectors_list.append(sector_info)
    elif "popular_sectors" in themes_data:
        # 新格式（物件，有 popular_sectors 鍵）
        sectors_list = themes_data.get("popular_sectors", [])
    else:
        # 舊格式（物件，有 族群清單 鍵）
        for theme_info in themes_data.get("族群清單", []):
            theme_name = theme_info.get("族群名稱", "")
            theme_to_stocks[theme_name] = set()

            # 遍歷上中下游的所有代表公司
            for stage in ["上游", "中游", "下游"]:
                if stage in theme_info:
                    companies = theme_info[stage].get("代表公司", [])
                    for company_str in companies:
                        codes = extract_stock_code_from_company_name(company_str)
                        theme_to_stocks[theme_name].update(codes)
        # 舊格式處理完畢，直接返回
        # 對每檔股票，找出它屬於哪些族群
        for _, row in stocks_df.iterrows():
            stock_code = str(row["code"]).zfill(4)
            matching_themes = []

            for theme_name, theme_stocks in theme_to_stocks.items():
                if stock_code in theme_stocks:
                    matching_themes.append(theme_name)

            stock_to_themes[stock_code] = matching_themes

        return stock_to_themes
    
    # 處理新格式或直接陣列格式
    if sectors_list is not None:
        for sector_info in sectors_list:
            sector_name = sector_info.get("sector_name", "")
            theme_to_stocks[sector_name] = set()

            # 優先檢查是否有扁平化的 stocks 陣列（頂層）
            if "stocks" in sector_info:
                stocks = sector_info.get("stocks", [])
                if isinstance(stocks, list):
                    for stock in stocks:
                        if isinstance(stock, dict):
                            ticker = stock.get("ticker", "")
                            # 只處理台股代碼（4位數字），跳過 note 等其他欄位
                            if ticker and isinstance(ticker, str) and ticker.isdigit() and len(ticker) == 4:
                                theme_to_stocks[sector_name].add(ticker)
            else:
                # 如果沒有扁平化的 stocks，則從 upstream/midstream/downstream 讀取
                for stage in ["upstream", "midstream", "downstream"]:
                    if stage in sector_info:
                        categories = sector_info[stage]
                        if isinstance(categories, list):
                            for category_info in categories:
                                if isinstance(category_info, dict):
                                    stocks = category_info.get("stocks", [])
                                    if isinstance(stocks, list):
                                        for stock in stocks:
                                            if isinstance(stock, dict):
                                                ticker = stock.get("ticker", "")
                                                # 只處理台股代碼（4位數字），跳過 note 等其他欄位
                                                if ticker and isinstance(ticker, str) and ticker.isdigit() and len(ticker) == 4:
                                                    theme_to_stocks[sector_name].add(ticker)

    # 對每檔股票，找出它屬於哪些族群
    for _, row in stocks_df.iterrows():
        stock_code = str(row["code"]).zfill(4)
        matching_themes = []

        for theme_name, theme_stocks in theme_to_stocks.items():
            if stock_code in theme_stocks:
                matching_themes.append(theme_name)

        stock_to_themes[stock_code] = matching_themes

    return stock_to_themes


def calc_theme_heat(
    stocks_df: pd.DataFrame, stock_to_themes: Dict[str, List[str]]
) -> pd.DataFrame:
    """
    計算每個族群的熱度指標。

    指標包括：
    - count_in_topN: 在 Top N 中出現的檔數
    - avg_turnover: 平均週轉率
    - avg_chg_pct: 平均漲跌幅（若資料中有）

    Args:
        stocks_df: 股票 DataFrame
        stock_to_themes: 從 map_stock_to_themes() 得到的對應關係

    Returns:
        DataFrame，欄位：theme_name, count_in_topN, avg_turnover, avg_chg_pct
        按 count_in_topN（降序）、avg_turnover（降序）排序
    """
    # 統計每個族群
    theme_stats: Dict[str, Dict] = {}

    for _, row in stocks_df.iterrows():
        stock_code = str(row["code"]).zfill(4)
        themes = stock_to_themes.get(stock_code, [])

        for theme_name in themes:
            if theme_name not in theme_stats:
                theme_stats[theme_name] = {
                    "count": 0,
                    "turnover_sum": 0.0,
                    "chg_pct_sum": 0.0,
                    "chg_pct_count": 0,
                }

            theme_stats[theme_name]["count"] += 1
            theme_stats[theme_name]["turnover_sum"] += row["turnover"]

            if pd.notna(row.get("chg_pct")):
                theme_stats[theme_name]["chg_pct_sum"] += row["chg_pct"]
                theme_stats[theme_name]["chg_pct_count"] += 1

    # 轉換成 DataFrame
    results = []
    for theme_name, stats in theme_stats.items():
        count = stats["count"]
        avg_turnover = stats["turnover_sum"] / count if count > 0 else 0.0

        avg_chg_pct = None
        if stats["chg_pct_count"] > 0:
            avg_chg_pct = stats["chg_pct_sum"] / stats["chg_pct_count"]

        results.append({
            "theme_name": theme_name,
            "count_in_topN": count,
            "avg_turnover": round(avg_turnover, 2),
            "avg_chg_pct": round(avg_chg_pct, 2) if avg_chg_pct is not None else None,
        })

    df = pd.DataFrame(results)

    # 如果 DataFrame 為空，返回空的 DataFrame（但要有正確的欄位）
    if df.empty:
        df = pd.DataFrame(columns=["theme_name", "count_in_topN", "avg_turnover", "avg_chg_pct"])
    else:
        # 排序：先按 count_in_topN（降序），再按 avg_turnover（降序）
        df = df.sort_values(
            ["count_in_topN", "avg_turnover"], ascending=[False, False]
        ).reset_index(drop=True)

    return df


def get_stocks_in_theme(
    stocks_df: pd.DataFrame,
    stock_to_themes: Dict[str, List[str]],
    theme_name: str,
) -> pd.DataFrame:
    """
    取得屬於指定族群的所有股票（從 Top N 中）。

    Args:
        stocks_df: 股票 DataFrame
        stock_to_themes: 從 map_stock_to_themes() 得到的對應關係
        theme_name: 族群名稱

    Returns:
        DataFrame，包含該族群的所有股票
    """
    matching_stocks = []

    for _, row in stocks_df.iterrows():
        stock_code = str(row["code"]).zfill(4)
        themes = stock_to_themes.get(stock_code, [])

        if theme_name in themes:
            matching_stocks.append(row.to_dict())

    if not matching_stocks:
        return pd.DataFrame()

    df = pd.DataFrame(matching_stocks)
    # 按週轉率排序
    df = df.sort_values("turnover", ascending=False).reset_index(drop=True)
    return df


def get_all_members_of_theme(theme_name: str, themes_data: Dict) -> List[Dict]:
    """
    取得該族群所有股票（從 all_themes_supply_chain.json 取得）。
    
    Args:
        theme_name: 族群名稱
        themes_data: 從 load_supply_chain_json() 載入的族群資料
    
    Returns:
        該族群所有股票的列表，每個元素包含 ticker, name, description
    """
    # 判斷格式
    sectors_list = None
    if isinstance(themes_data, list):
        sectors_list = themes_data
    elif "themes" in themes_data:
        # themes_new.json 格式（物件，有 themes 鍵）
        themes_list = themes_data.get("themes", [])
        # 轉換格式：將 theme 欄位轉為 sector_name，intro 轉為 description
        sectors_list = []
        for theme_info in themes_list:
            if not isinstance(theme_info, dict):
                continue
            sector_info = {
                "sector_name": theme_info.get("theme", ""),
                "description": theme_info.get("description", ""),
                "stocks": []
            }
            # 轉換 stocks：將 intro 轉為 description
            stocks = theme_info.get("stocks", [])
            if isinstance(stocks, list):
                for stock in stocks:
                    if isinstance(stock, dict):
                        sector_info["stocks"].append({
                            "ticker": stock.get("ticker", ""),
                            "name": stock.get("name", ""),
                            "description": stock.get("intro", "")  # intro 轉為 description
                        })
            sectors_list.append(sector_info)
    elif "popular_sectors" in themes_data:
        sectors_list = themes_data.get("popular_sectors", [])
    else:
        # 舊格式，不支援
        return []
    
    # 尋找對應的族群
    for sector_info in sectors_list:
        if not isinstance(sector_info, dict):
            continue
        
        sector_name = sector_info.get("sector_name", "")
        if sector_name == theme_name:
            # 優先檢查扁平化的 stocks 陣列（頂層）
            if "stocks" in sector_info:
                stocks = sector_info.get("stocks", [])
                if isinstance(stocks, list):
                    # 過濾有效的股票（有 ticker）
                    valid_stocks = []
                    for stock in stocks:
                        if isinstance(stock, dict):
                            ticker = stock.get("ticker", "")
                            if ticker and isinstance(ticker, str) and ticker.isdigit() and len(ticker) == 4:
                                valid_stocks.append({
                                    "ticker": ticker,
                                    "name": stock.get("name", ""),
                                    "description": stock.get("description", "")
                                })
                    return valid_stocks
            else:
                # 如果沒有扁平化的 stocks，則從 upstream/midstream/downstream 讀取
                valid_stocks = []
                for stage in ["upstream", "midstream", "downstream"]:
                    if stage in sector_info:
                        categories = sector_info[stage]
                        if isinstance(categories, list):
                            for category_info in categories:
                                if isinstance(category_info, dict):
                                    stocks = category_info.get("stocks", [])
                                    if isinstance(stocks, list):
                                        for stock in stocks:
                                            if isinstance(stock, dict):
                                                ticker = stock.get("ticker", "")
                                                if ticker and isinstance(ticker, str) and ticker.isdigit() and len(ticker) == 4:
                                                    # 避免重複（同一檔股票可能出現在多個階段）
                                                    if not any(s["ticker"] == ticker for s in valid_stocks):
                                                        valid_stocks.append({
                                                            "ticker": ticker,
                                                            "name": stock.get("name", ""),
                                                            "description": stock.get("description", "")
                                                        })
                return valid_stocks
    
    return []


def get_today_members_of_theme(
    theme_name: str,
    today_df: pd.DataFrame,
    stock_to_themes: Dict[str, List[str]]
) -> List[Dict]:
    """
    取得該族群當天出現的股票（從 today_df 中過濾）。
    
    Args:
        theme_name: 族群名稱
        today_df: 今日股票資料 DataFrame（需包含 code 欄位，可能包含 turnover, chg_pct, is_focus 等）
        stock_to_themes: 從 map_stock_to_themes() 得到的對應關係
    
    Returns:
        該族群今日出現的股票列表，每個元素包含 ticker, name, turnover, chg_pct, is_focus
    """
    today_members = []
    
    for _, row in today_df.iterrows():
        stock_code = str(row["code"]).zfill(4)
        themes = stock_to_themes.get(stock_code, [])
        
        if theme_name in themes:
            member = {
                "ticker": stock_code,
                "name": row.get("name", ""),
            }
            
            # 加入週轉率（如果有）
            if "turnover" in row and pd.notna(row["turnover"]):
                member["turnover"] = float(row["turnover"])
            else:
                member["turnover"] = None
            
            # 加入漲跌幅（如果有）
            if "chg_pct" in row and pd.notna(row["chg_pct"]):
                member["chg_pct"] = float(row["chg_pct"])
            else:
                member["chg_pct"] = None
            
            # 加入是否為注意股（如果有）
            if "is_focus" in row:
                member["is_focus"] = bool(row["is_focus"])
            else:
                member["is_focus"] = False
            
            today_members.append(member)
    
    # 按週轉率排序（降序）
    today_members.sort(key=lambda x: x["turnover"] if x["turnover"] is not None else 0, reverse=True)
    
    return today_members

