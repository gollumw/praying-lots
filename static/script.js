document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const btnStart = document.getElementById('btn-start');
    const btnThrow = document.getElementById('btn-throw');
    const btnDraw = document.getElementById('btn-draw');
    const btnRestart = document.getElementById('btn-restart');

    const stepQuestion = document.getElementById('step-question');
    const stepBlocks = document.getElementById('step-blocks');
    const stepDraw = document.getElementById('step-draw');
    const stepResult = document.getElementById('step-result');

    const blocks = [document.getElementById('block-1'), document.getElementById('block-2')];
    const blockResultText = document.getElementById('block-result');
    const sticksContainer = document.querySelector('.stick-bucket');

    // Transitions
    function showStep(step) {
        [stepQuestion, stepBlocks, stepDraw, stepResult].forEach(s => s.classList.add('hidden'));
        step.classList.remove('hidden');
        step.classList.add('active');
    }

    // Start
    btnStart.addEventListener('click', () => {
        showStep(stepBlocks);
    });

    // Throw Moon Blocks
    btnThrow.addEventListener('click', async () => {
        btnThrow.disabled = true;
        blockResultText.textContent = "";

        // CSS Animation
        blocks.forEach(b => {
            b.classList.remove('flat-down');
            b.classList.add('throwing');
        });

        setTimeout(() => {
            blocks.forEach(b => b.classList.remove('throwing'));

            // Random result (聖杯, 笑杯, 陰杯)
            // 0: flat up, 1: flat down
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

    // Draw Lot
    btnDraw.addEventListener('click', async () => {
        btnDraw.disabled = true;
        sticksContainer.classList.add('shaking');

        try {
            const response = await fetch('/api/draw');
            const lot = await response.json();

            setTimeout(() => {
                sticksContainer.classList.remove('shaking');
                displayResult(lot);
                showStep(stepResult);
                btnDraw.disabled = false;
            }, 1500);

        } catch (error) {
            console.error("Error drawing lot:", error);
            alert("抽籤過程中發生錯誤，請稍後再試。");
            btnDraw.disabled = false;
        }
    });

    function displayResult(lot) {
        document.getElementById('result-number').textContent = lot.number;
        document.getElementById('result-title').textContent = lot.title;
        document.getElementById('result-poem').textContent = lot.poem;
        document.getElementById('result-meaning').textContent = lot.meaning;
        document.getElementById('result-explanation').textContent = lot.explanation;
    }

    btnRestart.addEventListener('click', () => {
        showStep(stepQuestion);
    });
});
