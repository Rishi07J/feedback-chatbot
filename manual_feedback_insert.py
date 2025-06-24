from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# MongoDB config
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "feedback_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "feedback")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def insert_feedback(prompt, response, rating="upvote", comment=""):
    doc = {
        "prompt": prompt,
        "response": response,
        "rating": rating,
        "comment": comment
    }
    collection.insert_one(doc)
    print(f"✅ Inserted feedback:\n- Prompt: {prompt}\n- Rating: {rating}\n")

if __name__ == "__main__":
    # ✍️ Manually feed entries here:
    insert_feedback(
        prompt="What is a black hole?",
        response="A black hole is a region in space where gravity is so strong that nothing can escape from it.",
        rating="upvote",
        comment="Very clear and concise!"
    )

    insert_feedback(
        prompt="Explain quantum entanglement",
        response="Quantum entanglement is a phenomenon where particles become linked and the state of one instantly affects the other, regardless of distance.",
        rating="upvote",
        comment="Add analogy next time"
    )

feedback_entries = [
    {
        "prompt": "What is a black hole?",
        "response": "A black hole is a region in space with gravitational pull so strong that not even light can escape it.",
        "rating": "upvote",
        "comment": "Concise and informative."
    },
    {
        "prompt": "Tell me about black holes.",
        "response": "Black holes are dense regions in space-time where gravity is so strong that nothing, not even light, can escape.",
        "rating": "upvote",
        "comment": "Good rephrasing."
    },
    {
        "prompt": "Explain black holes in simple words.",
        "response": "A black hole is like a space vacuum that sucks in everything nearby, even light.",
        "rating": "upvote",
        "comment": "Nice analogy."
    },
    {
        "prompt": "What is quantum entanglement?",
        "response": "Quantum entanglement is a phenomenon where two particles become connected and affect each other instantly, no matter the distance.",
        "rating": "upvote",
        "comment": "Clear explanation."
    },
    {
        "prompt": "Explain entanglement.",
        "response": "Entanglement means two particles share a state such that changing one affects the other, instantly.",
        "rating": "upvote",
        "comment": "Short and useful."
    },
    {
        "prompt": "What is the capital of France?",
        "response": "The capital of France is Paris.",
        "rating": "upvote",
        "comment": "Straight to the point."
    },
    {
        "prompt": "What's France's capital?",
        "response": "Paris is the capital of France.",
        "rating": "upvote",
        "comment": "Correct and concise."
    },
    {
        "prompt": "Summarize Newton's first law.",
        "response": "An object stays at rest or in motion unless acted on by an external force.",
        "rating": "upvote",
        "comment": "Good summary."
    },
    {
        "prompt": "Explain Newton’s laws.",
        "response": "Newton's first law: Objects maintain their state unless a force changes it.",
        "rating": "upvote",
        "comment": "Give shorter"
    },
    {
        "prompt": "Explain relativity.",
        "response": "Einstein's theory says that space and time are relative and linked to gravity and motion.",
        "rating": "upvote",
        "comment": "Simple and effective."
    },
    {
        "prompt": "Tell me about Einstein's relativity.",
        "response": "Relativity is the idea that time and space depend on the observer's speed and gravity.",
        "rating": "downvote",
        "comment": "Make more detailed"
    },
    {
        "prompt": "What is a star?",
        "response": "A star is a huge ball of gas that emits light due to nuclear fusion in its core.",
        "rating": "upvote",
        "comment": "Great!"
    },
    {
        "prompt": "Define galaxy.",
        "response": "A galaxy is a massive system of stars, gas, dust, and dark matter held together by gravity.",
        "rating": "upvote",
        "comment": "Perfect"
    },
    {
        "prompt": "Give an example of AI application.",
        "response": "AI is used in voice assistants like Siri or Alexa.",
        "rating": "upvote",
        "comment": "Mention one more example"
    },
    {
        "prompt": "What is machine learning?",
        "response": "Machine learning is a branch of AI that enables systems to learn from data without being explicitly programmed.",
        "rating": "upvote",
        "comment": "Great!"
    },
    {
        "prompt": "Explain machine learning simply.",
        "response": "It’s a way computers learn patterns from data and make decisions without being told how.",
        "rating": "upvote",
        "comment": "Nice"
    },
]

for entry in feedback_entries:
    insert_feedback(
        prompt=entry["prompt"],
        response=entry["response"],
        rating=entry["rating"],
        comment=entry["comment"]
    )
