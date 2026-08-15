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

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Callender - Gestion d'Emploi du Temps")
        self.root.geometry("1200x800") # A bit larger for modern feel
        
        # Initialiser Flask
        self.flask_app = create_app("development")
        self.app_context = self.flask_app.app_context()
        self.app_context.push()

        # Premier lancement : créer les tables et insérer les données de démo si la DB est vide
        self._ensure_db_seeded()

        self.current_frame = None
        self.user = None
        
        self.show_login()

    def _ensure_db_seeded(self):
        """Crée les tables et remplit la base avec les données de démo si elle est vide (exe premier lancement)."""
        try:
            db.create_all()
            if db.session.query(Utilisateur).count() == 0:
                from scripts.seed_db import seed
                seed()
        except Exception:
            pass

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
