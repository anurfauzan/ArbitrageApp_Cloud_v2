import asyncio
import os
import websockets
import json
import time
from binance.client import Client
from binance.enums import *

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "") 
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "") 

SYMBOLS_TO_MONITOR = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

binance_market_data = {}

connected_clients = set()

async def fetch_binance_data():
    streams = "/".join([f"{symbol.lower()}@bookTicker" for symbol in SYMBOLS_TO_MONITOR])
    uri = f"wss://stream.binance.com:9443/ws/{streams}"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to Binance WebSocket: {uri}")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if 's' in data and 'b' in data and 'a' in data:
                        symbol = data['s']
                        bid_price = float(data['b'])
                        ask_price = float(data['a'])

                        binance_market_data[symbol] = {
                            "bidPrice": bid_price,
                            "askPrice": ask_price
                        }

        except websockets.exceptions.ConnectionClosedOK:
            print("Binance WebSocket connection closed normally. Attempting to reconnect...")
        except Exception as e:
            print(f"Error connecting/receiving from Binance WebSocket: {e}. Attempting to reconnect in 5 seconds...")
        await asyncio.sleep(5)

async def arbitrage_engine():
    simulated_another_exchange_data = {
        "BTCUSDT": {"bidPrice": 0.0, "askPrice": 0.0},
        "ETHUSDT": {"bidPrice": 0.0, "askPrice": 0.0},
        "BNBUSDT": {"bidPrice": 0.0, "askPrice": 0.0},
    }

    def update_simulated_data():
        for symbol in SYMBOLS_TO_MONITOR:
            if symbol in binance_market_data:
                binance_bid = binance_market_data[symbol]["bidPrice"]
                binance_ask = binance_market_data[symbol]["askPrice"]

                variance_factor = (time.time() % 100) / 100000 + 0.0005 

                if hash(symbol) % 2 == 0:
                    simulated_another_exchange_data[symbol]["bidPrice"] = binance_bid * (1 + variance_factor)
                    simulated_another_exchange_data[symbol]["askPrice"] = binance_ask * (1 + variance_factor)
                else:
                    simulated_another_exchange_data[symbol]["bidPrice"] = binance_bid * (1 - variance_factor)
                    simulated_another_exchange_data[symbol]["askPrice"] = binance_ask * (1 - variance_factor)

    while True:
        await asyncio.sleep(1)

        update_simulated_data()

        opportunities = []
        for symbol in SYMBOLS_TO_MONITOR
      
