import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from app.services.resource_service import ResourceService
from app.services.auth_service import AuthService
from app.extensions import db
from app.models import Reservation
from app.services.settings_service import SchoolSettingsService

class AdminDashboard(ttk.Frame):
    def __init__(self, parent, controller, user):
        super().__init__(parent)
        self.controller = controller
        self.user = user
        
        # Header with branding
        header = ttk.Frame(self, bootstyle="primary", padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="Smart Callender", font=("Helvetica", 16, "bold"), bootstyle="inverse-primary").pack(side="left")
        ttk.Label(header, text=f" | Espace Admin: {user.nom} {user.prenom}", font=("Helvetica", 12), bootstyle="inverse-primary").pack(side="left", padx=10)
        ttk.Button(header, text="Déconnexion", command=controller.logout, bootstyle="secondary").pack(side="right")
        
        # Tabs
        self.notebook = ttk.Notebook(self, padding=10)
        self.notebook.pack(expand=True, fill="both")
        
        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.tab_reservations = ttk.Frame(self.notebook, padding=10)
        self.tab_salles = ttk.Frame(self.notebook, padding=10)
        self.tab_enseignants = ttk.Frame(self.notebook, padding=10)
        self.tab_groupes = ttk.Frame(self.notebook, padding=10)
        self.tab_planning = ttk.Frame(self.notebook, padding=10)
        self.tab_parametres = ttk.Frame(self.notebook, padding=10)
        self.tab_utilisateurs = ttk.Frame(self.notebook, padding=10)
        self.tab_classes = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_dashboard, text="Tableau de bord")
        self.notebook.add(self.tab_planning, text="📅 Planning")
        self.notebook.add(self.tab_reservations, text="🔔 Réservations")
        self.notebook.add(self.tab_salles, text="🏢 Salles")
        self.notebook.add(self.tab_enseignants, text="👨‍🏫 Enseignants")
        self.notebook.add(self.tab_groupes, text="🎓 Groupes")
        self.notebook.add(self.tab_utilisateurs, text="👥 Utilisateurs")
        self.notebook.add(self.tab_classes, text="📘 Filières / Matières")
        self.notebook.add(self.tab_parametres, text="⚙️ Paramètres")
        
        self.setup_dashboard()
        self.setup_reservations()
        self.setup_salles()
        self.setup_enseignants()
        self.setup_groupes()
        self.setup_utilisateurs()
        self.setup_classes()
        self.setup_parametres()
        
        # Charger le module planning
        from app.gui.schedule_ui import ScheduleFrame
        ScheduleFrame(self.tab_planning, controller).pack(fill="both", expand=True)

    def setup_dashboard(self):
        # KPIs Container
        kpi_frame = ttk.Frame(self.tab_dashboard)
        kpi_frame.pack(fill="x", pady=20)
        
        nb_salles = len(ResourceService.get_all_salles())
        nb_profs = len(ResourceService.get_all_enseignants())
        nb_groupes = len(ResourceService.get_all_groupes())
        nb_res_pending = db.session.query(Reservation).filter_by(statut="en_attente").count()
        
        # Creating colored cards
        self.create_kpi_card(kpi_frame, "Salles", nb_salles, "info").pack(side="left", padx=20, fill="y")
        self.create_kpi_card(kpi_frame, "Enseignants", nb_profs, "success").pack(side="left", padx=20, fill="y")
        self.create_kpi_card(kpi_frame, "Groupes", nb_groupes, "warning").pack(side="left", padx=20, fill="y")
        self.create_kpi_card(kpi_frame, "Demandes", nb_res_pending, "danger" if nb_res_pending > 0 else "secondary").pack(side="left", padx=20, fill="y")

    def create_kpi_card(self, parent, title, value, bootstyle="primary"):
        frame = ttk.Labelframe(parent, text=title, bootstyle=bootstyle, padding=20)
        ttk.Label(frame, text=str(value), font=("Helvetica", 36, "bold"), bootstyle=bootstyle).pack()
        return frame

    # --- Gestion Réservations ---
    def setup_reservations(self):
        # Toolbar
        btn_frame = ttk.Frame(self.tab_reservations)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(btn_frame, text="✅ Valider", command=self.valider_reservation, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Refuser", command=self.refuser_reservation, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Rafraîchir", command=self.refresh_reservations, bootstyle="info-outline").pack(side="left", padx=5)
        
        cols = ("id", "prof", "date", "heure", "salle", "statut", "motif")
        self.tree_res = ttk.Treeview(self.tab_reservations, columns=cols, show="headings", bootstyle="primary")
        for col in cols: self.tree_res.heading(col, text=col.capitalize())
        self.tree_res.column("id", width=50)
        self.tree_res.pack(expand=True, fill="both")
        
        self.refresh_reservations()

    def refresh_reservations(self):
        for row in self.tree_res.get_children():
            self.tree_res.delete(row)
        
        res_list = db.session.query(Reservation).order_by(Reservation.date_reservation).all()
        for r in res_list:
            prof_nom = r.demandeur.nom if r.demandeur else "?"
            salle_nom = r.salle.nom if r.salle else "?"
            # Tag rows based on status? Treeview tags need configuration, keeping simple for now
            self.tree_res.insert("", "end", values=(r.id, prof_nom, r.date_reservation, f"{r.heure_debut}-{r.heure_fin}", salle_nom, r.statut, r.motif))

    def get_selected_reservation(self):
        selected = self.tree_res.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réservation.")
            return None
        item = self.tree_res.item(selected[0])
        return item['values'][0]

    def valider_reservation(self):
        res_id = self.get_selected_reservation()
        if res_id:
            res = db.session.get(Reservation, res_id)
            if res:
                res.statut = "acceptee"
                db.session.commit()
                messagebox.showinfo("Succès", "Réservation acceptée.")
                self.refresh_reservations()

    def refuser_reservation(self):
        res_id = self.get_selected_reservation()
        if res_id:
            res = db.session.get(Reservation, res_id)
            if res:
                res.statut = "refusee"
                db.session.commit()
                messagebox.showinfo("Succès", "Réservation refusée.")
                self.refresh_reservations()

    # --- Gestion Salles ---
    def setup_salles(self):
        btn_frame = ttk.Frame(self.tab_salles)
        btn_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_frame, text="+ Ajouter Salle", command=self.add_salle, bootstyle="success").pack(side="left")
        ttk.Button(btn_frame, text="🗑 Supprimer Salle", command=self.delete_selected_salle, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Rafraîchir", command=self.refresh_salles, bootstyle="info-outline").pack(side="left", padx=5)
        
        columns = ("id", "nom", "type", "capacite")
        self.tree_salles = ttk.Treeview(self.tab_salles, columns=columns, show="headings", bootstyle="info")
        for col in columns: self.tree_salles.heading(col, text=col.capitalize())
        self.tree_salles.column("id", width=50)
        self.tree_salles.pack(expand=True, fill="both")
        
        self.refresh_salles()

    def refresh_salles(self):
        for row in self.tree_salles.get_children():
            self.tree_salles.delete(row)
        for s in ResourceService.get_all_salles():
            self.tree_salles.insert("", "end", values=(s.id, s.nom, s.type_salle, s.capacite))

    def add_salle(self):
        nom = simpledialog.askstring("Ajout Salle", "Nom de la salle:")
        if not nom:
            return
        capacite = simpledialog.askinteger("Ajout Salle", "Capacité:", initialvalue=30)
        if capacite is None:
            return
        type_salle = simpledialog.askstring("Ajout Salle", "Type (cours, tp, amphi):", initialvalue="cours")
        ResourceService.create_salle({
            "nom": nom,
            "capacite": capacite,
            "type_salle": type_salle or "cours",
        })
        self.refresh_salles()

    def delete_selected_salle(self):
        selected = self.tree_salles.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez une salle.")
            return
        values = self.tree_salles.item(selected[0], "values")
        if not values:
            return
        salle_id = int(values[0])
        if messagebox.askyesno("Confirmer", f"Supprimer la salle {values[1]} ?"):
            if ResourceService.delete_salle(salle_id):
                messagebox.showinfo("Succès", "Salle supprimée.")
                self.refresh_salles()
            else:
                messagebox.showerror("Erreur", "Suppression impossible.")

    # --- Gestion Enseignants ---
    def setup_enseignants(self):
        self.tree_profs = ttk.Treeview(self.tab_enseignants, columns=("id", "nom", "email"), show="headings", bootstyle="success")
        self.tree_profs.heading("id", text="ID")
        self.tree_profs.heading("nom", text="Nom")
        self.tree_profs.heading("email", text="Email")
        self.tree_profs.column("id", width=50)
        self.tree_profs.pack(expand=True, fill="both")
        self.refresh_profs()

    def refresh_profs(self):
        for row in self.tree_profs.get_children():
            self.tree_profs.delete(row)
        for u in ResourceService.get_all_enseignants():
            self.tree_profs.insert("", "end", values=(u.id, f"{u.nom} {u.prenom}", u.email))

    # --- Gestion Groupes ---
    def setup_groupes(self):
        self.tree_groupes = ttk.Treeview(self.tab_groupes, columns=("id", "nom", "effectif", "filiere"), show="headings", bootstyle="warning")
        self.tree_groupes.heading("id", text="ID")
        self.tree_groupes.heading("nom", text="Nom")
        self.tree_groupes.heading("effectif", text="Effectif")
        self.tree_groupes.heading("filiere", text="Filière")
        self.tree_groupes.column("id", width=50)
        self.tree_groupes.pack(expand=True, fill="both")

        btn_frame = ttk.Frame(self.tab_groupes)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="➕ Ajouter un groupe", command=self.add_groupe, bootstyle="success").pack(side="left")
        ttk.Button(btn_frame, text="🗑 Supprimer", command=self.delete_selected_groupe, bootstyle="danger").pack(side="left", padx=6)

        self.refresh_groupes()

    def refresh_groupes(self):
        for row in self.tree_groupes.get_children():
            self.tree_groupes.delete(row)
        for g in ResourceService.get_all_groupes():
            filiere_nom = g.filiere.nom if g.filiere else "?"
            self.tree_groupes.insert("", "end", values=(g.id, g.nom, g.effectif, filiere_nom))

    def add_groupe(self):
        nom = simpledialog.askstring("Ajouter un groupe", "Nom du groupe:")
        if not nom:
            return
        effectif = simpledialog.askinteger("Ajouter un groupe", "Effectif:", initialvalue=30)
        if effectif is None:
            return
        filieres = ResourceService.get_all_filieres()
        options = [f"{f.id}: {f.nom}" for f in filieres]
        if not options:
            messagebox.showwarning("Attention", "Aucune filière disponible. Créez d'abord une filière.")
            return
        choix = simpledialog.askstring("Ajouter un groupe", f"Filière (id): {', '.join(options)}")
        if not choix:
            return
        try:
            filiere_id = int(choix.split(":")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Erreur", "ID filière invalide.")
            return
        ResourceService.create_groupe(nom=nom, effectif=effectif, filiere_id=filiere_id)
        self.refresh_groupes()

    def delete_selected_groupe(self):
        selected = self.tree_groupes.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un groupe.")
            return
        values = self.tree_groupes.item(selected[0], "values")
        if not values:
            return
        if messagebox.askyesno("Confirmer", f"Supprimer le groupe {values[1]} ?"):
            if ResourceService.delete_groupe(int(values[0])):
                self.refresh_groupes()
            else:
                messagebox.showerror("Erreur", "Suppression impossible.")

    # --- Gestion Utilisateurs ---
    def setup_utilisateurs(self):
        frame = ttk.Labelframe(self.tab_utilisateurs, text="Comptes", padding=15, bootstyle="secondary")
        frame.pack(fill="both", expand=True)

        self.tree_users = ttk.Treeview(
            frame,
            columns=("id", "nom", "prenom", "email", "role", "groupe", "actif"),
            show="headings",
            bootstyle="primary"
        )
        self.tree_users.heading("id", text="ID")
        self.tree_users.heading("nom", text="Nom")
        self.tree_users.heading("prenom", text="Prénom")
        self.tree_users.heading("email", text="Email")
        self.tree_users.heading("role", text="Rôle")
        self.tree_users.heading("groupe", text="Groupe")
        self.tree_users.heading("actif", text="Actif")
        self.tree_users.column("id", width=50)
        self.tree_users.pack(expand=True, fill="both")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="➕ Ajouter enseignant", command=self.add_enseignant, bootstyle="success").pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="➕ Ajouter étudiant", command=self.add_etudiant, bootstyle="success").pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🗑 Supprimer", command=self.delete_selected_user, bootstyle="danger").pack(side="left")
        ttk.Button(btn_frame, text="✅ Activer/Désactiver", command=self.toggle_selected_user, bootstyle="warning").pack(side="left", padx=(6, 0))
        self.refresh_utilisateurs()

    def refresh_utilisateurs(self):
        for row in self.tree_users.get_children():
            self.tree_users.delete(row)
        for u in AuthService.get_all():
            groupe_nom = u.groupe.nom if u.groupe else "-"
            self.tree_users.insert("", "end", values=(u.id, u.nom, u.prenom, u.email, u.role, groupe_nom, "Oui" if u.actif else "Non"))

    def _ask_user_values(self, role):
        nom = simpledialog.askstring("Créer un compte", "Nom:")
        if not nom:
            return None
        prenom = simpledialog.askstring("Créer un compte", "Prénom:")
        if not prenom:
            return None
        email = simpledialog.askstring("Créer un compte", "Email:")
        if not email:
            return None
        password = simpledialog.askstring("Créer un compte", "Mot de passe initial:")
        if not password:
            return None
        return {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "password": password,
            "role": role,
        }

    def add_enseignant(self):
        data = self._ask_user_values("enseignant")
        if not data:
            return
        try:
            AuthService.create_user(
                email=data["email"],
                password=data["password"],
                nom=data["nom"],
                prenom=data["prenom"],
                role="enseignant",
            )
            self.refresh_utilisateurs()
            self.refresh_profs()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def add_etudiant(self):
        data = self._ask_user_values("etudiant")
        if not data:
            return
        groupes = ResourceService.get_all_groupes()
        options = [f"{g.id}: {g.nom}" for g in groupes]
        if not options:
            messagebox.showwarning("Attention", "Aucun groupe disponible.")
            return
        choix = simpledialog.askstring("Créer un étudiant", f"Groupe (id): {', '.join(options)}")
        if not choix:
            return
        try:
            groupe_id = int(choix.split(":")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Erreur", "ID de groupe invalide.")
            return
        try:
            AuthService.create_user(
                email=data["email"],
                password=data["password"],
                nom=data["nom"],
                prenom=data["prenom"],
                role="etudiant",
                groupe_id=groupe_id,
            )
            self.refresh_utilisateurs()
            self.refresh_groupes()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def delete_selected_user(self):
        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un utilisateur.")
            return
        values = self.tree_users.item(selected[0], "values")
        if not values:
            return
        user_id = int(values[0])
        if user_id == self.user.id:
            messagebox.showwarning("Attention", "Vous ne pouvez pas supprimer votre propre compte.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cet utilisateur ?"):
            if AuthService.delete_user(user_id):
                self.refresh_utilisateurs()
                self.refresh_profs()
                self.refresh_groupes()
                self.refresh_reservations()
            else:
                messagebox.showerror("Erreur", "Suppression impossible (compte référencé).")

    def toggle_selected_user(self):
        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un utilisateur.")
            return
        values = self.tree_users.item(selected[0], "values")
        if not values:
            return
        user_id = int(values[0])
        if user_id == self.user.id:
            messagebox.showwarning("Attention", "Vous ne pouvez pas désactiver votre propre compte.")
            return
        current_status = str(values[6]).strip().lower() in {"oui", "true", "1"}
        if AuthService.set_status(user_id, not current_status):
            self.refresh_utilisateurs()
        else:
            messagebox.showerror("Erreur", "Impossible de modifier le statut.")

    # --- Gestion Filières / Matières ---
    def setup_classes(self):
        frame = ttk.Labelframe(self.tab_classes, text="Filières et matières", padding=15, bootstyle="warning")
        frame.pack(fill="both", expand=True)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="➕ Ajouter filière", command=self.add_filiere, bootstyle="success").pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="➕ Ajouter matière", command=self.add_matiere, bootstyle="success").pack(side="left", padx=(0, 6))

        self.tree_classes = ttk.Treeview(frame, columns=("id", "nom", "type", "detail"), show="headings", bootstyle="warning")
        self.tree_classes.heading("id", text="ID")
        self.tree_classes.heading("nom", text="Nom")
        self.tree_classes.heading("type", text="Type")
        self.tree_classes.heading("detail", text="Détail")
        self.tree_classes.column("id", width=50)
        self.tree_classes.pack(expand=True, fill="both")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="🗑 Supprimer sélection", command=self.delete_selected_class_item, bootstyle="danger").pack(side="left")

        self.refresh_classes()

    def refresh_classes(self):
        for row in self.tree_classes.get_children():
            self.tree_classes.delete(row)
        for f in ResourceService.get_all_filieres():
            self.tree_classes.insert("", "end", values=(f"f-{f.id}", f.nom, "Filière", f.code or ""))
        for m in ResourceService.get_all_matieres():
            filiere_nom = m.filiere.nom if m.filiere else "Générale"
            self.tree_classes.insert("", "end", values=(f"m-{m.id}", m.nom, "Matière", filiere_nom))

    def add_filiere(self):
        nom = simpledialog.askstring("Ajouter une filière", "Nom :")
        if not nom:
            return
        code = simpledialog.askstring("Ajouter une filière", "Code :", initialvalue="")
        ResourceService.create_filiere(nom=nom, code=code or None)
        self.refresh_classes()
        self.refresh_groupes()

    def add_matiere(self):
        nom = simpledialog.askstring("Ajouter une matière", "Nom :")
        if not nom:
            return
        code = simpledialog.askstring("Ajouter une matière", "Code :", initialvalue="")
        filieres = ResourceService.get_all_filieres()
        filiere_id = None
        if filieres:
            choix = simpledialog.askstring("Ajouter une matière", f"Filière (id): {', '.join(f'{f.id}: {f.nom}' for f in filieres)}")
            if choix:
                try:
                    filiere_id = int(choix.split(":")[0])
                except (ValueError, IndexError):
                    messagebox.showerror("Erreur", "ID de filière invalide.")
                    return
        ResourceService.create_matiere(nom=nom, code=code, filiere_id=filiere_id)
        self.refresh_classes()

    def delete_selected_class_item(self):
        selected = self.tree_classes.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un élément.")
            return
        selected_value = self.tree_classes.item(selected[0], "values")
        if not selected_value:
            return
        prefix = str(selected_value[0])
        if prefix.startswith("f-"):
            filiere_id = int(prefix.replace("f-", ""))
            if messagebox.askyesno("Confirmer", f"Supprimer la filière {selected_value[1]} ?"):
                if not ResourceService.delete_filiere(filiere_id):
                    messagebox.showerror("Erreur", "Suppression impossible (dépendances existantes).")
                    return
        elif prefix.startswith("m-"):
            matiere_id = int(prefix.replace("m-", ""))
            if messagebox.askyesno("Confirmer", f"Supprimer la matière {selected_value[1]} ?"):
                if not ResourceService.delete_matiere(matiere_id):
                    messagebox.showerror("Erreur", "Suppression impossible (dépendances existantes).")
                    return
                self.refresh_groupes()
        self.refresh_classes()
        self.refresh_groupes()

    # --- Paramètres planning ---
    def setup_parametres(self):
        frame = ttk.Labelframe(self.tab_parametres, text="Planification", padding=15, bootstyle="secondary")
        frame.pack(fill="x", pady=(0, 20))

        # Jours actifs
        ttk.Label(frame, text="Jours actifs (0=Lundi ... 6=Dimanche, séparés par des virgules)").pack(anchor="w")
        self.setting_work_days = ttk.Entry(frame, width=40)
        self.setting_work_days.pack(fill="x", pady=(0, 10))
        self.setting_work_days.insert(0, ", ".join(str(d) for d in SchoolSettingsService.get_working_days()))

        # Créneaux actifs
        ttk.Label(frame, text="Créneaux (HH:MM, séparés par des virgules)").pack(anchor="w")
        slot_times = SchoolSettingsService.get_slot_times()
        self.setting_slot_times = ttk.Entry(frame, width=40)
        self.setting_slot_times.pack(fill="x", pady=(0, 10))
        self.setting_slot_times.insert(0, ", ".join(t.strftime("%H:%M") for t in slot_times))

        # Durée des créneaux
        ttk.Label(frame, text="Durée d'un créneau (minutes)").pack(anchor="w")
        self.setting_slot_duration = ttk.Entry(frame, width=15)
        self.setting_slot_duration.pack(anchor="w", pady=(0, 10))
        self.setting_slot_duration.insert(0, str(SchoolSettingsService.get_slot_duration_minutes()))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_frame, text="💾 Enregistrer les paramètres", command=self.save_planning_parameters, bootstyle="success").pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="🔄 Recharger", command=self.refresh_parameters_view, bootstyle="info").pack(side="left")

        self.refresh_parameters_view()

    def refresh_parameters_view(self):
        self.setting_work_days.delete(0, "end")
        self.setting_slot_times.delete(0, "end")
        self.setting_slot_duration.delete(0, "end")

        self.setting_work_days.insert(0, ", ".join(str(d) for d in SchoolSettingsService.get_working_days()))
        self.setting_slot_times.insert(0, ", ".join(t.strftime("%H:%M") for t in SchoolSettingsService.get_slot_times()))
        self.setting_slot_duration.insert(0, str(SchoolSettingsService.get_slot_duration_minutes()))

    def save_planning_parameters(self):
        work_days = self.setting_work_days.get().strip()
        slot_times = self.setting_slot_times.get().strip()
        slot_duration = self.setting_slot_duration.get().strip()
        try:
            SchoolSettingsService.set_planning_settings(work_days, slot_times, slot_duration)
            messagebox.showinfo("Succès", "Paramètres planification enregistrés.")
            self.refresh_parameters_view()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))
