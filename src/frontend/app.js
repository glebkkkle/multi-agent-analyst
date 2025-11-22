const API_BASE = "http://localhost:8000/api";
let threadId = "user-123";
let waitingForClarification = false;

const messagesDiv = document.getElementById("messages");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

function addMessage(text, sender) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", sender);
    
    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.textContent = sender === "user" ? "👤" : "🤖";
    
    const content = document.createElement("div");
    content.classList.add("message-content");
    
    try {
        const parsed = JSON.parse(text);
        content.innerHTML = `<pre>${JSON.stringify(parsed, null, 2)}</pre>`;
    } catch {
        content.textContent = text;
    }
    
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addDataTable(data) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", "bot", "data-message");
    
    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.textContent = "📊";
    
    const content = document.createElement("div");
    content.classList.add("message-content");
    
    if (Array.isArray(data)) {
        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        const keys = Object.keys(data[0] || {});
        
        keys.forEach(key => {
            const th = document.createElement("th");
            th.textContent = key;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        const tbody = document.createElement("tbody");
        data.forEach(row => {
            const tr = document.createElement("tr");
            keys.forEach(key => {
                const td = document.createElement("td");
                td.textContent = row[key];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        content.appendChild(table);
    } else if (typeof data === 'object') {
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(data, null, 2);
        content.appendChild(pre);
    } else {
        content.textContent = String(data);
    }
    
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addImage(base64OrBlob) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", "bot", "image-message");
    
    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.textContent = "📈";
    
    const content = document.createElement("div");
    content.classList.add("message-content");
    
    const img = document.createElement("img");
    if (typeof base64OrBlob === 'string') {
        img.src = "data:image/png;base64," + base64OrBlob;
    } else {
        img.src = URL.createObjectURL(base64OrBlob);
    }
    
    content.appendChild(img);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addLoadingIndicator() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", "bot", "loading");
    wrapper.id = "loading-indicator";
    
    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.textContent = "🤖";
    
    const content = document.createElement("div");
    content.classList.add("message-content");
    content.textContent = "Thinking";
    
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return wrapper;
}

function removeLoadingIndicator() {
    const loading = document.getElementById("loading-indicator");
    if (loading) loading.remove();
}

async function fetchObjectData(objId) {
    try {
        const resp = await fetch(`${API_BASE}/object/${objId}`);
        if (!resp.ok) {
            console.error(`Failed to fetch object ${objId}`);
            return null;
        }
        
        const contentType = resp.headers.get('content-type');
        if (contentType && contentType.includes('image')) {
            const blob = await resp.blob();
            return { type: 'image', data: blob };
        }
        
        const data = await resp.json();
        return { type: 'data', data: data };
    } catch (error) {
        console.error(`Error fetching object ${objId}:`, error);
        return null;
    }
}

async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";
    sendBtn.disabled = true;

    const loadingIndicator = addLoadingIndicator();

    try {
        let endpoint = waitingForClarification ? "/clarify" : "/message";
        let payload = waitingForClarification
            ? { thread_id: threadId, clarification: msg }
            : { thread_id: threadId, message: msg };

        const resp = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status}`);
        }

        const data = await resp.json();
        console.log("FULL RESPONSE:", data);

        removeLoadingIndicator();

        if (data.status === "needs_clarification") {
            waitingForClarification = true;
            addMessage(data.message_to_user, "bot");
            return;
        }

        waitingForClarification = false;

        let finalResponse = null;
        let imageBase64 = null;
        let objId = null;

        if (data.result?.summarizer_node) {
            finalResponse = data.result.summarizer_node.final_response;
            imageBase64 = data.result.summarizer_node.image_base64;
            objId = data.result.summarizer_node.final_obj_id;
        } else if (data.result) {
            finalResponse = data.result.final_response;
            imageBase64 = data.result.image_base64;
            objId = data.result.final_obj_id;
        } else if (data.final_response) {
            finalResponse = data.final_response;
            imageBase64 = data.image_base64;
            objId = data.final_obj_id;
        }

        if (!objId && data.result) {
            const allNodes = Object.values(data.result);
            for (const node of allNodes) {
                if (node && typeof node === 'object') {
                    if (node.object_id) {
                        objId = node.object_id;
                        break;
                    }
                    if (node.final_obj_id) {
                        objId = node.final_obj_id;
                        break;
                    }
                    if (node.structured_response?.object_id) {
                        objId = node.structured_response.object_id;
                        break;
                    }
                }
            }
        }

        console.log("Final Response:", finalResponse);
        console.log("Image Base64:", imageBase64 ? "Present" : "Not present");
        console.log("Object ID:", objId);
        console.log("Full result structure:", data.result);

        if (finalResponse) {
            addMessage(finalResponse, "bot");
        }

        if (objId) {
            console.log("Fetching object data for:", objId);
            const objectResult = await fetchObjectData(objId);
            
            if (objectResult) {
                console.log("Object Result:", objectResult);
                
                if (objectResult.type === 'image') {
                    addImage(objectResult.data);
                } else if (objectResult.type === 'data') {
                    addDataTable(objectResult.data);
                }
            }
        }

        if (imageBase64) {
            addImage(imageBase64);
        }

        if (!finalResponse && !objId && !imageBase64) {
            addMessage("Task completed successfully.", "bot");
        }

    } catch (error) {
        removeLoadingIndicator();
        console.error("Error sending message:", error);
        addMessage("Sorry, there was an error processing your request. Please try again.", "bot");
    } finally {
        sendBtn.disabled = false;
    }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

window.addEventListener("load", () => {
    input.focus();
});