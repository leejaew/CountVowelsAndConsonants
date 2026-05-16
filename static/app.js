(function () {
    const root = document.getElementById('app-root');
    const MAX_LEN = parseInt(root.dataset.maxLength, 10) || 50000;
    const input = document.getElementById('text-input');
    const editor = document.getElementById('editor');
    const clearBtn = document.getElementById('clear-btn');
    const statusHint = document.getElementById('status-hint');
    const counter = document.getElementById('counter');
    const statValues = document.querySelectorAll('.stat-value');

    let debounceTimer = null;
    let inFlight = null;

    function setStatus(text, isError) {
        statusHint.textContent = text;
        statusHint.classList.toggle('error-text', !!isError);
        editor.classList.toggle('error', !!isError);
    }

    function updateCounter(len) {
        counter.textContent = len + ' / ' + MAX_LEN;
        counter.classList.toggle('warn', len >= MAX_LEN);
    }

    function validate(text) {
        if (typeof text !== 'string') return 'Invalid input.';
        if (text.length > MAX_LEN) return 'Text exceeds maximum length.';
        return null;
    }

    async function analyze(text) {
        const err = validate(text);
        if (err) { setStatus(err, true); return; }

        if (inFlight) inFlight.abort();
        const controller = new AbortController();
        inFlight = controller;

        try {
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text }),
                signal: controller.signal
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                setStatus(data.error || 'Request failed.', true);
                return;
            }
            statValues.forEach(function (el) {
                const key = el.dataset.key;
                if (key in data) el.textContent = String(data[key]);
            });
            setStatus(text.length > 0 ? 'Analyzed' : 'Ready', false);
        } catch (err) {
            if (err.name === 'AbortError') return;
            setStatus('Network error.', true);
        }
    }

    input.addEventListener('input', function () {
        updateCounter(input.value.length);
        setStatus('Analyzing...', false);
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () { analyze(input.value); }, 200);
    });

    clearBtn.addEventListener('click', function () {
        input.value = '';
        updateCounter(0);
        input.focus();
        analyze('');
    });

    updateCounter(0);
})();
