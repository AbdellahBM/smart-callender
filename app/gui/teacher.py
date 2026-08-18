import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from app.gui.simple_date_entry import SimpleDateEntry
from tkinter import messagebox
from app.gui.schedule_ui import ScheduleFrame
from app.models import Reservation, Indisponibilite, Salle
from app.extensions import db
from app.services.room_service import get_free_salles
from app.services.settings_service import SchoolSettingsService
from datetime import datetime, date

class TeacherDashboard(ttk.Frame):
    def __init__(self, parent, controller, user):
        super().__init__(parent)
        self.controller = controller
        self.user = user
        
        # Header
        header = ttk.Frame(self, bootstyle="info", padding=10)
        header.pack(fill="x")
        ttk.Label(header, text=f"Espace Enseignant: {user.nom} {user.prenom}", font=("Helvetica", 14, "bold"), bootstyle="inverse-info").pack(side="left")
        ttk.Button(header, text="Déconnexion", command=controller.logout, bootstyle="secondary").pack(side="right")
        
        # Tabs
        self.notebook = ttk.Notebook(self, padding=10)
        self.notebook.pack(expand=True, fill="both")
        
        self.tab_planning = ttk.Frame(self.notebook, padding=10)
        self.tab_reservations = ttk.Frame(self.notebook, padding=10)
        self.tab_search = ttk.Frame(self.notebook, padding=10)
        self.tab_indispos = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_planning, text="📅 Mon Planning")
        self.notebook.add(self.tab_reservations, text="✍️ Réserver")
        self.notebook.add(self.tab_search, text="🔍 Trouver Salle")
        self.notebook.add(self.tab_indispos, text="⛔ Indisponibilités")
        
        self.setup_planning()
        self.setup_reservations()
        self.setup_search()
        self.setup_indispos()

    def setup_planning(self):
        ScheduleFrame(self.tab_planning, self.controller, role="enseignant", filter_id=self.user.id).pack(fill="both", expand=True)

    def setup_reservations(self):
        # Formulaire
        form_frame = ttk.Labelframe(self.tab_reservations, text="Nouvelle Demande", padding=15, bootstyle="info")
        form_frame.pack(fill="x", pady=(0, 20))
        
        grid_opts = {'padx': 10, 'pady': 10}
        
        ttk.Label(form_frame, text="Date (JJ/MM/AAAA):").grid(row=0, column=0, **grid_opts)
        self.res_date = SimpleDateEntry(form_frame, default_date=date.today(), width=12, bootstyle="info")
        self.res_date.grid(row=0, column=1, **grid_opts)
        
        ttk.Label(form_frame, text="Début (HH:MM):").grid(row=0, column=2, **grid_opts)
        self.res_start = ttk.Entry(form_frame, width=10)
        self.res_start.grid(row=0, column=3, **grid_opts)
        self.res_start.insert(0, "08:30")

        ttk.Label(form_frame, text="Fin (HH:MM):").grid(row=0, column=4, **grid_opts)
        self.res_end = ttk.Entry(form_frame, width=10)
        self.res_end.grid(row=0, column=5, **grid_opts)
        self.res_end.insert(0, "10:00")
        
        ttk.Label(form_frame, text="Salle:").grid(row=1, column=0, **grid_opts)
        self.res_salle = ttk.Combobox(form_frame, values=[f"{s.id}: {s.nom}" for s in db.session.query(Salle).all()], width=20)
        self.res_salle.grid(row=1, column=1, **grid_opts)
        
        ttk.Label(form_frame, text="Motif:").grid(row=1, column=2, **grid_opts)
        self.res_motif = ttk.Entry(form_frame, width=30)
        self.res_motif.grid(row=1, column=3, columnspan=3, **grid_opts, sticky="we")
        
        ttk.Button(form_frame, text="Envoyer demande", command=self.submit_reservation, bootstyle="success").grid(row=2, column=0, columnspan=6, pady=10)
        
        # Liste
        list_frame = ttk.Labelframe(self.tab_reservations, text="Mes Demandes", padding=10, bootstyle="secondary")
        list_frame.pack(fill="both", expand=True)
        
        self.tree_res = ttk.Treeview(list_frame, columns=("date", "heure", "salle", "statut"), show="headings", bootstyle="info")
        for col in ["Date", "Heure", "Salle", "Statut"]: self.tree_res.heading(col.lower(), text=col)
        self.tree_res.pack(fill="both", expand=True)
        self.refresh_reservations()

    def _parse_date(self, s):
        s = s.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError("Date invalide (utilisez JJ/MM/AAAA)")

    def submit_reservation(self):
        try:
            date_str = self.res_date.get()
            date_obj = self._parse_date(date_str)
            start = datetime.strptime(self.res_start.get(), "%H:%M").time()
            end = datetime.strptime(self.res_end.get(), "%H:%M").time()
            SchoolSettingsService.validate_teacher_reservation_request(
                self.user.id,
                date_obj,
                start,
                end,
            )
            salle_str = self.res_salle.get()
            if not salle_str: raise ValueError("Choisir une salle")
            salle_id = int(salle_str.split(":")[0])
            
            res = Reservation(
                enseignant_id=self.user.id,
                salle_id=salle_id,
                date_reservation=date_obj,
                heure_debut=start,
                heure_fin=end,
                motif=self.res_motif.get()
            )
            db.session.add(res)
            db.session.commit()
            messagebox.showinfo("Succès", "Demande envoyée")
            self.refresh_reservations()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def refresh_reservations(self):
        for row in self.tree_res.get_children():
            self.tree_res.delete(row)
        res_list = db.session.query(Reservation).filter_by(enseignant_id=self.user.id).all()
        for r in res_list:
            self.tree_res.insert("", "end", values=(r.date_reservation, f"{r.heure_debut}-{r.heure_fin}", r.salle.nom, r.statut))

    def setup_search(self):
        ctrl = ttk.Labelframe(self.tab_search, text="Filtres", padding=15)
        ctrl.pack(fill="x", pady=(0, 20))
        
        ttk.Label(ctrl, text="Date (JJ/MM/AAAA):").pack(side="left", padx=5)
        self.search_date = SimpleDateEntry(ctrl, default_date=date.today(), width=12, bootstyle="primary")
        self.search_date.pack(side="left", padx=5)
        
        ttk.Label(ctrl, text="Début:").pack(side="left", padx=5)
        self.search_start = ttk.Entry(ctrl, width=8)
        self.search_start.pack(side="left", padx=5)
        self.search_start.insert(0, "08:30")
        
        ttk.Label(ctrl, text="Fin:").pack(side="left", padx=5)
        self.search_end = ttk.Entry(ctrl, width=8)
        self.search_end.pack(side="left", padx=5)
        self.search_end.insert(0, "10:00")
        
        ttk.Button(ctrl, text="🔍 Rechercher", command=self.do_search, bootstyle="primary").pack(side="left", padx=20)
        
        self.tree_search = ttk.Treeview(self.tab_search, columns=("nom", "capacite", "type"), show="headings", bootstyle="primary")
        self.tree_search.heading("nom", text="Nom")
        self.tree_search.heading("capacite", text="Capacité")
        self.tree_search.heading("type", text="Type")
        self.tree_search.pack(expand=True, fill="both")
    
    def do_search(self):
        for row in self.tree_search.get_children():
            self.tree_search.delete(row)
        try:
            day_date = self._parse_date(self.search_date.get())
            start = datetime.strptime(self.search_start.get().strip(), "%H:%M").time()
            end = datetime.strptime(self.search_end.get().strip(), "%H:%M").time()
            salles = get_free_salles(day_date, start, end)
            for s in salles:
                self.tree_search.insert("", "end", values=(s.nom, s.capacite, s.type_salle))
            if not salles:
                self.tree_search.insert("", "end", values=("— Aucune salle libre —", "", ""))
        except Exception as e:
            messagebox.showerror("Erreur", f"Saisie invalide : {e}")

    def setup_indispos(self):
        form_frame = ttk.Labelframe(self.tab_indispos, text="Ajouter Indisponibilité Récurrente", padding=15, bootstyle="danger")
        form_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(form_frame, text="Jour (0=Lundi):").pack(side="left", padx=5)
        self.ind_jour = ttk.Combobox(form_frame, values=["0 (Lundi)", "1 (Mardi)", "2 (Mercredi)", "3 (Jeudi)", "4 (Vendredi)"], width=15)
        self.ind_jour.pack(side="left", padx=5)
        
        ttk.Label(form_frame, text="Début:").pack(side="left", padx=5)
        self.ind_start = ttk.Entry(form_frame, width=8)
        self.ind_start.pack(side="left", padx=5)
        self.ind_start.insert(0, "08:00")
        
        ttk.Label(form_frame, text="Fin:").pack(side="left", padx=5)
        self.ind_end = ttk.Entry(form_frame, width=8)
        self.ind_end.pack(side="left", padx=5)
        self.ind_end.insert(0, "12:00")
        
        ttk.Button(form_frame, text="Ajouter", command=self.add_indispo, bootstyle="danger").pack(side="left", padx=20)
        
        self.tree_ind = ttk.Treeview(self.tab_indispos, columns=("jour", "heure"), show="headings", bootstyle="danger")
        self.tree_ind.heading("jour", text="Jour")
        self.tree_ind.heading("heure", text="Heure")
        self.tree_ind.pack(expand=True, fill="both")
        self.refresh_indispos()

    def add_indispo(self):
        try:
            jour_str = self.ind_jour.get()
            jour = int(jour_str.split()[0])
            start = datetime.strptime(self.ind_start.get(), "%H:%M").time()
            end = datetime.strptime(self.ind_end.get(), "%H:%M").time()
            
            ind = Indisponibilite(
                enseignant_id=self.user.id,
                jour_semaine=jour,
                heure_debut=start,
                heure_fin=end
            )
            db.session.add(ind)
            db.session.commit()
            self.refresh_indispos()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def refresh_indispos(self):
        for row in self.tree_ind.get_children():
            self.tree_ind.delete(row)
        inds = db.session.query(Indisponibilite).filter_by(enseignant_id=self.user.id).all()
        for i in inds:
            self.tree_ind.insert("", "end", values=(i.jour_semaine, f"{i.heure_debut}-{i.heure_fin}"))


