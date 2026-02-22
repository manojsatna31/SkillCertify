from functools import wraps

from flask import Blueprint,render_template, request, jsonify, session, redirect, url_for

# Import your existing modules
from web_app import app
from web_app.utils.data_loader import DataLoader
from web_app.utils.groq_ai_loader import generate_questions as ai_generate_questions

admin = Blueprint("admin", __name__, url_prefix="/admin")


# Initialize DataLoader
data_loader = DataLoader()


# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # Check if user is admin (implement your authentication logic)
#         if not session.get('is_admin'):
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#
#     return decorated_function


@admin.route('/')
# @admin._required
def admin_index():
    return render_template('admin/admin-base.html')

@admin.route('/dashboard')
# @admin._required
def admin_dashboard():

    admin_data = data_loader.get_admin_dashboard_data()

    # Sample recent activities
    recent_activities = [
        {"type": "New", "message": "Added Python technology", "time": "2 hours ago", "color": "blue"},
        {"type": "Update", "message": "Modified AWS exam set", "time": "1 day ago", "color": "green"},
        {"type": "AI", "message": "Generated 5 questions for JavaScript", "time": "2 days ago", "color": "yellow"}
    ]
    return render_template('admin/admin-dashboard.html',
                               data=admin_data,
                               recent_activities=recent_activities)


@admin.route('/admin/technologies')
# @admin._required
def admin_technologies():
    technologies = data_loader.get_all_technologies()

    if request.headers.get('HX-Request'):
        return render_template('admin/admin-technologies.html', technologies=technologies)

    return render_template('admin/admin-base.html', technologies=technologies)


@admin.route('/admin/exam-sets')
# @admin._required
def admin_exam_sets():
    technologies = data_loader.get_all_technologies()
    exam_sets = []

    for tech in technologies:
        for exam_set in tech.get('exam_sets', []):
            exam_set['technology_name'] = tech['name']
            exam_set['technology_id'] = tech['id']
            exam_sets.append(exam_set)

    if request.headers.get('HX-Request'):
        return render_template('admin/admin-exam_sets.html', exam_sets=exam_sets, technologies=technologies)

    return render_template('admin/admin-base.html', exam_sets=exam_sets, technologies=technologies)


@admin.route('/admin/questions')
# @admin._required
def admin_questions():
    technologies = data_loader.get_all_technologies()
    all_questions = []

    for tech in technologies:
        for exam_set in tech.get('exam_sets', []):
            for question in exam_set.get('questions', []):
                question['technology_name'] = tech['name']
                question['exam_set_name'] = exam_set['name']
                all_questions.append(question)

    if request.headers.get('HX-Request'):
        return render_template('admin/admin-questions.html', questions=all_questions, technologies=technologies)

    return render_template('admin/admin-base.html', questions=all_questions, technologies=technologies)


@admin.route('/admin/ai-generator')
# @admin._required
def admin_ai_generator():
    technologies = data_loader.get_all_technologies()

    if request.headers.get('HX-Request'):
        return render_template('admin/admin-AI-Generator.html', technologies=technologies)

    return render_template('admin/admin-base.html', technologies=technologies)


# # API endpoints for CRUD operations
# @admin.route('/api/technologies', methods=['GET', 'POST', 'PUT', 'DELETE'])
# # @admin._required
# def admin_api_technologies():
#     if request.method == 'GET':
#         tech_id = request.args.get('id')
#         if tech_id:
#             # Find the technology by ID from  data loader
#             technology = next((t for t in data_loader.get_technologies() if t['id'] == tech_id), None)
#             if technology:
#                 return jsonify(technology)
#             else:
#                 return jsonify({"error": "Technology not found"}), 404
#         else:
#             technologies = data_loader.get_all_technologies()
#             return jsonify(technologies)
#     elif request.method == 'POST':
#         tech_id = request.args.get('id')
#         data = request.get_json()
#         success = data_loader.add_technology(data)
#         return jsonify({"status": "success" if success else "error"})
#
#     elif request.method == 'PUT':
#         tech_id = request.args.get('id')
#         data = request.get_json()
#         success = data_loader.update_technology(tech_id, data)
#         return jsonify({"status": "success" if success else "error"})
#
#     elif request.method == 'DELETE':
#         tech_id = request.args.get('id')
#         success = data_loader.delete_technology(tech_id)
#         return jsonify({"status": "success" if success else "error"})

from flask import request, jsonify


# API endpoints for CRUD operations
@admin.route('/admin/api/technologies', methods=['GET', 'POST', 'PUT', 'DELETE'])
# @admin._required
def admin_api_technologies():
    if request.method == 'GET':
        tech_id = request.args.get('id')
        if tech_id:
            # Find the technology by ID from data loader
            technology = next((t for t in data_loader.get_technologies() if t['id'] == tech_id), None)
            if technology:
                return jsonify(technology)
            else:
                return jsonify({"error": "Technology not found"}), 404
        else:
            technologies = data_loader.get_all_technologies()
            return jsonify(technologies)

    elif request.method == 'POST':
        # Handle both single technology and bulk operations
        operation_type = request.args.get('type', 'single')  # 'single' or 'bulk'

        if operation_type == 'bulk':
            # Save all technologies
            data = request.get_json()
            success = data_loader.save_all_technologies(data.get('technologies', []))
            return jsonify({"status": "success" if success else "error"})
        else:
            # Add a single technology
            data = request.get_json()
            success = data_loader.add_technology(data)
            return jsonify({"status": "success" if success else "error"})

    elif request.method == 'PUT':
        # Handle both single technology update and bulk update
        operation_type = request.args.get('type', 'single')  # 'single' or 'bulk'

        if operation_type == 'bulk':
            # Update all technologies
            data = request.get_json()
            success = data_loader.update_all_technologies(data.get('technologies', []))
            return jsonify({"status": "success" if success else "error"})
        else:
            # Update a single technology
            tech_id = request.args.get('id')
            data = request.get_json()
            success = data_loader.update_technology(tech_id, data)
            return jsonify({"status": "success" if success else "error"})

    elif request.method == 'DELETE':
        tech_id = request.args.get('id')
        success = data_loader.delete_technology(tech_id)
        return jsonify({"status": "success" if success else "error"})


# Additional endpoint specifically for single technology operations
@admin.route('/admin/api/technologies/single', methods=['POST', 'PUT'])
# @admin._required
def admin_api_single_technology():
    if request.method == 'POST':
        # Add a single technology
        data = request.get_json()
        success = data_loader.add_technology(data)
        return jsonify({"status": "success" if success else "error", "id": data.get('id')})

    elif request.method == 'PUT':
        # Update a single technology
        tech_id = request.args.get('id')
        data = request.get_json()
        success = data_loader.update_technology(tech_id, data)
        return jsonify({"status": "success" if success else "error"})

@admin.route('/admin/api/exam-sets', methods=['GET', 'POST', 'PUT', 'DELETE'])
# @admin._required
def admin_api_exam_sets():
    if request.method == 'GET':
        tech_id = request.args.get('tech_id')
        exam_sets = data_loader.get_exam_sets_for_technology(tech_id)
        return jsonify(exam_sets)

    elif request.method == 'POST':
        tech_id = request.args.get('tech_id')
        data = request.get_json()
        success = data_loader.add_exam_set(tech_id, data)
        return jsonify({"status": "success" if success else "error"})

    elif request.method == 'PUT':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        data = request.get_json()
        success = data_loader.update_exam_set(tech_id, set_id, data)
        return jsonify({"status": "success" if success else "error"})

    elif request.method == 'DELETE':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        success = data_loader.delete_exam_set(tech_id, set_id)
        return jsonify({"status": "success" if success else "error"})


@admin.route('/admin/api/questions', methods=['GET', 'POST', 'PUT', 'DELETE'])
# @admin._required
def admin_api_questions():
    if request.method == 'GET':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        questions = data_loader.get_questions_for_exam_set(tech_id, set_id)
        return jsonify(questions)

    elif request.method == 'POST':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        data = request.get_json()
        success = data_loader.add_question(tech_id, set_id, data)
        return jsonify({"status": "success" if success else "error"})

    elif request.method == 'PUT':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        question_id = request.args.get('question_id')
        data = request.get_json()
        success = data_loader.update_question(tech_id, set_id, question_id, data)
        return jsonify({"status": "success" if success else "error"})

    elif request.method == 'DELETE':
        tech_id = request.args.get('tech_id')
        set_id = request.args.get('set_id')
        question_id = request.args.get('question_id')
        success = data_loader.delete_question(tech_id, set_id, question_id)
        return jsonify({"status": "success" if success else "error"})


@admin.route('/admin/api/generate-questions', methods=['POST'])
# @admin._required
def admin_api_generate_questions():
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        # Use your existing AI question generator
        result = ai_generate_questions(prompt)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/api/save-generated-questions', methods=['POST'])
# @admin._required
def admin_api_save_generated_questions():
    try:
        data = request.get_json()
        tech_id = data.get('tech_id')
        set_id = data.get('set_id')
        questions = data.get('questions', [])

        # Add questions to the specified exam set
        for question in questions:
            data_loader.add_question(tech_id, set_id, question)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500