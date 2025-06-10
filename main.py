# bitget_top20_screener/main.py
import requests
import pandas as pd
import time
import ta
import os

# === CONFIGURATION ===
PAUSED = False  # Toggle this to True to pause the screener
BOT_TOKEN = os.getenv("BOT_TOKEN", "7323205302:AAEkxPBzPTVcUJoXU2BtsLa2S__E6ygxuUQ")
CHAT_ID = os.getenv("CHAT_ID", "-4793050089")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
           "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "TONUSDT", "LINKUSDT",
           "TRXUSDT", "DOTUSDT", "MATICUSDT", "SHIBUSDT", "WBTCUSDT",
           "BCHUSDT", "ICPUSDT", "NEARUSDT", "UNIUSDT", "LTCUSDT"]
BITGET_URL = "https://api.bitget.com/api/v2/spot/market/candles"

# === FUNCTIONS ===
def fetch_candles(symbol):
    try:
        url = f"{BITGET_URL}?symbol={symbol}&granularity=15min&limit=100"
        res = requests.get(url)
        if res.status_code == 200 and res.json().get("data"):
            df = pd.DataFrame(res.json()["data"], columns=[
                "timestamp", "open", "high", "low", "close", "volume", "quoteVolume", "confirm"])
            df = df.iloc[::-1]  # reverse to chronological
            df["close"] = pd.to_numeric(df["close"])
            df["volume"] = pd.to_numeric(df["volume"])
            return df
        else:
            print(f"⚠️ No candle data for {symbol}")
            return None
    except Exception as e:
        print(f"❌ Error fetching candles for {symbol}", e)
        return None

def analyze_coin(symbol):
    df = fetch_candles(symbol)
    if df is None:
        return None

    try:
        rsi = ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1]
        ema9 = ta.trend.EMAIndicator(df["close"], window=9).ema_indicator()
        ema21 = ta.trend.EMAIndicator(df["close"], window=21).ema_indicator()
        volume_ratio = df["volume"].iloc[-1] / df["volume"].mean()

        price_change = ((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]) * 100

        crossover = ema9.iloc[-1] > ema21.iloc[-1]

        print(f"\n🔍 Analyzing {symbol}:")
        print(f"Price change: {price_change:.2f}%")
        print(f"Volume ratio: {volume_ratio:.2f}x")
        print(f"RSI: {rsi:.2f}")
        print(f"EMA Crossover (9 > 21): {crossover}")

        if crossover and rsi > 50 and volume_ratio > 1.5 and price_change > 0.5:
            return {
                "symbol": symbol,
                "price_change": price_change,
                "volume_ratio": volume_ratio,
                "rsi": rsi
            }
        return None
    except Exception as e:
        print(f"❌ Analysis error for {symbol}:", e)
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    print(f"📨 Telegram response: {response.status_code}")

def run_screener():
    if PAUSED:
        print("⏸ Screener is paused. No analysis performed.")
        return

    print("\n🚀 Scanning Top 20 ranked coins...")
    trending = []

    for symbol in SYMBOLS:
        result = analyze_coin(symbol)
        if result:
            trending.append(result)
            send_telegram_message(f"🚀 Trending Alert: {symbol}\nPrice Change: {result['price_change']:.2f}%\nRSI: {result['rsi']:.2f}\nVolume Spike: {result['volume_ratio']:.2f}x")

    if not trending:
        print("📭 No trending coins found in current scan.")

# === Run Immediately for Test ===
if __name__ == "__main__":
    run_screener()
