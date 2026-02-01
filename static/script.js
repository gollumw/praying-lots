document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const btnStart = document.getElementById('btn-start');
    const btnThrow = document.getElementById('btn-throw');
    const btnDraw = document.getElementById('btn-draw');
    const btnRestart = document.getElementById('btn-restart');
    const btnCloseDialog = document.getElementById('btn-close-dialog');
    const btnSendChat = document.getElementById('btn-send-chat');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const lotDialog = document.getElementById('lot-dialog');

    const stepQuestion = document.getElementById('step-question');
    const stepBlocks = document.getElementById('step-blocks');
    const stepDraw = document.getElementById('step-draw');
    const stepResult = document.getElementById('step-result');

    const blocks = [document.getElementById('block-1'), document.getElementById('block-2')];
    const blockResultText = document.getElementById('block-result');
    const sticksContainer = document.querySelector('.stick-bucket');

    let currentLot = null;
    let chatHistory = [];

    // Transitions
    function showStep(step) {
        [stepQuestion, stepBlocks, stepDraw, stepResult].forEach(s => s.classList.add('hidden'));
        step.classList.remove('hidden');
        step.classList.add('active');
    }

    async function openResultDialog(lot) {
        currentLot = lot;
        chatHistory = [];

        const userQuestion = (document.getElementById('user-question').value || '').trim();
        document.getElementById('dialog-result-title').textContent = userQuestion
            ? '籤詩結果- ' + userQuestion
            : '籤詩結果';

        document.getElementById('dialog-number').textContent = lot.number;
        document.getElementById('dialog-level').textContent = lot.level || '';
        document.getElementById('dialog-title').textContent = lot.title;
        document.getElementById('dialog-poem').textContent = lot.poem;
        document.getElementById('dialog-story').textContent = lot.story || '—';
        document.getElementById('dialog-meaning').textContent = lot.meaning || '';
        document.getElementById('dialog-explanation').textContent = lot.explanation || '';

        chatMessages.innerHTML = '';
        chatInput.value = '';
        lotDialog.classList.remove('hidden');

        const statusEl = document.getElementById('ollama-status');
        statusEl.textContent = '正在檢查本機 LLM 連線…';
        statusEl.className = 'ollama-status checking';
        try {
            const res = await fetch('/api/ollama/status');
            const data = await res.json();
            if (data.ok) {
                statusEl.textContent = '本機 LLM 已連線，可與觀世音菩薩聊聊。';
                statusEl.className = 'ollama-status ok';
            } else {
                statusEl.textContent = data.message || '本機 LLM 未連線，請先執行：ollama serve';
                statusEl.className = 'ollama-status error';
            }
        } catch (e) {
            statusEl.textContent = '無法檢查 LLM 連線，請確認伺服器已啟動。';
            statusEl.className = 'ollama-status error';
        }
    }

    function closeResultDialog() {
        lotDialog.classList.add('hidden');
        currentLot = null;
        chatHistory = [];
        showStep(stepQuestion);
    }

    function appendChatMessage(role, text) {
        const div = document.createElement('div');
        div.className = 'chat-msg ' + role;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendChat() {
        const text = (chatInput.value || '').trim();
        if (!text || !currentLot) return;

        chatInput.value = '';
        appendChatMessage('user', text);

        const placeholder = document.createElement('div');
        placeholder.className = 'chat-msg assistant chat-streaming';
        placeholder.textContent = '…';
        chatMessages.appendChild(placeholder);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const payload = {
            message: text,
            history: chatHistory,
            lot: {
                number: currentLot.number,
                title: currentLot.title,
                level: currentLot.level,
                poem: currentLot.poem,
                story: currentLot.story,
                meaning: currentLot.meaning,
                explanation: currentLot.explanation
            }
        };

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok || !response.body) {
                throw new Error('串流不可用');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullReply = '';
            placeholder.textContent = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.content) {
                                fullReply += data.content;
                                placeholder.textContent = fullReply;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                            if (data.error) fullReply = data.error;
                            if (data.done) break;
                        } catch (_) {}
                    }
                }
            }

            placeholder.classList.remove('chat-streaming');
            if (!fullReply) fullReply = '目前無法取得 AI 回覆，請確認已啟動本機 LLM（如 Ollama）。';
            placeholder.textContent = fullReply;
            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: fullReply });
        } catch (err) {
            console.error(err);
            try {
                const fallback = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await fallback.json();
                placeholder.classList.remove('chat-streaming');
                placeholder.textContent = data.reply || '目前無法取得 AI 回覆，請確認已啟動本機 LLM（如 Ollama）。';
                chatHistory.push({ role: 'user', content: text });
                chatHistory.push({ role: 'assistant', content: placeholder.textContent });
            } catch (e2) {
                placeholder.remove();
                appendChatMessage('assistant', '連線錯誤，請稍後再試。若使用本機 LLM，請確認 Ollama 已啟動。');
            }
        }
    }

    btnStart.addEventListener('click', () => {
        showStep(stepBlocks);
    });

    btnThrow.addEventListener('click', async () => {
        btnThrow.disabled = true;
        blockResultText.textContent = "";

        blocks.forEach(b => {
            b.classList.remove('flat-down');
            b.classList.add('throwing');
        });

        setTimeout(() => {
            blocks.forEach(b => b.classList.remove('throwing'));

            const r1 = Math.round(Math.random());
            const r2 = Math.round(Math.random());

            if (r1 === 1) blocks[0].classList.add('flat-down');
            if (r2 === 1) blocks[1].classList.add('flat-down');

            let resultMsg = "";
            let success = false;

            if (r1 !== r2) {
                resultMsg = "【聖杯】請抽籤";
                success = true;
            } else if (r1 === 0 && r2 === 0) {
                resultMsg = "【笑杯】再敘述一次您的問題";
            } else {
                resultMsg = "【陰杯】神明不允，請再次誠心祈求";
            }

            blockResultText.textContent = resultMsg;
            btnThrow.disabled = false;

            if (success) {
                setTimeout(() => showStep(stepDraw), 1500);
            }
        }, 800);
    });

    btnDraw.addEventListener('click', async () => {
        btnDraw.disabled = true;
        sticksContainer.classList.add('shaking');

        try {
            const response = await fetch('/api/draw');
            const lot = await response.json();

            setTimeout(() => {
                sticksContainer.classList.remove('shaking');
                showStep(stepResult);
                openResultDialog(lot);
                btnDraw.disabled = false;
            }, 1500);

        } catch (error) {
            console.error("Error drawing lot:", error);
            alert("抽籤過程中發生錯誤，請稍後再試。");
            btnDraw.disabled = false;
        }
    });

    btnCloseDialog.addEventListener('click', closeResultDialog);
    btnRestart.addEventListener('click', closeResultDialog);

    lotDialog.querySelector('.lot-dialog-backdrop').addEventListener('click', closeResultDialog);

    btnSendChat.addEventListener('click', sendChat);
    chatInput.addEventListener('keydown', (e) => {
        // Enter 送出；中文輸入法選字時按 Enter 不送出（等 composition 結束）
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            sendChat();
        }
    });
});
