import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from app.gui.simple_date_entry import SimpleDateEntry
from tkinter import messagebox
from app.gui.schedule_ui import ScheduleFrame
from app.models import Salle
from app.extensions import db
from app.services.room_service import get_free_salles
from datetime import datetime, date

class StudentDashboard(ttk.Frame):
    def __init__(self, parent, controller, user):
        super().__init__(parent)
        self.controller = controller
        self.user = user
        
        # Header
        header = ttk.Frame(self, bootstyle="success", padding=10)
        header.pack(fill="x")
        ttk.Label(header, text=f"Espace Étudiant: {user.nom} {user.prenom}", font=("Helvetica", 14, "bold"), bootstyle="inverse-success").pack(side="left")
        ttk.Button(header, text="Déconnexion", command=controller.logout, bootstyle="secondary").pack(side="right")
        
        # Tabs
        self.notebook = ttk.Notebook(self, padding=10)
        self.notebook.pack(expand=True, fill="both")
        
        self.tab_planning = ttk.Frame(self.notebook, padding=10)
        self.tab_search = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_planning, text="📅 Mon Planning")
        self.notebook.add(self.tab_search, text="🔍 Trouver une salle")
        
        self.setup_planning()
        self.setup_search()

    def setup_planning(self):
        # Affiche le planning du groupe de l'étudiant
        group_id = self.user.groupe_id
        if group_id:
            ScheduleFrame(self.tab_planning, self.controller, role="etudiant", filter_id=group_id).pack(fill="both", expand=True)
        else:
            ttk.Label(self.tab_planning, text="Vous n'êtes assigné à aucun groupe.", font=("Helvetica", 12), bootstyle="warning").pack(pady=50)

    def setup_search(self):
        ctrl = ttk.Labelframe(self.tab_search, text="Recherche rapide", padding=15, bootstyle="success")
        ctrl.pack(fill="x", pady=(0, 20))
        
        ttk.Label(ctrl, text="Date (JJ/MM/AAAA):").pack(side="left", padx=5)
        self.search_date = SimpleDateEntry(ctrl, default_date=date.today(), width=12, bootstyle="success")
        self.search_date.pack(side="left", padx=5)
        
        ttk.Label(ctrl, text="Début:").pack(side="left", padx=5)
        self.search_start = ttk.Entry(ctrl, width=8)
        self.search_start.pack(side="left", padx=5)
        self.search_start.insert(0, "08:30")
        
        ttk.Label(ctrl, text="Fin:").pack(side="left", padx=5)
        self.search_end = ttk.Entry(ctrl, width=8)
        self.search_end.pack(side="left", padx=5)
        self.search_end.insert(0, "10:00")
        
        ttk.Button(ctrl, text="🔍 Rechercher", command=self.do_search, bootstyle="success").pack(side="left", padx=20)
        
        self.tree_search = ttk.Treeview(self.tab_search, columns=("nom", "capacite", "type"), show="headings", bootstyle="success")
        self.tree_search.heading("nom", text="Nom")
        self.tree_search.heading("capacite", text="Capacité")
        self.tree_search.heading("type", text="Type")
        self.tree_search.pack(expand=True, fill="both")

    def _parse_date(self, s):
        s = s.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError("Date invalide (utilisez JJ/MM/AAAA)")

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
