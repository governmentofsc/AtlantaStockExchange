# websocket_broadcast.py
from fastapi import WebSocket
import asyncio

# very simple in-memory websocket manager
clients = set()

async def connect(ws: WebSocket):
    await ws.accept()
    clients.add(ws)

async def disconnect(ws: WebSocket):
    clients.remove(ws)

def broadcast_price(ticker: str, price: float):
    # schedule coroutines on event loop; avoid blocking path
    msg = {"type":"price_update", "ticker": ticker, "price": price}
    import asyncio, json
    loop = asyncio.get_event_loop()
    for ws in list(clients):
        asyncio.run_coroutine_threadsafe(ws.send_text(json.dumps(msg)), loop)
