async function registerUser() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorDiv = document.getElementById("error");
    const registerBtn = document.getElementById("registerBtn");
    const btnText = document.getElementById("btnText");
    
    errorDiv.classList.remove("show");
    errorDiv.innerText = "";
    
    if (!email || !password) {
        showError("Please fill out all fields.");
        return;
    }
    
    btnText.innerHTML = '<span class="loading-spinner"></span>Creating...';
    registerBtn.disabled = true;
    
    try {
        const res = await fetch("/api/register_raw", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        let data;
        try {
            data = await res.json();
        } catch {
            data = {};
        }
        
        if (!res.ok) {
            const message =
                (data && typeof data === "object" && data.detail) ||
                (typeof data === "string" && data) ||
                "Registration failed.";
            showError(message);
            return;
        }
        
        localStorage.setItem("access_token", data.access_token);
        
        btnText.innerHTML = "✓ Success!";
        await new Promise(r => setTimeout(r, 600));
        window.location.href = "/app";
    } catch (err) {
        showError("Server error.");
    } finally {
        registerBtn.disabled = false;
        btnText.innerHTML = "Create account";
    }
}

function showError(msg) {
    const errorDiv = document.getElementById("error");
    const container = document.querySelector(".register-container");
    errorDiv.innerText = msg;
    errorDiv.classList.add("show");
    if (container) {
        container.classList.add("shake");
        setTimeout(() => container.classList.remove("shake"), 500);
    }
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("email").focus();
});