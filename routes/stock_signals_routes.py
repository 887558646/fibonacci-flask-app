from flask import Blueprint, request
import numpy as np
import pandas as pd
import requests
import warnings
import logging
from datetime import datetime, timedelta
import time
import math
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

signals_bp = Blueprint('signals', __name__)
import sys
import os
# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 抑制警告訊息
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.ERROR)

# 配置日誌
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 嘗試導入 yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance 未安裝，將僅使用台灣證交所 API")


def get_tick_size(price):
    """
    根據價格獲取台股 Tick Size
    規則：
    - < 10: 0.01
    - 10-50: 0.05
    - 50-100: 0.10
    - 100-500: 0.50
    - 500-1000: 1.00
    - >= 1000: 5.00
    """
    if price < 10:
        return 0.01
    elif price < 50:
        return 0.05
    elif price < 100:
        return 0.10
    elif price < 500:
        return 0.50
    elif price < 1000:
        return 1.00
    else:
        return 5.00


def adjust_to_tick(price, direction):
    """
    將價格調整到符合台股 Tick Size 規則的核心修正函數
    
    參數:
        price: 原始價格
        direction: 'resistance' (壓力/擴展) 或 'support' (支撐/回撤)
    
    規則:
        - direction='resistance' (壓力/擴展): 向下取整 (floor)，取最接近且小於或等於 price 的 Tick 價格
        - direction='support' (支撐/回撤): 向上取整 (ceil)，取最接近且大於或等於 price 的 Tick 價格
    
    返回:
        調整後的價格（符合台股 Tick Size 規則）
    """
    tick_size = get_tick_size(price)
    
    if direction == 'resistance':
        # 壓力/擴展：向下取整 (floor)，取最接近且小於或等於 price 的 Tick 價格
        adjusted_price = math.floor(price / tick_size) * tick_size
    elif direction == 'support':
        # 支撐/回撤：向上取整 (ceil)，取最接近且大於或等於 price 的 Tick 價格
        adjusted_price = math.ceil(price / tick_size) * tick_size
    else:
        # 預設行為：不調整
        adjusted_price = price
    
    return round(adjusted_price, 2)


def calculate_kdj(high, low, close, period=9, k_period=3, d_period=3):
    """
    計算 KDJ 指標
    參數: period=9, k_period=3, d_period=3
    """
    # 轉換為 pandas Series 以便使用 rolling
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    close_series = pd.Series(close)
    
    # 計算 RSV
    lowest_low = low_series.rolling(window=period, min_periods=1).min()
    highest_high = high_series.rolling(window=period, min_periods=1).max()
    
    rsv = ((close_series - lowest_low) / (highest_high - lowest_low) * 100).fillna(50)
    
    # 計算 K 值（使用 EMA，平滑係數為 1/3）
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    k = k.fillna(50)
    
    # 計算 D 值（K 值的 EMA）
    d = k.ewm(alpha=1/3, adjust=False).mean()
    d = d.fillna(50)
    
    return k.values, d.values


def get_twse_stock_data(stock_no, days=180):
    """
    從台灣證交所 API 獲取股票數據（改進版：支援重試、更長超時、詳細日誌）
    
    參數:
        stock_no: 股票代碼（4位數字，例如 "2330"）
        days: 需要獲取的天數
    
    返回:
        pandas DataFrame 包含 Open, High, Low, Close, Volume 欄位
    """
    # 配置重試策略
    try:
        retry_strategy = Retry(
            total=3,  # 總共重試 3 次
            backoff_factor=1,  # 重試間隔：1秒、2秒、4秒
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重試的 HTTP 狀態碼
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
    except Exception:
        # 如果 urllib3 版本較舊，使用簡單的 session
        adapter = HTTPAdapter()
    
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.twse.com.tw/',
    })
    
    all_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 台灣證交所 API 一次只能獲取一個月的數據，需要逐月獲取
    # 從起始月份的第一天開始，逐月獲取
    current_month = start_date.replace(day=1)
    end_month = end_date.replace(day=1)
    
    total_months = (end_month.year - current_month.year) * 12 + (end_month.month - current_month.month) + 1
    logger.info(f"開始獲取股票 {stock_no} 的數據，共需獲取 {total_months} 個月的數據")
    
    month_count = 0
    while current_month <= end_month:
        month_count += 1
        # 格式化日期為 YYYYMMDD（取該月第一天）
        date_str = current_month.strftime('%Y%m%d')
        
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
                params = {
                    'response': 'json',
                    'date': date_str,
                    'stockNo': stock_no
                }
                
                # 增加超時時間到 30 秒，適應 Render 的網路環境
                response = session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # 檢查 API 回應
                if data.get('stat') == 'OK' and 'data' in data:
                    # 解析數據
                    row_count = 0
                    for row in data['data']:
                        try:
                            # 日期格式：民國年/MM/DD，需要轉換為西元年
                            date_str_row = row[0].strip()
                            date_parts = date_str_row.split('/')
                            if len(date_parts) == 3:
                                roc_year = int(date_parts[0])
                                year = roc_year + 1911  # 轉換為西元年
                                month = int(date_parts[1])
                                day = int(date_parts[2])
                                
                                date = datetime(year, month, day)
                                if start_date <= date <= end_date:
                                    # 台灣證交所 API 數據格式：
                                    # [0]日期, [1]成交股數, [2]成交金額, [3]開盤, [4]最高, [5]最低, [6]收盤, [7]漲跌價差, [8]成交筆數
                                    open_price = float(str(row[3]).replace(',', '').replace('--', '0'))
                                    high_price = float(str(row[4]).replace(',', '').replace('--', '0'))
                                    low_price = float(str(row[5]).replace(',', '').replace('--', '0'))
                                    close_price = float(str(row[6]).replace(',', '').replace('--', '0'))
                                    
                                    # 成交量（成交股數）
                                    volume_str = str(row[1]).replace(',', '').replace('--', '0')
                                    volume = int(float(volume_str)) if volume_str else 0
                                    
                                    all_data.append({
                                        'Date': date,
                                        'Open': open_price,
                                        'High': high_price,
                                        'Low': low_price,
                                        'Close': close_price,
                                        'Volume': volume
                                    })
                                    row_count += 1
                        except (ValueError, IndexError, TypeError) as e:
                            # 跳過無法解析的數據
                            continue
                    
                    if row_count > 0:
                        logger.info(f"成功獲取 {current_month.strftime('%Y-%m')} 的數據，共 {row_count} 筆")
                        success = True
                    else:
                        logger.warning(f"{current_month.strftime('%Y-%m')} 的數據為空")
                        success = True  # 即使沒有數據，也算成功（可能是非交易日）
                elif data.get('stat') != 'OK':
                    error_msg = data.get('message', 'Unknown error')
                    logger.warning(f"API 返回錯誤狀態: {error_msg} (月份: {current_month.strftime('%Y-%m')})")
                    if '很抱歉' in str(error_msg) or '沒有符合條件的資料' in str(error_msg):
                        # 該月份沒有數據，視為成功
                        success = True
                    else:
                        retry_count += 1
                else:
                    logger.warning(f"API 回應格式異常 (月份: {current_month.strftime('%Y-%m')})")
                    retry_count += 1
                
            except requests.exceptions.Timeout:
                retry_count += 1
                logger.warning(f"請求超時 (月份: {current_month.strftime('%Y-%m')}, 重試 {retry_count}/{max_retries})")
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # 指數退避
            except requests.exceptions.RequestException as e:
                retry_count += 1
                logger.warning(f"請求失敗: {str(e)} (月份: {current_month.strftime('%Y-%m')}, 重試 {retry_count}/{max_retries})")
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # 指數退避
            except Exception as e:
                logger.error(f"處理數據時發生錯誤: {str(e)} (月份: {current_month.strftime('%Y-%m')})")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)
        
        # 避免請求過於頻繁（增加延遲時間）
        time.sleep(1.0)  # 增加到 1 秒，避免觸發 API 頻率限制
        
        # 移到下一個月
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    if not all_data:
        logger.error(f"無法獲取股票 {stock_no} 的任何數據")
        return None
    
    # 轉換為 DataFrame
    df = pd.DataFrame(all_data)
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)
    
    # 確保欄位名稱與 yfinance 格式一致
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    logger.info(f"成功獲取股票 {stock_no} 的數據，共 {len(df)} 筆")
    
    return df


def try_get_stock_data_yfinance(ticker):
    """
    使用 yfinance 獲取股票數據（第一順位）
    返回: (daily_data, weekly_data, stock_info, error_msg) 或 (None, None, None, error_msg) 如果失敗
    """
    if not YFINANCE_AVAILABLE:
        return None, None, None, "yfinance 未安裝"
    
    try:
        # 嘗試 .TW 和 .TWO 兩種格式
        tickers_to_try = [f"{ticker}.TW", f"{ticker}.TWO"]
        
        for ticker_with_suffix in tickers_to_try:
            try:
                logger.info(f"嘗試使用 yfinance 獲取 {ticker_with_suffix} 的數據")
                stock = yf.Ticker(ticker_with_suffix)
                
                # 獲取日線數據（最近 180 天）
                daily_data = stock.history(period="6mo")
                
                if daily_data is None or daily_data.empty:
                    logger.warning(f"yfinance 無法獲取 {ticker_with_suffix} 的日線數據")
                    continue
                
                # 獲取週線數據（最近 2 年）
                weekly_data_full = stock.history(period="2y")
                
                if weekly_data_full is None or weekly_data_full.empty:
                    logger.warning(f"yfinance 無法獲取 {ticker_with_suffix} 的週線數據")
                    continue
                
                # 將日線數據轉換為週線數據
                weekly_data = weekly_data_full.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
                
                # 獲取股票資訊
                stock_info = {}
                try:
                    info = stock.info
                    if info:
                        stock_info['longName'] = info.get('longName', info.get('shortName', ticker))
                except:
                    stock_info['longName'] = ticker
                
                logger.info(f"成功使用 yfinance 獲取 {ticker_with_suffix} 的數據")
                return daily_data, weekly_data, stock_info, None
                
            except Exception as e:
                logger.warning(f"yfinance 獲取 {ticker_with_suffix} 失敗: {str(e)}")
                continue
        
        return None, None, None, f"yfinance 無法獲取股票代碼 {ticker} 的數據（已嘗試 .TW 和 .TWO）"
    
    except Exception as e:
        return None, None, None, f"使用 yfinance 獲取股票數據時發生錯誤: {str(e)}"


def try_get_stock_data_twse(stock_no):
    """
    使用台灣證交所 API 獲取股票數據（第二順位）
    返回: (daily_data, weekly_data, stock_info, error_msg) 或 (None, None, None, error_msg) 如果失敗
    """
    try:
        logger.info(f"嘗試使用台灣證交所 API 獲取 {stock_no} 的數據")
        
        # 獲取日線數據（最近 180 天）
        daily_data = get_twse_stock_data(stock_no, days=180)
        
        if daily_data is None or daily_data.empty:
            return None, None, None, f"無法從台灣證交所獲取股票代碼 {stock_no} 的日線數據"
        
        # 獲取週線數據（最近 2 年，用於計算週線指標）
        weekly_data_full = get_twse_stock_data(stock_no, days=730)
        
        if weekly_data_full is None or weekly_data_full.empty:
            return None, None, None, f"無法從台灣證交所獲取股票代碼 {stock_no} 的週線數據"
        
        # 將日線數據轉換為週線數據（取每週最後一個交易日的數據）
        weekly_data = weekly_data_full.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        # 獲取股票名稱（從證交所 API）
        stock_info = {}
        try:
            # 嘗試獲取股票名稱
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': datetime.now().strftime('%Y%m%d'),
                'stockNo': stock_no
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('stat') == 'OK' and 'title' in data:
                    # 從 title 中提取股票名稱
                    title = data['title']
                    # title 格式通常是 "2330 台積電 個股日成交資訊"
                    parts = title.split()
                    if len(parts) >= 2:
                        stock_info['longName'] = parts[1]
        except:
            pass
        
        logger.info(f"成功使用台灣證交所 API 獲取 {stock_no} 的數據")
        return daily_data, weekly_data, stock_info, None
    
    except Exception as e:
        return None, None, None, f"獲取股票數據時發生錯誤: {str(e)}"


def get_stock_data(ticker):
    """
    獲取股票數據：優先使用 yfinance，失敗後使用台灣證交所 API
    返回: (daily_data, weekly_data, stock_info, error_msg, data_source)
    """
    # 先嘗試 yfinance（第一順位）
    daily_data, weekly_data, stock_info, error_msg = try_get_stock_data_yfinance(ticker)
    
    if daily_data is not None and weekly_data is not None:
        logger.info(f"使用 yfinance 成功獲取 {ticker} 的數據")
        return daily_data, weekly_data, stock_info, None, "yfinance"
    
    # yfinance 失敗，嘗試台灣證交所 API（第二順位）
    logger.info(f"yfinance 失敗，嘗試使用台灣證交所 API 獲取 {ticker} 的數據")
    daily_data, weekly_data, stock_info, error_msg = try_get_stock_data_twse(ticker)
    
    if daily_data is not None and weekly_data is not None:
        logger.info(f"使用台灣證交所 API 成功獲取 {ticker} 的數據")
        return daily_data, weekly_data, stock_info, None, "TWSE"
    
    # 兩個數據源都失敗
    return None, None, None, error_msg or "所有數據源都無法獲取數據", None


def get_stock_data_2years(ticker):
    """
    獲取股票過去2年的歷史數據（用於計算支撐壓力位）
    返回: (daily_data_2y, stock_info, error_msg, data_source) 或 (None, None, error_msg, None) 如果失敗
    """
    if not YFINANCE_AVAILABLE:
        # 使用台灣證交所 API 獲取2年數據
        try:
            logger.info(f"嘗試使用台灣證交所 API 獲取 {ticker} 的2年數據")
            daily_data_2y = get_twse_stock_data(ticker, days=730)
            
            if daily_data_2y is None or daily_data_2y.empty:
                return None, None, f"無法從台灣證交所獲取股票代碼 {ticker} 的2年數據", None
            
            # 獲取股票名稱
            stock_info = {}
            try:
                url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
                params = {
                    'response': 'json',
                    'date': datetime.now().strftime('%Y%m%d'),
                    'stockNo': ticker
                }
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('stat') == 'OK' and 'title' in data:
                        title = data['title']
                        parts = title.split()
                        if len(parts) >= 2:
                            stock_info['longName'] = parts[1]
            except:
                pass
            
            logger.info(f"成功使用台灣證交所 API 獲取 {ticker} 的2年數據")
            return daily_data_2y, stock_info, None, "TWSE"
        except Exception as e:
            return None, None, f"獲取2年數據時發生錯誤: {str(e)}", None
    
    # 優先使用 yfinance
    try:
        tickers_to_try = [f"{ticker}.TW", f"{ticker}.TWO"]
        
        for ticker_with_suffix in tickers_to_try:
            try:
                logger.info(f"嘗試使用 yfinance 獲取 {ticker_with_suffix} 的2年數據")
                stock = yf.Ticker(ticker_with_suffix)
                
                # 獲取過去2年的日線數據
                daily_data_2y = stock.history(period="2y")
                
                if daily_data_2y is None or daily_data_2y.empty:
                    logger.warning(f"yfinance 無法獲取 {ticker_with_suffix} 的2年數據")
                    continue
                
                # 獲取股票資訊
                stock_info = {}
                try:
                    info = stock.info
                    if info:
                        stock_info['longName'] = info.get('longName', info.get('shortName', ticker))
                except:
                    stock_info['longName'] = ticker
                
                logger.info(f"成功使用 yfinance 獲取 {ticker_with_suffix} 的2年數據")
                return daily_data_2y, stock_info, None, "yfinance"
                
            except Exception as e:
                logger.warning(f"yfinance 獲取 {ticker_with_suffix} 的2年數據失敗: {str(e)}")
                continue
        
        # yfinance 失敗，嘗試台灣證交所 API
        logger.info(f"yfinance 失敗，嘗試使用台灣證交所 API 獲取 {ticker} 的2年數據")
        daily_data_2y = get_twse_stock_data(ticker, days=730)
        
        if daily_data_2y is None or daily_data_2y.empty:
            return None, None, f"無法從台灣證交所獲取股票代碼 {ticker} 的2年數據", None
        
        # 獲取股票名稱
        stock_info = {}
        try:
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': datetime.now().strftime('%Y%m%d'),
                'stockNo': ticker
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('stat') == 'OK' and 'title' in data:
                    title = data['title']
                    parts = title.split()
                    if len(parts) >= 2:
                        stock_info['longName'] = parts[1]
        except:
            pass
        
        logger.info(f"成功使用台灣證交所 API 獲取 {ticker} 的2年數據")
        return daily_data_2y, stock_info, None, "TWSE"
    
    except Exception as e:
        return None, None, f"獲取2年數據時發生錯誤: {str(e)}", None


def calculate_support_resistance_levels(daily_data_2y, current_price):
    """
    計算多重分形支撐與壓力位（參考 TradingView Fractals 指標）
    
    參數:
        daily_data_2y: 過去2年的日線數據 (DataFrame)
        current_price: 當前價格
    
    返回:
        dict 包含 R1, R2, R3, S1, S2, S3（多重支撐壓力位）
    """
    try:
        if daily_data_2y is None or daily_data_2y.empty or len(daily_data_2y) < 11:
            return {
                'r1': None, 'r2': None, 'r3': None,
                's1': None, 's2': None, 's3': None,
                'error': '數據不足，無法計算支撐壓力位（需要至少11根K棒）'
            }
        
        # 確保數據按日期排序（由舊到新）
        daily_data_2y = daily_data_2y.sort_index()
        
        # 1. 找出所有分形高點和分形低點（Fractals）
        # 分形高點：高於左右各5根K棒的最高價
        # 分形低點：低於左右各5根K棒的最低價
        window = 5
        
        fractal_highs = []  # 儲存 (日期, 價格)
        fractal_lows = []   # 儲存 (日期, 價格)
        
        for i in range(window, len(daily_data_2y) - window):
            current_high = daily_data_2y['High'].iloc[i]
            current_low = daily_data_2y['Low'].iloc[i]
            current_date = daily_data_2y.index[i]
            
            # 檢查是否為分形高點（高於左右各5根K棒）
            is_fractal_high = True
            for j in range(i - window, i + window + 1):
                if j != i and daily_data_2y['High'].iloc[j] >= current_high:
                    is_fractal_high = False
                    break
            
            if is_fractal_high:
                fractal_highs.append((current_date, current_high))
            
            # 檢查是否為分形低點（低於左右各5根K棒）
            is_fractal_low = True
            for j in range(i - window, i + window + 1):
                if j != i and daily_data_2y['Low'].iloc[j] <= current_low:
                    is_fractal_low = False
                    break
            
            if is_fractal_low:
                fractal_lows.append((current_date, current_low))
        
        # 2. 篩選與排序多重壓力位 (Resistances)
        # 找出所有 > 當前價格 的分形高點，由近到遠排序（按日期降序），取前3個
        valid_resistances = [(date, price) for date, price in fractal_highs if price > current_price]
        
        # 按日期降序排序（最近的在前）
        valid_resistances.sort(key=lambda x: x[0], reverse=True)
        
        # 過濾重複價格值（保留第一個出現的）
        seen_prices = set()
        unique_resistances = []
        for date, price in valid_resistances:
            # 將價格四捨五入到小數點後2位進行比較
            price_rounded = round(price, 2)
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                unique_resistances.append((date, price))
                if len(unique_resistances) >= 3:
                    break
        
        # 應用台股 Tick Size 修正（壓力位向下取整）
        r1 = adjust_to_tick(unique_resistances[0][1], direction='resistance') if len(unique_resistances) >= 1 else None
        r2 = adjust_to_tick(unique_resistances[1][1], direction='resistance') if len(unique_resistances) >= 2 else None
        r3 = adjust_to_tick(unique_resistances[2][1], direction='resistance') if len(unique_resistances) >= 3 else None
        
        # 3. 篩選與排序多重支撐位 (Supports)
        # 找出所有 < 當前價格 的分形低點，由近到遠排序（按日期降序），取前3個
        valid_supports = [(date, price) for date, price in fractal_lows if price < current_price]
        
        # 按日期降序排序（最近的在前）
        valid_supports.sort(key=lambda x: x[0], reverse=True)
        
        # 過濾重複價格值（保留第一個出現的）
        seen_prices = set()
        unique_supports = []
        for date, price in valid_supports:
            # 將價格四捨五入到小數點後2位進行比較
            price_rounded = round(price, 2)
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                unique_supports.append((date, price))
                if len(unique_supports) >= 3:
                    break
        
        # 應用台股 Tick Size 修正（支撐位向上取整）
        s1 = adjust_to_tick(unique_supports[0][1], direction='support') if len(unique_supports) >= 1 else None
        s2 = adjust_to_tick(unique_supports[1][1], direction='support') if len(unique_supports) >= 2 else None
        s3 = adjust_to_tick(unique_supports[2][1], direction='support') if len(unique_supports) >= 3 else None
        
        return {
            'r1': round(r1, 2) if r1 is not None else None,
            'r2': round(r2, 2) if r2 is not None else None,
            'r3': round(r3, 2) if r3 is not None else None,
            's1': round(s1, 2) if s1 is not None else None,
            's2': round(s2, 2) if s2 is not None else None,
            's3': round(s3, 2) if s3 is not None else None,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"計算多重支撐壓力位時發生錯誤: {str(e)}")
        return {
            'r1': None, 'r2': None, 'r3': None,
            's1': None, 's2': None, 's3': None,
            'error': f'計算多重支撐壓力位時發生錯誤: {str(e)}'
        }


def get_stock_signals(ticker):
    """
    獲取股票訊號：日 KD 金叉、週 KD 金叉、站上 20MA
    優先使用 yfinance 獲取數據，失敗後使用台灣證交所 API
    
    參數:
        ticker: 股票代碼（純數字，例如 "2330"）
    
    返回: dict 包含各項訊號狀態或錯誤訊息
    """
    # 清理輸入：移除可能的 .TW 或 .TWO 後綴，確保是純數字
    ticker_clean = ticker.replace('.TW', '').replace('.TWO', '').strip().upper()
    
    # 驗證股票代碼格式（應該是4位數字）
    if not ticker_clean.isdigit() or len(ticker_clean) != 4:
        return {
            "error": f"股票代碼格式錯誤。請輸入4位數字，例如：2330、2317、2454"
        }
    
    # 獲取股票數據：優先使用 yfinance，失敗後使用台灣證交所 API
    daily_data, weekly_data, stock_info, error_msg, data_source = get_stock_data(ticker_clean)
    
    if daily_data is None or weekly_data is None:
        error_detail = error_msg if error_msg else "未知錯誤"
        source_info = f"（已嘗試 yfinance 和台灣證交所 API）" if data_source is None else f"（使用 {data_source}）"
        return {
            "error": f"無法獲取股票代碼 {ticker_clean} 的數據{source_info}。\n錯誤詳情: {error_detail}\n\n請確認：\n1. 股票代碼是否正確（4位數字）\n2. 該股票是否為台股上市/上櫃股票\n3. 該股票是否仍在交易中"
        }
    
    try:
        signals = {}
        
        # 計算日線 KDJ
        daily_high = daily_data['High'].values
        daily_low = daily_data['Low'].values
        daily_close = daily_data['Close'].values
        daily_k, daily_d = calculate_kdj(daily_high, daily_low, daily_close)
        
        # 判斷日 KD 金叉（K 值上穿 D 值）
        if len(daily_k) >= 2 and len(daily_d) >= 2:
            current_k = daily_k[-1]
            current_d = daily_d[-1]
            prev_k = daily_k[-2]
            prev_d = daily_d[-2]
            
            # 金叉：前一天 K < D，今天 K > D
            daily_golden_cross = (prev_k < prev_d) and (current_k > current_d)
            signals['daily_kd_golden_cross'] = daily_golden_cross
            signals['daily_k'] = round(current_k, 2)
            signals['daily_d'] = round(current_d, 2)
        else:
            signals['daily_kd_golden_cross'] = False
            signals['daily_k'] = None
            signals['daily_d'] = None
        
        # 計算週線 KDJ
        weekly_high = weekly_data['High'].values
        weekly_low = weekly_data['Low'].values
        weekly_close = weekly_data['Close'].values
        weekly_k, weekly_d = calculate_kdj(weekly_high, weekly_low, weekly_close)
        
        # 判斷週 KD 金叉
        if len(weekly_k) >= 2 and len(weekly_d) >= 2:
            current_wk = weekly_k[-1]
            current_wd = weekly_d[-1]
            prev_wk = weekly_k[-2]
            prev_wd = weekly_d[-2]
            
            # 金叉：前一週 K < D，本週 K > D
            weekly_golden_cross = (prev_wk < prev_wd) and (current_wk > current_wd)
            signals['weekly_kd_golden_cross'] = weekly_golden_cross
            signals['weekly_k'] = round(current_wk, 2)
            signals['weekly_d'] = round(current_wd, 2)
        else:
            signals['weekly_kd_golden_cross'] = False
            signals['weekly_k'] = None
            signals['weekly_d'] = None
        
        # 計算日線 20 日均線
        daily_data['MA20'] = daily_data['Close'].rolling(window=20).mean()
        current_price = daily_data['Close'].iloc[-1]
        daily_ma20 = daily_data['MA20'].iloc[-1]
        
        # 計算週線 20 週均線
        weekly_data['MA20'] = weekly_data['Close'].rolling(window=20).mean()
        weekly_price = weekly_data['Close'].iloc[-1]
        weekly_ma20 = weekly_data['MA20'].iloc[-1]
        
        # 判斷日線價格是否站上 20MA
        daily_price_above_ma20 = current_price > daily_ma20 if not np.isnan(daily_ma20) else False
        
        # 判斷週線價格是否站上 20MA
        weekly_price_above_ma20 = weekly_price > weekly_ma20 if not np.isnan(weekly_ma20) else False
        
        signals['current_price'] = round(current_price, 2)
        signals['daily_ma20'] = round(daily_ma20, 2) if not np.isnan(daily_ma20) else None
        signals['daily_price_above_ma20'] = daily_price_above_ma20
        
        signals['weekly_price'] = round(weekly_price, 2)
        signals['weekly_ma20'] = round(weekly_ma20, 2) if not np.isnan(weekly_ma20) else None
        signals['weekly_price_above_ma20'] = weekly_price_above_ma20
        
        # 獲取股票名稱
        signals['stock_name'] = stock_info.get('longName', ticker_clean)
        
        # 顯示時只顯示數字部分
        signals['ticker_display'] = ticker_clean
        signals['ticker'] = ticker_clean
        
        # 計算多重分形支撐與壓力位
        try:
            # 獲取過去2年的歷史數據
            daily_data_2y, stock_info_2y, error_msg_2y, data_source_2y = get_stock_data_2years(ticker_clean)
            
            if daily_data_2y is not None and not daily_data_2y.empty:
                # 計算多重支撐壓力位
                support_resistance = calculate_support_resistance_levels(daily_data_2y, current_price)
                
                # 將結果加入到 signals 字典
                signals['r1'] = support_resistance.get('r1')
                signals['r2'] = support_resistance.get('r2')
                signals['r3'] = support_resistance.get('r3')
                signals['s1'] = support_resistance.get('s1')
                signals['s2'] = support_resistance.get('s2')
                signals['s3'] = support_resistance.get('s3')
                signals['support_resistance_error'] = support_resistance.get('error')
            else:
                # 無法獲取2年數據，設置為 None
                signals['r1'] = None
                signals['r2'] = None
                signals['r3'] = None
                signals['s1'] = None
                signals['s2'] = None
                signals['s3'] = None
                signals['support_resistance_error'] = f"無法獲取2年歷史數據: {error_msg_2y}" if error_msg_2y else "無法獲取2年歷史數據"
        except Exception as e:
            logger.error(f"計算多重支撐壓力位時發生錯誤: {str(e)}")
            signals['r1'] = None
            signals['r2'] = None
            signals['r3'] = None
            signals['s1'] = None
            signals['s2'] = None
            signals['s3'] = None
            signals['support_resistance_error'] = f"計算多重支撐壓力位時發生錯誤: {str(e)}"
        
        return signals
        
    except Exception as e:
        return {"error": f"計算股票訊號時發生錯誤: {str(e)}"}


def stock_signals():
    """股票訊號查詢邏輯（返回數據字典）"""
    from flask import request
    
    error = None
    stock_signals_data = None
    
    if request.method == 'POST':
        try:
            ticker = request.form.get('ticker', '').strip().upper()
            
            if not ticker:
                error = "請輸入股票代碼"
            else:
                # 移除可能的 .TW 或 .TWO 後綴，讓 get_stock_signals 處理
                ticker_clean = ticker.replace('.TW', '').replace('.TWO', '').strip()
                
                # 獲取股票訊號（使用台灣證交所 API）
                signals = get_stock_signals(ticker_clean)
                
                if 'error' in signals:
                    error = signals['error']
                else:
                    stock_signals_data = signals
        
        except Exception as e:
            error = f"查詢股票訊號時發生錯誤: {str(e)}"
    
    return {
        'signal_error': error,
        'stock_signals': stock_signals_data
    }


@signals_bp.route('/', methods=['GET', 'POST'])
def signals_route():
    """股票訊號查詢路由"""
    return stock_signals()
