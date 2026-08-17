"""
app/gui/schedule_ui.py - Grille d'emploi du temps (séances + réservations acceptées)

Affiche les séances récurrentes et, pour l'enseignant (et l'admin filtré par prof),
les réservations de salle acceptées afin que le prof les prenne en compte.
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from app.services.scheduler import SchedulerService
from app.extensions import db
from app.models import Seance, Reservation
from app.services.resource_service import ResourceService
from app.services.settings_service import SchoolSettingsService
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class ScheduleFrame(ttk.Frame):
    def __init__(self, parent, controller, role="admin", filter_id=None):
        super().__init__(parent)
        self.controller = controller
        self.role = role
        self.filter_id = filter_id # ID du prof ou groupe si non-admin
        
        # Controls Toolbar
        ctrl_frame = ttk.Frame(self, padding=10)
        ctrl_frame.pack(fill="x")
        
        if self.role == "admin":
            ttk.Button(ctrl_frame, text="⚡ Générer Auto", command=self.generate_schedule, bootstyle="primary").pack(side="left", padx=5)
        
        ttk.Button(ctrl_frame, text="🔄 Rafraîchir", command=self.load_schedule, bootstyle="info-outline").pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="📄 Exporter PDF", command=self.export_pdf, bootstyle="secondary").pack(side="left", padx=5)

        # Filters (pour admin)
        if self.role == "admin":
            enseignants = ResourceService.get_all_enseignants()
            self._prof_display_to_id = {"Tous": None}
            prof_names = ["Tous"]
            for u in enseignants:
                label = f"{u.nom} {u.prenom}"
                prof_names.append(label)
                self._prof_display_to_id[label] = u.id
                
            ttk.Label(ctrl_frame, text="Filtre Prof:").pack(side="left", padx=(20, 5))
            self.combo_profs = ttk.Combobox(ctrl_frame, values=prof_names, state="readonly", width=25)
            self.combo_profs.current(0)
            self.combo_profs.pack(side="left")
            self.combo_profs.bind("<<ComboboxSelected>>", self.load_schedule)

        # Grid view
        # Use primary bootstyle for header color
        self.tree = ttk.Treeview(self, columns=("day", "time", "matiere", "groupe", "salle", "prof"), show="headings", bootstyle="primary")
        
        cols = ["Jour", "Heure", "Matière", "Groupe", "Salle", "Enseignant"]
        keys = ["day", "time", "matiere", "groupe", "salle", "prof"]
        
        for k, c in zip(keys, cols):
            self.tree.heading(k, text=c)
        
        self.tree.column("day", width=80)
        self.tree.column("time", width=120)
        self.tree.column("matiere", width=200)
        self.tree.column("groupe", width=100)
        self.tree.column("salle", width=80)
        self.tree.column("prof", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.load_schedule()

    def generate_schedule(self):
        try:
            msg = SchedulerService.generate_schedule()
            messagebox.showinfo("Génération", msg)
            self.load_schedule()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def load_schedule(self, event=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Séances récurrentes
        seances = self.get_seances_data()
        for s in seances:
            jour = SchoolSettingsService.get_day_name(s.jour_semaine)
            heure = f"{s.heure_debut.strftime('%H:%M')} - {s.heure_fin.strftime('%H:%M')}"
            matiere = s.matiere.nom if s.matiere else "?"
            groupe = s.groupe.nom if s.groupe else "?"
            salle = s.salle.nom if s.salle else "?"
            prof = s.enseignant.nom if s.enseignant else "?"
            self.tree.insert("", "end", values=(jour, heure, matiere, groupe, salle, prof))

        # Réservations acceptées (pour prof et admin filtré par prof)
        reservations = self.get_reservations_data()
        for r in reservations:
            jour = r.date_reservation.strftime("%d/%m/%Y")
            heure = f"{r.heure_debut.strftime('%H:%M')} - {r.heure_fin.strftime('%H:%M')}"
            matiere = "Réservation" + (f" ({r.motif})" if r.motif else "")
            groupe = "—"
            salle = r.salle.nom if r.salle else "?"
            prof = r.demandeur.nom if r.demandeur else "?"
            self.tree.insert("", "end", values=(jour, heure, matiere, groupe, salle, prof))

    def get_seances_data(self):
        query = db.session.query(Seance).filter(Seance.heure_debut != None).order_by(Seance.jour_semaine, Seance.heure_debut)
        if self.role == "enseignant":
            query = query.filter(Seance.enseignant_id == self.filter_id)
        elif self.role == "etudiant":
            query = query.filter(Seance.groupe_id == self.filter_id)
        elif self.role == "admin" and hasattr(self, "_prof_display_to_id"):
            selected = self.combo_profs.get()
            prof_id = self._prof_display_to_id.get(selected)
            if prof_id is not None:
                query = query.filter(Seance.enseignant_id == prof_id)
        return query.all()

    def get_reservations_data(self):
        """Réservations acceptées à afficher dans le planning."""
        query = db.session.query(Reservation).filter(Reservation.statut == "acceptee").order_by(
            Reservation.date_reservation, Reservation.heure_debut
        )
        if self.role == "enseignant":
            query = query.filter(Reservation.enseignant_id == self.filter_id)
        elif self.role == "etudiant":
            # L'étudiant voit toutes les réservations acceptées (salles réservées à telle date)
            pass
        elif self.role == "admin":
            if not hasattr(self, "_prof_display_to_id"):
                return []
            selected = self.combo_profs.get()
            prof_id = self._prof_display_to_id.get(selected)
            if prof_id is not None:
                query = query.filter(Reservation.enseignant_id == prof_id)
            else:
                return []  # "Tous" : pas d'affichage des résa dans la grille
        return query.all()

    def export_pdf(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not filename:
            return
            
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Emploi du Temps")
        
        c.setFont("Helvetica", 10)
        y = height - 80
        
        # Headers
        c.drawString(50, y, "Jour")
        c.drawString(120, y, "Heure")
        c.drawString(200, y, "Matière")
        c.drawString(320, y, "Groupe")
        c.drawString(400, y, "Salle")
        c.drawString(480, y, "Prof")
        y -= 20
        c.line(50, y+15, 550, y+15)
        
        seances = self.get_seances_data()
        reservations = self.get_reservations_data()

        for s in seances:
            if y < 50:
                c.showPage()
                y = height - 50
            jour = SchoolSettingsService.get_day_name(s.jour_semaine)
            heure = f"{s.heure_debut.strftime('%H:%M')}-{s.heure_fin.strftime('%H:%M')}"
            matiere = (s.matiere.nom if s.matiere else "?")[:20]
            groupe = s.groupe.nom if s.groupe else "?"
            salle = s.salle.nom if s.salle else "?"
            prof = s.enseignant.nom if s.enseignant else "?"
            c.drawString(50, y, jour)
            c.drawString(120, y, heure)
            c.drawString(200, y, matiere)
            c.drawString(320, y, groupe)
            c.drawString(400, y, salle)
            c.drawString(480, y, prof)
            y -= 15

        for r in reservations:
            if y < 50:
                c.showPage()
                y = height - 50
            jour = r.date_reservation.strftime("%d/%m/%Y")
            heure = f"{r.heure_debut.strftime('%H:%M')}-{r.heure_fin.strftime('%H:%M')}"
            matiere = ("Réservation" + (f" ({r.motif})" if r.motif else ""))[:20]
            groupe = "—"
            salle = r.salle.nom if r.salle else "?"
            prof = r.demandeur.nom if r.demandeur else "?"
            c.drawString(50, y, jour)
            c.drawString(120, y, heure)
            c.drawString(200, y, matiere)
            c.drawString(320, y, groupe)
            c.drawString(400, y, salle)
            c.drawString(480, y, prof)
            y -= 15

        c.save()
        messagebox.showinfo("Export", f"PDF sauvegardé sous {filename}")
