document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chat-box");
  const promptInput = document.getElementById("prompt-input");
  const chatForm = document.getElementById("chat-form");
  const clearMemoryBtn = document.getElementById("clear-memory-btn");

  const feedbackModal = document.getElementById("feedback-modal");
  const feedbackCommentInput = document.getElementById("feedback-comment");
  const submitFeedbackBtn = document.getElementById("submit-feedback-btn");
  const modalCloseBtn = feedbackModal.querySelector(".close");

  let learnedResponses = new Set();

  let currentFeedback = {
    prompt: "",
    response: "",
    rating: "upvote"
  };

  // ✅ Fetch all learned responses from backend
  async function fetchLearnedResponses() {
    try {
      const res = await fetch("/learned_responses");
      if (res.ok) {
        const data = await res.json();
        learnedResponses = new Set(data.responses);
      }
    } catch (err) {
      console.error("Error fetching learned responses:", err);
    }
  }
  fetchLearnedResponses();

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function createFeedbackButtons(prompt, response) {
    const container = document.createElement("div");
    container.className = "feedback-buttons";

    const upvoteBtn = document.createElement("button");
    upvoteBtn.type = "button";
    upvoteBtn.title = "Upvote";
    upvoteBtn.textContent = "👍";
    upvoteBtn.onclick = () => sendFeedback(prompt, response, "upvote", "");

    const downvoteBtn = document.createElement("button");
    downvoteBtn.type = "button";
    downvoteBtn.title = "Downvote";
    downvoteBtn.textContent = "👎";
    downvoteBtn.onclick = () => {
      currentFeedback = { prompt, response, rating: "downvote" };
      openFeedbackModal();
    };

    const commentBtn = document.createElement("button");
    commentBtn.type = "button";
    commentBtn.title = "Add comment";
    commentBtn.textContent = "💬";
    commentBtn.onclick = () => {
      currentFeedback = { prompt, response, rating: "upvote" };
      openFeedbackModal();
    };

    container.appendChild(upvoteBtn);
    container.appendChild(downvoteBtn);
    container.appendChild(commentBtn);

    return container;
  }

  function openFeedbackModal() {
    feedbackCommentInput.value = "";
    feedbackModal.style.display = "flex";
    feedbackCommentInput.focus();
  }

  function closeFeedbackModal() {
    feedbackModal.style.display = "none";
  }

  async function sendFeedback(prompt, response, rating, comment) {
    try {
      await fetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, response, rating, comment }),
      });
      alert("Feedback saved.");
      await fetchLearnedResponses(); // Refresh learned tags
    } catch (error) {
      console.error("Error sending feedback:", error);
      alert("Failed to send feedback.");
    }
  }

  submitFeedbackBtn.addEventListener("click", async () => {
    const comment = feedbackCommentInput.value.trim();
    await sendFeedback(currentFeedback.prompt, currentFeedback.response, currentFeedback.rating, comment);
    closeFeedbackModal();
  });

  modalCloseBtn.addEventListener("click", () => {
    closeFeedbackModal();
  });

  feedbackModal.addEventListener("click", (e) => {
    if (e.target === feedbackModal) {
      closeFeedbackModal();
    }
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    try {
      chatBox.innerHTML += `<div class="chat-entry user"><strong>You:</strong> ${escapeHtml(prompt)}</div>`;

      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();
      const botResponseEscaped = escapeHtml(data.response);

      const botDiv = document.createElement("div");
      botDiv.className = "chat-entry bot";
      botDiv.innerHTML = `<strong>Bot:</strong> ${botResponseEscaped}`;

      // ✅ Add tag based on response source
      const source = data.source || "";
      const tagSpan = document.createElement("span");
      tagSpan.className = "tag-learned";

      if (source === "mongo") {
        tagSpan.title = "Learned from exact upvoted feedback";
        tagSpan.textContent = " 📦 Learned from feedback";
        botDiv.appendChild(tagSpan);
      } else if (source === "faiss") {
        tagSpan.title = "Recalled from similar past memory";
        tagSpan.textContent = " 🧠 Recalled from memory";
        botDiv.appendChild(tagSpan);
      }

      const feedbackButtons = createFeedbackButtons(prompt, data.response);
      botDiv.appendChild(feedbackButtons);

      chatBox.appendChild(botDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
      promptInput.value = "";

    } catch (error) {
      alert("Error sending message. Try again.");
      console.error(error);
    }
  });


  clearMemoryBtn.addEventListener("click", async () => {
    if (!confirm("Clear all training memory? This cannot be undone.")) return;

    try {
      const res = await fetch("/clear-memory", { method: "POST" });
      if (res.ok) {
        alert("Memory cleared.");
        chatBox.innerHTML = "";
        learnedResponses.clear();
        promptInput.value = "";
      } else {
        alert("Failed to clear memory.");
      }
    } catch (error) {
      console.error("Error clearing memory:", error);
      alert("Something went wrong.");
    }
  });
});
