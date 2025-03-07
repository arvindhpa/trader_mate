import os
import time
import threading
from collections import deque  
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from dotenv import load_dotenv
import talib
import numpy as np
from flask import Flask, jsonify, request
import sys

load_dotenv()
app = Flask(__name__) 

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Trading Parameters
SYMBOL = None
LEVERAGE = None
QUANTITY = None
ENTRY_PRICE = None
POSITION = None  
trading_active = False 
stop_loss = None  
take_profit = None  

# Initialize Binance Client
client = Client(API_KEY, API_SECRET)
    
# Function to get current price
def get_current_price():
    ticker = client.futures_symbol_ticker(symbol=SYMBOL)
    return float(ticker['price'])
    
# Function to place order
def place_order(order_type):
    global ENTRY_PRICE, POSITION
    side = SIDE_BUY if order_type == 'long' else SIDE_SELL
    try:
        order = client.futures_create_order(
            symbol=SYMBOL,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=QUANTITY
        )
        print("Order:", order)
        ENTRY_PRICE = get_current_price()
        POSITION = order_type
        print(f"\nOrder placed: {order_type.upper()} at {ENTRY_PRICE}")
    except Exception as e:  
        print(f"Error placing order: {e}")

# Function to close position
def close_position():
    global POSITION
    if POSITION:
        side = SIDE_SELL if POSITION == 'long' else SIDE_BUY
        try:
            order = client.futures_create_order(
                symbol=SYMBOL,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=QUANTITY
            )
            print("Order:", order)
            print(f"Position closed: {POSITION}")
            POSITION = None
        except Exception as e:  
            print(f"Error closing position: {e}")

# Function to get historical data for indicators
def get_historical_data(interval):
    klines = client.futures_klines(symbol=SYMBOL, interval=interval, limit=100)
    close_prices = [float(kline[4]) for kline in klines]
    return np.array(close_prices)

# Function to calculate Moving Averages
def calculate_moving_averages():
    ma_short_1m, ma_long_1m = calculate_ma_for_interval('1m')
    ma_short_15m, ma_long_15m = calculate_ma_for_interval('15m')
    ma_short_1h, ma_long_1h = calculate_ma_for_interval('1h')
    ma_short_4h, ma_long_4h = calculate_ma_for_interval('4h')
    
    # Add debug print
    print(f"\n--- MA Values ---")
    print(f"MA(6) 1m: {ma_short_1m:.6f}, MA(25) 1m: {ma_long_1m:.6f}, Diff: {ma_short_1m - ma_long_1m:.6f}")
    print(f"MA(6) 15m: {ma_short_15m:.6f}, MA(25) 15m: {ma_long_15m:.6f}, Diff: {ma_short_15m - ma_long_15m:.6f}")
    print(f"MA(6) 1h: {ma_short_1h:.6f}, MA(25) 1h: {ma_long_1h:.6f}, Diff: {ma_short_1h - ma_long_1h:.6f}")
    print(f"MA(6) 4h: {ma_short_4h:.6f}, MA(25) 4h: {ma_long_4h:.6f}, Diff: {ma_short_4h - ma_long_4h:.6f}")
    
    return ma_short_1m, ma_long_1m, ma_short_15m, ma_long_15m, ma_short_1h, ma_long_1h, ma_short_4h, ma_long_4h

def calculate_ma_for_interval(interval):
    klines = client.futures_klines(symbol=SYMBOL, interval=interval, limit=30)  # Need at least 25 candles for MA(25)
    close_prices = np.array([float(kline[4]) for kline in klines])
    
    # Calculate MA(6) and MA(25)
    ma_short = talib.SMA(close_prices, timeperiod=6)
    ma_long = talib.SMA(close_prices, timeperiod=25)
    
    return ma_short[-1] if len(ma_short) > 0 and not np.isnan(ma_short[-1]) else 0.0, ma_long[-1] if len(ma_long) > 0 and not np.isnan(ma_long[-1]) else 0.0

# Function to calculate RSI with shorter period
def calculate_rsi():
    rsi_1m = calculate_rsi_for_interval('1m')
    rsi_15m = calculate_rsi_for_interval('15m')
    rsi_1h = calculate_rsi_for_interval('1h')
    rsi_4h = calculate_rsi_for_interval('4h')
    
    # Add debug print
    print(f"\n--- RSI(6) Values ---")
    print(f"RSI(6) 1m: {rsi_1m:.2f}")
    print(f"RSI(6) 15m: {rsi_15m:.2f}")
    print(f"RSI(6) 1h: {rsi_1h:.2f}")
    print(f"RSI(6) 4h: {rsi_4h:.2f}")
    
    return rsi_1m, rsi_15m, rsi_1h, rsi_4h

def calculate_rsi_for_interval(interval):
    klines = client.futures_klines(symbol=SYMBOL, interval=interval, limit=10)  # Need fewer candles for RSI(6)
    close_prices = np.array([float(kline[4]) for kline in klines])
    rsi = talib.RSI(close_prices, timeperiod=6)  # Changed from 14 to 6
    return rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else 50.0
    
# Function to calculate Bollinger Bands
def calculate_bollinger_bands():
    klines = client.futures_klines(symbol=SYMBOL, interval='15m', limit=21) 
    close_prices = np.array([float(kline[4]) for kline in klines])
    upperband, middleband, lowerband = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    
    current_price = get_current_price()
    
    # Add debug print
    print(f"\n--- Bollinger Bands ---")
    print(f"Upper Band: {upperband[-1]:.2f}")
    print(f"Middle Band: {middleband[-1]:.2f}")
    print(f"Lower Band: {lowerband[-1]:.2f}")
    print(f"Current Price: {current_price:.2f}")
    print(f"Price vs Upper: {(current_price - upperband[-1]):.2f}")
    print(f"Price vs Lower: {(current_price - lowerband[-1]):.2f}")
    
    return upperband[-1] if len(upperband) > 0 and not np.isnan(upperband[-1]) else 0.0, middleband[-1] if len(middleband) > 0 and not np.isnan(middleband[-1]) else 0.0, lowerband[-1] if len(lowerband) > 0 and not np.isnan(lowerband[-1]) else 0.0

# Function to calculate Volatility
def calculate_atr():
    klines = client.futures_klines(symbol=SYMBOL, interval='1m', limit=100)
    high_prices = np.array([float(kline[2]) for kline in klines])
    low_prices = np.array([float(kline[3]) for kline in klines])
    close_prices = np.array([float(kline[4]) for kline in klines])
    atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
    
    current_price = get_current_price()
    atr_percentage = (atr[-1] / current_price) * 100 if current_price != 0 else 0.0
    
    # Add debug print
    print(f"\n--- ATR Values ---")
    print(f"ATR: {atr[-1]:.4f}")
    print(f"ATR % of Price: {atr_percentage:.4f}%")
    
    return atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else 0.0

def calculate_bollinger_band_width():
    upperband, middleband, lowerband = calculate_bollinger_bands()
    if middleband != 0: 
        bb_width = (upperband - lowerband) / middleband * 100 #Bandwidth as percentage of middle band
    else:
        bb_width = 0.0
        
    # Add debug print
    print(f"BB Width: {bb_width:.2f}%")
    
    return bb_width

# Constants for Historical Data and Percentiles
HISTORICAL_ATR_PERIOD = '1h'  # Interval to calculate ATR for historical data (e.g., 1h, 4h, 15m) - 1h is a good starting point
HISTORICAL_ATR_TIMEFRAME_DAYS = 3 # Look back period for historical ATR (last 3 days)
ATR_HISTORY_LENGTH = HISTORICAL_ATR_TIMEFRAME_DAYS * 24 # For 1h interval, 24 periods per day
ATR_HISTORY = deque(maxlen=ATR_HISTORY_LENGTH) # Use deque for efficient adding/removing

LOW_VOLATILITY_PERCENTILE = 25  # Percentile for low volatility threshold
HIGH_VOLATILITY_PERCENTILE = 75 # Percentile for high volatility threshold

# Function to calculate ATR for a specific interval (missing function that was called)
def calculate_atr_value(interval, limit):
    klines = client.futures_klines(symbol=SYMBOL, interval=interval, limit=limit)
    high_prices = np.array([float(kline[2]) for kline in klines])
    low_prices = np.array([float(kline[3]) for kline in klines])
    close_prices = np.array([float(kline[4]) for kline in klines])
    atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
    
    # Add debug print for historical ATR
    if interval == HISTORICAL_ATR_PERIOD:
        print(f"Historical ATR ({interval}): {atr[-1]:.6f}")
        
    return atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else 0.0

# Function to update Historical ATR Data
def update_historical_atr():
    atr_value = calculate_atr_value(interval=HISTORICAL_ATR_PERIOD, limit=100) # Calculate ATR for historical interval
    ATR_HISTORY.append(atr_value) # Add to deque, automatically removes oldest if full
    
    # Add debug print
    print(f"\n--- Historical ATR Data ---")
    print(f"ATR History Length: {len(ATR_HISTORY)}")
    print(f"Latest ATR Value Added: {atr_value:.6f}")
    if len(ATR_HISTORY) > 0:
        print(f"Min ATR: {min(ATR_HISTORY):.6f}, Max ATR: {max(ATR_HISTORY):.6f}")
    
# Function to get Dynamic Volatility Thresholds
def get_dynamic_atr_thresholds():
    if len(ATR_HISTORY) < ATR_HISTORY_LENGTH // 4: # Not enough historical data yet, reduced required data to 1/4
        print("Not enough historical ATR data yet. Using default thresholds.")
        return 0.01, 0.03 # Return default thresholds initially 

    atr_array = np.array(list(ATR_HISTORY)) # Convert deque to numpy array for percentile calculation

    low_atr_threshold_dynamic = np.percentile(atr_array, LOW_VOLATILITY_PERCENTILE)
    high_atr_threshold_dynamic = np.percentile(atr_array, HIGH_VOLATILITY_PERCENTILE)
    
    # Add debug print
    print(f"Dynamic ATR Thresholds - Low: {low_atr_threshold_dynamic:.6f}, High: {high_atr_threshold_dynamic:.6f}")
    
    return low_atr_threshold_dynamic, high_atr_threshold_dynamic

# Function to determine Volatility Level (Dynamic Thresholds Used)
def get_volatility_level():
    # Update historical ATR data first
    update_historical_atr()
    
    atr_value = calculate_atr_value(interval='1m', limit=100) # Calculate current ATR (1m interval for responsiveness)
    bb_width_value = calculate_bollinger_band_width()
    low_atr_threshold_dynamic, high_atr_threshold_dynamic = get_dynamic_atr_thresholds() # Get dynamic thresholds

    current_price = get_current_price()
    atr_percentage = (atr_value / current_price) * 100 if current_price != 0 else 0.0

    bb_width_threshold_low = 1.0 # Still using static BB width thresholds for now - can be made dynamic too later
    bb_width_threshold_high = 3.0
    
    # Add debug print
    print(f"\n--- Volatility Analysis ---")
    print(f"Current ATR: {atr_value:.6f}, ATR %: {atr_percentage:.4f}%")
    print(f"BB Width: {bb_width_value:.2f}%")
    print(f"Low ATR Threshold: {low_atr_threshold_dynamic:.6f}, High ATR Threshold: {high_atr_threshold_dynamic:.6f}")
    print(f"BB Width Low Threshold: {bb_width_threshold_low}, BB Width High Threshold: {bb_width_threshold_high}")

    volatility_level = "medium_volatility"  # Default value
    
    if atr_value < low_atr_threshold_dynamic and bb_width_value < bb_width_threshold_low:
        volatility_level = "low_volatility"
    elif atr_value > high_atr_threshold_dynamic or bb_width_value > bb_width_threshold_high:
        volatility_level = "high_volatility"
    
    print(f"Volatility Level: {volatility_level.upper()}")
    
    return volatility_level

# Function to generate trade signal using combined indicators for different volatility conditions
def generate_signal():
    volatility_level = get_volatility_level()
    rsi_1m, rsi_15m, rsi_1h, rsi_4h = calculate_rsi()
    ma_short_1m, ma_long_1m, ma_short_15m, ma_long_15m, ma_short_1h, ma_long_1h, ma_short_4h, ma_long_4h = calculate_moving_averages()
    upperband, middleband, lowerband = calculate_bollinger_bands()
    current_price = get_current_price()

    print("\n--- Signal Generation ---")
    print(f"Volatility Level: {volatility_level}")
    
    signal = None
    
    if volatility_level == "low_volatility":
        # Relaxed Conditions for Low Volatility
        if (rsi_15m > 55 and                      # Using RSI(6) now, so we can use different thresholds
            ma_short_15m > ma_long_15m and        # MA crossover instead of MACD
            current_price > middleband):          # Price above middle band
            signal = "long"
            print("LOW VOLATILITY LONG signal generated with MA crossover")
        elif (rsi_15m < 45 and                    # Using RSI(6) now
              ma_short_15m < ma_long_15m and      # MA crossover instead of MACD
              current_price < middleband):        # Price below middle band
            signal = "short"
            print("LOW VOLATILITY SHORT signal generated with MA crossover")

    elif volatility_level == "medium_volatility":
        # Relaxed Conditions for Medium Volatility
        if (rsi_1m > 50 and                      # RSI(6) 1m above 50
            ma_short_15m > ma_long_15m):         # MA crossover on 15m, removed price vs middleband
            signal = "long"
            print("MEDIUM VOLATILITY LONG signal generated with MA crossover")
        elif (rsi_1m < 50 and                    # RSI(6) 1m below 50
              ma_short_15m < ma_long_15m):       # MA crossover on 15m, removed price vs middleband
            signal = "short"
            print("MEDIUM VOLATILITY SHORT signal generated with MA crossover")

    elif volatility_level == "high_volatility":
        # Relaxed Conditions for high volatility - just MA crossover
        if ma_short_15m > ma_long_15m:           # Only using MA crossover for high volatility
            signal = "long"
            print("HIGH VOLATILITY LONG signal generated with MA crossover")
        elif ma_short_15m < ma_long_15m:         # Only using MA crossover for high volatility
            signal = "short"
            print("HIGH VOLATILITY SHORT signal generated with MA crossover")
    
    # Print detailed reason for signal generation or lack thereof
    if signal:
        print(f"SIGNAL GENERATED: {signal.upper()}")
    else:
        print("NO SIGNAL GENERATED - Conditions not met")
        # Print detailed analysis of conditions not met
        if volatility_level == "low_volatility":
            print(f"For LONG: RSI(6) 15m > 55 ({rsi_15m > 55}), MA(6) > MA(25) on 15m ({ma_short_15m > ma_long_15m}), Price > Middle ({current_price > middleband})")
            print(f"For SHORT: RSI(6) 15m < 45 ({rsi_15m < 45}), MA(6) < MA(25) on 15m ({ma_short_15m < ma_long_15m}), Price < Middle ({current_price < middleband})")
        elif volatility_level == "medium_volatility":
            print(f"For LONG: RSI(6) 1m > 50 ({rsi_1m > 50}), MA(6) > MA(25) on 15m ({ma_short_15m > ma_long_15m})")
            print(f"For SHORT: RSI(6) 1m < 50 ({rsi_1m < 50}), MA(6) < MA(25) on 15m ({ma_short_15m < ma_long_15m})")
        elif volatility_level == "high_volatility":
            print(f"For LONG: MA(6) > MA(25) on 15m ({ma_short_15m > ma_long_15m})")
            print(f"For SHORT: MA(6) < MA(25) on 15m ({ma_short_15m < ma_long_15m})")
    
    return signal

# Function to calculate dynamic stop loss and take profit based on ATR
def calculate_dynamic_levels(entry_price, position_type):
    atr = calculate_atr()
    
    # Adjust multipliers for faster TP hits
    sl_multiplier = 1.5  # Reduced from 2
    tp_multiplier = 3.0  # Reduced from 4
    
    if position_type == 'long':
        stop_loss = entry_price - (sl_multiplier * atr)
        take_profit = entry_price + (tp_multiplier * atr)
    else:
        stop_loss = entry_price + (sl_multiplier * atr)
        take_profit = entry_price - (tp_multiplier * atr)
    
    # Add debug print
    print(f"\n--- Dynamic SL/TP Levels ---")
    print(f"ATR: {atr:.4f}")
    print(f"Entry: {entry_price:.4f}, Stop Loss: {stop_loss:.4f}, Take Profit: {take_profit:.4f}")
    print(f"SL Distance: {abs(entry_price - stop_loss):.4f}, TP Distance: {abs(entry_price - take_profit):.4f}")
    
    return stop_loss, take_profit

# Function Trading loop
def trading_loop():
    global stop_loss, take_profit, POSITION, ENTRY_PRICE
    
    print("\n=== TRADING BOT STARTED ===")
    print(f"Trading Symbol: {SYMBOL}, Leverage: {LEVERAGE}x, Quantity: {QUANTITY}")
    
    last_signal_check = time.time()
    check_interval = 30  # seconds
    
    while True:
        try:
            current_time = time.time()
            time_diff = current_time - last_signal_check
            
            print(f"\n\n===== TRADING LOOP ITERATION =====")
            print(f"Time since last check: {time_diff:.1f} seconds")
            print(f"Trading Active: {trading_active}, Position: {POSITION}")
            
            # First, check if we need to close an existing position
            if POSITION:
                current_price = get_current_price()
                print(f"\n--- Position Check ---")
                print(f"Position: {POSITION.upper() if POSITION else 'None'}")
                print(f"Entry Price: {ENTRY_PRICE}")
                print(f"Current Price: {current_price}")
                print(f"Stop Loss: {stop_loss}")
                print(f"Take Profit: {take_profit}")
                
                if POSITION == 'long':
                    if current_price <= stop_loss:
                        print(f"STOP LOSS TRIGGERED: Current price {current_price} <= Stop loss {stop_loss}")
                        close_position()
                    elif current_price >= take_profit:
                        print(f"TAKE PROFIT TRIGGERED: Current price {current_price} >= Take profit {take_profit}")
                        close_position()
                elif POSITION == 'short':
                    if current_price >= stop_loss:
                        print(f"STOP LOSS TRIGGERED: Current price {current_price} >= Stop loss {stop_loss}")
                        close_position()
                    elif current_price <= take_profit:
                        print(f"TAKE PROFIT TRIGGERED: Current price {current_price} <= Take profit {take_profit}")
                        close_position()
            
            # Then, check for new signals if no position and enough time has passed
            if trading_active and not POSITION and time_diff >= check_interval:
                print("\n--- Checking for new signals ---")
                signal = generate_signal()
                if signal:
                    place_order(signal)
                    # Calculate stop loss and take profit after placing order
                    stop_loss, take_profit = calculate_dynamic_levels(ENTRY_PRICE, signal)
                    print(f"Signal: {signal}, Entry: {ENTRY_PRICE}, Stop Loss: {stop_loss}, Take Profit: {take_profit}")
                
                last_signal_check = current_time
            
            # Sleep briefly to avoid CPU overuse
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(30)  # Sleep longer on error

@app.route('/start', methods=['POST'])
def start_trading():
    global trading_active
    if not trading_active:
        trading_active = True
        threading.Thread(target=trading_loop, daemon=True).start()
        return jsonify({"status": "Trading started"})
    return jsonify({"status": "Already running"})


@app.route('/stop', methods=['POST'])
def stop_trading():
    global trading_active
    trading_active = False
    close_position()
    return jsonify({"status": "Trading stopped"})


@app.route('/close', methods=['POST'])
def close_trade():
    close_position()
    return jsonify({"status": "Position closed"})


@app.route('/config', methods=['POST'])
def update_config():
    global SYMBOL, LEVERAGE, QUANTITY
    data = request.json
    print(data)
    SYMBOL = data.get("symbol", SYMBOL).upper()
    LEVERAGE = int(data.get("leverage", LEVERAGE))
    QUANTITY = float(data.get("quantity", QUANTITY))
    
    # Set leverage on the Binance client
    try:
        client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
        print(f"Leverage set to {LEVERAGE}x for {SYMBOL}")
    except Exception as e:
        print(f"Error setting leverage: {e}")
        
    return jsonify({"status": "Config updated", "symbol": SYMBOL})


@app.route('/check', methods=['GET'])
def check_indicators():
    """New endpoint to manuall
