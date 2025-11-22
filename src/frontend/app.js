async function send() {
  const message = document.getElementById("msg").value;

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      thread_id: "browser-user",
      message
    })
  });

  const data = await res.json();

  addMessage("You", message);
  addMessage("AI", data.reply);

  if (data.requires_clarification)
      addMessage("System", "(Waiting for your clarification…)");

  document.getElementById("msg").value = "";
}