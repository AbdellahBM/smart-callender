"""
seed.py - Point d'entrée pour initialiser la base de données.

Délègue à scripts/seed_db.py pour créer les tables et insérer
les données marocaines (filieres SMI/SEG, salles, enseignants, etc.).
Exécuter : python seed.py
"""

import sys
import os

# S'assurer que le répertoire racine est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.seed_db import seed

if __name__ == "__main__":
    seed()
