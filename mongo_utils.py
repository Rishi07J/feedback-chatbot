from pymongo import MongoClient, DESCENDING
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI: str = os.getenv("MONGO_URI", "")
DB_NAME: str = os.getenv("DB_NAME", "feedback_db")
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "feedback")

# Initialize MongoDB client and collection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def save_feedback(prompt: str, response: str, rating: str, comment: str) -> None:
    """Save user feedback into MongoDB."""
    try:
        doc = {
            "prompt": prompt,
            "response": str(response),
            "rating": rating,
            "comment": comment
        }
        collection.insert_one(doc)
        print(f"✅ Feedback saved for prompt: {prompt[:50]}...")
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")


def get_top_feedback_examples(limit: int = 5) -> list:
    """Fetch top rated (upvoted) feedback entries with non-empty comments."""
    try:
        examples = list(
            collection.find(
                {"rating": "upvote", "comment": {"$ne": ""}}
            ).sort("_id", DESCENDING).limit(limit)
        )
        print(f"🧠 Using {len(examples)} few-shot examples from feedback.")
        return examples
    except Exception as e:
        print(f"❌ Error fetching top feedback examples: {e}")
        return []


def clear_feedback_memory() -> None:
    """Delete all feedback entries from the collection."""
    try:
        result = collection.delete_many({})
        print(f"🗑️ Cleared training memory. Deleted {result.deleted_count} documents.")
    except Exception as e:
        print(f"❌ Error clearing feedback memory: {e}")


def get_last_conversation_entry() -> dict | None:
    """Get the latest feedback document."""
    try:
        doc = collection.find_one({}, sort=[("_id", DESCENDING)])
        if doc:
            print(f"🔍 Last comment: {doc.get('comment', '')}")
            return {
                "prompt": doc.get("prompt", ""),
                "bot_response": doc.get("response", ""),
                "comment": doc.get("comment", "")
            }
    except Exception as e:
        print(f"❌ Error fetching last conversation entry: {e}")
    return None


def find_upvoted_response(user_prompt: str) -> str | None:
    """Find the most recent upvoted response for a given prompt."""
    try:
        doc = collection.find_one(
            {"prompt": user_prompt, "rating": "upvote"},
            sort=[("_id", DESCENDING)]
        )
        if doc:
            print(f"📦 Found upvoted response for: {user_prompt[:50]}...")
            return doc.get("response")
    except Exception as e:
        print(f"❌ Error finding upvoted response: {e}")
    return None


def find_last_downvoted_comment(user_prompt: str) -> str | None:
    """Get the latest comment for a downvoted response to the prompt."""
    try:
        doc = collection.find_one(
            {"prompt": user_prompt, "rating": "downvote", "comment": {"$ne": ""}},
            sort=[("_id", DESCENDING)]
        )
        if doc:
            print(f"💬 Found downvote comment: {doc['comment']}")
            return doc.get("comment")
    except Exception as e:
        print(f"❌ Error finding downvoted comment: {e}")
    return None


def get_all_upvoted_responses() -> list:
    """Return all learned responses that were upvoted."""
    try:
        docs = collection.find({"rating": "upvote"})
        return [doc["response"] for doc in docs if doc.get("response")]
    except Exception as e:
        print(f"❌ Error retrieving upvoted responses: {e}")
        return []
