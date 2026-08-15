"""
my_config.py - Configuration de l'application Smart Callender

Ce fichier centralise toutes les configurations de l'application Flask.
Il gère les différents environnements (développement, production, test)
et les variables sensibles via des variables d'environnement.
"""

import os
from pathlib import Path

# Répertoire de base de l'application (racine du projet)
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Configuration de base commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # SQLAlchemy - Base de données
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'smart_callender.db')}"

    # Flask-Login
    REMEMBER_COOKIE_DURATION = 86400  # 24 heures
    SESSION_PROTECTION = "strong"

    # Paramètres par défaut pour les emplois du temps
    DEFAULT_START_HOUR = 8
    DEFAULT_END_HOUR = 18
    SLOT_DURATION_MINUTES = 90
    DAYS_OF_WEEK = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]


class DevelopmentConfig(Config):
    """Configuration pour l'environnement de développement."""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Configuration pour l'environnement de production."""

    DEBUG = False


class TestingConfig(Config):
    """Configuration pour les tests."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


# Mapping des configurations par nom d'environnement
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
