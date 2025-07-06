import json
from flask import Blueprint, render_template, abort

from skillcertify_web_app import Q_BANK

routes = Blueprint('main', __name__)

@routes.route('/')
def home():
    """Renders the home page with all available topics."""
    return render_template('pages/index.html', topics=Q_BANK)

@routes.route('/exam/<string:topic_id>')
def exam(topic_id):
    """Renders the exam SPA for a selected topic."""
    topic_data = Q_BANK.get(topic_id)
    if not topic_data:
        abort(404) # Trigger the 404 error page

    all_sets_data = topic_data.get('sets', {})
    all_sets_data_json = json.dumps(all_sets_data)

    return render_template(
        'pages/exam.html',
        topic_title=topic_data['title'],
        all_sets_data_json=all_sets_data_json
    )