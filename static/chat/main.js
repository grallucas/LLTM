
//Big ups to the bbg copilot <3
/*
 low priority - magnify window design (like textbook)
 */

const socketHost = "http://localhost:8001";

const identity = "example.identity@msoe.edu";
var sockets;
var sendDisable = false;

function format_msg(text) {
    let words = text.split(' ');

    const randomIndex = Math.floor(Math.random() * words.length);

    words.forEach((w,i) => {
        words[i] = `<span onclick=toggleClickableWindow('${w}') class="word ${i == randomIndex ? "feedback-underline" : ""}">${w}</span>`
    });
    
    return words.join(' ');
}

$('document').ready(()=>{
    sockets = io(socketHost);
    sockets.emit("identify", identity)
    sockets.on("chat-interface", (token) => {
        if(token == "<START>"){
            respondToUser("")
            sendDisable = true
        }else if(token == "<END>"){
            last_msg = $(".bot-message").last()[0]
            last_msg.innerHTML = format_msg(last_msg.innerHTML) + '<span class="spinner"></span>'
        }else if(token == "<TTS>"){
            const audio = new Audio(`/tts/${identity}/latest/${new Date().getTime()}`);
            audio.play().then(() => {
                // console.log('Audio is playing');
            }).catch(error => {
                console.error('Error playing audio:', error);
            });

            sendDisable = false
            $(".bot-message > .spinner").last()[0].remove()
        }else{
            $(".bot-message").last()[0].innerText += token
        }
    });
    sockets.on('disconnect', ()=>{
        confirm("Server disconnected")
        window.location.reload()
    })
});

document.getElementById('user-input').addEventListener('keypress', function(evt) {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    if ( evt.key === "Enter" && !sendDisable) {
        addMessage(format_msg(message), true);
        sockets.emit("chat-interface", message)
        userInput.value = '';
        //respondToUser(message);
    }
});
function addMessage(message, isUser = false) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    messageElement.classList.add('message');
    if (isUser) {
        messageElement.classList.add('user-message');
    } else {
        messageElement.classList.add('bot-message');
    }
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
function toggleClickableWindow(word) {
    // const audio = new Audio(`/tts/word/${word}`);
    // audio.play().then().catch(e => {
    //     console.error('Error playing audio:', e)
    // });

    const clickableWindow = document.getElementById('clickable-window');
    const wordParts = word.split('').join(' ');
    const pronunciation = word.split('').join('-');
    if (clickableWindow.style.display === 'none' || ! clickableWindow.innerHTML.includes(word)) {
        clickableWindow.innerHTML = `
           <div id="close-button-container">
            <button id="close-clickable-window">Close</button>
           </div>
            <h2>${word}</h2>

            <hr class="thick-line">

            <audio controls>
                <source src="/tts/word/${word}" type="audio/wav">
                Your browser does not support the audio tag.
            </audio>

            <hr class="thick-line">

            <details>
                <summary style="cursor: pointer"><b>See translation and image. This will make you see the word more often.</b></summary>

                <hr class="thick-line">

                <p><b>Translation:</b> blah blah</p>

                <hr class="thick-line">

                <div style="position:relative; border: 1px solid white; aspect-ratio: 1/1; margin-bottom: 15px;">
                    <div class="spinner" style="position:absolute; top:22%; left:22%; width:50%; height:50%; border-width: 30px;"></div>
                    <img id="word-img" src="/img/word/${word}" style="width:100%; position:absolute;">
                </div>
                <textarea id="imggen-input" placeholder="Generate an Image..." style="resize: vertical; word-wrap: break-word; white-space: pre-wrap;"></textarea>                
            </details>

            <hr class="thick-line">

            <p>Could be a Comment From Rose such as "Need More Help?, Try This"</p>
            <hr class="thick-line">
            <p><strong>Word broken down into parts:</strong>${wordParts}</p>
            <hr class="thick-line">
            <p><strong>Pronunciation breakdown:</strong> ${pronunciation}</p>
            <hr class="thick-line">
            <p>future links for more in depth information on language</p>
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
    addMessage(message);
}
function toggleStatsWindow() {
    const overlay = document.getElementById('overlay');
    if (overlay.style.display === 'none' || overlay.style.display === '') {
        overlay.style.display = 'flex';
        $('#stats').on("load", function () {
            $(this).height($(this).contents().height());
            $(this).width($(this).contents().width());
        });
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



