# main.py
from fastapi import FastAPI, WebSocket
from .database import Base, engine
from . import models
from .trading import router as trading_router
from .admin import router as admin_router
from . import websocket_broadcast

app = FastAPI(title="Atlanta Stock Exchange - Backend")

# create tables (for dev); use alembic for prod migrations
Base.metadata.create_all(bind=engine)

app.include_router(trading_router)
app.include_router(admin_router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_broadcast.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # we won't use incoming messages for now
    except Exception:
        await websocket_broadcast.disconnect(websocket)
