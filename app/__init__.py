"""
app/__init__.py - Application Factory pour Smart Callender

Ce module implémente le pattern Application Factory de Flask.
Il initialise l'application, les extensions, et enregistre les blueprints
pour une architecture modulaire et maintenable.
"""

from flask import Flask
from my_config import config
from app.extensions import db, migrate, login_manager, bcrypt


def create_app(config_name=None):
    """
    Crée et configure l'instance Flask.

    Args:
        config_name: Nom de la configuration ('development', 'production', 'testing').

    Returns:
        Instance Flask configurée.
    """
    import os

    app = Flask(__name__, instance_relative_config=True)

    # Charger la configuration
    if config_name is None:
        config_name = "default"
    app.config.from_object(config[config_name])

    # Créer le répertoire instance si nécessaire
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Importer les modèles pour les enregistrer avec SQLAlchemy
    from app import models  # noqa: F401
    from app.models.utilisateur import Utilisateur

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    # Configurer le chemin de redirection après login
    login_manager.login_view = "auth.connexion"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "info"

    # Enregistrer les blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp
    from app.teacher import teacher_bp
    from app.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/enseignant")
    app.register_blueprint(student_bp, url_prefix="/etudiant")

    return app
