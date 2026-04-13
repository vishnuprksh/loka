import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from src.db import init_db, reset_db
from src.environment import THE_GROVE
from src.simulation import (
    TICK_INTERVAL,
    create_agent,
    get_state_dict,
    seed_default_agents,
    tick,
)

# ------------------------------------------------------------------ #
# WebSocket client registry                                           #
# ------------------------------------------------------------------ #
clients: set[WebSocket] = set()


async def broadcast(data: dict) -> None:
    message = json.dumps(data)
    dead: set[WebSocket] = set()
    for ws in list(clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    clients.difference_update(dead)


# ------------------------------------------------------------------ #
# Simulation background loop                                          #
# ------------------------------------------------------------------ #
async def simulation_loop() -> None:
    await asyncio.sleep(2)  # Let startup complete
    while True:
        loop = asyncio.get_event_loop()
        try:
            new_tick = await loop.run_in_executor(None, tick)
            state    = await loop.run_in_executor(None, get_state_dict)
            await broadcast(state)
            alive = sum(1 for a in state["agents"] if a["alive"])
            print(f"[Tick {new_tick}] alive={alive}  berries={state['berry_count']}")
        except Exception as exc:
            print(f"[Tick Error] {exc}")
        await asyncio.sleep(TICK_INTERVAL)


# ------------------------------------------------------------------ #
# App lifecycle                                                       #
# ------------------------------------------------------------------ #
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Clear and re-seed the DB on every startup
    reset_db(THE_GROVE)
    seed_default_agents()
    asyncio.create_task(simulation_loop())
    yield


app = FastAPI(title="Loka — The Grove", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #
@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/state")
def get_state() -> dict:
    return get_state_dict()


class AgentCreate(BaseModel):
    name:          str   = Field(..., min_length=2, max_length=20)
    greed:         float = Field(0.5, ge=0.0, le=1.0)
    sociability:   float = Field(0.7, ge=0.0, le=1.0)
    curiosity:     float = Field(0.5, ge=0.0, le=1.0)
    empathy:       float = Field(0.5, ge=0.0, le=1.0)
    assertiveness: float = Field(0.5, ge=0.0, le=1.0)


@app.post("/agents")
def new_agent(body: AgentCreate) -> dict:
    agent_id = create_agent(body.name, body.greed, body.sociability, body.curiosity, 
                            body.empathy, body.assertiveness)
    return {"id": agent_id, "name": body.name}


@app.post("/reset")
def reset_simulation() -> dict:
    reset_db(THE_GROVE)
    seed_default_agents()
    return {"status": "reset complete", "tick": 0}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    clients.add(ws)
    try:
        # Push current state immediately on connect
        await ws.send_text(json.dumps(get_state_dict()))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)
    except Exception:
        clients.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
