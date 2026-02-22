# app.py

from flask import Flask, render_template, session, request, redirect, url_for, render_template_string, \
    jsonify  # Flask core imports for web app, session, and request handling
from web_app.utils.data_loader import DataLoader           # Import DataLoader to fetch technology and exam data
from web_app.config.config_loader import config            # Import global config (not used directly here, but may be used elsewhere)
from flask_session import Session                          # Flask-Session for server-side session management
from web_app.utils.exam_manager import ExamManager        # Import the global ExamManager instance for exam logic
from web_app.logging_config.logger import logger, inject_logger, get_context_logger  # Import logging utilities
from uuid import uuid4
from datetime import datetime, timedelta
import time
from pydantic import BaseModel
from web_app.utils.groq_ai_loader import generate_groq_response
# Load environment variables (create a .env file with GROQ_API_KEY=your_key_here)
from dotenv import load_dotenv
import json


load_dotenv()


app = Flask(__name__)                                     # Create Flask app instance
app.secret_key = "your-secret-key"                        # Set secret key for session security
app.config['SESSION_TYPE'] = 'filesystem'                 # Use filesystem for server-side session storage
app.config['SESSION_PERMANENT'] = False                   # Sessions are not permanent (expire on browser close)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # # Add session timeout configuration # 2 hour timeout
Session(app)                                              # Initialize Flask-Session extension
from web_app.admin_routes import admin

# Register admin blueprint
app.register_blueprint(admin)

# --- Initialize the Data Loader ---
# Create a single, reusable instance of our DataLoader.
# We point it to our 'data' directory.
data_loader = DataLoader()                                # Instantiate DataLoader for use in routes

# Create an instance to access logger
logger.info("Application Started")                        # Log application startup

# Simple in-memory cache of live exam sessions (exam_id -> ExamManager instance)
_EXAMS = {}

# Define a Pydantic model for the request body (optional but good practice)
class PromptRequest(BaseModel):
    prompt: str

# Add session cleanup function
def _clean_inactive_sessions():
    global _EXAMS
    current_time = time.time()
    timeout = 30 * 60  # 30 minutes timeout (adjust as needed)
    to_remove = []
    for exam_id, manager in _EXAMS.items():
        if current_time - manager.last_activity > timeout:
            to_remove.append(exam_id)
    for exam_id in to_remove:
        del _EXAMS[exam_id]

def _get_manager() -> ExamManager:
    """
    Fetch the current user's ExamManager from our memory cache using session['exam_id'].
    Returns None if no valid session is found.
    """
    _clean_inactive_sessions()  # Clean inactive sessions on each call
    exam_id = session.get("exam_id")              # Get exam_id from Flask session
    if not exam_id or exam_id not in _EXAMS:      # If not found or expired, return None
        return None
    return _EXAMS[exam_id]                        # Return the ExamManager instance for this session
# New Code -- Start
@app.route('/manage-tech')
def manage_tech():
    technologies = data_loader.get_technologies()  # Fetch list of available technologies
    # return render_template('technologies-copy.html', technologies=technologies)  # Render technologies list
    return render_template('Manage-Technologies.html', technologies=technologies)
@app.route('/admin-panel')
def admin_panel():
    return render_template('Admin-Panel.html')



@app.route('/user-prompt')
def get_user_prompt():
    logger.info("SkillCertify AI Question Generator UI")                    # Log home page access
    return render_template('AI-Question-Generator.html')                  # Render the homepage template

@app.route('/question_set', methods=["POST"])
def get_question_set():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')
        if not user_prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Check if this is a large request (more than 20 questions)
        is_large_request = any(word in user_prompt for word in ["40","45","50","55","60", "forty", "fifty", "large", "big", "extensive"])

        # Generate response using Groq
        result = generate_groq_response(user_prompt,is_large_request)
        return jsonify(result)
    except Exception as e:
        # Handle any other unexpected errors (e.g., API errors, network issues)
        print(f"An error occurred: {e}")
        return "Error", 404




# New Code -- End
@app.route('/')
def home():
    logger.info("Application Started")                    # Log home page access
    return render_template('index.html')                  # Render the homepage template

@app.route('/technologies')
@inject_logger                                            # Inject logger into request context for this route
def get_technologies():
    logger.info("Technologies endpoint called")           # Log endpoint call
    technologies = data_loader.get_technologies()         # Fetch list of available technologies
    # return render_template('technologies-copy.html', technologies=technologies)  # Render technologies list
    return render_template('technologies.html', technologies=technologies)  # Render technologies list

@app.route('/exam_sets/<string:tech_id>')
def exam_sets(tech_id):
    # Find the technology by ID from the exam manager's data loader
    technology = next((t for t in data_loader.get_technologies() if t['id'] == tech_id), None)
    if not technology:
        return "Technology not found", 404                # Return 404 if technology not found
    exam_catalog = data_loader.get_exam_catalog_by_technology_id(tech_id)  # Fetch exam sets for this technology
    if not exam_catalog:
        return "Exam Sets not found", 404                 # Return 404 if no exam sets found
    return render_template('exam_set.html', tech_id=tech_id, exam_catalog=exam_catalog)  # Render exam sets page

@app.route('/exam-confirm/<string:tech_id>/<string:set_id>/<string:name>')
def confirm(tech_id, set_id, name):
    data = data_loader.get_exam_set_by_id(tech_id, set_id, include_questions=False)  # Fetch exam set details (no questions)
    return render_template('confirm.html', data=data, tech_id=tech_id)               # Render confirmation page

@app.route('/start-exam/<string:tech_id>/<string:set_id>/<string:name>')
def start_exam(tech_id, set_id, name):
    # Clear any existing exam session for this user
    old_exam_id = session.get("exam_id")
    if old_exam_id and old_exam_id in _EXAMS:
        del _EXAMS[old_exam_id]

    exam_id = str(uuid4())  # Generate a unique exam session ID
    session["exam_id"] = exam_id # Store exam_id in Flask session

    manager = ExamManager(tech_id, set_id)  # Create an ExamManager bound to this exam
    _EXAMS[exam_id] = manager  # Store manager in the global cache

    # You can also render a full page: return render_template("questions.html", data=manager.get_current_question())
    return render_template("questions.html",
                           data=manager.get_current_question())  # Render the first question block

@app.route("/exam/jump-focus", methods=["POST"])
def jump_focus():
    """
    Jump directly to a selected question inside a focus list (review or unanswered).
    POST fields:
      - target_index: global question index (0-based)
      - focus_type: "review" or "unanswered"
    Returns updated question block.
    """
    manager = _get_manager()
    if not manager:
        return "Session expired. Please restart the exam.", 400
    if manager.finished:
        return "Exam already finished. You cannot perform further actions.", 400

    try:
        target = int(request.form.get("target_index"))
    except (TypeError, ValueError):
        target = None

    focus_type = request.form.get("focus_type", "review")  # default to review

    if target is not None:
        manager.jump_to_focus_index(target, focus_type)

    return render_template("question_block.html", data=manager.get_current_question())




@app.route("/exam/jump-review", methods=["POST"])
def jump_review():
    """
    Jump directly to a selected review chip (auto-switches to review mode).
    POST field:
      - target_index: global question index (0-based)
    Returns updated question block.
    """
    manager = _get_manager()
    if not manager:
        return "Session expired. Please restart the exam.", 400

    if manager.finished:
        return "Exam already finished. You cannot perform further actions.", 400

    try:
        target = int(request.form.get("target_index"))
    except (TypeError, ValueError):
        target = None

    if target is not None:
        manager.jump_to_review_index(target)

    return render_template("question_block.html", data=manager.get_current_question())


@app.route("/exam/jump-unanswered", methods=["POST"])
def jump_unanswered():
    manager = _get_manager()

    if not manager:
        return "Session expired. Please restart the exam.", 400
    if manager.finished:
        return "Exam already finished. You cannot perform further actions.", 400

    target_index = int(request.form.get("target_index", 0))

    # Ensure valid index
    target_index = max(0, min(target_index, len(manager.questions) - 1))

    # Jump directly in MAIN mode (not review)
    manager.switch_mode("main")
    manager.main_current_index = target_index

    data = manager.get_current_question()
    return render_template("question_block.html", data=data)

@app.route('/exam/submit-answer', methods=['POST'])
def submit_answer():
    manager = _get_manager()

    if not manager:
        return "Session expired. Please restart the exam.", 400  # If session expired, return error
    if manager.finished:
        return "Exam already finished. You cannot perform further actions.", 400

    selected = request.form.get("option")  # Get selected answer option from form data (may be None)
    action = request.form.get("action", "stay")  # Get navigation action (default to "stay")

    if selected is not None:
        manager.save_answer(int(selected))  # Save user's answer for the current question

    toggle_review = request.form.get("toggle_review")  # Check if user toggled review for this question
    if toggle_review == "true":
        manager.toggle_review()             # Mark or unmark question for review

    if action == "main" or action == "review":
        manager.switch_mode(action)

    # Handle navigation based on action
    if action == "prev":
        manager.go_prev()  # Move to previous question
    elif action == "next":
        manager.go_next()  # Move to next question
    elif action == "finish":
        report_data = manager.generate_report()
        # Clean up session after exam completion
        # exam_id = session.get("exam_id")
        # if exam_id and exam_id in _EXAMS:
        #     del _EXAMS[exam_id]
        # session.pop("exam_id", None)
        return render_template("exam_report.html", **report_data)

    # Re-render the current question block
    return render_template("question_block.html", data=manager.get_current_question())


@app.route('/exam-report/page/<int:page>', methods=['GET'])
def exam_report_page(page):
    manager = _get_manager()
    if not manager:
        return "Session expired. Please restart the exam.", 400

    report_data = manager.generate_report(page)
    logger.info(f"report_data={report_data.get("pagination")}")
    return render_template("report_question_container.html", **report_data)
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)                # Start Flask app in debug mode (no auto-reload)