document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-message');
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];

    // Create voice button
    const voiceButton = document.createElement('button');
    voiceButton.type = 'button';
    voiceButton.className = 'btn btn-outline-primary';
    voiceButton.innerHTML = '<i class="bi bi-mic"></i>';

    function appendMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'assistant-message'}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${isUser ? '<i class="bi bi-person-circle"></i>' : '<i class="bi bi-robot"></i>'}
                <p>${message}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage(message, true);
        userInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message})
            });
            const data = await response.json();
            appendMessage(data.response, false);
        } catch (error) {
            console.error('Error:', error);
            appendMessage('Sorry, I encountered an error. Please try again.', false);
        }
    });

    voiceButton.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks);
                    const audioData = await audioBlob.arrayBuffer();
                    const floatArray = new Float32Array(audioData);

                    try {
                        const response = await fetch('/api/voice/process', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                audio: Array.from(floatArray)
                            })
                        });

                        const data = await response.json();
                        if (data.error) {
                            appendMessage(data.error, false);
                            return;
                        }

                        if (data.text) {
                            appendMessage(data.text, true);
                        }
                        if (data.response) {
                            appendMessage(data.response, false);
                        }

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
                };

                mediaRecorder.start();
                isRecording = true;
                voiceButton.innerHTML = '<i class="bi bi-mic-fill text-danger"></i>';
                voiceButton.classList.add('recording');

                setTimeout(() => {
                    if (isRecording) {
                        mediaRecorder.stop();
                        isRecording = false;
                        voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
                        voiceButton.classList.remove('recording');
                        stream.getTracks().forEach(track => track.stop());
                    }
                }, 5000); // Record for 5 seconds

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
    // Initialize welcome message
    appendMessage("👋 Hi! I'm your AI financial assistant. How can I help you with your finances today?", false);

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