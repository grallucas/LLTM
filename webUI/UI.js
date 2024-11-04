
//Big ups to the bbg copilot <3
//fix g bug
document.getElementById('user-input').addEventListener('keypress', function(evt) {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    function underlineRandomWord(text) {
        const words = text.split(' ');
        const randomIndex = Math.floor(Math.random() * words.length);
        words[randomIndex] = `<a href="#" style="text-decoration: underline; text-decoration-color: red; color: black;" 
  onclick="openClickableWindow('${words[randomIndex]}')">${words[randomIndex]}</a>`;
        return words.join(' ');
    }

    if ( evt.key === "Enter") {
        addMessage('User: ' + underlineRandomWord(message));
        userInput.value = '';
        respondToUser(message);
    }
});
function addMessage(message) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

document.getElementById('view-stats').addEventListener('click', function() {
    toggleStatsWindow();
});

document.getElementById('close-clickable-window').addEventListener('click', function() {
    closeClickableWindow();
});
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
function toggleStatsWindow() {
    const statsWindow = document.getElementById('stats-window');
    if (statsWindow.style.display === 'none') {
        statsWindow.style.display = 'block';
    } else {
        statsWindow.style.display = 'none';
    }
}

// Re-attach the event listener for the close button
document.getElementById('close-clickable-window').addEventListener('click', function() {
    closeClickableWindow();
});

function closeClickableWindow() {
    const clickableWindow = document.getElementById('clickable-window');
    clickableWindow.style.display = 'none';
}

function openClickableWindow(word) {
    const clickableWindow = document.getElementById('clickable-window');
    clickableWindow.innerHTML = `
        <button id="close-clickable-window">Close</button>
        <h2>${word}</h2>
        <p>This is a new window opened by clicking the underlined word.</p>
    `;
    clickableWindow.style.display = 'block';
}



