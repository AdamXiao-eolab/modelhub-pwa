// ===== AI Chat Assistant — global for all pages =====
(function() {
  "use strict";

  // Build HTML
  var html =
    '<div class="aicb"><button class="aibt" onclick="toggleAIChat()" id="aicbtn">🤖</button></div>' +
    '<div class="aicd" id="aichat">' +
      '<div class="aich">' +
        '<span class="aichl">🤖 ModelHub Assistant</span>' +
        '<button class="aichc" onclick="toggleAIChat()">✕</button>' +
      '</div>' +
      '<div class="aibox" id="aibox">' +
        '<div class="aiu aib"><div class="aic">👋 Hi! I\'m the ModelHub assistant. Ask me anything about our API, pricing, or getting started.</div></div>' +
      '</div>' +
      '<div class="aiinput">' +
        '<input type="text" id="aimsg" placeholder="Ask me anything..." onkeypress="handleAIKeyPress(event)">' +
        '<button onclick="sendAIChat()">➤</button>' +
      '</div>' +
    '</div>';

  // Append to body after DOM ready
  function init() {
    var d = document.createElement("div");
    d.id = "ai-assistant-root";
    d.innerHTML = html;
    document.body.appendChild(d);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

// Expose functions globally (inline onclick handlers)
function toggleAIChat() {
  var el = document.getElementById("aichat");
  if (!el) return;
  el.style.display = el.style.display === "flex" ? "none" : "flex";
  if (el.style.display === "flex") {
    var input = document.getElementById("aimsg");
    if (input) {
      input.focus();
      input.selectionStart = input.selectionEnd = input.value.length;
    }
  }
}

function sendAIChat() {
  
  var input = document.getElementById("aimsg");
  if (!input) return;
  var msg = input.value.trim();
  if (!msg) return;
  var box = document.getElementById("aibox");
  if (!box) return;
  box.innerHTML += '<div class="aiu aiur"><div class="aic">' + esc(msg) + '</div></div>';
  input.value = "";
  box.scrollTop = box.scrollHeight;

  var loading = document.createElement("div");
  loading.className = "aiu aias";
  loading.innerHTML = '<div class="aic"><div class="aith">...</div></div>';
  loading.id = "aiload";
  box.appendChild(loading);
  box.scrollTop = box.scrollHeight;

  fetch("https://modelhub-api.com/v1/assistant/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg })
  }).then(function(r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function(d) {
    var loader = document.getElementById("aiload");
    if (loader) loader.remove();
    var reply = d.reply;
    box.innerHTML += '<div class="aiu aib"><div class="aic aip">' + esc(reply).replace(/\n/g, "<br>") + '</div></div>';
    box.scrollTop = box.scrollHeight;
  }).catch(function(e) {
    var loader = document.getElementById("aiload");
    if (loader) loader.remove();
    box.innerHTML += '<div class="aiu aib"><div class="aic aip" style="color:#ef4444;">Sorry, an error occurred: ' + esc(e.message) + '</div></div>';
    box.scrollTop = box.scrollHeight;
  });
}

function handleAIKeyPress(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendAIChat();
  }
}

function esc(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
