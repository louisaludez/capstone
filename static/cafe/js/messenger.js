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
    const senderService = cfg.getAttribute('data-sender-service') || '';

    let chatSocket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let isConnecting = false; // Flag to prevent duplicate connections
    const seenMessageIds = new Set(); // Track seen messages to prevent duplicates

    function connectWebSocket() {
        // Prevent duplicate connections
        if (isConnecting || (chatSocket && chatSocket.readyState === WebSocket.OPEN)) {
            return;
        }

        // Close existing connection if any
        if (chatSocket) {
            try {
                chatSocket.close();
            } catch (e) {
                // Ignore errors
            }
        }

        isConnecting = true;
        chatSocket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/chat/' + roomName + '/');

        chatSocket.onopen = function () {
            reconnectAttempts = 0;
            isConnecting = false;
        };

        chatSocket.onmessage = function (e) {
            try {
                const data = JSON.parse(e.data);

                // Check for duplicate messages using message_id if available
                const messageId = data.message_id || data.timestamp + '_' + data.sender_id + '_' + data.body;
                if (seenMessageIds.has(messageId)) {
                    console.log('Duplicate message detected, ignoring:', messageId);
                    return;
                }
                seenMessageIds.add(messageId);

                // Keep only last 100 message IDs to prevent memory issues
                if (seenMessageIds.size > 100) {
                    const firstId = seenMessageIds.values().next().value;
                    seenMessageIds.delete(firstId);
                }

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
            isConnecting = false;
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connectWebSocket, 1000);
            } else {
                window.location.reload();
            }
        };

        chatSocket.onerror = function (error) {
            console.error('WebSocket error:', error);
            isConnecting = false;
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

    let isSending = false; // Flag to prevent duplicate sends
    let listenersAttached = false; // Flag to prevent duplicate event listeners

    function sendMessage() {
        // Prevent duplicate sends
        if (isSending) return;

        const input = document.getElementById('chat-input');
        if (!input) return;
        const message = input.value.trim();
        if (!message) return;

        // Set flag to prevent duplicate sends
        isSending = true;

        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({ body: message, sender_id: senderId, receiver_role: receiverRole, sender_service: senderService }));
            input.value = '';
            // Reset flag after a short delay
            setTimeout(() => {
                isSending = false;
            }, 300);
        } else {
            connectWebSocket();
            isSending = false;
        }
    }

    // Attach event listeners only once
    if (!listenersAttached) {
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            // Remove any existing onclick handler
            sendBtn.onclick = null;
            // Use addEventListener
            sendBtn.addEventListener('click', sendMessage);
        }

        const inputEl = document.getElementById('chat-input');
        if (inputEl) {
            // Add event listener for Enter key
            inputEl.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Prevent form submission if any
                    sendMessage();
                }
            });
        }

        listenersAttached = true;
    }

    setInterval(function () {
        if (chatSocket && chatSocket.readyState === WebSocket.CLOSED) {
            connectWebSocket();
        }
    }, 5000);
})();
