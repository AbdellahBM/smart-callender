import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from app.services.resource_service import ResourceService
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
        
        self.notebook.add(self.tab_dashboard, text="Tableau de bord")
        self.notebook.add(self.tab_planning, text="📅 Planning")
        self.notebook.add(self.tab_reservations, text="🔔 Réservations")
        self.notebook.add(self.tab_salles, text="🏢 Salles")
        self.notebook.add(self.tab_enseignants, text="👨‍🏫 Enseignants")
        self.notebook.add(self.tab_groupes, text="🎓 Groupes")
        self.notebook.add(self.tab_parametres, text="⚙️ Paramètres")
        
        self.setup_dashboard()
        self.setup_reservations()
        self.setup_salles()
        self.setup_enseignants()
        self.setup_groupes()
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
        if nom:
            ResourceService.create_salle({"nom": nom, "capacite": 30, "type_salle": "cours"})
            self.refresh_salles()

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
        self.tree_groupes = ttk.Treeview(self.tab_groupes, columns=("id", "nom", "effectif"), show="headings", bootstyle="warning")
        self.tree_groupes.heading("id", text="ID")
        self.tree_groupes.heading("nom", text="Nom")
        self.tree_groupes.heading("effectif", text="Effectif")
        self.tree_groupes.column("id", width=50)
        self.tree_groupes.pack(expand=True, fill="both")
        self.refresh_groupes()

    def refresh_groupes(self):
        for row in self.tree_groupes.get_children():
            self.tree_groupes.delete(row)
        for g in ResourceService.get_all_groupes():
            self.tree_groupes.insert("", "end", values=(g.id, g.nom, g.effectif))

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
