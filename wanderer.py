import re
import os
import json
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import google.generativeai as genai
# Load environment variables
load_dotenv("app.env")

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vision_guide.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Configuration Variables ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Control debug logging: set DEBUG_LOGGING=on in app.env to enable
DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "off").lower() == "on"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. API calls may fail.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

PERSONA = (
    "You are a wise and adventurous Traveler from Teyvat named 'Wanderer Bot'. "
    "You help young adventurers learn about the rich lore of Genshin Impact — including regions, characters, Visions, and legends. "
    "If you don’t know something, say: 'Hmm, even the Archons don’t have all the answers sometimes! Let me think...' "
    "Topics you can explain such as:\n"
    "- Regions: Mondstadt, Liyue, Inazawa, Sumeru, Fontaine, Natlan, etc\n"
    "- Characters: Diluc, Zhongli, Raiden Shogun, Alhaitham, Neuvillette, Mavuika, etc\n"
    "- Factions: Fatui, Harbinger, Church of Favonius, Tenryou Commission, etc\n"
    "- Lore: The Seven, Abyss, Dvalin, Ballad of Boreas, etc\n"
    "Always keep your tone friendly and immersive. Format your responses using Markdown, including headings, bold text, and lists where appropriate for readability."
)


class User(db.Model):
    """
    User model for storing user data including username, points, stickers, and chat history.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    stickers = db.Column(db.Text)
    chat_history = db.Column(db.Text, default="[]")


# Create database tables
with app.app_context():
    db.create_all()


@app.route("/get_users", methods=["GET"])
def get_users():
    """
    Retrieves a list of all registered users.
    """
    users = User.query.all()
    user_list = [{"username": user.username, "points": user.points, "stickers": user.stickers or "None"} for user in
                 users]
    return jsonify(user_list)


@app.route("/select_user", methods=["POST"])
def select_user():
    """
    Handles user login or creation.
    If the user exists, returns their data; otherwise, creates a new user.
    """
    data = request.json
    username = data.get("username", "").strip()

    if DEBUG_LOGGING:
        print(f"DEBUG: /select_user received username: {username}")

    if not username:
        return jsonify({"error": "Username cannot be empty"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, points=0, stickers="", chat_history="[]")
        db.session.add(user)
        db.session.commit()
        response_data = {
            "message": f"Welcome, new Traveler {username}!",
            "username": user.username,
            "points": user.points,
            "stickers": user.stickers or "None",
            "chat_history": user.chat_history
        }
        if DEBUG_LOGGING:
            print(f"DEBUG: /select_user created new user: {response_data}")
        return jsonify(response_data)
    else:
        response_data = {
            "message": f"Welcome back, Traveler {username}!",
            "username": user.username,
            "points": user.points,
            "stickers": user.stickers or "None",
            "chat_history": user.chat_history
        }
        if DEBUG_LOGGING:
            print(f"DEBUG: /select_user loaded existing user: {response_data}")
        return jsonify(response_data)


@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles chatbot conversation. Retrieves chat history, appends new message,
    sends limited history to Gemini model, and saves updated history.
    """
    data = request.json
    user_input = data.get("message", "")
    username = data.get("username", "").strip()

    if DEBUG_LOGGING:
        print(f"DEBUG: /chat received input: '{user_input}' from user: '{username}'")

    if not username:
        return jsonify({"error": "Username not provided for chat."}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found. Please select or create a user first."}), 404

    chat_history_list = json.loads(user.chat_history)
    chat_history_list.append({"role": "user", "parts": [{"text": user_input}]})

    MAX_CONVERSATION_MESSAGES = 10  # 5 user inputs + 5 bot responses (5 complete turns)

    # Prepare contents for the model including persona and limited chat history
    contents_for_model = [{"role": "user", "parts": [{"text": PERSONA}]}]
    effective_chat_history_for_model = chat_history_list[-(MAX_CONVERSATION_MESSAGES - 1):]
    contents_for_model.extend(effective_chat_history_for_model)

    bot_response = "Oops, I couldn't reach Teyvat right now. Try again later!"

    if DEBUG_LOGGING:
        print(f"DEBUG: Contents sent to Gemini: {contents_for_model}")

    try:
        response = model.generate_content(
            contents=contents_for_model,
            generation_config=genai.GenerationConfig(
                temperature=0.0
            )
        )

        if response.candidates and len(response.candidates) > 0 and \
                response.candidates[0].content and response.candidates[0].content.parts and \
                len(response.candidates[0].content.parts) > 0:
            bot_response = response.candidates[0].content.parts[0].text.strip()
        else:
            print(f"Gemini API chat response structure unexpected: {response.text}")

    except Exception as e:
        print(f"Error calling Gemini API for chat: {e}")
        if DEBUG_LOGGING:
            print(f"DEBUG: Gemini API error: {e}")

    chat_history_list.append({"role": "model", "parts": [{"text": bot_response}]})

    # Trim chat history for storage
    if len(chat_history_list) > MAX_CONVERSATION_MESSAGES:
        chat_history_list = chat_history_list[-MAX_CONVERSATION_MESSAGES:]

    user.chat_history = json.dumps(chat_history_list)
    user.points += 500
    db.session.commit()

    response_data = {
        "response": bot_response,
        "points": user.points,
        "stickers": user.stickers or "None",
        "chat_history": user.chat_history
    }
    if DEBUG_LOGGING:
        print(f"DEBUG: /chat sending response: {response_data}")
    return jsonify(response_data)


def normalize_answer_text(text):
    """
    Normalizes text for quiz answer comparison (removes formatting, converts to lowercase).
    """
    normalized_text = text.replace('**', '').replace('"', '').replace("'", '').strip()
    normalized_text = normalized_text.lower()
    normalized_text = re.sub(r"^[a-d1-4]\)\s*|^\*\s*|^-+\s*", "", normalized_text).strip()
    normalized_text = re.sub(r'[^a-z0-9\s-]', '', normalized_text)
    normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()
    return normalized_text


@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    """
    Generates a multiple-choice quiz question based on a given topic using the Gemini model.
    """
    data = request.json
    topic = data.get("topic", "general lore")

    if DEBUG_LOGGING:
        print(f"DEBUG: /generate_quiz received topic: {topic}")

    prompt = (
        f"Create a fun multiple-choice quiz question themed around Genshin Impact for young adventurers learning lore. "
        f"The topic is '{topic}'. Make it relevant to Teyvat lore and include 4 choices labeled A), B), C), D). "
        f"The question should start with '**Question:**'. Each choice should start with '**A)**', '**B)**', etc. "
        f"Indicate the correct answer clearly at the end with the exact prefix '**Correct Answer: ' followed by the choice text."
    )

    quiz_content = ""

    try:
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            generation_config=genai.GenerationConfig(
                temperature=0.0
            )
        )

        if response.candidates and len(response.candidates) > 0 and \
                response.candidates[0].content and response.candidates[0].content.parts and \
                len(response.candidates[0].content.parts) > 0:
            quiz_content = response.candidates[0].content.parts[0].text.strip()
            if DEBUG_LOGGING:
                print(f"DEBUG: Raw LLM Quiz Content: {quiz_content}")
        else:
            print(f"Gemini API quiz response structure unexpected: {response.text}")
            return jsonify({"error": "Failed to generate quiz: Unexpected AI response format."}), 500

    except Exception as e:
        print(f"Error calling Gemini API for quiz: {e}")
        if DEBUG_LOGGING:
            print(f"DEBUG: Gemini API error for quiz: {e}")
        return jsonify({"error": f"Failed to fetch quiz from AI model: {e}"}), 500

    question = ""
    choices_for_display = []
    correct_answer_normalized = ""

    lines = quiz_content.split("\n")

    found_question = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not found_question and line.lower().startswith('**question:'):
            question_match = re.search(r'\*\*Question:\*\*\s*(.*)', line, re.IGNORECASE)
            if question_match:
                question = question_match.group(1).strip().replace('**', '').strip()
                found_question = True
            continue

        choice_match = re.search(r'\*\*([A-D])\)\*\*\s*(.*)', line, re.IGNORECASE)
        if choice_match:
            label = choice_match.group(1)
            content = choice_match.group(2).strip()
            choices_for_display.append(f"{label}) {content.replace('**', '').strip()}")
            continue

        if line.lower().startswith('**correct answer:') or line.lower().startswith('correct answer:'):
            correct_answer_match = re.search(r'Correct Answer:\s*(.*)', line, re.IGNORECASE)
            if correct_answer_match:
                raw_correct_answer_text = correct_answer_match.group(1).strip()
                correct_answer_normalized = normalize_answer_text(raw_correct_answer_text)
            break

    if not question or not correct_answer_normalized or len(choices_for_display) < 2:
        if DEBUG_LOGGING:
            print(
                f"DEBUG: Quiz generation failed parsing. Question: '{question}', Correct Answer: '{correct_answer_normalized}', Choices: {choices_for_display}")
        return jsonify({
            "error": "Failed to generate a valid quiz question. AI response format was unexpected. Please try again with a different topic."}), 400

    response_data = {
        "question": question,
        "choices": choices_for_display[:4],
        "correct_answer": correct_answer_normalized
    }
    if DEBUG_LOGGING:
        print(f"DEBUG: /generate_quiz sending response: {response_data}")
    return jsonify(response_data)


@app.route("/quiz_answer", methods=["POST"])
def quiz_answer():
    """
    Checks the user's quiz answer against the correct answer and updates user points/stickers.
    """
    data = request.json
    user_answer_raw = data.get("answer", "").strip()
    correct_answer_raw = data.get("correct_answer", "").strip()
    username = data.get("username", "").strip()

    if DEBUG_LOGGING:
        print(
            f"DEBUG: /quiz_answer received user: '{username}', answer: '{user_answer_raw}', correct: '{correct_answer_raw}'")

    if not username:
        return jsonify({"error": "Username not provided for quiz answer."}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found. Please select or create a user first."}), 404

    user_answer_normalized = normalize_answer_text(user_answer_raw)
    correct_answer_normalized = normalize_answer_text(correct_answer_raw)

    if DEBUG_LOGGING:
        print(f"DEBUG: Normalized User Answer: '{user_answer_normalized}'")
        print(f"DEBUG: Normalized Correct Answer: '{correct_answer_normalized}'")

    if user_answer_normalized == correct_answer_normalized:
        stickers = user.stickers.split(',') if user.stickers else []
        stickers.append("paimon_4.png")
        user.stickers = ','.join(stickers)
        db.session.commit()
        response_data = {
            "message": "Correct! You've earned a Paimon Orb!",
            "points": user.points,
            "stickers": user.stickers
        }
        if DEBUG_LOGGING:
            print(f"DEBUG: /quiz_answer correct. Response: {response_data}")
        return jsonify(response_data)
    else:
        response_data = {
            "message": "Oops, that's not correct. Try again!",
            "points": user.points,
            "stickers": user.stickers
        }
        if DEBUG_LOGGING:
            print(f"DEBUG: /quiz_answer incorrect. Response: {response_data}")
        return jsonify(response_data)


@app.route("/")
def home():
    """
    Renders the main application HTML page.
    """
    return render_template("index_wanderer.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5000', debug=True)

