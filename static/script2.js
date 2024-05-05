$(document).ready(function () {
    // Retrieve the issue ID dynamically from the data attribute or other source
    const issueContainer = document.querySelector(".issue-container");
    const issueId = issueContainer.dataset.issueId;

    // Create WebSocket URL dynamically using the issue ID
    const websocket = new WebSocket(`ws://localhost:8000/ws/${issueId}`);
    let message_finished = true;
    let ongoingBotMessageId = null;

    // WebSocket connection established
    websocket.onopen = function (event) {
        console.log("Connection established");
    };

    // WebSocket error
    websocket.onerror = function (error) {
        console.log("WebSocket error: ", error);
    };

    // Enable automatic text area resizing
    autosize(document.querySelector("#prompt-input"));

    // Send message on Enter key (without Shift)
    $("#prompt-input").keydown(function (event) {
        if (event.keyCode === 13 && !event.shiftKey) {
            event.preventDefault();
            $("#prompt-form").submit();
        }
    });

    // Form submission handling
    $("#prompt-form").submit(function (e) {
        e.preventDefault(); // Prevent form submission from refreshing the page

        if (!message_finished) {
            return; // Prevent new messages while a previous bot response is ongoing
        }

        // Retrieve user input and clear the input field
        const prompt_term = $("#prompt-input").val();
        $("#prompt-input").val("");

        // Add user message to chat history
        $("#chat-history").append(`<li class='user-response'><span class='label'>User:</span> ${prompt_term}</li>`);

        // Generate a unique ID for the bot's response and create a placeholder in chat history
        ongoingBotMessageId = "botMessage" + Date.now();
        $("#chat-history").append(`<li class='bot-response' id='${ongoingBotMessageId}'><span class='label'>Bot:</span> </li>`);

        // Set message_finished to false until the bot completes its response
        message_finished = false;
        websocket.send(prompt_term); // Send user message via WebSocket
    });

    // WebSocket message handling (responses from the server)
    websocket.onmessage = function (event) {
        if (event.data === "__message_finished__") {
            // Mark the end of a bot response
            message_finished = true;
        } else {
            // Append the bot response to the ongoing response ID
            const botMessageElement = $("#" + ongoingBotMessageId);
            botMessageElement.html(botMessageElement.html() + event.data);
        }

        // Auto-scroll the chat container to the latest message
        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };
});
