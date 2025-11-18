from flask import Blueprint, request
import numpy as np
import pandas as pd
import requests
import warnings
import logging
from datetime import datetime, timedelta
import time

signals_bp = Blueprint('signals', __name__)

# 抑制警告訊息
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.ERROR)


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
    從台灣證交所 API 獲取股票數據
    
    參數:
        stock_no: 股票代碼（4位數字，例如 "2330"）
        days: 需要獲取的天數
    
    返回:
        pandas DataFrame 包含 Open, High, Low, Close, Volume 欄位
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    })
    
    all_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 台灣證交所 API 一次只能獲取一個月的數據，需要逐月獲取
    # 從起始月份的第一天開始，逐月獲取
    current_month = start_date.replace(day=1)
    end_month = end_date.replace(day=1)
    
    while current_month <= end_month:
        # 格式化日期為 YYYYMMDD（取該月第一天）
        date_str = current_month.strftime('%Y%m%d')
        
        try:
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': date_str,
                'stockNo': stock_no
            }
            
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 檢查 API 回應
            if data.get('stat') == 'OK' and 'data' in data:
                # 解析數據
                for row in data['data']:
                    try:
                        # 日期格式：民國年/MM/DD，需要轉換為西元年
                        date_str = row[0].strip()
                        date_parts = date_str.split('/')
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
                    except (ValueError, IndexError, TypeError) as e:
                        # 跳過無法解析的數據
                        continue
            
            # 避免請求過於頻繁
            time.sleep(0.5)
            
        except Exception as e:
            # 如果某個月獲取失敗，繼續下一個月
            pass
        
        # 移到下一個月
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    if not all_data:
        return None
    
    # 轉換為 DataFrame
    df = pd.DataFrame(all_data)
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)
    
    # 確保欄位名稱與 yfinance 格式一致
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    return df


def try_get_stock_data_twse(stock_no):
    """
    使用台灣證交所 API 獲取股票數據
    返回: (daily_data, weekly_data, stock_info, error_msg) 或 (None, None, None, error_msg) 如果失敗
    """
    try:
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
            response = requests.get(url, params=params, timeout=10)
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
        
        return daily_data, weekly_data, stock_info, None
    
    except Exception as e:
        return None, None, None, f"獲取股票數據時發生錯誤: {str(e)}"


def get_stock_signals(ticker):
    """
    獲取股票訊號：日 KD 金叉、週 KD 金叉、站上 20MA
    使用台灣證交所 API 獲取數據
    
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
    
    # 使用台灣證交所 API 獲取數據
    daily_data, weekly_data, stock_info, error_msg = try_get_stock_data_twse(ticker_clean)
    
    if daily_data is None or weekly_data is None:
        error_detail = error_msg if error_msg else "未知錯誤"
        return {
            "error": f"無法獲取股票代碼 {ticker_clean} 的數據。\n錯誤詳情: {error_detail}\n\n請確認：\n1. 股票代碼是否正確（4位數字）\n2. 該股票是否為台股上市/上櫃股票\n3. 該股票是否仍在交易中"
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
