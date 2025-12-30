from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.ext import db
from app.services.gemini_service import gemini_service
from app.models.mongo_models import ChatHistoryModel, QuizHistoryModel
import json

main_bp = Blueprint('main', __name__)

PERSONA = (
    "You are a wise and adventurous Traveler from Teyvat named 'Wanderer Bot'. "
    "You help young adventurers learn about the rich lore of Genshin Impact. "
    "Keep your tone friendly and immersive."
)

@main_bp.route('/')
def index():
    return render_template('landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_input = data.get("message", "")
    
    # Get History from Mongo
    history = ChatHistoryModel.get_history(current_user.id)
    
    # Generate Response
    response_text = gemini_service.generate_response(history, user_input, PERSONA)
    
    # Update History (Append new turn)
    history.append({"role": "user", "parts": [{"text": user_input}]})
    history.append({"role": "model", "parts": [{"text": response_text}]})
    
    # Save to Mongo
    ChatHistoryModel.save_history(current_user.id, history)
    
    # Update Points (Gamification)
    current_user.points += 500
    db.session.commit()
    
    return jsonify({
        "response": response_text,
        "points": current_user.points
    })

@main_bp.route('/api/chat_history', methods=['GET'])
@login_required
def get_chat_history():
    history = ChatHistoryModel.get_history(current_user.id)
    return jsonify(history)

@main_bp.route('/api/quiz', methods=['POST'])
@login_required
def quiz():
    data = request.json
    topic = data.get("topic", "general lore")
    
    quiz_data = gemini_service.generate_quiz(topic)
    
    if not quiz_data or not quiz_data.get('question'):
        return jsonify({"error": "Failed to generate quiz. Try another topic."}), 500
    
    # Save Generated Quiz to Mongo History
    quiz_id = QuizHistoryModel.add_quiz_record(current_user.id, quiz_data)
    
    return jsonify({
        "quiz_id": quiz_id,
        "question": quiz_data['question'],
        "choices": quiz_data['choices']
    })

@main_bp.route('/api/quiz_answer', methods=['POST'])
@login_required
def quiz_answer():
    data = request.json
    quiz_id = data.get("quiz_id")
    user_answer = data.get("answer") # The full string e.g. "B) The Weaver..."
    
    # We need to verify correctness. 
    # Option 1: Store correctness in backend session?
    # Option 2: Retrive from Mongo.
    
    user_history = QuizHistoryModel.get_user_quizzes(current_user.id)
    # Find the quiz
    target_quiz = next((q for q in user_history if q.get('id') == quiz_id), None)
    
    if not target_quiz:
        return jsonify({"message": "Quiz session expired or not found.", "correct": False})
    
    correct_answer = target_quiz.get('correct_answer', '')
    
    # Simple normalization check
    # e.g. check if "B)" is in both, or exact match
    # Let's strip ** and space
    u_norm = user_answer.replace('*', '').strip().lower()
    c_norm = correct_answer.replace('*', '').strip().lower()
    
    # Improved check: Check if the ANSWER LETTER matches
    u_letter = u_norm.split(')')[0] if ')' in u_norm else u_norm
    c_letter = c_norm.split(')')[0] if ')' in c_norm else c_norm
    
    is_correct = (u_letter == c_letter)
    
    # Update Mongo
    QuizHistoryModel.update_quiz_answer(current_user.id, quiz_id, user_answer, is_correct)
    
    if is_correct:
        current_user.points += 1000
        current_user.correct_quizzes += 1
        db.session.commit()
        return jsonify({
            "message": "Correct! +1000 Points", 
            "points": current_user.points, 
            "trophies": current_user.correct_quizzes,
            "correct": True
        })
    
    return jsonify({
        "message": f"Incorrect! The answer was {correct_answer}", 
        "points": current_user.points, 
        "trophies": current_user.correct_quizzes,
        "correct": False
    })

@main_bp.route('/api/quiz_history', methods=['GET'])
@login_required
def get_quiz_history():
    history = QuizHistoryModel.get_user_quizzes(current_user.id)
    return jsonify(history)
