document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-message');

    function appendMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message p-2 mb-2 ${isUser ? 'text-end' : ''}`;

        const bubble = document.createElement('div');
        bubble.className = `d-inline-block p-3 rounded ${isUser ? 'bg-primary text-white' : 'bg-light border'}`;
        bubble.style.maxWidth = '80%';
        bubble.style.wordWrap = 'break-word';

        // Convert markdown-style bold text to HTML
        const formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        bubble.innerHTML = formattedMessage;

        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const message = userInput.value.trim();
        if (!message) return;

        // Append user message
        appendMessage(message, true);
        userInput.value = '';

        try {
            // Show loading indicator with a friendly message
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-message p-2 mb-2';
            loadingDiv.innerHTML = `
                <div class="d-inline-block p-3 rounded bg-light border">
                    <div class="d-flex align-items-center">
                        <div class="spinner-grow spinner-grow-sm text-primary me-2" role="status"></div>
                        Analyzing your finances...
                    </div>
                </div>
            `;
            chatMessages.appendChild(loadingDiv);

            // Get AI response
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            // Remove loading indicator
            loadingDiv.remove();

            // Append AI response
            appendMessage(data.response);

        } catch (error) {
            console.error('Error:', error);
            loadingDiv?.remove();
            appendMessage('Sorry, I encountered an error. Please try again.');
        }
    });

    // Add quick action buttons for common queries
    const addQuickActionButton = (text, query) => {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-primary me-2 mb-2';
        button.innerHTML = text; // Use innerHTML to support emojis
        button.onclick = () => {
            userInput.value = query;
            chatForm.dispatchEvent(new Event('submit'));
        };
        return button;
    };

    const quickActionsDiv = document.createElement('div');
    quickActionsDiv.className = 'quick-actions mt-3';

    const commonQueries = [
        ['💰 Analyze Spending', 'Why did I overspend this month?'],
        ['💡 Saving Tips', 'Give me some tips to save money as a student'],
        ['🎯 Budget Help', 'Help me create a realistic student budget'],
        ['📊 Simulate Income', 'Simulate my finances if I get a part-time job'],
    ];

    commonQueries.forEach(([text, query]) => {
        quickActionsDiv.appendChild(addQuickActionButton(text, query));
    });

    chatForm.parentNode.insertBefore(quickActionsDiv, chatForm);
});