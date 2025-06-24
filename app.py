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
    get_all_upvoted_responses,
    find_downvoted_comment_by_prompt,
)
from faiss_utils import (
    search_similar_prompt,
    build_faiss_index,
    initialize_faiss,
    add_to_faiss_index,
    get_all_prompt_vectors,
    get_top_similar_prompts,  # NEW helper to get similar prompts from FAISS
)

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")

# LLM setup
llm = ChatGroq(api_key=groq_api_key, model_name="llama3-70b-8192")

# Initialize FAISS index
initialize_faiss()

@app.route("/")
def index():
    return render_template("index.html")

def find_comment_for_similar_prompt(user_prompt: str) -> tuple[str, str] | None:
    """Find downvoted comment from a prompt that's semantically similar."""
    similar_prompts = get_top_similar_prompts(user_prompt, top_k=3)
    for sim_prompt in similar_prompts:
        comment = find_downvoted_comment_by_prompt(sim_prompt)
        if comment:
            return comment, sim_prompt
    return None

@app.route("/chat", methods=["POST"])
def chat():
    user_prompt = request.json.get("prompt", "").strip()
    memory = session.get("memory", {})

    if "my name is" in user_prompt.lower():
        name = user_prompt.lower().split("my name is")[-1].strip().split()[0]
        memory["user_name"] = name
        session["memory"] = memory

    memory_info = f"My name is {memory['user_name']}.\n" if "user_name" in memory else ""

    # STEP 1: Try exact MongoDB upvote match
    cached_response = find_upvoted_response(user_prompt)
    if cached_response:
        # Check for any downvoted comment from similar prompts
        result = find_comment_for_similar_prompt(user_prompt)
        if result:
            comment, related_prompt = result
            print("✂️ Applying comment from similar prompt:", comment)
            prompt_to_model = f"{comment.strip().capitalize()} version of this:\n{cached_response}"
            response_text = llm.invoke(prompt_to_model).content
        else:
            print("✅ MongoDB: Found exact upvoted response")
            response_text = cached_response

        memory["last_prompt"] = user_prompt
        memory["last_response"] = response_text
        session["memory"] = memory
        return jsonify({"response": response_text})

    # STEP 2: FAISS semantic similarity search
    faiss_result = search_similar_prompt(user_prompt)

    if faiss_result:
        # Check for comment related to similar prompt
        result = find_comment_for_similar_prompt(user_prompt)
        if result:
            comment, related_prompt = result
            print("✂️ Applying comment from similar prompt:", comment)
            prompt_to_model = f"{comment.strip().capitalize()} version of this:\n{faiss_result}"
            response_text = llm.invoke(prompt_to_model).content
        else:
            print("🔍 FAISS: Found similar response via embedding match")
            response_text = faiss_result

        memory["last_prompt"] = user_prompt
        memory["last_response"] = response_text
        session["memory"] = memory
        return jsonify({"response": response_text})

    # STEP 3: Check for comment from exact downvote
    comment = find_last_downvoted_comment(user_prompt)
    if comment:
        print("✂️ Using comment to guide new response:", comment)
        prompt_to_model = f"{comment.strip().capitalize()} version of this:\n{memory.get('last_response', '')}"
        response_text = llm.invoke(prompt_to_model).content
    else:
        # STEP 4: Few-shot generation
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

    memory["last_prompt"] = user_prompt
    memory["last_response"] = response_text
    session["memory"] = memory

    return jsonify({"response": response_text})


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    prompt = data["prompt"]
    response = data["response"]
    rating = data["rating"]
    comment = data.get("comment", "")

    save_feedback(prompt, response, rating, comment)

    # Only add to FAISS if upvoted
    if rating == "upvote":
        add_to_faiss_index(prompt, response)

    return jsonify({"message": "Feedback saved!"})


@app.route("/clear-memory", methods=["POST"])
def clear_memory():
    clear_feedback_memory()
    session.clear()
    return jsonify({"message": "Training memory cleared!"})


@app.route("/learned_responses", methods=["GET"])
def learned_responses():
    return jsonify({"responses": get_all_upvoted_responses()})


@app.route("/vectors", methods=["GET"])
def view_vectors():
    vector_data = get_all_prompt_vectors()
    vector_json = [
        {"prompt": prompt, "vector": vec.tolist()}
        for prompt, vec in vector_data
    ]
    return jsonify(vector_json)


if __name__ == "__main__":
    app.run(debug=True)
