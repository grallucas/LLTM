
//Big ups to the bbg copilot <3
/*
 low priority - magnify window design (like textbook)
 */

const socketHost = "http://localhost:8001";

const identity = "example.identity";
var sockets;
var sendDisable = false;

function format_msg(text) {
    let words = text.split(' ');

    words.forEach((w,i) => {
        words[i] = `<span onclick=toggleClickableWindow('${w}') class="word">${w}</span>`
    });
    
    return words.join(' ');
}

async function feedback_msg(text){
    await new Promise(resolve => {
        sockets.emit('generate-feedback', text, done => resolve(done))
    });

    const resp = await fetch(`/feedback/${identity}`);
    const data = await resp.json();

    let words = data['words'];
    const feedbacks = data['feedbacks'];

    words.forEach((w,i) => {
        if (i in feedbacks){
            words[i] = `<span onclick="toggleClickableWindow('${w}', '${feedbacks[i].replace(/"/g, "'").replace(/'/g, "\\'")}')" class="word feedback-underline">${w}</span>`;
        }else{
            words[i] = `<span onclick="toggleClickableWindow('${w}')" class="word">${w}</span>`;
        }
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

    if (evt.key === "Enter" && !sendDisable) {
        const feedback = feedback_msg(message)

        addMessage(format_msg(message), true, true);
        const userMsg = $('.user-message').last()[0]

        sockets.emit("chat-interface", message)
        userInput.value = '';

        // await feedback then update 
        feedback.then(data => {
            userMsg.innerHTML = data
        });
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
async function toggleClickableWindow(word, feedback='') {
    // const audio = new Audio(`/tts/word/${word}`);
    // audio.play().then().catch(e => {
    //     console.error('Error playing audio:', e)
    // });

    const clickableWindow = document.getElementById('clickable-window');
    if (clickableWindow.style.display === 'none' || ! clickableWindow.innerHTML.includes(word)) {
        let pronunciation_html = 'Loading... <span class="spinner"></span>';
        let translation_html = 'Loading Definition... <span class="spinner"></span>';
        let wiktionary_url = 'Loading Wiktionary... <span class="spinner"></span>'
        let ctxtranslation_html = '<h3>In-Ctx Translation</h3><span class="spinner"></span>';

        // TODO: in the future this could change elements so that the page responds right away
        // ^ DO this by making placeholder elements with certain ids, then updateData changes those elements, and await AFTER popup.
        // ^ ALSO only do these when translation is opened
        // TODO: also should try to cache somehow (on server)?
        async function updateData(word){
            // await fetch(`/ctxtranslate/${identity}/${word}`).then(r => r.json()).then(data => {
            //     // ctxtranslation_html = '<h3>In-Ctx Translation</h3>';
            //     ctxtranslation_html += `<h4>${data['translated']}</h4>`;
            //     ctxtranslation_html += `<p>Breakdown: <i>${data['breakdown']}</i></p>`;
            //     ctxtranslation_html += `<p>${data['explanation']}</p>`;
            // }).catch(e => console.log(e));

            // await fetch(`/lexicon/${word}`).then(r => r.json()).then(data => {
            //     pronunciation_html = data['ipa'];
            //     wiktionary_url = `<a href="${data['url']}" target="_blank">More Info</a>`;

            //     translation_html = '';
                
            //     for (const [wordType, defs] of Object.entries(data['definitions'])){
            //         translation_html += `<h3>${wordType}</h3>`;
            //         for (const [def, examples] of defs) {
            //             translation_html += `<h4>${def}</h4>`;
            //             if (examples.length > 0){
            //                 translation_html += `<details>`;
            //                 translation_html += `<summary>See examples</summary>`;
            //                 for (const ex of examples) translation_html += `<p style="padding-left: 2em;">• ${ex}</p>`;
            //                 translation_html += `</details>`;
            //             }
            //         }
            //     }
            // }).catch(e => console.log(e));
        }
        await updateData(word);

        const feedback_html = feedback === '' ? '' : `
            <hr class="thick-line">

            <h3 style="color: rgb(53, 217, 255);">Feedback</h3>
            <p>${feedback}<p>
        `

        clickableWindow.innerHTML = `
           <div id="close-button-container">
            <button id="close-clickable-window">Close</button>
           </div>
            <h2>${word}</h2>

            ${feedback_html}

            <hr class="thick-line">

            <p><b>Pronunciation</b></p>

            <p>${pronunciation_html}</p>

            <!-- TODO: IPA character descriptions here -->

            <audio controls>
                <source src="/tts/word/${word}" type="audio/wav">
                Your browser does not support the audio tag.
            </audio>

            <hr class="thick-line">

            <details>
                <summary><b>See Translation & Image.</b> Do this to see the word more often in the future.</summary>

                <hr class="thick-line">

                ${ctxtranslation_html}

                <hr class="thick-line">

                ${translation_html}

                <hr class="thick-line">

                ${wiktionary_url}

                <hr class="thick-line">

                <div style="position:relative; border: 1px solid white; aspect-ratio: 1/1; margin-bottom: 15px;">
                    <div class="spinner" style="position:absolute; top:22%; left:22%; width:50%; height:50%; border-width: 30px;"></div>
                    <img id="word-img" src="/img/word/${word}" style="width:100%; position:absolute;">
                </div>
                <!-- <textarea id="imggen-input" placeholder="Generate an Image..." style="resize: vertical; word-wrap: break-word; white-space: pre-wrap;"></textarea> -->
            </details>

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



