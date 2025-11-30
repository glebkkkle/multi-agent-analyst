async function login() {
    console.log("LOGIN JS EXECUTED");
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorDiv = document.getElementById("error");
    const loginBtn = document.getElementById("loginBtn");
    const btnText = document.getElementById("btnText");

    errorDiv.classList.remove("show", "shake");
    errorDiv.innerText = "";

    if (!email || !password) {
        showError("Please enter both email and password.");
        return;
    }

    loginBtn.disabled = true;
    btnText.innerHTML = '<span class="loading-spinner"></span>Signing in...';

    try {
        const res = await fetch("http://localhost:8000/login_raw", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            showError(data.detail || "Invalid login credentials.");
            return;
        }

        // -----------------------
        // ⭐ IMPORTANT FIX ⭐
        // Save JWT token
        // -----------------------
        localStorage.setItem("access_token", data.access_token);

        btnText.innerHTML = '✓ Success!';
        await new Promise(resolve => setTimeout(resolve, 500));

        // Redirect to secured app
        window.location.href = "/app";

    } catch (err) {
        showError("Server error. Try again later.");
        console.error(err);
    } finally {
        loginBtn.disabled = false;
        btnText.innerHTML = 'Sign in';
    }
}

function showError(message) {
    const errorDiv = document.getElementById("error");
    const container = document.querySelector(".login-container");
    errorDiv.innerText = message;
    errorDiv.classList.add("show");
    container.classList.add("shake");
    setTimeout(() => { container.classList.remove("shake"); }, 500);
}

// Input effects
document.querySelectorAll("input").forEach(input => {
    input.addEventListener("focus", () => input.parentElement.style.transform = "scale(1.01)");
    input.addEventListener("blur", () => input.parentElement.style.transform = "scale(1)");
});

// Press Enter to login
document.getElementById("password")
    .addEventListener("keypress", e => {
        if (e.key === "Enter") login();
    });
