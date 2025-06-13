🧠 Feedback-Driven Smart Chatbot

A Flask-based chatbot that continuously improves by learning from user feedback. Built using LangChain, Groq API (LLM), and MongoDB for memory and response optimization.

![image](https://github.com/user-attachments/assets/7ebd0518-6d2d-4ae2-b2aa-d0343f332161)


---

## 🚀 Features

- 💬 Conversational AI powered by `llama3-70b` via Groq API
- 📦 Memory-enabled: stores user name and past prompts
- 🔁 Learns from upvoted responses and reuses them
- 📉 Adjusts future responses based on downvote comments (e.g., "give shorter")
- 💾 MongoDB storage for all feedback
- 🧹 One-click memory clearing
- 🎥 Animated background UI
- 🧠 Few-shot prompt tuning using real feedback

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **LLM**: Groq API (LLaMA 3 70B via LangChain)
- **Database**: MongoDB
- **Prompt Engineering**: Few-shot prompting using upvoted examples

---

## 🧪 How It Works

1. User sends a prompt ➜ Bot checks MongoDB first.
2. If an **upvoted response exists** for that prompt ➜ Returns it directly.
3. If **comment like "give shorter"** is present ➜ Bot adjusts accordingly.
4. If no good match ➜ Falls back to LLM with enhanced prompts.
5. Feedback (👍👎💬) helps the bot learn and improve over time.
