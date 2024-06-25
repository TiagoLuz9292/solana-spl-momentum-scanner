# app/main.py
import time
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class PoolAddress(BaseModel):
    pairAddress: str

def fetch_pool_data(poolAddress, minuteOrHour, timeFrame, frameAmount):
    url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{poolAddress}/ohlcv/{minuteOrHour}?aggregate={timeFrame}&limit={frameAmount}"
    max_retries = 5
    retry_delay = 10

    for i in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            ohlcv_list = data['data']['attributes']['ohlcv_list']
            ohlcv_data = pd.DataFrame(ohlcv_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            pd.set_option('display.float_format', '{:.15f}'.format)
            return ohlcv_data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"Error 404: Not Found for URL: {url}")
                raise HTTPException(status_code=404, detail="Pool address not found.")
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e
    raise Exception(f"Failed to fetch data after {max_retries} attempts.")

@app.post("/check_ohlcv_v2")
def analyze_conditions(data: PoolAddress):
    pairAddress = data.pairAddress
    print("Request received for pairAddress:", pairAddress)
    
    ohlcv_data_1m = fetch_pool_data(pairAddress, "minute", 1, 100)
    time.sleep(1)
    ohlcv_data_5m = fetch_pool_data(pairAddress, "minute", 5, 100)
    time.sleep(1)
    ohlcv_data_15m = fetch_pool_data(pairAddress, "minute", 15, 50)
    time.sleep(1)
    
    if len(ohlcv_data_1m) < 10 or len(ohlcv_data_5m) < 3:
        raise HTTPException(status_code=400, detail="Insufficient data for analysis")
    
    ohlcv_data_1m['ema_20'] = calculate_ema(ohlcv_data_1m, 20)
    ohlcv_data_1m['ema_50'] = calculate_ema(ohlcv_data_1m, 50)
    ohlcv_data_1m['macd_line'], ohlcv_data_1m['signal_line'], ohlcv_data_1m['macd_histogram'] = calculate_macd(ohlcv_data_1m)
    ohlcv_data_1m['rsi'] = calculate_rsi(ohlcv_data_1m)

    ohlcv_data_5m['ema_20'] = calculate_ema(ohlcv_data_5m, 20)
    ohlcv_data_5m['ema_50'] = calculate_ema(ohlcv_data_5m, 50)
    ohlcv_data_5m['macd_line'], ohlcv_data_5m['signal_line'], ohlcv_data_5m['macd_histogram'] = calculate_macd(ohlcv_data_5m)
    ohlcv_data_5m['rsi'] = calculate_rsi(ohlcv_data_5m)

    ohlcv_data_15m['ema_20'] = calculate_ema(ohlcv_data_15m, 20)
    ohlcv_data_15m['ema_50'] = calculate_ema(ohlcv_data_15m, 50)
    ohlcv_data_15m['macd_line'], ohlcv_data_15m['signal_line'], ohlcv_data_15m['macd_histogram'] = calculate_macd(ohlcv_data_15m)
    ohlcv_data_15m['rsi'] = calculate_rsi(ohlcv_data_15m)

    macd_above_signal_1m = (ohlcv_data_1m['macd_line'].iloc[-1] > ohlcv_data_1m['signal_line'].iloc[-1] and
                            ohlcv_data_1m['macd_line'].iloc[-1] < 0)
    macd_above_signal_5m = (ohlcv_data_5m['macd_line'].iloc[-1] > ohlcv_data_5m['signal_line'].iloc[-1] and
                            ohlcv_data_5m['macd_line'].iloc[-1] < 0)
    
    bullish_engulfing_5m = any(is_bullish_engulfing(ohlcv_data_5m.iloc[i-1:i+1]) for i in range(-4, 0))
    
    macd_cross_1m = any((ohlcv_data_1m['macd_line'].iloc[i-1] < ohlcv_data_1m['signal_line'].iloc[i-1]) and
                                    (ohlcv_data_1m['macd_line'].iloc[i] > ohlcv_data_1m['signal_line'].iloc[i]) and
                                    (ohlcv_data_1m['macd_line'].iloc[i] < 0)
                                    for i in range(-10, 0))
    
    macd_cross_5m = any((ohlcv_data_5m['macd_line'].iloc[i-1] < ohlcv_data_5m['signal_line'].iloc[i-1]) and
                                    (ohlcv_data_5m['macd_line'].iloc[i] > ohlcv_data_5m['signal_line'].iloc[i]) and
                                    (ohlcv_data_5m['macd_line'].iloc[i] < 0)
                                    for i in range(-5, 0))

    macd_cross_15m = any((ohlcv_data_15m['macd_line'].iloc[i-1] < ohlcv_data_15m['signal_line'].iloc[i-1]) and
                                    (ohlcv_data_15m['macd_line'].iloc[i] > ohlcv_data_15m['signal_line'].iloc[i]) and
                                    (ohlcv_data_15m['macd_line'].iloc[i] < 0)
                                    for i in range(-2, 0))      

    
    rsi_1m_condition = ohlcv_data_1m['rsi'].iloc[-1] > 37 and ohlcv_data_1m['rsi'].diff().iloc[-1] > 0

    ema_20_above_ema_50_1m = ohlcv_data_1m['ema_20'].iloc[-1] > ohlcv_data_1m['ema_50'].iloc[-1]
    ema_20_crossed_ema_50_1m_in_last_10 = any((ohlcv_data_1m['ema_20'].iloc[i-1] < ohlcv_data_1m['ema_50'].iloc[i-1]) and
                                             (ohlcv_data_1m['ema_20'].iloc[i] > ohlcv_data_1m['ema_50'].iloc[i])
                                             for i in range(-5, 0))
    
    ema_20_above_ema_50_5m = ohlcv_data_5m['ema_20'].iloc[-1] > ohlcv_data_5m['ema_50'].iloc[-1]
    ema_20_crossed_ema_50_5m_in_last_3 = any((ohlcv_data_5m['ema_20'].iloc[i-1] < ohlcv_data_5m['ema_50'].iloc[i-1]) and
                                            (ohlcv_data_5m['ema_20'].iloc[i] > ohlcv_data_5m['ema_50'].iloc[i])
                                            for i in range(-3, 0))

    price_crossed_ema_20_50_1m = any((ohlcv_data_1m['close'].iloc[i-1] < ohlcv_data_1m['ema_20'].iloc[i-1] and
                                      ohlcv_data_1m['close'].iloc[i] > ohlcv_data_1m['ema_20'].iloc[i]) or
                                     (ohlcv_data_1m['close'].iloc[i-1] < ohlcv_data_1m['ema_50'].iloc[i-1] and
                                      ohlcv_data_1m['close'].iloc[i] > ohlcv_data_1m['ema_50'].iloc[i])
                                     for i in range(-5, 0))

    price_crossed_ema_20_50_5m = any((ohlcv_data_5m['close'].iloc[i-1] < ohlcv_data_5m['ema_20'].iloc[i-1] and
                                      ohlcv_data_5m['close'].iloc[i] > ohlcv_data_5m['ema_20'].iloc[i]) or
                                     (ohlcv_data_5m['close'].iloc[i-1] < ohlcv_data_5m['ema_50'].iloc[i-1] and
                                      ohlcv_data_5m['close'].iloc[i] > ohlcv_data_5m['ema_50'].iloc[i])
                                     for i in range(-2, 0))


    macd_above_signal_1m = bool(macd_above_signal_1m)
    macd_above_signal_5m = bool(macd_above_signal_5m)
    bullish_engulfing_5m = bool(bullish_engulfing_5m)
    macd_cross_1m = bool(macd_cross_1m)
    macd_cross_5m = bool(macd_cross_5m)
    macd_cross_15m = bool(macd_cross_15m)
    rsi_1m_condition = bool(rsi_1m_condition)
    ema_20_above_ema_50_1m = bool(ema_20_above_ema_50_1m)
    ema_20_crossed_ema_50_1m_in_last_10 = bool(ema_20_crossed_ema_50_1m_in_last_10)
    ema_20_above_ema_50_5m = bool(ema_20_above_ema_50_5m)
    ema_20_crossed_ema_50_5m_in_last_3 = bool(ema_20_crossed_ema_50_5m_in_last_3)
    price_crossed_ema_20_50_1m = bool(price_crossed_ema_20_50_1m)
    price_crossed_ema_20_50_5m = bool(price_crossed_ema_20_50_5m)

    print(f"MACD above signal 1m: {'Yes' if macd_above_signal_1m else 'No'}")
    print(f"MACD above signal 5m: {'Yes' if macd_above_signal_5m else 'No'}")
    print(f"Bullish Engulfing 5m: {'Yes' if bullish_engulfing_5m else 'No'}")
    print(f"MACD Cross 1m: {'Yes' if macd_cross_1m else 'No'}")
    print(f"MACD Cross 5m: {'Yes' if macd_cross_5m else 'No'}")
    print(f"MACD Cross 15m: {'Yes' if macd_cross_15m else 'No'}")
    print(f"RSI 1m > 37 and rising: {'Yes' if rsi_1m_condition else 'No'}")
    print(f"EMA 20 above EMA 50 1m: {'Yes' if ema_20_above_ema_50_1m else 'No'}")
    print(f"EMA 20 crossed above EMA 50 in last 10 1m candles: {'Yes' if ema_20_crossed_ema_50_1m_in_last_10 else 'No'}")
    print(f"EMA 20 above EMA 50 5m: {'Yes' if ema_20_above_ema_50_5m else 'No'}")
    print(f"EMA 20 crossed above EMA 50 in last 3 5m candles: {'Yes' if ema_20_crossed_ema_50_5m_in_last_3 else 'No'}")
    print(f"Price crossed above EMA 20 or EMA 50 in last 5 1m candles: {'Yes' if price_crossed_ema_20_50_1m else 'No'}")
    print(f"Price crossed above EMA 20 or EMA 50 in last 2 5m candles: {'Yes' if price_crossed_ema_20_50_5m else 'No'}")

    return {
        "macd_above_signal_1m": macd_above_signal_1m,
        "macd_above_signal_5m": macd_above_signal_5m,
        "bullish_engulfing_5m": bullish_engulfing_5m,
        "macd_cross_1m": macd_cross_1m,
        "macd_cross_5m": macd_cross_5m,
        "macd_cross_15m": macd_cross_15m,
        "rsi_1m_condition": rsi_1m_condition,
        "ema_20_above_ema_50_1m": ema_20_above_ema_50_1m,
        "ema_20_crossed_ema_50_1m_in_last_10": ema_20_crossed_ema_50_1m_in_last_10,
        "ema_20_above_ema_50_5m": ema_20_above_ema_50_5m,
        "ema_20_crossed_ema_50_5m_in_last_3": ema_20_crossed_ema_50_5m_in_last_3,
        "price_crossed_ema_20_50_1m": price_crossed_ema_20_50_1m,
        "price_crossed_ema_20_50_5m": price_crossed_ema_20_50_5m,
    }

def calculate_ema(df, period, column='close'):
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_macd(df, column='close', fast_period=12, slow_period=26, signal_period=9):
    fast_ema = df[column].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df[column].ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_rsi(df, period=14, column='close'):
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def is_bullish_engulfing(df):
    if len(df) < 2:
        return False
    last_candle = df.iloc[-1]
    previous_candle = df.iloc[-2]
    return (last_candle['close'] > last_candle['open'] and
            previous_candle['close'] < previous_candle['open'] and
            last_candle['close'] > previous_candle['open'])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here if needed