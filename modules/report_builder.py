"""
報告資料整理模組
將熱度計算結果、族群說明、成分股整理成適合 Web 顯示的結構。
"""

from typing import Dict, List, Optional

import pandas as pd

import sys
import os
# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme_engine import get_stocks_in_theme, get_all_members_of_theme, get_today_members_of_theme


def build_theme_report(
    stocks_df: pd.DataFrame,
    theme_heat_df: pd.DataFrame,
    stock_to_themes: Dict[str, List[str]],
    themes_data: Dict,
) -> Dict:
    """
    建立完整的族群報告資料結構。

    Args:
        stocks_df: 股票 DataFrame
        theme_heat_df: 從 calc_theme_heat() 得到的熱度 DataFrame
        stock_to_themes: 從 map_stock_to_themes() 得到的對應關係
        themes_data: 從 load_supply_chain_json() 載入的族群資料

    Returns:
        字典，包含：
        - summary: 摘要資訊
        - theme_heat_ranking: 族群熱度排行榜（DataFrame）
        - theme_details: 各族群的詳細資訊
    """
    # 建立族群詳細資訊
    theme_details = {}

    # 判斷是新格式還是舊格式
    # 支援四種格式：
    # 1. themes_new.json 格式（物件，有 themes 鍵）
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
    
    if sectors_list is not None:
        # 新格式或直接陣列格式
        for sector_info in sectors_list:
            sector_name = sector_info.get("sector_name", "")
            description = sector_info.get("description", "")

            # 取得該族群在 Top N 中實際出現的股票
            theme_stocks = get_stocks_in_theme(stocks_df, stock_to_themes, sector_name)

            # 整理供應鏈結構
            supply_chain = {}
            
            # 檢查是否有扁平化的 stocks 陣列（新扁平格式）
            if "stocks" in sector_info:
                # 扁平格式：沒有上中下游，只有單一 stocks 陣列
                # 為了向後相容，我們仍然建立 supply_chain 結構，但將所有 stocks 放在一個類別中
                stocks = sector_info.get("stocks", [])
                valid_stocks = []
                if isinstance(stocks, list):
                    for stock in stocks:
                        if isinstance(stock, dict) and stock.get("ticker"):
                            valid_stocks.append(stock)
                
                # 扁平格式：所有股票放在一個類別中
                supply_chain = {
                    "上游": {"類別": []},
                    "中游": {"類別": []},
                    "下游": {"類別": [{"category": "代表公司", "stocks": valid_stocks}]}
                }
            else:
                # 舊格式：有 upstream/midstream/downstream
                for stage_key, stage_name in [("upstream", "上游"), ("midstream", "中游"), ("downstream", "下游")]:
                    if stage_key in sector_info:
                        categories = sector_info[stage_key]
                        stage_info = {
                            "類別": []
                        }
                        if isinstance(categories, list):
                            for category_info in categories:
                                if isinstance(category_info, dict):
                                    category_name = category_info.get("category", "")
                                    stocks = category_info.get("stocks", [])
                                    # 過濾掉沒有 ticker 的項目（如 note 等）
                                    valid_stocks = []
                                    if isinstance(stocks, list):
                                        for stock in stocks:
                                            if isinstance(stock, dict) and stock.get("ticker"):
                                                valid_stocks.append(stock)
                                    stage_info["類別"].append({
                                        "category": category_name,
                                        "stocks": valid_stocks
                                    })
                        supply_chain[stage_name] = stage_info
                    else:
                        supply_chain[stage_name] = {"類別": []}

            theme_details[sector_name] = {
                "description": description,
                "supply_chain": supply_chain,
                "stocks_in_topN": theme_stocks.to_dict("records") if not theme_stocks.empty else [],
            }
    else:
        # 舊格式
        for theme_info in themes_data.get("族群清單", []):
            theme_name = theme_info.get("族群名稱", "")

            # 取得該族群在 Top N 中實際出現的股票
            theme_stocks = get_stocks_in_theme(stocks_df, stock_to_themes, theme_name)

            theme_details[theme_name] = {
                "supply_chain": {
                    "上游": theme_info.get("上游", {}),
                    "中游": theme_info.get("中游", {}),
                    "下游": theme_info.get("下游", {}),
                },
                "stocks_in_topN": theme_stocks.to_dict("records") if not theme_stocks.empty else [],
            }

    return {
        "summary": {
            "total_stocks": len(stocks_df),
            "total_themes": len(theme_heat_df),
        },
        "theme_heat_ranking": theme_heat_df,
        "theme_details": theme_details,
    }


def get_theme_detail_for_display(
    theme_name: str,
    today_df: pd.DataFrame,
    themes_data: Dict,
    stock_to_themes: Dict[str, List[str]]
) -> Optional[Dict]:
    """
    取得指定族群的詳細資訊（用於 Web 顯示）。
    
    新的簡化版本：不包含 supply_chain 結構，只包含：
    - sector_name: 族群名稱
    - description: 族群說明
    - today_members: 今日出現的族群股票
    - all_members: 該族群所有股票（從 all_themes_supply_chain.json）

    Args:
        theme_name: 族群名稱
        today_df: 今日股票資料 DataFrame
        themes_data: 從 load_supply_chain_json() 載入的族群資料
        stock_to_themes: 從 map_stock_to_themes() 得到的對應關係

    Returns:
        族群詳細資訊字典，若不存在則返回 None
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
        return None
    
    # 尋找對應的族群
    selected_sector = None
    for sector_info in sectors_list:
        if not isinstance(sector_info, dict):
            continue
        sector_name = sector_info.get("sector_name", "")
        if sector_name == theme_name:
            selected_sector = sector_info
            break
    
    if not selected_sector:
        return None
    
    # 取得族群說明
    description = selected_sector.get("description", "")
    
    # 取得今日出現的股票
    today_members = get_today_members_of_theme(theme_name, today_df, stock_to_themes)
    
    # 取得該族群所有股票
    all_members = get_all_members_of_theme(theme_name, themes_data)
    
    return {
        "sector_name": theme_name,
        "description": description,
        "today_members": today_members,
        "all_members": all_members
    }

