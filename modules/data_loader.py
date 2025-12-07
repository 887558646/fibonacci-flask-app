"""
資料載入模組
負責從各種來源載入當日 Top N 週轉率股票資料，以及族群供應鏈 JSON 定義檔。
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import sys
import os
# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scraper


def load_supply_chain_json(json_path: Optional[str] = None, use_session_state: bool = True) -> Dict:
    """
    載入族群供應鏈 JSON 定義檔。

    優先順序：
    1. Session State 中的自訂族群資料（如果 use_session_state=True）
    2. 指定的 json_path（如果提供）
    3. themes_new.json
    4. all_themes_supply_chain.json
    5. data/themes_supply_chain.json

    Args:
        json_path: JSON 檔案路徑，若為 None 則使用預設路徑
        use_session_state: 是否優先使用 session_state 中的自訂族群資料

    Returns:
        包含族群清單的字典
    """
    # 不再使用 session_state 中的自訂族群資料（族群管理功能已移除）
    # 系統只使用 themes_new.json（唯讀）
    
    if json_path is None:
        # 使用相對路徑，從 final 資料夾出發
        # __file__ 是 final/modules/data_loader.py
        # parent.parent 是 final 資料夾
        base_path = Path(__file__).parent.parent
        
        # 優先讀取 themes_new.json（在 final 資料夾中）
        themes_new_path = base_path / "themes_new.json"
        if themes_new_path.exists():
            json_path = themes_new_path
        else:
            # 其次嘗試從小工具資料夾找
            parent_path = base_path.parent
            themes_new_path = parent_path / "小工具" / "themes_new.json"
            if themes_new_path.exists():
                json_path = themes_new_path
            else:
                # 最後嘗試其他可能的路徑
                all_themes_path = base_path / "all_themes_supply_chain.json"
            if all_themes_path.exists():
                json_path = all_themes_path
            else:
                json_path = base_path / "data" / "themes_supply_chain.json"

    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"找不到族群定義檔: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def load_full_supply_chain(path: Optional[str] = None) -> List[Dict]:
    """
    載入完整供應鏈 JSON。
    
    讀取 all_themes_supply_chain.json（合併後的完整檔案，包含 stocks 陣列和上中下游結構）。
    如果不存在，則嘗試讀取 suppy_chain.json 作為備用。
    
    檔案格式預期為 JSON array，每個元素為一個族群物件。
    此函式用於「產業鏈學習模式」，提供完整的上下游結構。
    
    Args:
        path: JSON 檔案路徑，若為 None 則使用預設路徑（優先 all_themes_supply_chain.json）
    
    Returns:
        族群列表，每個元素是一個族群物件（包含 sector_name, description, 
        upstream, midstream, downstream, related_sectors 等）
    
    Raises:
        FileNotFoundError: 檔案不存在
        json.JSONDecodeError: JSON 格式錯誤
    """
    # __file__ 是 final/modules/data_loader.py
    # parent.parent 是 final 資料夾
    base_path = Path(__file__).parent.parent
    
    if path is None:
        # 優先讀取 all_themes_supply_chain.json（合併後的完整檔案）
        all_themes_path = base_path / "all_themes_supply_chain.json"
        if all_themes_path.exists():
            json_path = all_themes_path
        else:
            # 備用：讀取 suppy_chain.json（僅在 all_themes_supply_chain.json 不存在時使用）
            json_path = base_path / "suppy_chain.json"
            if not json_path.exists():
                # 嘗試其他可能的路徑
                alt_path = base_path / "supply_chain.json"
                if alt_path.exists():
                    json_path = alt_path
                else:
                    return []
    else:
        json_path = base_path / path
        if not json_path.exists():
            return []
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 確保回傳的是 list
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "popular_sectors" in data:
        return data.get("popular_sectors", [])
    else:
        return []


def load_today_topN_from_csv(csv_path: str, top_n: int = 50) -> pd.DataFrame:
    """
    從本地 CSV 檔案載入當日 Top N 週轉率股票資料。

    CSV 欄位預期：
    - code: 股票代碼（4 位數字字串）
    - name: 股票名稱
    - turnover: 週轉率（float）
    - close: 收盤價（float）
    - chg_pct: 漲跌幅%（float，可選）

    Args:
        csv_path: CSV 檔案路徑
        top_n: 取前 N 檔

    Returns:
        DataFrame，包含 code, name, turnover, close, chg_pct 欄位
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到 CSV 檔案: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8")

    # 確保必要欄位存在
    required_cols = ["code", "name", "turnover"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV 缺少必要欄位: {missing_cols}")

    # 標準化欄位名稱（處理可能的變體）
    col_mapping = {
        "股票代碼": "code",
        "股票名稱": "name",
        "週轉率": "turnover",
        "收盤價": "close",
        "漲跌幅": "chg_pct",
    }
    df = df.rename(columns=col_mapping)

    # 確保 code 是字串，補零到 4 位
    df["code"] = df["code"].astype(str).str.zfill(4)

    # 確保 turnover 是數值
    df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")

    # 按週轉率排序，取 Top N
    df = df.sort_values("turnover", ascending=False).head(top_n).reset_index(drop=True)

    # 確保有 close 和 chg_pct 欄位（若不存在則設為 NaN）
    if "close" not in df.columns:
        df["close"] = None
    if "chg_pct" not in df.columns:
        df["chg_pct"] = None

    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["chg_pct"] = pd.to_numeric(df["chg_pct"], errors="coerce")

    return df[["code", "name", "turnover", "close", "chg_pct"]]


def load_today_topN(top_n: Optional[int] = None, source: str = "paste", pasted_text: Optional[str] = None) -> pd.DataFrame:
    """
    載入當日 Top N 週轉率股票資料（主要入口函式）。

    目前支援：
    - "paste": 從貼上的文字解析資料（推薦）
    - "web": 自動從網路抓取（玩股網）
    - "api": 從 TWSE 和 TPEx 官方 API 抓取並計算週轉率（推薦，最準確）
    - "mock": 產生假資料（用於測試）

    Args:
        top_n: 取前 N 檔（None 表示不限制，分析所有資料）
        source: 資料來源
        pasted_text: 貼上的文字內容（當 source="paste" 時使用）

    Returns:
        DataFrame，包含 code, name, turnover, close, chg_pct 欄位
    """
    if source == "paste":
        if not pasted_text:
            raise ValueError("使用 'paste' 來源時，必須提供 pasted_text 參數")
        return _parse_pasted_data(pasted_text, top_n)
    elif source == "mock":
        return _generate_mock_data(top_n if top_n else 50)
    elif source == "web":
        return scraper.fetch_turnover_rank_data(top_n)
    elif source == "api":
        return scraper.fetch_turnover_from_api(top_n if top_n else 50)
    else:
        return _generate_mock_data(top_n if top_n else 50)


def _parse_pasted_data(pasted_text: str, top_n: Optional[int] = None) -> pd.DataFrame:
    """
    解析貼上的表格資料。
    
    支援多種格式：
    - Tab 分隔
    - 多個空格分隔
    - 包含表頭的表格
    
    Args:
        pasted_text: 貼上的文字內容
        top_n: 取前 N 檔（None 表示不限制，分析所有資料）
    
    Returns:
        DataFrame，包含 code, name, turnover, close, chg_pct 欄位
    """
    lines = pasted_text.strip().split('\n')
    if not lines:
        raise Exception("貼上的資料為空")
    
    data = []
    
    # 尋找表頭行（包含「代碼」、「股票」、「週轉率」等關鍵字）
    header_line_idx = -1
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ['代碼', '股票', '週轉率', '周轉率', '成交價', '收盤']):
            header_line_idx = i
            break
    
    # 如果找到表頭，從下一行開始解析資料
    start_idx = header_line_idx + 1 if header_line_idx >= 0 else 0
    
    # 解析每一行資料
    for line in lines[start_idx:]:
        line = line.strip()
        if not line:
            continue
        
        # 移除特殊符號（▲ ▼）
        line_cleaned = line.replace('▲', '').replace('▼', '').strip()
        
        # 嘗試用 tab 分隔（優先）
        if '\t' in line:
            parts = [p.strip() for p in line_cleaned.split('\t')]
        else:
            # 用多個空格分隔
            parts = [p.strip() for p in re.split(r'\s{2,}', line_cleaned)]
        
        if len(parts) < 3:
            continue
        
        try:
            # 根據欄位位置直接提取（Tab 分隔的格式較固定）
            # 格式：排名	代碼	股票	成交價	漲跌	漲跌%	周漲跌%	振幅%	最高	最低	成交量	成交值 (億)	周轉率%
            
            # 尋找各欄位
            code_text = ""
            name_text = ""
            turnover_text = ""
            close_text = ""
            chg_pct_text = ""
            
            # 方法1：如果欄位數量足夠，嘗試按位置提取
            if len(parts) >= 13:
                # 標準格式：排名(0)	代碼(1)	股票(2)	成交價(3)	漲跌(4)	漲跌%(5)	周漲跌%(6)	振幅%(7)	最高(8)	最低(9)	成交量(10)	成交值(11)	周轉率%(12)
                if len(parts[1]) == 4 and parts[1].isdigit():
                    code_text = parts[1]
                if parts[2] and any(c >= '\u4e00' and c <= '\u9fff' for c in parts[2]):
                    name_text = parts[2]
                if parts[3]:
                    close_text = parts[3].replace(",", "")
                if parts[5]:
                    chg_pct_text = parts[5].replace("%", "").replace("+", "").replace(",", "")
                if parts[12]:
                    turnover_text = parts[12].replace("%", "").replace(",", "")
            
            # 方法2：如果方法1失敗，使用原本的智能識別
            if not code_text or not turnover_text:
                for idx, part in enumerate(parts):
                    # 尋找 4 位數字（股票代碼）
                    if not code_text:
                        code_match = re.search(r'\b(\d{4})\b', part)
                        if code_match:
                            code_text = code_match.group(1)
                            continue
                    
                    # 尋找週轉率（包含 %，且不是漲跌幅）
                    if "%" in part and not turnover_text:
                        # 排除漲跌幅（通常有 + 或 -，或在特定位置）
                        if "+" not in part and "-" not in part and "周轉率" not in part and "週轉率" not in part:
                            # 週轉率通常在最後幾欄
                            if idx >= len(parts) - 3:
                                turnover_text = part.replace("%", "").replace(",", "").strip()
                                continue
                    
                    # 尋找漲跌幅（包含 % 和 + 或 -）
                    if ("+" in part or "-" in part) and "%" in part and not chg_pct_text:
                        # 漲跌幅通常在前面幾欄（第5或第6欄）
                        if 4 <= idx <= 6:
                            chg_pct_text = part.replace("%", "").replace("+", "").replace(",", "").strip()
                            continue
                    
                    # 尋找價格（數字，有小數點，通常在合理範圍內）
                    if "." in part and not close_text:
                        try:
                            price = float(part.replace(",", "").replace("$", ""))
                            if 1 <= price <= 10000:  # 合理的股價範圍
                                # 成交價通常在代碼後面（第3或第4欄）
                                if 2 <= idx <= 4:
                                    close_text = part.replace(",", "").replace("$", "")
                                    continue
                        except:
                            pass
                    
                    # 尋找中文股票名稱（至少 2 個中文字）
                    if not name_text:
                        chinese_match = re.search(r'[\u4e00-\u9fff]{2,}', part)
                        if chinese_match:
                            name_text = chinese_match.group(0)
                            continue
            
            # 如果沒有找到代碼，嘗試從第二欄提取（通常是代碼位置）
            if not code_text and len(parts) >= 2:
                if parts[1].isdigit() and len(parts[1]) == 4:
                    code_text = parts[1]
            
            # 驗證代碼
            if not code_text or not code_text.isdigit() or len(code_text) != 4:
                continue
            
            # 轉換資料格式
            try:
                turnover = float(turnover_text) if turnover_text else 0.0
                close = float(close_text) if close_text else None
                chg_pct = float(chg_pct_text) if chg_pct_text else None
            except ValueError:
                continue
            
            # 只保留有週轉率的資料
            if turnover > 0:
                data.append({
                    "code": code_text.zfill(4),
                    "name": name_text if name_text else "",
                    "turnover": turnover,
                    "close": close,
                    "chg_pct": chg_pct,
                })
        except Exception as e:
            # 跳過無法解析的行
            continue
    
    if not data:
        raise Exception("無法從貼上的資料中提取股票資訊。請確認資料格式是否正確。")
    
    # 轉換為 DataFrame
    df = pd.DataFrame(data)
    df["code"] = df["code"].astype(str).str.zfill(4)
    df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["chg_pct"] = pd.to_numeric(df["chg_pct"], errors="coerce")
    
    # 按週轉率排序
    df = df.sort_values("turnover", ascending=False).reset_index(drop=True)
    
    # 如果指定了 top_n，才限制數量
    if top_n is not None and top_n > 0:
        df = df.head(top_n)
    
    return df[["code", "name", "turnover", "close", "chg_pct"]]


def parse_focus_stock_list(raw_text: str) -> pd.DataFrame:
    """
    解析使用者貼上的注意股公告文字，只抽出「股票代碼 + 股票名稱」。

    輸入：
        raw_text: 使用者從證交所/公開資訊觀測站複製貼上的整段文字

    輸出：
        DataFrame，至少包含欄位：
            - code: 4 位數字字串，例如 "2375"
            - name: 股票名稱，例如 "凱美"

    規則：
        - 掃過整段文字，每一行中如果是一行形如 2375凱美、1815富喬 這種
          「4 碼數字 + 至少一個中文字」的，就視為一筆股票
        - 自動切割：前 4 碼 → code，後面全部 → name
        - 忽略空行、標題行（例如「股票名稱 事項」）、純中文行（只有說明文字那種）
        - 不需要解析「事項」那一行文字（漲幅幾%、第幾款等等全部略過）
    """
    if not raw_text or not raw_text.strip():
        return pd.DataFrame(columns=["code", "name"])

    lines = raw_text.strip().split("\n")
    stocks = []

    # 正則表達式：匹配「4位數字 + 至少一個中文字」的格式
    # 例如：1326台化、1815富喬、2375凱美
    # 使用非貪婪匹配，只取到第一個中文字後的所有內容（可能包含其他字元）
    pattern = re.compile(r"^(\d{4})([\u4e00-\u9fff].*?)$")

    for line in lines:
        line = line.strip()
        if not line:
            continue  # 跳過空行

        # 跳過標題行（包含「股票名稱」、「事項」等關鍵字）
        if "股票名稱" in line or "事項" in line:
            continue

        # 嘗試匹配「4位數字 + 中文名稱」的格式
        match = pattern.match(line)
        if match:
            code = match.group(1)  # 前4碼數字
            name = match.group(2).strip()  # 後面的中文名稱

            # 確保 code 是 4 位數字字串
            if code.isdigit() and len(code) == 4:
                stocks.append({"code": code, "name": name})

    if not stocks:
        return pd.DataFrame(columns=["code", "name"])

    df = pd.DataFrame(stocks)

    # 去重（同一檔股票可能出現多次）
    df = df.drop_duplicates(subset=["code"], keep="first").reset_index(drop=True)

    return df


def load_attention_stocks_from_web() -> pd.DataFrame:
    """
    從網路抓取注意股資料（MoneyDJ）。
    
    Returns:
        DataFrame，包含 code, name
    """
    return scraper.fetch_attention_stock_data()


def _generate_mock_data(top_n: int = 50) -> pd.DataFrame:
    """
    產生假資料用於測試（包含一些真實的台股代碼與名稱）。

    Args:
        top_n: 產生幾檔股票

    Returns:
        DataFrame
    """
    import random

    # 一些真實的台股代碼與名稱（涵蓋不同族群）
    mock_stocks = [
        ("2313", "華通", 15.5, 85.2, 2.3),
        ("3037", "欣興", 12.8, 245.0, 1.8),
        ("3189", "景碩", 8.5, 156.5, -0.5),
        ("3711", "日月光", 6.2, 142.3, 0.8),
        ("2308", "台達電", 4.8, 385.0, 1.2),
        ("2382", "廣達", 9.1, 285.5, 2.5),
        ("6669", "緯穎", 7.3, 1980.0, 3.1),
        ("2330", "台積電", 3.5, 580.0, 0.5),
        ("2454", "聯發科", 5.2, 1250.0, 1.5),
        ("3324", "雙鴻", 11.2, 456.0, 4.2),
        ("3017", "奇鋐", 9.8, 380.0, 3.8),
        ("2059", "川湖", 6.5, 1250.0, 2.1),
        ("1609", "大亞", 8.2, 45.5, 1.5),
        ("1519", "華城", 12.5, 285.0, 5.2),
        ("1513", "中興電", 10.8, 125.0, 3.5),
        ("8046", "南電", 7.8, 320.0, 2.8),
        ("4958", "臻鼎-KY", 5.5, 185.0, 1.2),
        ("1815", "富喬", 9.5, 28.5, 2.5),
        ("3260", "威剛", 8.8, 95.0, 1.8),
        ("3035", "智原", 6.8, 420.0, 2.2),
    ]

    # 如果 top_n 超過 mock_stocks 數量，重複使用並加入隨機變動
    data = []
    for i in range(top_n):
        stock = mock_stocks[i % len(mock_stocks)]
        code, name, base_turnover, base_close, base_chg = stock

        # 加入一些隨機變動，讓資料更真實
        turnover = base_turnover * (0.8 + random.random() * 0.4)
        close = base_close * (0.95 + random.random() * 0.1)
        chg_pct = base_chg + (random.random() - 0.5) * 2

        data.append({
            "code": code,
            "name": name,
            "turnover": round(turnover, 2),
            "close": round(close, 2),
            "chg_pct": round(chg_pct, 2),
        })

    df = pd.DataFrame(data)

    # 按週轉率排序
    df = df.sort_values("turnover", ascending=False).reset_index(drop=True)

    return df
