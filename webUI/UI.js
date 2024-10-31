
//Big ups to the bbg copilot <3
document.getElementById('user-input').addEventListener('keypress', function(evt) {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    function underlineRandomWord(text) {
        const words = text.split(' ');
        const randomIndex = Math.floor(Math.random() * words.length);
        words[randomIndex] = `<a href="#" style="text-decoration: underline; text-decoration-color: red; color: black;" 
  onclick="openNewWindow('${words[randomIndex]}')">${words[randomIndex]}</a>`;
        return words.join(' ');
    }

    if ( evt.key === "Enter") {
        addMessage('User: ' + underlineRandomWord(message));
        userInput.value = '';
        respondToUser(message);
    }
});

document.getElementById('View Stats').addEventListener('click', function() {
    openVideoWindow();
});

function addMessage(message) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function respondToUser(message) {
    // Simple response logic
    let response = "I didn't understand that.";
    if (message.toLowerCase().includes('hello')) {
        response = "Hello! How can I help you today?";
    } else if (message.toLowerCase().includes('bye')) {
        response = "Goodbye! Have a great day!";
    }
    addMessage('Bot: ' + response);
}

function openNewWindow(word) {
    window.open('', 'NewWindow', 'width=600,height=400').document.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>${word}</title>
        </head>
        <body>
            <h1>${word}</h1>
            <p>This is a new window opened by clicking the underlined word.</p>
        </body>
        </html>
    `);
}

function openVideoWindow() {
    const videoWindow = window.open('', 'Video', 'width=600,height=400');
    videoWindow.document.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Video</title>
        </head>
        <body>
            <video width="100%" controls>
                <source src="videoplayback.mp4" type="video/mp4">
                Your browser does not support the video tag.
                video.volume = 1.0;
                video. Muted = false; 
            </video>
        </body>
        </html>
    `);
}