(function () {
    // Ensure receiver_role persists across reloads by using last selection
    try {
        const url = new URL(window.location.href);
        const params = url.searchParams;
        if (!params.has('receiver_role')) {
            const lastRole = localStorage.getItem('messenger_receiver_role');
            if (lastRole) {
                params.set('receiver_role', lastRole);
                window.location.search = params.toString();
                return; // stop further script until reload with param
            }
        }
    } catch (e) {
        // no-op
    }
    const cfg = document.getElementById('chat-config');
    if (!cfg) return;

    const roomName = (cfg.getAttribute('data-room-name') || '').replace(/ /g, '_');
    const senderId = cfg.getAttribute('data-sender-id');
    const senderUsername = cfg.getAttribute('data-sender-username');
    const receiverRole = cfg.getAttribute('data-receiver-role');

    let chatSocket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    function connectWebSocket() {
        chatSocket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/chat/' + roomName + '/');

        chatSocket.onopen = function () {
            reconnectAttempts = 0;
        };

        chatSocket.onmessage = function (e) {
            try {
                const data = JSON.parse(e.data);
                const chatBody = document.getElementById('chat-body');
                if (!chatBody) return;

                const isSender = String(data.sender_id) === String(senderId);

                const wrapper = document.createElement('div');
                wrapper.className = 'd-flex mb-3' + (isSender ? ' justify-content-end' : '');

                const infoDiv = document.createElement('div');
                infoDiv.className = isSender ? 'text-end me-2' : 'me-2';

                const nameDiv = document.createElement('div');
                nameDiv.className = 'small text-muted mb-1';
                nameDiv.textContent = isSender ? senderUsername : (data.sender_username || '');

                const bodyDiv = document.createElement('div');
                bodyDiv.className = 'p-3 bg-light rounded-3';
                bodyDiv.textContent = data.body || '';

                const timeDiv = document.createElement('div');
                timeDiv.className = 'small text-muted mt-1';
                timeDiv.textContent = new Date().toLocaleTimeString();

                infoDiv.appendChild(nameDiv);
                infoDiv.appendChild(bodyDiv);
                infoDiv.appendChild(timeDiv);

                const avatarDiv = document.createElement('div');
                avatarDiv.className = 'avatar bg-secondary rounded-circle text-white';
                avatarDiv.style.width = '40px';
                avatarDiv.style.height = '40px';
                avatarDiv.style.display = 'flex';
                avatarDiv.style.alignItems = 'center';
                avatarDiv.style.justifyContent = 'center';

                const icon = document.createElement('i');
                icon.className = 'bi bi-person';
                avatarDiv.appendChild(icon);

                wrapper.appendChild(infoDiv);
                wrapper.appendChild(avatarDiv);

                chatBody.appendChild(wrapper);
                chatBody.scrollTop = chatBody.scrollHeight;
            } catch (err) {
                console.error('Message handling error', err);
            }
        };

        chatSocket.onclose = function () {
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connectWebSocket, 1000);
            } else {
                window.location.reload();
            }
        };

        chatSocket.onerror = function (error) {
            console.error('WebSocket error:', error);
        };
    }

    connectWebSocket();

    document.querySelectorAll('.service-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const role = this.getAttribute('data-role');
            try { localStorage.setItem('messenger_receiver_role', role); } catch (e) { }
            const params = new URLSearchParams(window.location.search);
            params.set('receiver_role', role);
            window.location.search = params.toString();
        });
    });

    function sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input) return;
        const message = input.value;
        if (!message || message.trim() === '') return;

        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({ body: message, sender_id: senderId, receiver_role: receiverRole }));
            input.value = '';
        } else {
            connectWebSocket();
        }
    }

    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) sendBtn.onclick = sendMessage;

    const inputEl = document.getElementById('chat-input');
    if (inputEl) {
        inputEl.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    setInterval(function () {
        if (chatSocket && chatSocket.readyState === WebSocket.CLOSED) {
            connectWebSocket();
        }
    }, 5000);
})();
