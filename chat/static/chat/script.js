document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.getElementById("toggleButton");
    const status = document.getElementById("status");
    let isListening = false;
    let isProcessing = false;
    let audioFinished = true;
    let currentSessionId = null;

    // Function to toggle listening
    function toggleListening() {
        fetch("/toggle_listening/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
            .then(response => response.json())
            .then(data => {
                isListening = data.is_listening;  // Update listening state
                status.textContent = data.status;  // Update status text
                console.log("Listening toggled:", isListening);
            })
            .catch(error => console.error('Error:', error));
    }

    toggleButton.addEventListener("click", () => {
        // First toggle session
        fetch("/toggle_call_session/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
            .then(response => response.json())
            .then(data => {
                const sessionStarted = data.status.includes("started");
                // Update session status
                toggleButton.textContent = sessionStarted ? "End Session" : "Start Session"; // Change button text
                currentSessionId = data.call_session_id;
                status.textContent = data.status; // Update status

                // Then toggle listening
                toggleListening();
            })
            .catch(error => console.error('Error:', error));
    });

    function updateChat() {
        fetch("/get_chat/")
            .then(response => response.json())
            .then(data => {
                const chat = document.getElementById("chat");
                chat.innerHTML = "";  // Clear existing chat messages

                // Log the current states for debugging
                console.log("----------------------------------");
                console.log("currentSessionId:", currentSessionId);
                console.log("isListening:", isListening);
                console.log("isProcessing:", isProcessing);
                console.log("audioFinished:", audioFinished);

                // Update the isProcessing and isListening flags from the server response
                isProcessing = data.is_processing;
                isListening = data.is_listening;
                currentSessionId = data.current_session_id;

                // Iterate over the chat data
                data.chat_data.forEach(item => {
                    if (item.user_input && item.bot_response) {
                        chat.innerHTML += `<div class="user-message">You: ${item.user_input}</div>`;
                        chat.innerHTML += `<div class="bot-message">LLaMA: ${item.bot_response}</div>`;
                    }
                });

                chat.scrollTop = chat.scrollHeight;  // Scroll to the bottom of the chat

                // Update the status based on processing state
                if (isProcessing) {
                    status.textContent = "Processing...";
                } else {
                    status.textContent = "Ready for input.";
                }

                // Play the bot's speech if audio is finished
                if (audioFinished && !isProcessing) {
                    playBotSpeech();
                }

                // Toggle listening based on processing and listening states
                if ((isProcessing && isListening && !audioFinished) || (!isProcessing && !isListening && audioFinished)) {
                    toggleListening();
                }


            })
            .catch(error => console.error('Error:', error));
    }

    function playBotSpeech() {
        const audio = new Audio("/get_speech_audio/");
        audioFinished = false;
        audio.play();

        audio.onended = () => {
            audioFinished = true;
        };
    }

    setInterval(updateChat, 2000);

    function getCSRFToken() {
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken')).split('=')[1];
    }
});
