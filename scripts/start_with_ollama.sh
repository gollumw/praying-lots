#!/bin/bash
# 啟動 Ollama 服務並執行觀世音靈籤應用（M4 本機 LLM 串接用）
cd "$(dirname "$0")/.."

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

# 檢查 Ollama 是否已在運行
if curl -s --connect-timeout 2 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    echo "Ollama 已在運行 ($OLLAMA_URL)"
else
    echo "正在啟動 Ollama 服務..."
    (ollama serve &)
    sleep 3
    if ! curl -s --connect-timeout 2 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
        echo "無法連線至 Ollama，請手動執行：ollama serve"
        echo "然後再執行：python3 main.py"
        exit 1
    fi
    echo "Ollama 已啟動"
fi

echo "啟動觀世音靈籤應用 (http://localhost:8000)"
exec python3 main.py
