const chatContainer = document.getElementById("chat-container");
const chatContent = document.getElementById("chat-content");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");

function toggleChat() {
    chatContainer.style.display = chatContainer.style.display === "none" ? "flex" : "none";
}

async function fetchMessages() {
    try {
        const response = await fetch("/messages");
        const messages = await response.json();

        for (const message of messages) {
            appendMessage(message.sender, message.content);
        }
    } catch (error) {
        console.error("Error fetching messages:", error);
    }
}

// Fetch and display stored messages on page load
//fetchMessages();

// Initialize the chatbot by hiding the chat container
//toggleChat();
//toggleChat();

async function sendMessage(event) {
    // Prevent default form submission behavior
    if (event) event.preventDefault();

    const message = chatInput.value.trim();

    if (message === "") return false;

    appendMessage("User", message);
    chatInput.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        appendMessage("ChatGPT", data.response);
    } catch (error) {
        console.error("Error fetching response from ChatGPT:", error);
        appendMessage("ChatGPT", "An error occurred. Please try again.");
    }

    return false;
}

function appendMessage(sender, message) {
    const messageElement = document.createElement("div");
    messageElement.classList.add(sender === "User" ? "user-message" : "chatbot-message");
    messageElement.textContent = `${sender}: ${message}`;
    chatContent.appendChild(messageElement);

    // Scroll to the bottom of the chat content
    chatContent.scrollTop = chatContent.scrollHeight;
}

// Initialize the chatbot by hiding the chat container
toggleChat();
