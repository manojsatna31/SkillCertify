# SkillCertify_web_app/__init__.py
from .web_app.web_app import create_web_app
from .data_loader import Q_BANK
from .web_app.routes import routes

__all__ = ['create_web_app','Q_BANK','routes']