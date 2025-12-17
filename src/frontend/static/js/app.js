const token = localStorage.getItem("access_token");
if (!localStorage.getItem("access_token")) {
    window.location.href = "/";
}

const API_BASE = "http://localhost:8000/api";
let waitingForClarification = false;

const PUBLIC_PAGES = [
    "/",
    "/index.html",
    "/register.html"
];

const current = window.location.pathname;

if (PUBLIC_PAGES.includes(current)) {
    console.log("Public page loaded:", current);
} else {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
    }
}

const messagesDiv = document.getElementById("messages");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

let dataFileInput;
let dataUploadBtn;
let dataUploadStatus;
let dataSourceList;

function getToken() {
    return localStorage.getItem("access_token");
}

async function authorizedFetch(url, options = {}) {
    const token = getToken();
    if (!token) {
        window.location.href = "/login";
        return;
    }

    if (!options.headers) {
        options.headers = {};
    }

    // ONLY add Authorization, do NOT override FormData headers
    options.headers["Authorization"] = `Bearer ${token}`;

    return fetch(url, options);
}




document.addEventListener("click", function (e) {
    const target = e.target.closest("#data-upload-btn");
    if (target) {
        e.preventDefault();
        e.stopPropagation();
        uploadDataFile();
    }
});

function initDataPageListeners() {
    dataFileInput = document.getElementById("data-file-input");
    dataUploadBtn = document.getElementById("data-upload-btn");
    dataUploadStatus = document.getElementById("data-upload-status");
    dataSourceList = document.getElementById("data-source-list");

    const dataPage = document.getElementById("data-page");
    if (dataPage) {
        dataPage.style.pointerEvents = "auto";
        const allElements = dataPage.querySelectorAll("*");
        allElements.forEach(el => {
            el.style.pointerEvents = "auto";
        });
    }

    if (dataUploadBtn) {
        dataUploadBtn.style.pointerEvents = "auto";
        dataUploadBtn.style.cursor = "pointer";
        dataUploadBtn.style.zIndex = "9999";
    }
}
async function loadDataSources() {
    if (!dataSourceList) return;

    dataSourceList.innerHTML = "";

    try {
        const resp = await authorizedFetch(`${API_BASE}/data_sources`);
        if (!resp.ok) {
            dataSourceList.innerHTML = "<div class='empty'>Failed to load sources</div>";
            return;
        }

        const data = await resp.json();
        const sources = data.sources || [];

        if (sources.length === 0) {
            dataSourceList.innerHTML = "<div class='empty'>No data sources</div>";
            return;
        }

        sources.forEach(src => {
            const el = document.createElement("div");
            el.classList.add("data-source-item");

            el.innerHTML = `
                <div class="data-source-info">
                    <div class="data-source-icon">📄</div>
                    <div>
                        <div class="data-source-title">${src.table_name}</div>
                        <div class="data-source-meta">${src.filename || ""}</div>
                    </div>
                </div>

                <div class="data-source-meta">
                    ${src.uploaded_at ? new Date(src.uploaded_at).toLocaleString() : ""}
                </div>
            `;

            dataSourceList.appendChild(el);
        });

    } catch (err) {
        console.error("Failed to load data sources:", err);
        dataSourceList.innerHTML = "<div class='empty'>Error loading sources</div>";
    }
}


const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");

navItems.forEach(item => {
    item.addEventListener("click", () => {
        const pageName = item.getAttribute("data-page");

        navItems.forEach(nav => nav.classList.remove("active"));
        item.classList.add("active");

        pages.forEach(page => page.classList.remove("active"));
        const pageEl = document.getElementById(`${pageName}-page`);
        if (pageEl) {
            pageEl.classList.add("active");
        }

        if (pageName === "chat") {
            setTimeout(() => input.focus(), 0);
        }

        if (pageName === "data") {
            setTimeout(() => {
                initDataPageListeners();
                loadDataSources(); 
            }, 100);
        }
    });
});

const chatPage = document.getElementById("chat-page");

chatPage.addEventListener("click", e => {
    if (e.target.closest("#chat-input") || e.target.closest("#send-btn")) {
        return;
    }
    if (chatPage.classList.contains("active")) {
        input.focus();
    }
});

function showChatEmptyState() {
    messagesDiv.innerHTML = `
        <div class="chat-empty-state">
            <div class="chat-empty-icon-wrapper">
                <svg class="chat-empty-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    <line x1="9" y1="10" x2="15" y2="10"></line>
                    <line x1="9" y1="14" x2="13" y2="14"></line>
                </svg>
            </div>
            <h2 class="chat-empty-title">Start a Conversation</h2>
            <p class="chat-empty-subtitle">
                Ask questions about your data, request analysis, or explore insights.
            </p>
            <div class="chat-suggestions">
                <div class="suggestion-card" data-suggestion="What are the main trends in my data?">
                    <div class="suggestion-icon-wrapper">
                        <svg class="suggestion-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="20" x2="18" y2="10"></line>
                            <line x1="12" y1="20" x2="12" y2="4"></line>
                            <line x1="6" y1="20" x2="6" y2="14"></line>
                        </svg>
                    </div>
                    <div class="suggestion-title">Analyze Trends</div>
                    <div class="suggestion-description">Identify patterns and trends in your dataset</div>
                </div>
                <div class="suggestion-card" data-suggestion="Show me a summary of my data">
                    <div class="suggestion-icon-wrapper">
                        <svg class="suggestion-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                    </div>
                    <div class="suggestion-title">Get Summary</div>
                    <div class="suggestion-description">Quick overview of your data structure</div>
                </div>
                <div class="suggestion-card" data-suggestion="What insights can you provide?">
                    <div class="suggestion-icon-wrapper">
                        <svg class="suggestion-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                            <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                            <line x1="12" y1="22.08" x2="12" y2="12"></line>
                        </svg>
                    </div>
                    <div class="suggestion-title">Generate Insights</div>
                    <div class="suggestion-description">Discover hidden patterns and correlations</div>
                </div>
                <div class="suggestion-card" data-suggestion="Compare different metrics in my data">
                    <div class="suggestion-icon-wrapper">
                        <svg class="suggestion-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                            <polyline points="12 5 19 12 12 19"></polyline>
                        </svg>
                    </div>
                    <div class="suggestion-title">Compare Data</div>
                    <div class="suggestion-description">Side-by-side comparison of metrics</div>
                </div>
            </div>
        </div>
    `;

    messagesDiv.querySelectorAll(".suggestion-card").forEach(card => {
        card.addEventListener("click", () => {
            const suggestion = card.dataset.suggestion;
            input.value = suggestion;
            input.focus();
        });
    });
}

function addMessage(text, sender) {
    const emptyState = messagesDiv.querySelector(".chat-empty-state");
    if (emptyState) {
        emptyState.remove();
    }

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

    if (Array.isArray(data) && data.length > 0 && typeof data[0] === "object") {
        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        const keys = Object.keys(data[0]);

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
    } else if (typeof data === "object") {
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
    if (typeof base64OrBlob === "string") {
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
function renderVisualization(vis) {
    console.log("VIS RECEIVED:", vis);

    // vis from backend is already the spec:
    // { type: "visualization", plot_type: "scatter", x: [...], y: [...], ... }
    const spec = vis;

    const wrapper = document.createElement("div");
    wrapper.classList.add("message", "bot", "viz-message");

    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.textContent = "📊";

    const content = document.createElement("div");
    content.classList.add("message-content");

    const container = document.createElement("div");
    container.classList.add("viz-container");
    container.style.width = "100%";
    container.style.height = "550px";
    container.style.marginTop = "12px";

    content.appendChild(container);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // ---------- DYNAMIC TRACE BUILDING ----------
    let plotData = [];

switch (spec.plot_type) {
    case "scatter":
        plotData = [{
            x: spec.x,
            y: spec.y,
            type: "scatter",
            mode: "markers",
            marker: {
                size: 12,
                color: "#60a5fa",
                line: {
                    color: "#3b82f6",
                    width: 2
                },
                opacity: 0.85
            }
        }];
        break;

    case "line_plot":
        plotData = [{
            x: spec.x,
            y: spec.y,
            type: "scatter",
            mode: "lines",
            line: {
                width: 4,
                color: "#60a5fa",
                shape: "spline",
                smoothing: 0.3
            },
            fill: "tozeroy",
            fillcolor: "rgba(96, 165, 250, 0.1)"
        }];
        break;

    case "bar":
        plotData = [{
            x: spec.x,
            y: spec.y,
            type: "bar",
            marker: {
                color: "#60a5fa",
                line: {
                    color: "#3b82f6",
                    width: 1.5
                },
                opacity: 0.9
            }
        }];
        break;

    case "pie_chart":
        plotData = [{
            labels: spec.labels,
            values: spec.values,
            type: "pie",
            textinfo: "label+percent",
            textposition: "outside",
            automargin: true,
            marker: {
                line: {
                    color: "#0f172a",
                    width: 2
                }
            }
        }];
        break;

    default:
        console.warn("Unknown plot_type, falling back to scatter:", spec.plot_type);
        plotData = [{
            x: spec.x,
            y: spec.y,
            type: "scatter",
            mode: "markers",
            marker: {
                size: 12,
                color: "#60a5fa",
                line: {
                    color: "#3b82f6",
                    width: 2
                },
                opacity: 0.85
            }
        }];
}
    // ---------- LAYOUT (enhanced dark theme with beautiful styling) ----------
    const layout = {
        title: {
            text: spec.title,
            font: { 
                size: 24, 
                color: "#f1f5f9",
                family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                weight: 600
            },
            x: 0.5,
            y: 0.95,
            xanchor: "center",
            yanchor: "top"
        },
        xaxis: {
            title: {
                text: spec.labels?.x,
                font: { 
                    size: 14, 
                    color: "#cbd5e1",
                    family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                },
                standoff: 15
            },
            color: "#94a3b8",
            gridcolor: "rgba(148, 163, 184, 0.15)",
            gridwidth: 1,
            zeroline: false,
            showline: true,
            linecolor: "rgba(148, 163, 184, 0.3)",
            linewidth: 2,
            ticks: "outside",
            tickcolor: "rgba(148, 163, 184, 0.3)",
            tickfont: { 
                size: 12, 
                color: "#94a3b8" 
            }
        },
        yaxis: {
            title: {
                text: spec.labels?.y,
                font: { 
                    size: 14, 
                    color: "#cbd5e1",
                    family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                },
                standoff: 15
            },
            color: "#94a3b8",
            gridcolor: "rgba(148, 163, 184, 0.15)",
            gridwidth: 1,
            zeroline: false,
            showline: true,
            linecolor: "rgba(148, 163, 184, 0.3)",
            linewidth: 2,
            ticks: "outside",
            tickcolor: "rgba(148, 163, 184, 0.3)",
            tickfont: { 
                size: 12, 
                color: "#94a3b8" 
            }
        },
        plot_bgcolor: "#0f172a",
        paper_bgcolor: "rgba(0,0,0,0)",
        margin: { l: 80, r: 50, t: 80, b: 70 },
        hovermode: "closest",
        hoverlabel: {
            bgcolor: "#1e293b",
            bordercolor: "#60a5fa",
            font: { 
                size: 13, 
                color: "#f1f5f9",
                family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            }
        },
        font: {
            family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        }
    };

    // Enhanced config for better interactivity
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    // IMPORTANT: use plotData here, not "data"
    Plotly.newPlot(container, plotData, layout, config);
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
        const resp = await authorizedFetch(`${API_BASE}/object/${objId}`);
        if (!resp.ok) {
            console.error(`Failed to fetch object ${objId}`);
            return null;
        }

        const contentType = resp.headers.get("content-type");

        // Case 1: Image
        if (contentType && contentType.includes("image")) {
            const blob = await resp.blob();
            return { type: "image", data: blob };
        }

        // Case 2: JSON (dataframe OR visualization OR raw object)
        const json = await resp.json();

        // Visualization JSON
        if (json.type === "visualization") {
            return { type: "visualization", data: json };
        }

        // Otherwise raw data table or raw python object
        return { type: "data", data: json };

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
        const endpoint = waitingForClarification ? "/clarify" : "/message";
        const payload = waitingForClarification
            ? { clarification: msg }
            : { message: msg };

        const resp = await authorizedFetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status}`);
        }

        const data = await resp.json();

        removeLoadingIndicator();

        if (data.status === "needs_clarification") {
            waitingForClarification = true;
            addMessage(data.message_to_user, "bot");
            return;
        }

        if (data.status === "aborted") {
            waitingForClarification = false;

            addMessage(
                data.message_to_user ||
                data.result?.final_response ||
                "This task was aborted. Please rephrase your request.",
                "bot"
            );

            return;
        }

        if (data.status === "error") {
            waitingForClarification = false;
            addMessage(
                data.message_to_user ||
                "Something went wrong while executing the task.",
                "bot"
            );
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
                if (node && typeof node === "object") {
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

        if (finalResponse) {
            addMessage(finalResponse, "bot");
        }
        if (objId) {
            const objectResult = await fetchObjectData(objId);

            if (objectResult) {
                if (objectResult.type === "image") {
                    addImage(objectResult.data);

                } else if (objectResult.type === "visualization") {
                    renderVisualization(objectResult.data);

                } else if (objectResult.type === "data") {
                    addDataTable(objectResult.data);
                }
            }
        }

        if (imageBase64) {
            addImage(imageBase64);
        }

        if (
            data.status === "completed" &&
            !finalResponse &&
            !objId &&
            !imageBase64
        ) {
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

async function uploadDataFile() {
    const file = dataFileInput.files[0];
    if (!file) {
        dataUploadStatus.textContent = "❌ Please select a file.";
        return;
    }

    dataUploadBtn.disabled = true;
    dataUploadStatus.textContent = "⏳ Uploading...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const resp = await authorizedFetch(`${API_BASE}/upload_data`, {
            method: "POST",
            body: formData
        });

        if (!resp.ok) {
            const errorText = await resp.text();
            dataUploadStatus.textContent = "❌ Error: " + errorText;
            return;
        }

        const result = await resp.json();

        dataUploadStatus.textContent =
            `✅ Imported '${result.table_name}' — ${result.rows} rows`;

        const el = document.createElement("div");
        el.textContent = `📄 ${result.table_name} — ${result.rows} rows`;
        dataSourceList.appendChild(el);

    } catch (err) {
        dataUploadStatus.textContent = "❌ Error occurred: " + err.message;
    } finally {
        dataUploadBtn.disabled = false;
    }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

window.addEventListener("load", () => {
    input.focus();
    showChatEmptyState();
    initDataPageListeners();
    loadDataSources(); 
});

document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    window.location.href = "/";
});
