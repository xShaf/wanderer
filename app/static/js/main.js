const BASE_URL = window.location.origin;

let currentQuizId = null;

// Toast Function
function showToast(message, isSuccess = true) {
    const toastEl = document.getElementById('liveToast');
    const toastTitle = document.getElementById('toast-title');
    const toastBody = document.getElementById('toast-body');

    if (isSuccess) {
        toastEl.classList.remove('text-bg-danger');
        toastEl.classList.add('text-bg-success');
        toastTitle.innerText = "Success! ✨";
    } else {
        toastEl.classList.remove('text-bg-success');
        toastEl.classList.add('text-bg-danger');
        toastTitle.innerText = "Attention needed";
    }

    toastBody.innerText = message;

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Update UI
function updateUserDataDisplay(points, trophies) {
    const pointsEl = document.getElementById("user-points");
    const trophiesEl = document.getElementById("user-trophies");

    if (pointsEl && points !== null) pointsEl.textContent = points;
    if (trophiesEl && trophies !== null) trophiesEl.textContent = trophies;
}

function updateChatDisplay(chatHistory) {
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = "";
    if (chatHistory && chatHistory.length > 0) {
        chatHistory.forEach(message => {
            if (message.parts && message.parts.length > 0) {
                const messageText = message.parts[0].text;
                let displayHtml = marked.parse(messageText);
                if (message.role === 'user') {
                    chatBox.innerHTML += `<div class='user bg-primary text-white p-2 px-3 rounded-pill my-2 ms-auto'>${displayHtml}</div>`;
                } else if (message.role === 'model') {
                    chatBox.innerHTML += `<div class='bot bg-info-subtle text-dark p-2 px-3 rounded my-2 me-auto'>${displayHtml}</div>`;
                }
            }
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Chat
async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<div class='user bg-primary text-white p-2 px-3 rounded-pill my-2 ms-auto'>${message}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    input.value = "";
    input.disabled = true;

    try {
        const response = await fetch(`${BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        const data = await response.json();

        const displayHtml = marked.parse(data.response);
        chatBox.innerHTML += `<div class='bot bg-info-subtle text-dark p-2 px-3 rounded my-2 me-auto'>${displayHtml}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        if (data.points !== undefined) updateUserDataDisplay(data.points, null);

    } catch (error) {
        console.error("Chat Error:", error);
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function checkEnter(e) {
    if (e.key === "Enter") sendMessage();
}

// Quiz
async function generateQuiz() {
    const topic = document.getElementById("quiz-topic").value;
    const qContainer = document.getElementById("quiz-container");
    const qText = document.getElementById("quiz-question");
    const qChoices = document.getElementById("quiz-choices");

    if (!topic) {
        showToast("Please enter a topic!", false);
        return;
    }

    // Loading State
    qText.innerText = "Consulting the library...";
    qChoices.innerHTML = "";
    qContainer.style.display = "block";

    try {
        const response = await fetch(`${BASE_URL}/api/quiz`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic })
        });

        const data = await response.json();

        if (data.error) {
            qText.innerText = data.error;
            showToast(data.error, false);
            return;
        }

        currentQuizId = data.quiz_id;
        qText.innerText = data.question;
        qChoices.innerHTML = "";

        data.choices.forEach(choice => {
            const btn = document.createElement("button");
            btn.className = "btn btn-outline-info w-100 mb-2 text-start";
            btn.innerText = choice;
            btn.onclick = () => submitAnswer(choice);
            qChoices.appendChild(btn);
        });

        loadQuizHistory();

    } catch (e) {
        console.error(e);
        qText.innerText = "Error fetching quiz.";
        showToast("Error connecting to server.", false);
    }
}

async function submitAnswer(answer) {
    if (!currentQuizId) return;

    const response = await fetch(`${BASE_URL}/api/quiz_answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quiz_id: currentQuizId, answer: answer })
    });
    const result = await response.json();

    // Toast Notification
    showToast(result.message, result.correct);

    if (result.points !== undefined) updateUserDataDisplay(result.points, result.trophies);

    document.getElementById("quiz-choices").innerHTML = "<p class='text-muted'>Quiz Completed. Check History/Status.</p>";
    currentQuizId = null;
    loadQuizHistory();
}

async function loadQuizHistory() {
    const listEl = document.getElementById("quiz-history-list");
    if (!listEl) return;

    try {
        const response = await fetch(`${BASE_URL}/api/quiz_history`);
        const history = await response.json();

        listEl.innerHTML = "";
        if (history.length === 0) {
            listEl.innerHTML = "<li class='list-group-item bg-dark text-white'>No history yet.</li>";
            return;
        }

        history.forEach(item => {
            const li = document.createElement("li");
            li.className = "list-group-item bg-dark text-white border-secondary";

            const date = new Date(item.timestamp).toLocaleString();
            const status = item.is_correct === true ? '<span class="badge bg-success">Correct</span>' :
                item.is_correct === false ? '<span class="badge bg-danger">Incorrect</span>' :
                    '<span class="badge bg-warning text-dark">Pending</span>';

            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">${date}</small>
                    ${status}
                </div>
                <p class="mb-1 fw-bold">${item.question}</p>
                <p class="mb-0 small text-info">Your Answer: ${item.user_answer || "None"}</p>
            `;
            listEl.appendChild(li);
        });
    } catch (e) { console.error("History Error", e); }
}

async function loadChatHistory() {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    try {
        const response = await fetch(`${BASE_URL}/api/chat_history`);
        const history = await response.json();
        updateChatDisplay(history);
    } catch (e) {
        console.error("Failed to load chat history", e);
    }
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    loadQuizHistory();
});
