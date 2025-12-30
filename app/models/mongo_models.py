from app.ext import mongo_db
from datetime import datetime

class ChatHistoryModel:
    @staticmethod
    def get_history(user_id):
        if mongo_db is None:
            return []
        
        record = mongo_db.chat_history.find_one({"user_id": user_id})
        if record:
            return record.get("history", [])
        return []

    @staticmethod
    def save_history(user_id, history):
        if mongo_db is None:
            return

        mongo_db.chat_history.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "history": history,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

class QuizHistoryModel:
    @staticmethod
    def add_quiz_record(user_id, question_data):
        """
        Saves a generated quiz to the user's quiz history.
        question_data: {
            "question": str,
            "choices": list,
            "correct_answer": str,
            "user_answer": str (optional, updated later),
            "is_correct": bool (optional),
            "timestamp": datetime
        }
        """
        if mongo_db is None:
            return

        # We store quizzes in a valid list under 'quiz_history' collection or similar
        # Let's append to a list in a document for the user, similar to chat history
        # OR separate documents. Separate documents might be better for many quizzes.
        # Let's go with separate documents for scalability this time, or list for simplicity.
        # Given "History Tab", list in one doc is easiest for MVP.
        
        # Adding an ID to the quiz question to identify it later when answering
        import uuid
        if "id" not in question_data:
            question_data["id"] = str(uuid.uuid4())
            
        question_data["timestamp"] = datetime.utcnow()
        
        mongo_db.quiz_history.update_one(
            {"user_id": user_id},
            {"$push": {"quizzes": question_data}},
            upsert=True
        )
        return question_data["id"]

    @staticmethod
    def update_quiz_answer(user_id, quiz_id, user_answer, is_correct):
        if mongo_db is None:
            return

        mongo_db.quiz_history.update_one(
            {"user_id": user_id, "quizzes.id": quiz_id},
            {
                "$set": {
                    "quizzes.$.user_answer": user_answer,
                    "quizzes.$.is_correct": is_correct,
                    "quizzes.$.answered_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    def get_user_quizzes(user_id):
        if mongo_db is None:
            return []
        record = mongo_db.quiz_history.find_one({"user_id": user_id})
        if record:
            # Return reversed to show newest first
            return record.get("quizzes", [])[::-1] 
        return []
