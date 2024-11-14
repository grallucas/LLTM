
//Big ups to the bbg copilot <3
/*
 low priority - magnify window design (like textbook)
 */
document.getElementById('user-input').addEventListener('keypress', function(evt) {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    function highlightRandomWord(text) {
        const words = text.split(' ');
        const randomIndex = Math.floor(Math.random() * words.length);
        words[randomIndex] = `<a href="#" style="background-color: red; color: white; text-decoration: none;" 
  onclick="toggleClickableWindow('${words[randomIndex]}')">${words[randomIndex]}</a>`;
        return words.join(' ');
    }

    if ( evt.key === "Enter") {
        addMessage('You: ' + highlightRandomWord(message), true);
        userInput.value = '';
        respondToUser(message);
    }
});
function addMessage(message, isUser = false) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    if (isUser) {
        messageElement.classList.add('user-message');
    } else {
        messageElement.classList.add('bot-message');
    }
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
function toggleClickableWindow(word) {
    const clickableWindow = document.getElementById('clickable-window');
    if (clickableWindow.style.display === 'none' || clickableWindow.innerHTML.includes(word)) {
        clickableWindow.innerHTML = `
           <div id="close-button-container">
            <button id="close-clickable-window">Close</button>
           </div>
            <h2>${word}</h2>
            <hr class="thick-line">
            <p>This is a new window opened by clicking the highlighted word.</p>
        `;
        clickableWindow.style.display = 'block';
        document.getElementById('close-clickable-window').addEventListener('click', closeClickableWindow);
    } else {
        clickableWindow.style.display = 'none';
    }
}
document.getElementById('view-stats').addEventListener('click', function() {
    toggleStatsWindow();
});
document.getElementById('close-stats').addEventListener('click', function() {
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
    addMessage('ȒȰṦḜ: ' + response);
}
function toggleStatsWindow() {
    const overlay = document.getElementById('overlay');
    if (overlay.style.display === 'none' || overlay.style.display === '') {
        overlay.style.display = 'flex';
    } else {
        overlay.style.display = 'none';
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
