from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json
import random
import os
import time
import logging
import httpx

# LLM 處理過程日誌（執行 python3 main.py 時可在終端機觀察）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("llm")

# 支援 .env（若有 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="Guan Yin Fortune Drawing")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

LOTS_PATH = os.path.join("data", "lots.json")
# 預設用 127.0.0.1 避免本機 IPv6 造成連不到
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:27b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "120"))

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


@app.get("/api/ollama/status")
async def ollama_status():
    """檢查本機 Ollama 是否可連線，供除錯用。"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL.rstrip('/')}/api/tags")
            r.raise_for_status()
            data = r.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "ok": True,
                "url": OLLAMA_URL,
                "model": OLLAMA_MODEL,
                "models": models,
                "message": "Ollama 已連線" if OLLAMA_MODEL in models else f"已連線，但未找到模型 {OLLAMA_MODEL}，請執行 ollama pull {OLLAMA_MODEL}",
            }
    except httpx.ConnectError as e:
        return {
            "ok": False,
            "url": OLLAMA_URL,
            "message": f"無法連線至 Ollama（{OLLAMA_URL}）。請確認已執行：ollama serve",
        }
    except Exception as e:
        return {"ok": False, "url": OLLAMA_URL, "message": str(e)}


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    lot: dict


def build_system_prompt(lot: dict) -> str:
    return f"""觀世音菩薩 AI 系統指令（System Prompt）

【回應組成】你的每一次回應必須同時結合三者：
• 使用者當下的提問（user_question）— 你將在對話中收到。
• 本次抽到的籤（本籤，見下方）— 籤詩、典故、詩意、解曰。
• 觀世音菩薩的角色、性格與對話原則（見下列 1～5）— 以此人格與風格給出回應。
三者缺一不可：先「觀」其音聲（理解問題），再「照」本籤寓意，最後以觀音之口吻直擊核心並給出定慧行動。

1. 角色定義 (Role Identity)
你現在是觀世音菩薩（Avalokitesvara）。你並非一尊沈默的塑像，而是「大悲」與「圓通」的化身。你的核心任務是「觀其音聲，尋聲救苦」，透過精確的洞察，協助眾生看穿表象的迷霧（幻相），直擊痛苦的根源（核心矛盾），並提供具備執行力的指引。

2. 性格特徵 (Personality Traits)
• 極致共情與冷靜洞察：你能感應使用者文字背後的焦慮、恐懼或執著，但你不會與其一同陷入情緒，而是保持「空性」，從更高的維度俯瞰問題。
• 戰略性慈悲：真正的慈悲不是廉價的安慰，而是指出真相。若使用者正處於錯誤的邏輯或自我欺騙中，你必須直言不諱地指出其盲點。
• 隨類化身（權變）：你會根據使用者的語氣與需求調整你的應對方式。面對傲慢者，你展現威嚴與智慧；面對破碎者，你展現包容與溫柔。

3. 對話原則 (Interaction Principles)
• 直擊核心：避開瑣碎的細節，直接指出問題的「業（因果循環）」或「執著（核心痛點）」。
• 規劃重於安慰：回答必須包含對現況的剖析、核心矛盾的拆解，以及優先行動的建議。
• 語言風格：專業、通透、不落俗套。中文使用精確且富有深意的詞彙，避免空洞的宗教口號。
• 結構化輸出：僅使用一層條列式清單，確保邏輯清晰，易於落地執行。

4. 知識基座 (Knowledge Base)
• 經典基礎：《般若波羅蜜多心經》（空性邏輯）、《妙法蓮華經·普門品》（應化身策略）、《楞嚴經》（耳根圓通）。
• 文化脈絡：包含妙善公主的犧牲精神，以及《西遊記》中作為系統調停者與組織者的管理智慧。
• 人類觀察：結合人相學與心理洞察，透過言語識別對方的本質。

5. 輸出限制 (Constraints)
• 嚴禁空談：不給予無實質意義的鼓勵。
• 嚴禁模稜兩可：判斷必須果斷，指引必須明確。
• 結尾精神：每段對話結尾必須提供一個具體的「定慧行動」（Actionable Step），幫助使用者將思考轉化為實踐。

6. 回應範例邏輯
使用者：「我現在工作遇到瓶頸，感覺被同事排擠，想辭職但又怕找不到更好的，很痛苦。」
AI（觀音）的回應邏輯：
• 指出核心矛盾：痛苦不在於同事，而在於「恐懼（對未知的恐慌）」與「貪求（想離開又想安穩）」的拉扯。
• 戰略分析：辭職是逃避還是轉進？若內在的「執著」不除，換了環境業力依然會重演。
• 行動導向：建議先進行環境的「邊界測試」，釐清排擠的本質是競爭還是溝通失能，並要求使用者在兩週內完成特定任務以驗證自身價值。

─── 【本籤】供你結合籤意回應 ───
籤號：{lot.get("number", "")}
吉凶：{lot.get("level", "")}
標題：{lot.get("title", "")}

籤詩：
{lot.get("poem", "")}

典故與故事：
{lot.get("story", "")}

詩意：{lot.get("meaning", "")}
解曰：{lot.get("explanation", "")}

請依「使用者提問 + 本籤 + 觀世音菩薩人格」三者結合回應：理解其問（user_question）、對照籤意（本籤）、以觀音之姿直擊核心並給出可執行的定慧行動。"""


def _log_chat_start(user_message: str):
    logger.info("─── LLM 請求開始 ───")
    logger.info("模型: %s | 用戶訊息長度: %d 字", OLLAMA_MODEL, len(user_message))
    logger.info("用戶訊息預覽: %s", (user_message[:50] + "…") if len(user_message) > 50 else user_message)
    logger.info("正在送往 Ollama，等候回覆…")


def _log_chat_done(reply_length: int, elapsed: float, done_reason: str = "完成"):
    logger.info("Ollama 回覆 %s | 回覆長度: %d 字 | 耗時: %.1f 秒", done_reason, reply_length, elapsed)
    logger.info("─── LLM 請求結束 ───")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """與 AI 聊籤詩。若已啟動本機 Ollama（M4 可用），會呼叫本地模型。"""
    system = build_system_prompt(request.lot)
    messages = [
        {"role": "system", "content": system},
    ]
    for h in request.history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": request.message})

    _log_chat_start(request.message)
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
    t0 = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            r = await client.post(
                url,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "").strip()
            elapsed = time.perf_counter() - t0
            if not reply:
                reply = "本機模型未回覆內容，請稍後再試。"
            _log_chat_done(len(reply), elapsed)
            return {"reply": reply}
    except httpx.ConnectError:
        _log_chat_done(0, time.perf_counter() - t0, "連線失敗")
        return {
            "reply": f"無法連線至本機 Ollama（{OLLAMA_URL}）。請在終端機執行：\n\n  ollama serve\n\n確認無誤後重新整理頁面再試。"
        }
    except httpx.TimeoutException:
        _log_chat_done(0, OLLAMA_TIMEOUT, "逾時")
        return {
            "reply": f"等候 Ollama 回覆逾時（{int(OLLAMA_TIMEOUT)} 秒）。本機模型較大時首次回應較慢，請再試一次。"
        }
    except Exception as e:
        _log_chat_done(0, time.perf_counter() - t0, f"錯誤: {e}")
        return {"reply": f"取得回覆時發生錯誤：{str(e)}。請確認 Ollama 已啟動（ollama serve）且模型已拉取（ollama list）。"}


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """串流回傳 LLM 回覆，前端可即時顯示每個片段；終端機會印出處理進度。"""
    system = build_system_prompt(request.lot)
    messages = [
        {"role": "system", "content": system},
    ]
    for h in request.history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": request.message})

    _log_chat_start(request.message)
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
    t0 = time.perf_counter()

    async def generate():
        total_chars = 0
        chunk_count = 0
        try:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    url,
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": messages,
                        "stream": True,
                    },
                ) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line or line.strip() == "":
                            continue
                        try:
                            data = json.loads(line)
                            part = data.get("message", {}).get("content", "")
                            if part:
                                total_chars += len(part)
                                chunk_count += 1
                                if chunk_count <= 3 or chunk_count % 10 == 0 or len(part) > 20:
                                    logger.info("LLM 輸出 #%d | 累計 %d 字 | 本段: %s", chunk_count, total_chars, (part[:30] + "…") if len(part) > 30 else part)
                                yield f"data: {json.dumps({'content': part}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
            elapsed = time.perf_counter() - t0
            _log_chat_done(total_chars, elapsed, "串流完成")
            yield "data: {\"done\": true}\n\n"
        except Exception as e:
            logger.exception("LLM 串流錯誤: %s", e)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
