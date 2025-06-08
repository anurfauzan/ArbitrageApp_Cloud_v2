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
        for symbol in SYMBOLS_TO_MONITOR:
            if symbol in binance_market_data and symbol in simulated_another_exchange_data:
                binance_ask = binance_market_data[symbol]["askPrice"]
                binance_bid = binance_market_data[symbol]["bidPrice"]

                another_ask = simulated_another_exchange_data[symbol]["askPrice"]
                another_bid = simulated_another_exchange_data[symbol]["bidPrice"]

                FEE_RATE = 0.001

                if binance_ask > 0 and another_bid > 0:
                    gross_profit = (another_bid - binance_ask)
                    total_fee = (binance_ask * FEE_RATE) + (another_bid * FEE_RATE)
                    net_profit = gross_profit - total_fee
                    net_profit_percent = (net_profit / binance_ask) * 100 if binance_ask > 0 else 0

                    if net_profit_percent > 0.05:
                        opportunity_data = {
                            "symbol": symbol,
                            "buy_exchange": "Binance",
                            "buy_price": round(binance_ask, 8),
                            "sell_exchange": "AnotherExchange",
                            "sell_price": round(another_bid, 8),
                            "gross_profit_usd": round(gross_profit, 4),
                            "net_profit_percent": round(net_profit_percent, 4)
                        }
                        opportunities.append(opportunity_data)
                        print(f"PELUANG DITEMUKAN (Binance -> Other): {opportunity_data}")

                if another_ask > 0 and binance_bid > 0:
                    gross_profit = (binance_bid - another_ask)
                    total_fee = (another_ask * FEE_RATE) + (binance_bid * FEE_RATE)
                    net_profit = gross_profit - total_fee
                    net_profit_percent = (net_profit / another_ask) * 100 if another_ask > 0 else 0

                    if net_profit_percent > 0.05:
                        opportunity_data = {
                            "symbol": symbol,
                            "buy_exchange": "AnotherExchange",
                            "buy_price": round(another_ask, 8),
                            "sell_exchange": "Binance",
                            "sell_price": round(binance_bid, 8),
                            "gross_profit_usd": round(gross_profit, 4),
                            "net_profit_percent": round(net_profit_percent, 4)
                        }
                        opportunities.append(opportunity_data)
                        print(f"PELUANG DITEMUKAN (Other -> Binance): {opportunity_data}")

            if connected_clients:
                message = json.dumps({"type": "arbitrage_opportunities", "data": opportunities})
                await asyncio.gather(*[client.send(message) for client in connected_clients], return_exceptions=True)

async def websocket_server(websocket, path): 
    print(f"New client connected from {websocket.remote_address}")
    connected_clients.add(websocket)

    try:
        initial_data = {
            "type": "initial_data",
            "binance_prices": binance_market_data,
            "current_opportunities": []
        }
        await websocket.send(json.dumps(initial_data))
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected from {websocket.remote_address}")

async def main():
    port = int(os.getenv('PORT', 8080))

    server_task = websockets.serve(websocket_server, "0.0.0.0", port) 

    await asyncio.gather(
        fetch_binance_data(),
        arbitrage_engine(),
        server_task
    )

if __name__ == "__main__":
    print("Starting Arbitrage Backend...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBackend stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
      
