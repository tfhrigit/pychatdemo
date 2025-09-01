const socket = io();

// Handle connection
socket.on('connect', () => {
    console.log('Connected to server');
});

// Handle new messages
socket.on('new_message', (data) => {
    // Add new message to chat
    const messageElement = createMessageElement(data);
    document.getElementById('chat-messages').appendChild(messageElement);
    scrollToBottom();
});

// Handle user typing
socket.on('user_typing', (data) => {
    // Show typing indicator
    showTypingIndicator(data);
});

// Handle user stop typing
socket.on('user_stop_typing', (data) => {
    // Hide typing indicator
    hideTypingIndicator(data);
});

// Handle user status (online/offline)
socket.on('user_status', (data) => {
    // Update user status
    updateUserStatus(data);
});

// Send message
document.getElementById('message-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const recipientId = formData.get('recipient_id');
    const content = formData.get('content');
    
    if (content.trim()) {
        socket.emit('private_message', {
            recipient_id: parseInt(recipientId),
            content: content.trim()
        });
        
        e.target.reset();
    }
});

// Typing indicators
const messageInput = document.getElementById('message-input');
let typing = false;
let typingTimeout;

messageInput?.addEventListener('input', () => {
    if (!typing) {
        typing = true;
        const recipientId = document.querySelector('input[name="recipient_id"]').value;
        socket.emit('typing', { recipient_id: parseInt(recipientId) });
    }
    
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        typing = false;
        const recipientId = document.querySelector('input[name="recipient_id"]').value;
        socket.emit('stop_typing', { recipient_id: parseInt(recipientId) });
    }, 1000);
});

// Helper functions
function createMessageElement(data) {
    // Create and return message element
    // Implementation depends on message type
}

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator(data) {
    // Show typing indicator for user
}

function hideTypingIndicator(data) {
    // Hide typing indicator for user
}

function updateUserStatus(data) {
    // Update user status in UI
}