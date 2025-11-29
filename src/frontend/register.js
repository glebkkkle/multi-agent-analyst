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
        const res = await fetch("http://localhost:8000/register_raw", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            showError(data.detail || "Registration failed.");
            return;
        }

        localStorage.setItem("user", JSON.stringify(data));

        btnText.innerHTML = '✓ Success!';
        await new Promise(r => setTimeout(r, 600));

        window.location.href = "/frontend/app.html";

    } catch (err) {
        showError("Server error.");
    } finally {
        registerBtn.disabled = false;
        btnText.innerHTML = 'Create account';
    }
}

function showError(msg) {
    const errorDiv = document.getElementById("error");
    errorDiv.innerText = msg;
    errorDiv.classList.add("show");
}

// Allow Enter key to submit
document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                registerUser();
            }
        });
    });
});
