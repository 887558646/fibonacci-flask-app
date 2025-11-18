from flask import Blueprint, request
import yfinance as yf
import numpy as np
import pandas as pd
import requests

signals_bp = Blueprint('signals', __name__)

# 設置 requests 的 User-Agent，避免被網站阻擋
# yfinance 內部使用 requests，我們會在創建 Ticker 時傳入自定義 session


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


def try_get_stock_data(ticker_with_suffix):
    """
    嘗試獲取股票數據
    返回: (daily_data, weekly_data, stock_info, error_msg) 或 (None, None, None, error_msg) 如果失敗
    """
    import time
    from datetime import datetime, timedelta
    
    try:
        # 設置超時和重試機制
        # 使用自定義 session 設置 User-Agent 和更多 headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        stock = yf.Ticker(ticker_with_suffix, session=session)
        
        # 獲取日線數據，使用多種方法嘗試
        daily_data = None
        for attempt in range(3):  # 最多重試 3 次
            try:
                # 方法1: 使用 Ticker().history() with period
                try:
                    daily_data = stock.history(period="6mo")
                    if daily_data is not None and not daily_data.empty:
                        break
                except:
                    pass
                
                # 方法2: 使用明確的日期範圍
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=180)
                    daily_data = stock.history(start=start_date, end=end_date)
                    if daily_data is not None and not daily_data.empty:
                        break
                except:
                    pass
                
                # 方法3: 使用 yfinance.download() 作為備用
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=180)
                    daily_data = yf.download(ticker_with_suffix, start=start_date, end=end_date, progress=False, session=session)
                    if daily_data is not None and not daily_data.empty:
                        # download 返回的數據格式可能不同，需要調整
                        if isinstance(daily_data.columns, pd.MultiIndex):
                            daily_data = daily_data.droplevel(0, axis=1)
                        break
                except:
                    pass
                
                if attempt < 2:  # 不是最後一次嘗試
                    time.sleep(3)  # 等待 3 秒後重試
            except Exception as e:
                error_msg = str(e)
                # 過濾掉 yfinance 的警告訊息
                if "Expecting value" in error_msg or "No price data" in error_msg:
                    if attempt == 2:  # 最後一次嘗試
                        return None, None, None, f"無法從 Yahoo Finance 獲取 {ticker_with_suffix} 的日線數據。可能是股票代碼錯誤或該股票已下市。"
                else:
                    if attempt == 2:  # 最後一次嘗試
                        return None, None, None, f"獲取日線數據失敗: {error_msg}"
                if attempt < 2:
                    time.sleep(3)  # 等待 3 秒後重試
        
        if daily_data is None or daily_data.empty:
            return None, None, None, f"無法獲取 {ticker_with_suffix} 的日線數據（數據為空）"
        
        # 獲取週線數據，使用多種方法嘗試
        weekly_data = None
        for attempt in range(3):  # 最多重試 3 次
            try:
                # 方法1: 使用 Ticker().history() with period
                try:
                    weekly_data = stock.history(period="2y", interval="1wk")
                    if weekly_data is not None and not weekly_data.empty:
                        break
                except:
                    pass
                
                # 方法2: 使用明確的日期範圍
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=730)  # 2 年
                    weekly_data = stock.history(start=start_date, end=end_date, interval="1wk")
                    if weekly_data is not None and not weekly_data.empty:
                        break
                except:
                    pass
                
                # 方法3: 使用 yfinance.download() 作為備用
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=730)
                    weekly_data = yf.download(ticker_with_suffix, start=start_date, end=end_date, interval="1wk", progress=False, session=session)
                    if weekly_data is not None and not weekly_data.empty:
                        # download 返回的數據格式可能不同，需要調整
                        if isinstance(weekly_data.columns, pd.MultiIndex):
                            weekly_data = weekly_data.droplevel(0, axis=1)
                        break
                except:
                    pass
                
                if attempt < 2:  # 不是最後一次嘗試
                    time.sleep(3)  # 等待 3 秒後重試
            except Exception as e:
                error_msg = str(e)
                if "Expecting value" in error_msg or "No price data" in error_msg:
                    if attempt == 2:  # 最後一次嘗試
                        return None, None, None, f"無法從 Yahoo Finance 獲取 {ticker_with_suffix} 的週線數據。可能是股票代碼錯誤或該股票已下市。"
                else:
                    if attempt == 2:  # 最後一次嘗試
                        return None, None, None, f"獲取週線數據失敗: {error_msg}"
                if attempt < 2:
                    time.sleep(3)  # 等待 3 秒後重試
        
        if weekly_data is None or weekly_data.empty:
            return None, None, None, f"無法獲取 {ticker_with_suffix} 的週線數據（數據為空）"
        
        # 嘗試獲取股票資訊（非必需，失敗不影響）
        info = {}
        try:
            info = stock.info
        except:
            pass
        
        return daily_data, weekly_data, info, None
    
    except Exception as e:
        error_msg = str(e)
        if "Expecting value" in error_msg:
            return None, None, None, f"Yahoo Finance API 返回無效響應。可能是網路問題或股票代碼 {ticker_with_suffix} 不存在。"
        return None, None, None, f"獲取股票數據時發生錯誤: {error_msg}"


def get_stock_signals(ticker):
    """
    獲取股票訊號：日 KD 金叉、週 KD 金叉、站上 20MA
    實現「嘗試-回退」邏輯：
    - 優先嘗試使用 ticker + '.TW' 獲取數據
    - 如果獲取失敗，則回退嘗試使用 ticker + '.TWO' 獲取數據
    - 如果最終仍失敗，返回錯誤訊息
    
    參數:
        ticker: 股票代碼（純數字，例如 "2330"）
    
    返回: dict 包含各項訊號狀態或錯誤訊息
    """
    # 清理輸入：移除可能的 .TW 或 .TWO 後綴，確保是純數字
    ticker_clean = ticker.replace('.TW', '').replace('.TWO', '').strip().upper()
    
    # 嘗試-回退邏輯：先嘗試 .TW，失敗則嘗試 .TWO
    ticker_variants = [f"{ticker_clean}.TW", f"{ticker_clean}.TWO"]
    daily_data = None
    weekly_data = None
    stock_info = None
    final_ticker = None
    last_error = None
    
    for ticker_variant in ticker_variants:
        daily_data, weekly_data, stock_info, error_msg = try_get_stock_data(ticker_variant)
        if daily_data is not None and weekly_data is not None:
            final_ticker = ticker_variant
            break
        else:
            last_error = error_msg  # 記錄最後的錯誤訊息
    
    # 如果所有嘗試都失敗，返回詳細錯誤
    if daily_data is None or weekly_data is None:
        error_detail = last_error if last_error else "未知錯誤"
        
        # 檢查是否是 JSON 解析錯誤（Yahoo Finance API 問題）
        if "Expecting value" in error_detail or "Yahoo Finance API" in error_detail:
            return {
                "error": f"⚠️ 無法從 Yahoo Finance 獲取股票代碼 {ticker_clean} 的數據。\n\n可能的原因：\n1. Yahoo Finance 暫時無法提供台股數據\n2. 股票代碼可能不存在或已下市\n3. 網路連線問題\n\n建議：\n• 請稍後再試\n• 確認股票代碼是否正確（例如：2330、2317、2454）\n• 檢查該股票是否仍在交易中"
            }
        else:
            return {
                "error": f"無法獲取股票代碼 {ticker_clean} 的數據。\n錯誤詳情: {error_detail}\n\n請確認：\n1. 股票代碼是否正確\n2. 該股票是否為台股上市/上櫃股票\n3. 網路連線是否正常"
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
        try:
            signals['stock_name'] = stock_info.get('longName', ticker_clean)
        except:
            signals['stock_name'] = ticker_clean
        
        # 顯示時只顯示數字部分
        signals['ticker_display'] = ticker_clean
        signals['ticker'] = final_ticker
        
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
                
                # 獲取股票訊號（內部會自動嘗試 .TW 和 .TWO）
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
