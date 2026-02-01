from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import random
import os

app = FastAPI(title="Guan Yin Fortune Drawing")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

LOTS_PATH = os.path.join("data", "lots.json")

def load_lots():
    with open(LOTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/draw")
async def draw_lot():
    lots = load_lots()
    lot = random.choice(lots)
    return lot

@app.get("/api/lot/{lot_id}")
async def get_lot(lot_id: int):
    lots = load_lots()
    for lot in lots:
        if lot["id"] == lot_id:
            return lot
    raise HTTPException(status_code=404, detail="Lot not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
