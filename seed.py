"""
seed.py - Point d'entrée pour initialiser la base de données.

Ce script est volontairement explicite : il applique un seed complet en mode
démo et réinitialise la base si elle existe.
Exécuter : python seed.py
"""

import sys
import os

# S'assurer que le répertoire racine est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.seed_db import seed

if __name__ == "__main__":
    seed()
