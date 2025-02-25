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

    // Add voice control button to chat interface
    const voiceButton = document.createElement('button');
    voiceButton.type = 'button';
    voiceButton.className = 'btn btn-primary ms-2';
    voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
    voiceButton.title = 'Use voice assistant';

    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];

    voiceButton.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks);
                    const audioData = await audioBlob.arrayBuffer();
                    const floatArray = new Float32Array(audioData);

                    // Show recording indicator
                    appendMessage("Processing your voice message...", false);

                    try {
                        const response = await fetch('/api/voice/process', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ audio: Array.from(floatArray) })
                        });

                        if (!response.ok) throw new Error('Failed to process voice');

                        const data = await response.json();

                        // Display recognized text
                        appendMessage(data.text, true);

                        // Display and play response
                        appendMessage(data.response, false);

                        // Play audio response
                        if (data.audio && !data.audio.error) {
                            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            const audioBuffer = audioContext.createBuffer(1, data.audio.audio.length, data.audio.sample_rate);
                            audioBuffer.getChannelData(0).set(data.audio.audio);

                            const source = audioContext.createBufferSource();
                            source.buffer = audioBuffer;
                            source.connect(audioContext.destination);
                            source.start();
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        appendMessage("Sorry, I couldn't process your voice message. Please try again.", false);
                    }

                    audioChunks = [];
                };

                mediaRecorder.start();
                isRecording = true;
                voiceButton.innerHTML = '<i class="bi bi-mic-fill text-danger"></i>';
                voiceButton.classList.add('recording');

                // Stop recording after 10 seconds
                setTimeout(() => {
                    if (isRecording) {
                        mediaRecorder.stop();
                        isRecording = false;
                        voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
                        voiceButton.classList.remove('recording');
                        stream.getTracks().forEach(track => track.stop());
                    }
                }, 10000);

            } catch (error) {
                console.error('Error accessing microphone:', error);
                appendMessage("Sorry, I couldn't access your microphone. Please check your permissions.", false);
            }
        } else {
            mediaRecorder.stop();
            isRecording = false;
            voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
            voiceButton.classList.remove('recording');
        }
    });

    chatForm.appendChild(voiceButton);
});