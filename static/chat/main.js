const socketHost = "http://localhost:8002";

const identity = "example.identity";
var sockets;
var sendDisable = true;

function format_msg(text) {
    let words = text.replace(/<br>/g, ' <br> ').split(' ').filter(word => word !== '');;

    words.forEach((w,i) => {
        if (w === '<br>'){
            return;
        }
        words[i] = `<span onclick=toggleClickableWindow('${w}') class="word">${w}</span>`
    });
    
    return words.join(' ');
}

// --- INIT ---

const convMessageElement = document.createElement('div');
convMessageElement.innerHTML = '<button><b>Click</b> to Start the Conversation!</button>';
convMessageElement.classList.add('bot-message');
convMessageElement.classList.add('message');
document.getElementById('messages').appendChild(convMessageElement);

const conv_btn = convMessageElement.querySelector('button');
conv_btn.addEventListener('click', () => {
    sockets.emit("conversation-mode");
    convMessageElement.innerHTML += '<span class="spinner"></span>';
    document.getElementById('messages').removeChild(revMessageElement)
    document.getElementById('messages').removeChild(learnMessageElement)
});

const revMessageElement = document.createElement('div');
revMessageElement.innerHTML = '<button><b>Click</b> to Start the Review!</button>';
revMessageElement.classList.add('bot-message');
revMessageElement.classList.add('message');
document.getElementById('messages').appendChild(revMessageElement);

const rev_btn = revMessageElement.querySelector('button');
rev_btn.addEventListener('click', () => {
    sockets.emit("review-mode");
    revMessageElement.innerHTML += '<span class="spinner"></span>';
    document.getElementById('messages').removeChild(convMessageElement)
    document.getElementById('messages').removeChild(revMessageElement)
    document.getElementById('messages').removeChild(learnMessageElement)
});

const learnMessageElement = document.createElement('div');
learnMessageElement.innerHTML = '<button><b>Click</b> to Start the Learning!</button>';
learnMessageElement.classList.add('bot-message');
learnMessageElement.classList.add('message');
document.getElementById('messages').appendChild(learnMessageElement);

const learn_btn = learnMessageElement.querySelector('button');
learn_btn.addEventListener('click', () => {
    sockets.emit("learn-mode");
    learnMessageElement.innerHTML += '<span class="spinner"></span>';
    document.getElementById('messages').removeChild(convMessageElement)
    document.getElementById('messages').removeChild(revMessageElement)
    document.getElementById('messages').removeChild(learnMessageElement)
});

// --- SOCKET READING ---

$('document').ready(()=>{
    sockets = io(socketHost);
    sockets.emit("identify", identity)
    sockets.on("chat-interface", (token) => {
        if(token == "<START>"){
            convMessageElement.remove(); // TODO: a bit janky to remove this every time
            respondToUser("");
            sendDisable = true;
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
        }else if(token == "<NO-TTS>"){
            sendDisable = false
            $(".bot-message > .spinner").last()[0].remove()
        }else{
            const lastMessage = $(".bot-message").last()[0];
            lastMessage.innerText += token;
        }
    });
    sockets.on('disconnect', ()=>{
        // fetch(`/save-on-disconnect/${identity}`).catch(e => console.log(e));
        confirm("Server disconnected")
        window.location.reload()
    });
    sockets.on('srs-update', (srs_words)=>{
        toggleReviewWindow(srs_words)
    })
});

// --- MESSAGE SENDING ---

document.getElementById('user-input').addEventListener('keypress', function(evt) {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    if (evt.key === "Enter" && !sendDisable) {
        sockets.emit("chat-interface", message)
        const feedback = fetch(`/feedback/${identity}/generate`, {
            method: "POST",
            body: message
        })

        addMessage(format_msg(message), true, true);
        const userMsg = $('.user-message').last()[0]

        userInput.value = '';

        // await feedback then update 
        feedback.then(r => r.json()).then(data => {
            const words = data['words']
            const word_feedbacks = data['word_feedbacks'];
            const feedback_id = data['feedback_id']

            words.forEach((w,i) => {
                if (Object.values(word_feedbacks).includes(i)){
                    words[i] = `<span onclick="toggleClickableWindow('${w}', '${feedback_id},${i}')" class="word feedback-underline">${w}</span>`;
                }else{
                    words[i] = `<span onclick="toggleClickableWindow('${w}')" class="word">${w}</span>`;
                }
            });
            
            userMsg.innerHTML = words.join(' ');
            fetch(`/srs-due-before-tomorrow/${identity}`).then(data => data.text()).then(data => toggleReviewWindow(data));
        }).catch(e => console.log(e));;
    }else if(sendDisable){
        alert('Cannot send a message now')
    }

    const key_map = {
        'a': 'ä',
        'A': 'Ä',
        'o': 'ö',
        'O': 'Ö'
    };

    if (evt.key in key_map && message.charAt(message.length - 1) === ':'){
        evt.preventDefault();
        userInput.value = message.slice(0,-1) + key_map[evt.key];
    }
});

function addMessage(message, isUser=false, add_spinner=false) {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    if(add_spinner){
        messageElement.innerHTML += `<span class="spinner"></span>`
    }
    messageElement.classList.add('message');
    if (isUser) {
        messageElement.classList.add('user-message');
    } else {
        messageElement.classList.add('bot-message');
    }
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// --- REVIEW WINDOW ---

function toggleReviewWindow(words) {
    const window = document.getElementById('review-window');

    // Disable (easy case)
    // if(window.style.display !== 'none'){
    //     window.style.display = 'none';
    //     return
    // } 
    // else if (words.length == 0) {
    //     window.style.display = 'none'
    //     return
    // }
    if (words.length == 0) {
        window.style.display = 'none'
    } else {
        window.replaceChildren()
        window.style.display = ''
        const newWordElement = document.createElement('div');
        newWordElement.innerHTML = '<button><b>Click</b> to add new words</button>';
        const newWordButton = newWordElement.querySelector('button');
        newWordButton.addEventListener('click', () => {
            fetch(`/addwords/${identity}`);
            // update review screen
            srs_due_str = fetch(`/srs-due-before-tomorrow/${identity}`).then(data => data.text()).then(data => toggleReviewWindow(data));
        });
        document.getElementById('review-window').appendChild(newWordElement)
        
        const msgPara = document.createElement('p');
        msgPara.textContent = 'Use or look up each word to check it off!';
        window.appendChild(msgPara);

        const hr = document.createElement('hr');
        hr.classList.add('thick-line');
        window.appendChild(hr);

        const split_words = words.split(" ");
        split_words.forEach(w => {
            const p = document.createElement('p');
            p.className = 'word';
            p.textContent = w;
            p.onclick = () => toggleClickableWindow(w);
            window.appendChild(p);
        });
    }
}

// --- WORD WINDOW ---

function toggleClickableWindow(word, feedback_id='') {
    // const audio = new Audio(`/tts/word/${word}`);
    // audio.play().then().catch(e => {
    //     console.error('Error playing audio:', e)
    // });

    word = word.replace(/"/g, '') // quotes specifically break the url

    const clickableWindow = document.getElementById('clickable-window');
    if (clickableWindow.style.display === 'none' || ! clickableWindow.innerHTML.includes(word)) {
        const init_feedback_html = feedback_id === '' ? '' : `
            <hr class="thick-line">
            <h3 style="color: rgb(53, 217, 255);">Feedback</h3>
            <p id="word-feedback"><span class="spinner"></span><p>
        `

        clickableWindow.innerHTML = `
           <div id="close-button-container">
            <button id="close-clickable-window">Close</button>
           </div>
            <h2 class="center">${word}</h2>

            ${init_feedback_html}

            <hr class="thick-line">

            <p class="center"><b>Pronunciation</b></p>

            <p id="word-pronunciation"><span class="spinner"></span></p>

            <!-- TODO: IPA character descriptions here -->

            <audio controls>
                <source src="/tts/word/${word}" type="audio/wav">
                Your browser does not support the audio tag.
            </audio>

            <hr class="thick-line">

            <details>
                <summary id="word-info-dropdown"><b>See Translation & Image.</b> Do this to see the word more often in the future.</summary>

                <hr class="thick-line">

                <h3 class="center">Contextual Translation</h3>
                <div id="word-translation"><span class="spinner"></span></div>

                <hr class="thick-line">

                <div id="word-definition">Loading Definitions... <span class="spinner"></span></div>

                <hr class="thick-line">

                <div style="position:relative; border: 1px solid white; aspect-ratio: 1/1; margin-bottom: 15px;">
                    <div class="spinner" style="position:absolute; top:22%; left:22%; width:50%; height:50%; border-width: 30px;"></div>
                    <img id="word-img" src="#" style="width:100%; position:absolute;">
                </div>
                <!-- <textarea id="imggen-input" placeholder="Generate an Image..." style="resize: vertical; word-wrap: break-word; white-space: pre-wrap;"></textarea> -->
            </details>
        `;

        clickableWindow.style.display = 'block';
        document.getElementById('close-clickable-window').addEventListener('click', closeClickableWindow);

        if(feedback_id !== ''){
            fetch(`/feedback/${identity}/get/${feedback_id}`).then(r => r.json()).then(data => {
                $('#word-feedback').last()[0].innerText = data['feedback']
            }).catch(e => {
                $('#word-feedback').last()[0].innerText = e;
                console.log(e);
            });
        }

        fetch(`/lexicon/${word}`).then(r => r.json()).then(data => {
            if(Object.keys(data).length === 0){
                $('#word-pronunciation').last()[0].innerText = '';
                $('#word-definition').last()[0].innerHTML = 'Could not find definitions.';
                return;
            }

            $('#word-pronunciation').last()[0].innerText = data['ipa'];

            defs_html = '';
            for (const [wordType, defs] of Object.entries(data['definitions'])){
                defs_html += `<h3 class="center">${wordType}</h3>`;
                for (const [def, examples] of defs) {
                    defs_html += `<h4>${def}</h4>`;
                    if (examples.length > 0){
                        defs_html += `<details>`;
                        defs_html += `<summary>See examples</summary>`;
                        for (const ex of examples) defs_html += `<p style="padding-left: 2em;">• ${ex}</p>`;
                        defs_html += `</details>`;
                    }
                }
            }

            if (data['url']){
                defs_html += `<a href="${data['url']}" target="_blank">More Info</a>`;
            }

            $('#word-definition').last()[0].innerHTML = defs_html;
        }).catch(e => console.log(e));

        let dropped_down = false;

        $('#word-info-dropdown').last()[0].addEventListener('click', () => {
            $('#word-img').last()[0].src = `/img/word/${word}`;
            
            if (dropped_down)
                return;

            fetch(`/ctxtranslate/${identity}/${word}`).then(r => r.json()).then(data => {
                translation_html = '';
                translation_html += `<p class="center" style="font-size:1.5em;">"${data['translated']}"</p>`;
                translation_html += `<p>Breakdown: <i>${data['breakdown']}</i></p>`;
                translation_html += `<p>${data['explanation']}</p>`;
                $('#word-translation').last()[0].innerHTML = translation_html;
            }).catch(e => console.log(e));

            dropped_down = true;
            
            fetch(`/srs/review/${identity}/${word}`).catch(e => console.log(e));
        });
    } else {
        clickableWindow.style.display = 'none';
    }
}

// --- MISC ---

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

document.querySelectorAll('.typer-button').forEach(button => {
    button.addEventListener('click', () => {
        document.querySelector('#user-input').value += button.innerText;
    });
    const key_map = {
        'ä': 'a',
        'Ä': 'A',
        'ö': 'o',
        'Ö': 'O'
    };
    button.title = `TIP: type this via ":${key_map[button.innerText]}"`;
});
