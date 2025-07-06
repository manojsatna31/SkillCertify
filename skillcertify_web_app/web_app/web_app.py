from flask import Flask, render_template
from core_config import Config
from datetime import datetime

def create_web_app(config_class=Config):
    """Construct the core application."""
    skillcertify_web_app = Flask(__name__)
    skillcertify_web_app.config.from_object(config_class)

    # Configure Jinja2 for cleaner template output
    skillcertify_web_app.jinja_env.trim_blocks = True
    skillcertify_web_app.jinja_env.lstrip_blocks = True

    # Register the main blueprint
    from . import routes
    skillcertify_web_app.register_blueprint(routes.routes)

    # Register custom error handlers
    @skillcertify_web_app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @skillcertify_web_app.context_processor
    def inject_current_year():
        """Injects the current year into all templates."""
        return {'current_year': datetime.utcnow().year}

    return skillcertify_web_app