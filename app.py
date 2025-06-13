from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from mongo_utils import (
    save_feedback,
    get_top_feedback_examples,
    clear_feedback_memory,
    find_upvoted_response,
    find_last_downvoted_comment,
)

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")

# LLM setup
llm = ChatGroq(api_key=groq_api_key, model_name="llama3-70b-8192")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_prompt = request.json.get("prompt", "").strip()

    # Retrieve or initialize session memory
    memory = session.get("memory", {})

    # Personalization if user shares name
    if "my name is" in user_prompt.lower():
        name = user_prompt.lower().split("my name is")[-1].strip().split()[0]
        memory["user_name"] = name
        session["memory"] = memory

    memory_info = f"My name is {memory['user_name']}.\n" if "user_name" in memory else ""

    # STEP 1: Try to find a previously upvoted response
    cached_response = find_upvoted_response(user_prompt)
    if cached_response:
        print("✅ Responding from cached upvoted feedback.")
        memory["last_prompt"] = user_prompt
        memory["last_response"] = cached_response
        session["memory"] = memory
        return jsonify({"response": cached_response})

    # STEP 2: Check last downvoted comment (like "give shorter")
    comment = find_last_downvoted_comment(user_prompt)
    if comment:
        print("✂️ Using comment to guide new response:", comment)
        prompt_to_model = f"{comment.strip().capitalize()} version of this:\n{memory.get('last_response', '')}"
        response_text = llm.invoke(prompt_to_model).content
    else:
        # STEP 3: Use few-shot examples to generate fresh response
        examples = get_top_feedback_examples()
        example_prompt = PromptTemplate(
            input_variables=["input", "response"],
            template="User: {input}\nBot: {response}"
        )
        few_shot_prompt = FewShotPromptTemplate(
            examples=[{"input": ex["prompt"], "response": ex["response"]} for ex in examples],
            example_prompt=example_prompt,
            prefix="The following are helpful conversations between a user and an intelligent assistant:",
            suffix="User: {input}\nBot:",
            input_variables=["input"]
        )
        final_prompt = few_shot_prompt.format(input=memory_info + user_prompt)
        response_text = llm.invoke(final_prompt).content

    # Update memory
    memory["last_prompt"] = user_prompt
    memory["last_response"] = response_text
    session["memory"] = memory

    return jsonify({"response": response_text})


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    save_feedback(
        data["prompt"],
        data["response"],
        data["rating"],
        data.get("comment", "")
    )
    return jsonify({"message": "Feedback saved!"})


@app.route("/clear-memory", methods=["POST"])
def clear_memory():
    clear_feedback_memory()
    session.clear()
    return jsonify({"message": "Training memory cleared!"})


@app.route("/learned_responses", methods=["GET"])
def learned_responses():
    from mongo_utils import get_all_upvoted_responses
    return jsonify({"responses": get_all_upvoted_responses()})


if __name__ == "__main__":
    app.run(debug=True)
