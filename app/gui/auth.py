"""
app/gui/auth.py - Écran de connexion Smart Callender

Page de login avec mise en page type "card" : fond plein écran, carte centrée,
titre + sous-titre, champs email/mot de passe, bouton principal et indication démo.
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from app.services.auth_service import AuthService


class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Fond plein écran (couleur douce pour faire ressortir la carte)
        self.configure(bootstyle="light")
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Conteneur centré pour la carte
        center = ttk.Frame(self)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Carte de connexion (style primary pour un look moderne)
        card = ttk.Frame(center, padding=40, bootstyle="primary")
        card.pack(padx=20, pady=20)

        # Bloc titre
        title_frame = ttk.Frame(card)
        title_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(
            title_frame,
            text="📅 Smart Callender",
            font=("Segoe UI", 22, "bold"),
            bootstyle="inverse-primary",
        ).pack()
        ttk.Label(
            title_frame,
            text="Gestion des emplois du temps",
            font=("Segoe UI", 10),
            bootstyle="inverse-primary",
        ).pack(pady=(4, 0))

        # Séparateur visuel
        sep = ttk.Separator(card, orient="horizontal", bootstyle="primary")
        sep.pack(fill="x", pady=(20, 24))

        # Formulaire
        form = ttk.Frame(card)
        form.pack(fill="x")

        ttk.Label(form, text="Email", font=("Segoe UI", 10, "bold"), bootstyle="inverse-primary").pack(
            anchor="w", pady=(0, 4)
        )
        self.email_entry = ttk.Entry(form, width=36, font=("Segoe UI", 11), bootstyle="primary")
        self.email_entry.pack(fill="x", pady=(0, 16))
        self.email_entry.insert(0, "")

        ttk.Label(form, text="Mot de passe", font=("Segoe UI", 10, "bold"), bootstyle="inverse-primary").pack(
            anchor="w", pady=(0, 4)
        )
        self.password_entry = ttk.Entry(form, width=36, show="•", font=("Segoe UI", 11), bootstyle="primary")
        self.password_entry.pack(fill="x", pady=(0, 24))

        # Bouton connexion (pleine largeur, bien visible)
        self.login_btn = ttk.Button(
            form,
            text="Se connecter",
            command=self.login,
            bootstyle="primary-outline",
            width=28,
        )
        self.login_btn.pack(fill="x", pady=(0, 16))

        # Indication démo (discrète)
        demo_frame = ttk.Frame(card)
        demo_frame.pack(fill="x")
        ttk.Label(
            demo_frame,
            text="Démo : admin@test.com — password",
            font=("Segoe UI", 8),
            bootstyle="inverse-primary",
        ).pack()

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            user = AuthService.login(email, password)
            if user:
                self.controller.show_dashboard(user)
            else:
                messagebox.showerror("Erreur", "Email ou mot de passe incorrect.")
        except Exception as e:
            messagebox.showerror("Erreur Système", str(e))
