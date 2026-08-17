import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from app import create_app
from app.extensions import db
from app.models.utilisateur import Utilisateur
from app.gui.auth import LoginFrame
from app.gui.admin import AdminDashboard
from app.gui.teacher import TeacherDashboard
from app.gui.student import StudentDashboard
from app.services.settings_service import SchoolSettingsService

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Callender - Gestion d'Emploi du Temps")
        self.root.geometry("1200x800") # A bit larger for modern feel
        
        # Initialiser Flask
        self.flask_app = create_app("development")
        self.app_context = self.flask_app.app_context()
        self.app_context.push()

        # Premier lancement : créer les tables et garantir les réglages d'école.
        self.startup_hint = self._ensure_db_bootstrap()

        self.current_frame = None
        self.user = None
        
        self.show_login()

    def _ensure_db_bootstrap(self):
        """Crée les tables et vérifie l'état initial de l'installation."""
        startup_hint = None
        try:
            db.create_all()
            SchoolSettingsService.seed_default_settings()

            user_count = db.session.query(Utilisateur).count()
            if user_count == 0:
                return (
                    "Bienvenue dans Smart Callender !\n"
                    "Aucun compte trouvé. Exécutez d'abord `python seed.py` pour un démarrage rapide (compte admin inclus),\n"
                    "ou créez votre propre premier administrateur directement dans votre base de données."
                )

            admin_count = db.session.query(Utilisateur).filter_by(role="admin").count()
            if admin_count == 0:
                return (
                    "Aucun administrateur actif détecté.\n"
                    "Créez un compte admin en base ou relancez `python seed.py` selon votre stratégie de déploiement."
                )

            return startup_hint
        except Exception:
            return (
                "Impossible de vérifier l'état initial de la base.\n"
                "Vérifiez que la base de données est accessible et que `python seed.py` a été exécuté si nécessaire."
            )

    def show_login(self):
        self.clear_frame()
        self.current_frame = LoginFrame(self.root, self)
        self.current_frame.pack(expand=True, fill="both")

    def show_dashboard(self, user):
        self.user = user
        self.clear_frame()
        
        # Redirection selon le rôle
        if user.role == "admin":
            self.current_frame = AdminDashboard(self.root, self, user)
            self.current_frame.pack(expand=True, fill="both")
        elif user.role == "enseignant":
            self.current_frame = TeacherDashboard(self.root, self, user)
            self.current_frame.pack(expand=True, fill="both")
        elif user.role == "etudiant":
            self.current_frame = StudentDashboard(self.root, self, user)
            self.current_frame.pack(expand=True, fill="both")
        else:
            messagebox.showerror("Erreur", "Rôle inconnu")
            self.show_login()

    def logout(self):
        self.user = None
        self.show_login()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def _patch_dateentry_for_destroy(self, widget):
        """Workaround: tkcalendar DateEntry can miss _determine_downarrow_name_after_id on destroy."""
        try:
            if type(widget).__name__ == "DateEntry" and not hasattr(widget, "_determine_downarrow_name_after_id"):
                widget._determine_downarrow_name_after_id = None
        except Exception:
            pass
        try:
            for c in widget.winfo_children():
                self._patch_dateentry_for_destroy(c)
        except Exception:
            pass

    def on_close(self):
        try:
            self.app_context.pop()
        except LookupError:
            pass
        try:
            self._patch_dateentry_for_destroy(self.root)
            self.root.destroy()
        except Exception:
            try:
                self.root.quit()
            except Exception:
                pass
