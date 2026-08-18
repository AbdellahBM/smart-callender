import csv
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import BooleanVar, filedialog, messagebox, simpledialog
from datetime import date, datetime
from app.services.resource_service import ResourceService
from app.services.auth_service import AuthService
from app.services.admin_audit_service import AdminAuditService
from app.extensions import db
from app.models import (
    AcademicCycle,
    AcademicLevel,
    AcademicYear,
    Filiere,
    Groupe,
    Reservation,
    Utilisateur,
)
from app.services.room_service import get_occupied_salle_ids
from app.services.settings_service import SchoolSettingsService
from app.services.academic_structure_service import AcademicStructureService

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
        self.tab_organisation = ttk.Frame(self.notebook, padding=10)
        self.tab_planning = ttk.Frame(self.notebook, padding=10)
        self.tab_parametres = ttk.Frame(self.notebook, padding=10)
        self.tab_utilisateurs = ttk.Frame(self.notebook, padding=10)
        self.tab_classes = ttk.Frame(self.notebook, padding=10)
        self.tab_audit = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_dashboard, text="Tableau de bord")
        self.notebook.add(self.tab_planning, text="📅 Planning")
        self.notebook.add(self.tab_reservations, text="🔔 Réservations")
        self.notebook.add(self.tab_salles, text="🏢 Salles")
        self.notebook.add(self.tab_enseignants, text="👨‍🏫 Enseignants")
        self.notebook.add(self.tab_groupes, text="🎓 Groupes")
        self.notebook.add(self.tab_organisation, text="🏫 Organisation scolaire")
        self.notebook.add(self.tab_utilisateurs, text="👥 Utilisateurs")
        self.notebook.add(self.tab_classes, text="📘 Filières / Matières")
        self.notebook.add(self.tab_parametres, text="⚙️ Paramètres")
        self.notebook.add(self.tab_audit, text="🧾 Journal")
        
        self.setup_dashboard()
        self.setup_reservations()
        self.setup_salles()
        self.setup_enseignants()
        self.setup_groupes()
        self.setup_organisation()
        self.setup_utilisateurs()
        self.setup_classes()
        self.setup_parametres()
        self.setup_audit()
        
        # Charger le module planning
        from app.gui.schedule_ui import ScheduleFrame
        ScheduleFrame(self.tab_planning, controller).pack(fill="both", expand=True)

    def _selected_tree_values(self, tree):
        selected = tree.selection()
        if not selected:
            return None
        return tree.item(selected[0], "values")

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

    def _record_admin_action(self, action, entity_type=None, entity_id=None, details=None):
        if AdminAuditService.log_action(self.user, action, entity_type=entity_type, entity_id=entity_id, details=details):
            if hasattr(self, "tree_audit"):
                try:
                    self.refresh_audit()
                except Exception:
                    pass

    # --- Gestion Réservations ---
    def setup_reservations(self):
        # Toolbar
        btn_frame = ttk.Frame(self.tab_reservations)
        btn_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(btn_frame, text="Statut:").pack(side="left", padx=(0, 6))
        self.reservation_status_filter = ttk.Combobox(
            btn_frame,
            values=["Toutes", "En attente", "Acceptée", "Refusée"],
            state="readonly",
            width=14,
        )
        self.reservation_status_filter.set("Toutes")
        self.reservation_status_filter.pack(side="left")
        self.reservation_status_filter.bind("<<ComboboxSelected>>", lambda *_: self.refresh_reservations())
        
        ttk.Button(btn_frame, text="✅ Valider", command=self.valider_reservation, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Refuser", command=self.refuser_reservation, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="↩️ Remettre en attente", command=self.reinitialiser_reservation, bootstyle="warning").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📝 Modifier", command=self.edit_selected_reservation, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Supprimer", command=self.delete_selected_reservation, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="➕ Ajouter", command=self.add_reservation_direct, bootstyle="success").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Rafraîchir", command=self.refresh_reservations, bootstyle="info-outline").pack(side="left", padx=5)
        
        cols = ("id", "prof", "enseignant_id", "date", "heure", "salle", "statut", "motif", "commentaire_admin")
        self.tree_res = ttk.Treeview(self.tab_reservations, columns=cols, show="headings", bootstyle="primary")
        for col in cols: self.tree_res.heading(col, text=col.capitalize())
        self.tree_res.column("id", width=50)
        self.tree_res.column("enseignant_id", width=30)
        self.tree_res.pack(expand=True, fill="both")
        
        self.refresh_reservations()

    def refresh_reservations(self):
        for row in self.tree_res.get_children():
            self.tree_res.delete(row)
        
        query = db.session.query(Reservation).order_by(Reservation.date_reservation, Reservation.heure_debut)
        status_filter = self.reservation_status_filter.get()
        if status_filter == "En attente":
            query = query.filter_by(statut="en_attente")
        elif status_filter == "Acceptée":
            query = query.filter_by(statut="acceptee")
        elif status_filter == "Refusée":
            query = query.filter_by(statut="refusee")
        res_list = query.all()

        for r in res_list:
            prof_nom = r.demandeur.nom if r.demandeur else "?"
            salle_nom = r.salle.nom if r.salle else "?"
            # Tag rows based on status? Treeview tags need configuration, keeping simple for now
            self.tree_res.insert(
                "",
                "end",
                values=(
                    r.id,
                    prof_nom,
                    r.enseignant_id,
                    r.date_reservation.strftime("%d/%m/%Y") if r.date_reservation else "",
                    f"{r.heure_debut.strftime('%H:%M')}-{r.heure_fin.strftime('%H:%M')}",
                    salle_nom,
                    r.statut,
                    r.motif or "",
                    r.commentaire_admin or "",
                ),
            )

    def get_selected_reservation(self):
        selected = self.tree_res.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réservation.")
            return None
        item = self.tree_res.item(selected[0])
        return item['values'][0]

    def _parse_date(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("La date est obligatoire.")
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
        raise ValueError("Date invalide. Format attendu: JJ/MM/AAAA.")

    def _parse_time(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("L'heure est obligatoire.")
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                pass
        raise ValueError("Heure invalide. Format attendu: HH:MM.")

    def _extract_id(self, raw, label):
        try:
            return int(str(raw).split(":")[0].strip())
        except (ValueError, IndexError):
            raise ValueError(f"{label} invalide.")

    def _set_reservation_status(self, reservation_id, statut, commentaire_admin=None):
        res = db.session.get(Reservation, reservation_id)
        if not res:
            return False
        if statut == "acceptee" and res.statut != "acceptee":
            occupied = get_occupied_salle_ids(res.date_reservation, res.heure_debut, res.heure_fin)
            if res.salle_id in occupied:
                raise ValueError(
                    "La salle est déjà occupée pour ce créneau (emploi du temps ou autre réservation acceptée)."
                )
        res.statut = statut
        if commentaire_admin is not None:
            res.commentaire_admin = commentaire_admin.strip() or None
        db.session.commit()
        return True

    def valider_reservation(self):
        res_id = self.get_selected_reservation()
        if res_id:
            try:
                comment = simpledialog.askstring("Valider réservation", "Commentaire admin (optionnel):")
                if self._set_reservation_status(res_id, "acceptee", comment):
                    messagebox.showinfo("Succès", "Réservation acceptée.")
                    self._record_admin_action("reservation.approved", "reservation", res_id, comment or "ok")
                    self.refresh_reservations()
            except Exception as exc:
                messagebox.showerror("Erreur", str(exc))

    def refuser_reservation(self):
        res_id = self.get_selected_reservation()
        if res_id:
            try:
                comment = simpledialog.askstring("Refuser réservation", "Raison du refus :")
                if comment is None:
                    return
                if self._set_reservation_status(res_id, "refusee", comment):
                    messagebox.showinfo("Succès", "Réservation refusée.")
                    self._record_admin_action("reservation.rejected", "reservation", res_id, comment or "ok")
                    self.refresh_reservations()
            except Exception as exc:
                messagebox.showerror("Erreur", str(exc))

    def reinitialiser_reservation(self):
        res_id = self.get_selected_reservation()
        if res_id:
            try:
                if self._set_reservation_status(res_id, "en_attente", None):
                    messagebox.showinfo("Succès", "Statut remis en attente.")
                    self._record_admin_action("reservation.reset", "reservation", res_id, "Remettre en attente")
                    self.refresh_reservations()
            except Exception as exc:
                messagebox.showerror("Erreur", str(exc))

    def delete_selected_reservation(self):
        res_id = self.get_selected_reservation()
        if not res_id:
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cette réservation ?"):
            return
        res = db.session.get(Reservation, res_id)
        if not res:
            messagebox.showerror("Erreur", "Réservation introuvable.")
            return
        db.session.delete(res)
        db.session.commit()
        messagebox.showinfo("Succès", "Réservation supprimée.")
        self._record_admin_action("reservation.deleted", "reservation", res_id, f"Salle {res.salle_id} / Enseignant {res.enseignant_id}")
        self.refresh_reservations()

    def edit_selected_reservation(self):
        res_id = self.get_selected_reservation()
        if not res_id:
            return

        res = db.session.get(Reservation, res_id)
        if not res:
            messagebox.showerror("Erreur", "Réservation introuvable.")
            return

        enseignants = AuthService.get_all()
        enseignant_opts = [f"{u.id}: {u.nom} {u.prenom} ({u.email})" for u in enseignants if u.role == "enseignant"]
        if not enseignant_opts:
            messagebox.showerror("Erreur", "Aucun enseignant disponible.")
            return
        enseignant_input = simpledialog.askstring(
            "Modifier réservation",
            f"Enseignant (id): {', '.join(enseignant_opts)}",
            initialvalue=f"{res.enseignant_id}: {res.demandeur.nom if res.demandeur else 'utilisateur'}",
        )
        if enseignant_input is None:
            return

        salle_opts = [f"{s.id}: {s.nom}" for s in ResourceService.get_all_salles()]
        if not salle_opts:
            messagebox.showerror("Erreur", "Aucune salle disponible.")
            return
        salle_input = simpledialog.askstring(
            "Modifier réservation",
            f"Salle (id): {', '.join(salle_opts)}",
            initialvalue=f"{res.salle_id}: {res.salle.nom if res.salle else ''}",
        )
        if salle_input is None:
            return

        date_input = simpledialog.askstring(
            "Modifier réservation",
            "Date (JJ/MM/AAAA):",
            initialvalue=res.date_reservation.strftime('%d/%m/%Y') if res.date_reservation else "",
        )
        if date_input is None:
            return

        heure_debut_input = simpledialog.askstring(
            "Modifier réservation",
            "Heure début (HH:MM):",
            initialvalue=res.heure_debut.strftime('%H:%M') if res.heure_debut else "",
        )
        if heure_debut_input is None:
            return

        heure_fin_input = simpledialog.askstring(
            "Modifier réservation",
            "Heure fin (HH:MM):",
            initialvalue=res.heure_fin.strftime('%H:%M') if res.heure_fin else "",
        )
        if heure_fin_input is None:
            return

        motif_input = simpledialog.askstring("Modifier réservation", "Motif:", initialvalue=res.motif or "")
        if motif_input is None:
            return

        commentaire_input = simpledialog.askstring(
            "Modifier réservation",
            "Commentaire admin:",
            initialvalue=res.commentaire_admin or "",
        )
        if commentaire_input is None:
            return

        statut_input = simpledialog.askstring("Modifier réservation", "Statut (en_attente/acceptee/refusee):", initialvalue=res.statut)
        if statut_input is None:
            return
        statut_input = statut_input.strip().lower()
        if statut_input not in {"en_attente", "acceptee", "refusee"}:
            messagebox.showerror("Erreur", "Statut invalide.")
            return

        try:
            date_reservation = self._parse_date(date_input)
            heure_debut = self._parse_time(heure_debut_input)
            heure_fin = self._parse_time(heure_fin_input)
            if heure_debut >= heure_fin:
                messagebox.showerror("Erreur", "L'heure de fin doit être après l'heure de début.")
                return
            enseignant_id = self._extract_id(enseignant_input, "Enseignant")
            salle_id = self._extract_id(salle_input, "Salle")

            res.enseignant_id = enseignant_id
            res.salle_id = salle_id
            res.date_reservation = date_reservation
            res.heure_debut = heure_debut
            res.heure_fin = heure_fin
            res.motif = motif_input
            res.commentaire_admin = commentaire_input.strip() or None

            if statut_input == "acceptee" and res.statut != "acceptee":
                occupied = get_occupied_salle_ids(date_reservation, heure_debut, heure_fin)
                if salle_id in occupied:
                    messagebox.showerror(
                        "Conflit",
                        "Cette salle est déjà occupée sur ce créneau. Réservation non modifiée."
                    )
                    return

            res.statut = statut_input
            db.session.commit()
            self._record_admin_action(
                "reservation.updated",
                "reservation",
                res_id,
                f"enseignant={enseignant_id}, salle={salle_id}, date={date_reservation}, {heure_debut}-{heure_fin}, statut={statut_input}"
            )
            self.refresh_reservations()
            messagebox.showinfo("Succès", "Réservation mise à jour.")
        except Exception as exc:
            db.session.rollback()
            messagebox.showerror("Erreur", str(exc))

    def add_reservation_direct(self):
        enseignants = AuthService.get_all()
        enseignant_opts = [f"{u.id}: {u.nom} {u.prenom} ({u.email})" for u in enseignants if u.role == "enseignant"]
        if not enseignant_opts:
            messagebox.showerror("Erreur", "Aucun enseignant disponible.")
            return
        enseignant_input = simpledialog.askstring("Ajouter une réservation", f"Enseignant (id): {', '.join(enseignant_opts)}")
        if enseignant_input is None:
            return
        salles = ResourceService.get_all_salles()
        salle_opts = [f"{s.id}: {s.nom}" for s in salles]
        if not salle_opts:
            messagebox.showerror("Erreur", "Aucune salle disponible.")
            return
        salle_input = simpledialog.askstring("Ajouter une réservation", f"Salle (id): {', '.join(salle_opts)}")
        if salle_input is None:
            return
        date_input = simpledialog.askstring("Ajouter une réservation", "Date (JJ/MM/AAAA):", initialvalue=datetime.now().strftime('%d/%m/%Y'))
        if date_input is None:
            return
        heure_debut_input = simpledialog.askstring("Ajouter une réservation", "Heure début (HH:MM):", initialvalue="08:30")
        if heure_debut_input is None:
            return
        heure_fin_input = simpledialog.askstring("Ajouter une réservation", "Heure fin (HH:MM):", initialvalue="10:00")
        if heure_fin_input is None:
            return
        motif_input = simpledialog.askstring("Ajouter une réservation", "Motif (optionnel):")
        if motif_input is None:
            return

        try:
            enseignant_id = self._extract_id(enseignant_input, "Enseignant")
            salle_id = self._extract_id(salle_input, "Salle")
            date_reservation = self._parse_date(date_input)
            heure_debut = self._parse_time(heure_debut_input)
            heure_fin = self._parse_time(heure_fin_input)
            if heure_debut >= heure_fin:
                raise ValueError("L'heure de fin doit être après l'heure de début.")

            occupied = get_occupied_salle_ids(date_reservation, heure_debut, heure_fin)
            if salle_id in occupied:
                if not messagebox.askyesno(
                    "Conflit détecté",
                    "La salle est déjà occupée sur ce créneau. Créer quand même la demande en attente ?"
                ):
                    return

            new_reservation = Reservation(
                enseignant_id=enseignant_id,
                salle_id=salle_id,
                date_reservation=date_reservation,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                motif=motif_input,
                statut="en_attente",
            )
            db.session.add(new_reservation)
            db.session.commit()
            self._record_admin_action(
                "reservation.created",
                "reservation",
                new_reservation.id,
                f"enseignant={enseignant_id}, salle={salle_id}, date={date_reservation}, {heure_debut}-{heure_fin}",
            )
            self.refresh_reservations()
            messagebox.showinfo("Succès", "Réservation créée.")
        except Exception as exc:
            db.session.rollback()
            messagebox.showerror("Erreur", str(exc))

    # --- Gestion Salles ---
    def setup_salles(self):
        btn_frame = ttk.Frame(self.tab_salles)
        btn_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_frame, text="+ Ajouter Salle", command=self.add_salle, bootstyle="success").pack(side="left")
        ttk.Button(btn_frame, text="✏️ Modifier", command=self.edit_selected_salle, bootstyle="warning").pack(side="left", padx=5)
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
        salle = ResourceService.create_salle(
            {
                "nom": nom,
                "capacite": capacite,
                "type_salle": type_salle or "cours",
            }
        )
        if salle:
            self._record_admin_action(
                "salle.created",
                "salle",
                salle.id,
                f"nom={salle.nom}, type={salle.type_salle}, capacite={salle.capacite}",
            )
        self.refresh_salles()

    def edit_selected_salle(self):
        values = self._selected_tree_values(self.tree_salles)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez une salle.")
            return

        salle_id = int(values[0])
        nom = simpledialog.askstring("Modifier Salle", "Nom:", initialvalue=str(values[1]).strip())
        if nom is None:
            return
        capacite = simpledialog.askinteger("Modifier Salle", "Capacité:", initialvalue=int(values[3]) if str(values[3]).isdigit() else 30)
        if capacite is None:
            return
        type_salle = simpledialog.askstring("Modifier Salle", "Type (cours, tp, amphi):", initialvalue=str(values[2]).strip())
        if type_salle is None:
            return

        salle = ResourceService.update_salle(
            salle_id,
            {
                "nom": nom,
                "capacite": capacite,
                "type_salle": type_salle,
            },
        )
        if not salle:
            messagebox.showerror("Erreur", "Impossible de modifier la salle.")
            return
        self._record_admin_action(
            "salle.updated",
            "salle",
            salle_id,
            f"nom={nom}, type={type_salle}, capacite={capacite}",
        )
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
        salle_label = str(values[1]).strip()
        if messagebox.askyesno("Confirmer", f"Supprimer la salle {values[1]} ?"):
            if ResourceService.delete_salle(salle_id):
                self._record_admin_action("salle.deleted", "salle", salle_id, f"salle={salle_label}")
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

        btn_frame = ttk.Frame(self.tab_enseignants)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="🧩 Gérer matières", command=self.manage_teacher_matieres_from_list, bootstyle="warning").pack(side="left")

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
        ttk.Button(btn_frame, text="✏️ Modifier", command=self.edit_selected_groupe, bootstyle="warning").pack(side="left", padx=6)
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
        groupe = ResourceService.create_groupe(nom=nom, effectif=effectif, filiere_id=filiere_id)
        self._record_admin_action("groupe.created", "groupe", groupe.id, f"nom={nom}, effectif={effectif}, filiere_id={filiere_id}")
        self.refresh_groupes()

    def edit_selected_groupe(self):
        values = self._selected_tree_values(self.tree_groupes)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un groupe.")
            return

        groupe_id = int(values[0])
        filiere_nom = str(values[3]).strip()
        filieres = ResourceService.get_all_filieres()
        filiere_options = [f"{f.id}: {f.nom}" for f in filieres]
        current_filiere = next((f for f in filieres if f.nom == filiere_nom), None)
        current_filiere_id = current_filiere.id if current_filiere else None

        nom = simpledialog.askstring("Modifier groupe", "Nom:", initialvalue=str(values[1]).strip())
        if nom is None:
            return
        effectif = simpledialog.askinteger("Modifier groupe", "Effectif:", initialvalue=int(values[2]) if str(values[2]).isdigit() else 0)
        if effectif is None:
            return

        if filiere_options:
            choix = simpledialog.askstring(
                "Modifier groupe",
                f"Filière (id): {', '.join(filiere_options)}",
                initialvalue=f"{current_filiere_id}: {filiere_nom}" if current_filiere else "",
            )
            if not choix:
                messagebox.showerror("Erreur", "Une filière est obligatoire.")
                return
            try:
                filiere_id = int(choix.split(\":\")[0].strip())
            except (ValueError, IndexError):
                messagebox.showerror("Erreur", "ID filière invalide.")
                return
        else:
            messagebox.showwarning("Attention", "Aucune filière disponible.")
            return

        groupe = ResourceService.update_groupe(groupe_id, {"nom": nom, "effectif": effectif, "filiere_id": filiere_id})
        if not groupe:
            messagebox.showerror("Erreur", "Impossible de modifier ce groupe.")
            return
        self._record_admin_action(
            "groupe.updated",
            "groupe",
            groupe_id,
            f"nom={nom}, effectif={effectif}, filiere_id={filiere_id}",
        )

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
            groupe_id = int(values[0])
            groupe_label = str(values[1]).strip()
            if ResourceService.delete_groupe(groupe_id):
                self._record_admin_action("groupe.deleted", "groupe", groupe_id, f"nom={groupe_label}")
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
        ttk.Button(btn_frame, text="✏️ Modifier", command=self.edit_selected_user, bootstyle="info").pack(side="left", padx=(6, 0))
        ttk.Button(btn_frame, text="🔑 Réinitialiser mdp", command=self.reset_user_password, bootstyle="secondary").pack(side="left", padx=(6, 0))
        ttk.Button(btn_frame, text="🧩 Matières", command=self.manage_teacher_matieres, bootstyle="secondary").pack(side="left", padx=(6, 0))
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
            user = AuthService.create_user(
                email=data["email"],
                password=data["password"],
                nom=data["nom"],
                prenom=data["prenom"],
                role="enseignant",
            )
            self._record_admin_action("utilisateur.created", "utilisateur", user.id, f"email={user.email}, role=enseignant")
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
            user = AuthService.create_user(
                email=data["email"],
                password=data["password"],
                nom=data["nom"],
                prenom=data["prenom"],
                role="etudiant",
                groupe_id=groupe_id,
            )
            self._record_admin_action("utilisateur.created", "utilisateur", user.id, f"email={user.email}, role=etudiant, groupe_id={groupe_id}")
            self.refresh_utilisateurs()
            self.refresh_groupes()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def _ask_role(self, default_role):
        role = simpledialog.askstring("Modifier un utilisateur", "Rôle (admin/enseignant/etudiant):", initialvalue=default_role)
        if role is None:
            return None
        role = role.strip().lower()
        if role not in Utilisateur.ROLES:
            messagebox.showerror("Erreur", "Rôle invalide.")
            return None
        return role

    def edit_selected_user(self):
        values = self._selected_tree_values(self.tree_users)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un utilisateur.")
            return

        user_id = int(values[0])
        current_role = values[4]
        if user_id == self.user.id:
            messagebox.showwarning("Attention", "Vous ne pouvez pas modifier votre propre compte depuis cette liste.")
            return

        user_entity = AuthService.get_by_id(user_id)
        if not user_entity:
            messagebox.showerror("Erreur", "Utilisateur introuvable.")
            return

        nom = simpledialog.askstring("Modifier un utilisateur", "Nom:", initialvalue=str(values[1]).strip())
        if nom is None:
            return
        prenom = simpledialog.askstring("Modifier un utilisateur", "Prénom:", initialvalue=str(values[2]).strip())
        if prenom is None:
            return
        email = simpledialog.askstring("Modifier un utilisateur", "Email:", initialvalue=str(values[3]).strip())
        if email is None:
            return
        role = self._ask_role(current_role)
        if role is None:
            return

        groupe_id = None
        if role == "etudiant":
            groupes = ResourceService.get_all_groupes()
            options = [f"{g.id}: {g.nom}" for g in groupes]
            if not options:
                messagebox.showwarning("Attention", "Aucun groupe disponible. Créez d'abord un groupe.")
                return
            selected_group = simpledialog.askstring(
                "Groupe étudiant",
                f"Groupe (id): {', '.join(options)}",
                initialvalue=f"{user_entity.groupe_id}: {user_entity.groupe.nom}" if user_entity.groupe_id else "",
            )
            if not selected_group:
                messagebox.showerror("Erreur", "Un groupe est obligatoire pour un étudiant.")
                return
            try:
                groupe_id = int(selected_group.split(\":\")[0].strip())
            except (ValueError, IndexError):
                messagebox.showerror("Erreur", "ID de groupe invalide.")
                return

        try:
            utilisateur = AuthService.update_user(
                user_id=user_id,
                nom=nom,
                prenom=prenom,
                email=email,
                role=role,
                groupe_id=groupe_id,
            )
            if utilisateur is None:
                messagebox.showerror("Erreur", "Impossible de modifier cet utilisateur.")
                return
            self._record_admin_action(
                "utilisateur.updated",
                "utilisateur",
                user_id,
                f"nom={nom}, prenom={prenom}, role={current_role} -> {role}, groupe_id={groupe_id}",
            )
            self.refresh_utilisateurs()
            self.refresh_profs()
            self.refresh_groupes()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def reset_user_password(self):
        values = self._selected_tree_values(self.tree_users)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un utilisateur.")
            return

        user_id = int(values[0])
        if user_id == self.user.id:
            messagebox.showwarning("Attention", "Vous ne pouvez pas réinitialiser votre propre mot de passe ici.")
            return

        new_password = simpledialog.askstring("Réinitialiser le mot de passe", "Nouveau mot de passe:", show="*")
        if not new_password:
            return

        if AuthService.reset_password(user_id, new_password):
            self._record_admin_action("utilisateur.password_reset", "utilisateur", user_id, "Mot de passe réinitialisé par admin")
            messagebox.showinfo("Succès", "Mot de passe mis à jour.")
        else:
            messagebox.showerror("Erreur", "Impossible de modifier le mot de passe.")

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
                self._record_admin_action("utilisateur.deleted", "utilisateur", user_id, f"email={values[3]}")
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
        new_status = not current_status
        if AuthService.set_status(user_id, new_status):
            self._record_admin_action("utilisateur.toggled", "utilisateur", user_id, f"actif={current_status} -> {new_status}")
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
        ttk.Button(btn_frame, text="✏️ Modifier sélection", command=self.edit_selected_class_item, bootstyle="warning").pack(side="left", padx=(6, 0))

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
        filiere = ResourceService.create_filiere(nom=nom, code=code or None)
        self._record_admin_action("filiere.created", "filiere", filiere.id, f"nom={nom}, code={code or ''}")
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
        matiere = ResourceService.create_matiere(nom=nom, code=code, filiere_id=filiere_id)
        self._record_admin_action("matiere.created", "matiere", matiere.id, f"nom={nom}, code={code}, filiere_id={filiere_id}")
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
                self._record_admin_action("filiere.deleted", "filiere", filiere_id, f"nom={selected_value[1]}")
        elif prefix.startswith("m-"):
            matiere_id = int(prefix.replace("m-", ""))
            if messagebox.askyesno("Confirmer", f"Supprimer la matière {selected_value[1]} ?"):
                if not ResourceService.delete_matiere(matiere_id):
                    messagebox.showerror("Erreur", "Suppression impossible (dépendances existantes).")
                    return
                self._record_admin_action("matiere.deleted", "matiere", matiere_id, f"nom={selected_value[1]}")
                self.refresh_groupes()
        self.refresh_classes()
        self.refresh_groupes()

    def edit_selected_class_item(self):
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
            nom = simpledialog.askstring("Modifier une filière", "Nom :", initialvalue=str(selected_value[1]).strip())
            if nom is None:
                return
            code = simpledialog.askstring("Modifier une filière", "Code :", initialvalue=str(selected_value[3]).strip())
            if code is None:
                return
            if not ResourceService.update_filiere(filiere_id, {"nom": nom, "code": code}):
                messagebox.showerror("Erreur", "Impossible de modifier cette filière.")
                return
            self._record_admin_action("filiere.updated", "filiere", filiere_id, f"nom={nom}, code={code}")
            self.refresh_classes()
            self.refresh_groupes()
            return

        if prefix.startswith("m-"):
            matiere_id = int(prefix.replace("m-", ""))
            nom = simpledialog.askstring("Modifier une matière", "Nom :", initialvalue=str(selected_value[1]).strip())
            if nom is None:
                return
            code = simpledialog.askstring("Modifier une matière", "Code :", initialvalue=str(selected_value[3]).strip())
            if code is None:
                return

            if not ResourceService.update_matiere(matiere_id, {"nom": nom, "code": code}):
                messagebox.showerror("Erreur", "Impossible de modifier cette matière.")
                return
            self._record_admin_action("matiere.updated", "matiere", matiere_id, f"nom={nom}, code={code}")
            self.refresh_classes()
            return

    def manage_teacher_matieres_from_list(self):
        values = self._selected_tree_values(self.tree_profs)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un enseignant.")
            return
        user_id = int(values[0])
        self.manage_teacher_matieres(user_id)

    def manage_teacher_matieres(self, user_id_or_self=None):
        if user_id_or_self is None:
            values = self._selected_tree_values(self.tree_users)
            if not values:
                messagebox.showwarning("Attention", "Sélectionnez un utilisateur.")
                return
            user_id = int(values[0])
        else:
            user_id = int(user_id_or_self)

        teacher = AuthService.get_by_id(user_id)
        if not teacher:
            messagebox.showerror("Erreur", "Utilisateur introuvable.")
            return
        if teacher.role != "enseignant":
            messagebox.showwarning("Attention", "Vous pouvez gérer les matières uniquement pour un enseignant.")
            return

        all_matieres = ResourceService.get_all_matieres()
        if not all_matieres:
            messagebox.showwarning("Attention", "Aucune matière disponible.")
            return

        assigned = set(AuthService.get_teacher_matiere_ids(teacher.id))
        options = [f"{m.id}: {m.nom}" for m in all_matieres]
        current = ", ".join(f"{m.id}: {m.nom}" for m in all_matieres if m.id in assigned)

        answer = simpledialog.askstring(
            "Gestion matières enseignant",
            f"Sélectionnez les IDs matières séparés par des virgules.\nActuelles: {current}\n{', '.join(options)}",
            initialvalue=",".join(str(i) for i in sorted(assigned)),
        )
        if answer is None:
            return

        if not answer.strip():
            if messagebox.askyesno("Confirmation", "Aucune matière choisie: effacer toutes les affectations ?"):
                try:
                    if AuthService.set_teacher_matieres(teacher.id, []):
                        self._record_admin_action("enseignant_matieres.updated", "enseignant", teacher.id, f"matières: {sorted(set(assigned))} -> []")
                        messagebox.showinfo("Succès", "Affectations mises à jour.")
                except Exception as exc:
                    messagebox.showerror("Erreur", str(exc))
            return

        parts = [part.strip() for part in answer.split(",")]
        try:
            matiere_ids = [int(part) for part in parts if part]
        except ValueError:
            messagebox.showerror("Erreur", "Les IDs doivent être des nombres séparés par des virgules.")
            return

        try:
            if AuthService.set_teacher_matieres(teacher.id, matiere_ids):
                self._record_admin_action(
                    "enseignant_matieres.updated",
                    "enseignant",
                    teacher.id,
                    f"matières: {sorted(set(assigned))} -> {sorted(set(matiere_ids))}",
                )
                messagebox.showinfo("Succès", "Affectations mises à jour.")
            else:
                messagebox.showerror("Erreur", "Impossible de mettre à jour les matières.")
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    # --- Paramètres planning ---
    def setup_parametres(self):
        frame = ttk.Labelframe(self.tab_parametres, text="Planification", padding=15, bootstyle="secondary")
        frame.pack(fill="x", pady=(0, 20))

        # Jours actifs
        ttk.Label(frame, text="Jours actifs (0=Lundi ... 6=Dimanche, séparés par des virgules)").pack(anchor="w")
        self.setting_work_days = ttk.Entry(frame, width=40)
        self.setting_work_days.pack(fill="x", pady=(0, 10))

        # Créneaux actifs
        ttk.Label(frame, text="Créneaux (HH:MM, séparés par des virgules)").pack(anchor="w")
        slot_times = SchoolSettingsService.get_slot_times()
        self.setting_slot_times = ttk.Entry(frame, width=40)
        self.setting_slot_times.pack(fill="x", pady=(0, 10))

        # Durée des créneaux
        ttk.Label(frame, text="Durée d'un créneau (minutes)").pack(anchor="w")
        self.setting_slot_duration = ttk.Entry(frame, width=15)
        self.setting_slot_duration.pack(anchor="w", pady=(0, 10))

        profile_frame = ttk.Labelframe(self.tab_parametres, text="Paramètres école", padding=15, bootstyle="info")
        profile_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(profile_frame, text="Nom de l'établissement").pack(anchor="w")
        self.setting_school_name = ttk.Entry(profile_frame, width=50)
        self.setting_school_name.pack(fill="x", pady=(0, 10))

        ttk.Label(profile_frame, text="Année scolaire (ex: 2026-2027)").pack(anchor="w")
        self.setting_academic_year = ttk.Entry(profile_frame, width=30)
        self.setting_academic_year.pack(anchor="w", pady=(0, 10))

        ttk.Label(profile_frame, text="Début période (AAAA-MM-DD)").pack(anchor="w")
        self.setting_term_start = ttk.Entry(profile_frame, width=20)
        self.setting_term_start.pack(anchor="w", pady=(0, 10))

        ttk.Label(profile_frame, text="Fin période (AAAA-MM-DD)").pack(anchor="w")
        self.setting_term_end = ttk.Entry(profile_frame, width=20)
        self.setting_term_end.pack(anchor="w", pady=(0, 10))

        ttk.Label(profile_frame, text="Vacances (dates séparées par des virgules, AAAA-MM-DD)").pack(anchor="w")
        self.setting_holidays = ttk.Entry(profile_frame, width=60)
        self.setting_holidays.pack(fill="x", pady=(0, 10))

        ttk.Label(profile_frame, text="Nb max de demandes par enseignant par jour (0 = illimité)").pack(anchor="w")
        self.setting_max_daily_reservations = ttk.Entry(profile_frame, width=12)
        self.setting_max_daily_reservations.pack(anchor="w", pady=(0, 10))

        ttk.Label(profile_frame, text="Préavis minimum pour une demande (jours)").pack(anchor="w")
        self.setting_min_booking_notice = ttk.Entry(profile_frame, width=12)
        self.setting_min_booking_notice.pack(anchor="w", pady=(0, 10))

        self.setting_allow_booking_in_holidays = BooleanVar(value=SchoolSettingsService.get_allow_booking_in_holidays())
        ttk.Checkbutton(
            profile_frame,
            text="Autoriser les demandes durant les vacances",
            variable=self.setting_allow_booking_in_holidays,
            bootstyle="round-toggle",
        ).pack(anchor="w", pady=(0, 6))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(5, 0))
        ttk.Button(
            btn_frame,
            text="💾 Enregistrer les paramètres",
            command=self.save_admin_settings,
            bootstyle="success",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="🔄 Recharger", command=self.refresh_parameters_view, bootstyle="info").pack(side="left")

        self.refresh_parameters_view()

    def refresh_parameters_view(self):
        self.setting_work_days.delete(0, "end")
        self.setting_slot_times.delete(0, "end")
        self.setting_slot_duration.delete(0, "end")
        self.setting_school_name.delete(0, "end")
        self.setting_academic_year.delete(0, "end")
        self.setting_term_start.delete(0, "end")
        self.setting_term_end.delete(0, "end")
        self.setting_holidays.delete(0, "end")
        self.setting_max_daily_reservations.delete(0, "end")
        self.setting_min_booking_notice.delete(0, "end")

        self.setting_work_days.insert(0, ", ".join(str(d) for d in SchoolSettingsService.get_working_days()))
        self.setting_slot_times.insert(0, ", ".join(t.strftime("%H:%M") for t in SchoolSettingsService.get_slot_times()))
        self.setting_slot_duration.insert(0, str(SchoolSettingsService.get_slot_duration_minutes()))
        self.setting_school_name.insert(0, SchoolSettingsService.get_school_name())
        self.setting_academic_year.insert(0, SchoolSettingsService.get_academic_year())
        term_start = SchoolSettingsService.get_term_start()
        term_end = SchoolSettingsService.get_term_end()
        self.setting_term_start.insert(0, term_start.isoformat() if term_start else "")
        self.setting_term_end.insert(0, term_end.isoformat() if term_end else "")
        self.setting_holidays.insert(0, SchoolSettingsService.get_holidays_text())
        self.setting_max_daily_reservations.insert(0, str(SchoolSettingsService.get_max_daily_reservations_per_teacher()))
        self.setting_min_booking_notice.insert(0, str(SchoolSettingsService.get_min_booking_notice_days()))
        self.setting_allow_booking_in_holidays.set(SchoolSettingsService.get_allow_booking_in_holidays())

    def save_planning_parameters(self):
        self.save_admin_settings()

    def save_admin_settings(self):
        work_days = self.setting_work_days.get().strip()
        slot_times = self.setting_slot_times.get().strip()
        slot_duration = self.setting_slot_duration.get().strip()
        school_name = self.setting_school_name.get().strip()
        academic_year = self.setting_academic_year.get().strip()
        term_start = self.setting_term_start.get().strip()
        term_end = self.setting_term_end.get().strip()
        holidays = self.setting_holidays.get().strip()
        max_daily_reservations = self.setting_max_daily_reservations.get().strip()
        min_booking_notice = self.setting_min_booking_notice.get().strip()
        allow_booking_in_holidays = self.setting_allow_booking_in_holidays.get()
        try:
            SchoolSettingsService.set_planning_settings(work_days, slot_times, slot_duration)
            SchoolSettingsService.set_school_settings(
                school_name,
                academic_year,
                term_start,
                term_end,
                holidays,
                max_daily_reservations,
                min_booking_notice,
                allow_booking_in_holidays,
            )
            self._record_admin_action(
                "school_settings.updated",
                "school",
                None,
                "paramètres établissement enregistrés",
            )
            messagebox.showinfo("Succès", "Paramètres de planification et école enregistrés.")
            self.refresh_parameters_view()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    # --- Journal d'audit ---
    def setup_audit(self):
        frame = ttk.Labelframe(self.tab_audit, text="Journal d'activité admin", padding=15, bootstyle="primary")
        frame.pack(fill="both", expand=True)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="🔄 Rafraîchir", command=self.refresh_audit, bootstyle="info").pack(side="left")
        ttk.Button(toolbar, text="📤 Exporter CSV", command=self.export_audit_csv, bootstyle="success").pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="🧹 Vider", command=self.clear_audit, bootstyle="danger").pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="🗑 Purger...", command=self.purge_audit, bootstyle="secondary").pack(side="left", padx=(6, 0))

        columns = ("id", "date", "admin", "action", "type", "entity_id", "details")
        self.tree_audit = ttk.Treeview(frame, columns=columns, show="headings", bootstyle="info")
        self.tree_audit.heading("id", text="ID")
        self.tree_audit.heading("date", text="Date")
        self.tree_audit.heading("admin", text="Admin")
        self.tree_audit.heading("action", text="Action")
        self.tree_audit.heading("type", text="Type")
        self.tree_audit.heading("entity_id", text="ID Entité")
        self.tree_audit.heading("details", text="Détails")
        self.tree_audit.column("id", width=50)
        self.tree_audit.column("admin", width=160)
        self.tree_audit.column("action", width=180)
        self.tree_audit.column("type", width=120)
        self.tree_audit.column("entity_id", width=90)
        self.tree_audit.column("details", width=420)
        self.tree_audit.pack(expand=True, fill="both")

        self.refresh_audit()

    def refresh_audit(self):
        if not hasattr(self, "tree_audit"):
            return
        for row in self.tree_audit.get_children():
            self.tree_audit.delete(row)
        for log in AdminAuditService.get_recent(250):
            admin_name = "système"
            if log.admin:
                admin_name = f"{log.admin.nom} {log.admin.prenom} ({log.admin.email})"
            self.tree_audit.insert(
                "",
                "end",
                values=(
                    log.id,
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                    admin_name,
                    log.action,
                    log.entity_type or "",
                    log.entity_id or "",
                    log.details or "",
                ),
            )

    def clear_audit(self):
        if not messagebox.askyesno("Confirmer", "Supprimer tous les logs d'audit ?"):
            return
        try:
            deleted = AdminAuditService.purge_all()
            self._record_admin_action("audit.cleared", "audit", None, f"total={deleted}")
            self.refresh_audit()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def purge_audit(self):
        days = simpledialog.askinteger("Purger le journal", "Supprimer les logs plus anciens que X jours :")
        if days is None:
            return
        try:
            deleted = AdminAuditService.purge_older_than(days)
            self._record_admin_action("audit.purged", "audit", None, f"older_than_days={days}, removed={deleted}")
            messagebox.showinfo("Succès", f"{deleted} logs supprimés.")
            self.refresh_audit()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def export_audit_csv(self):
        output_path = filedialog.asksaveasfilename(
            title="Exporter le journal d'audit",
            defaultextension=".csv",
            filetypes=[("Fichier CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialfile=f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not output_path:
            return
        try:
            logs = AdminAuditService.get_for_export(10000)
            with open(output_path, "w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["ID", "Date", "Admin ID", "Admin", "Action", "Entity type", "Entity ID", "Details"])
                for log in logs:
                    admin_name = ""
                    if log.admin:
                        admin_name = f"{log.admin.nom} {log.admin.prenom} ({log.admin.email})"
                    writer.writerow(
                        [
                            log.id,
                            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                            log.admin_id or "",
                            admin_name,
                            log.action,
                            log.entity_type or "",
                            log.entity_id or "",
                            log.details or "",
                        ]
                    )
            self._record_admin_action("audit.exported", "audit", None, f"file={output_path}, total={len(logs)}")
            messagebox.showinfo("Succès", "Journal exporté en CSV.")
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    # --- Organisation scolaire ---
    def setup_organisation(self):
        ttk.Label(
            self.tab_organisation,
            text="Organisation scolaire",
            font=("Helvetica", 16, "bold"),
            bootstyle="primary",
        ).pack(anchor="w", pady=(0, 4))
        ttk.Label(
            self.tab_organisation,
            text="Configurez les années, cycles, niveaux, filières et classes sans intervention technique.",
        ).pack(anchor="w", pady=(0, 12))

        self.organisation_notebook = ttk.Notebook(self.tab_organisation)
        self.organisation_notebook.pack(expand=True, fill="both")
        self.tab_academic_years = ttk.Frame(self.organisation_notebook, padding=10)
        self.tab_academic_cycles = ttk.Frame(self.organisation_notebook, padding=10)
        self.tab_academic_levels = ttk.Frame(self.organisation_notebook, padding=10)
        self.tab_academic_classes = ttk.Frame(self.organisation_notebook, padding=10)
        self.organisation_notebook.add(self.tab_academic_years, text="Années scolaires")
        self.organisation_notebook.add(self.tab_academic_cycles, text="Cycles")
        self.organisation_notebook.add(self.tab_academic_levels, text="Niveaux")
        self.organisation_notebook.add(self.tab_academic_classes, text="Filières et classes")

        self.setup_academic_years_ui()
        self.setup_cycles_ui()
        self.setup_levels_ui()
        self.setup_classes_ui()

    def setup_academic_years_ui(self):
        toolbar = ttk.Frame(self.tab_academic_years)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Ajouter une année", command=self.add_academic_year, bootstyle="success").pack(side="left")
        ttk.Button(toolbar, text="Activer", command=self.activate_year, bootstyle="primary").pack(side="left", padx=6)
        ttk.Button(toolbar, text="Archiver / réouvrir", command=self.archive_year, bootstyle="warning").pack(side="left", padx=6)
        ttk.Button(toolbar, text="Dupliquer vers une nouvelle année", command=self.clone_year_structure, bootstyle="info").pack(side="left", padx=6)
        ttk.Button(toolbar, text="Rafraîchir", command=self.refresh_organisation, bootstyle="secondary").pack(side="right")

        columns = ("id", "libelle", "debut", "fin", "statut", "archive")
        self.tree_academic_years = ttk.Treeview(self.tab_academic_years, columns=columns, show="headings", bootstyle="primary")
        for column, title in zip(columns, ("ID", "Année", "Début", "Fin", "Statut", "Archive")):
            self.tree_academic_years.heading(column, text=title)
        self.tree_academic_years.column("id", width=55)
        self.tree_academic_years.column("libelle", width=160)
        self.tree_academic_years.pack(expand=True, fill="both")
        self.refresh_academic_years()

    def setup_cycles_ui(self):
        toolbar = ttk.Frame(self.tab_academic_cycles)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Ajouter un cycle", command=self.add_organisation_cycle, bootstyle="success").pack(side="left")
        ttk.Button(toolbar, text="Modifier", command=self.edit_selected_cycle, bootstyle="warning").pack(side="left", padx=6)
        ttk.Button(toolbar, text="Archiver / réouvrir", command=self.archive_selected_cycle, bootstyle="danger").pack(side="left", padx=6)

        columns = ("id", "nom", "code", "ordre", "statut")
        self.tree_academic_cycles = ttk.Treeview(self.tab_academic_cycles, columns=columns, show="headings", bootstyle="info")
        for column, title in zip(columns, ("ID", "Cycle", "Code", "Ordre", "Statut")):
            self.tree_academic_cycles.heading(column, text=title)
        self.tree_academic_cycles.column("id", width=55)
        self.tree_academic_cycles.pack(expand=True, fill="both")
        self.refresh_academic_cycles()

    def setup_levels_ui(self):
        toolbar = ttk.Frame(self.tab_academic_levels)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Ajouter un niveau", command=self.add_organisation_level, bootstyle="success").pack(side="left")
        ttk.Button(toolbar, text="Modifier", command=self.edit_selected_level, bootstyle="warning").pack(side="left", padx=6)
        ttk.Button(toolbar, text="Archiver / réouvrir", command=self.archive_selected_level, bootstyle="danger").pack(side="left", padx=6)

        columns = ("id", "nom", "cycle", "code", "ordre", "statut")
        self.tree_academic_levels = ttk.Treeview(self.tab_academic_levels, columns=columns, show="headings", bootstyle="info")
        for column, title in zip(columns, ("ID", "Niveau", "Cycle", "Code", "Ordre", "Statut")):
            self.tree_academic_levels.heading(column, text=title)
        self.tree_academic_levels.column("id", width=55)
        self.tree_academic_levels.pack(expand=True, fill="both")
        self.refresh_academic_levels()

    def setup_classes_ui(self):
        panes = ttk.PanedWindow(self.tab_academic_classes, orient="horizontal")
        panes.pack(expand=True, fill="both")
        streams_frame = ttk.Labelframe(panes, text="Filières / sections", padding=10, bootstyle="warning")
        groups_frame = ttk.Labelframe(panes, text="Classes", padding=10, bootstyle="warning")
        panes.add(streams_frame, weight=1)
        panes.add(groups_frame, weight=1)

        stream_toolbar = ttk.Frame(streams_frame)
        stream_toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(stream_toolbar, text="Ajouter", command=self.add_organisation_filiere, bootstyle="success").pack(side="left")
        ttk.Button(stream_toolbar, text="Modifier", command=self.edit_selected_organisation_filiere, bootstyle="warning").pack(side="left", padx=6)
        ttk.Button(stream_toolbar, text="Archiver / réouvrir", command=self.archive_selected_organisation_filiere, bootstyle="danger").pack(side="left", padx=6)
        self.tree_organisation_filieres = ttk.Treeview(streams_frame, columns=("id", "nom", "niveau", "code", "ordre", "statut"), show="headings", bootstyle="warning")
        for column, title in zip(("id", "nom", "niveau", "code", "ordre", "statut"), ("ID", "Filière", "Niveau", "Code", "Ordre", "Statut")):
            self.tree_organisation_filieres.heading(column, text=title)
        self.tree_organisation_filieres.column("id", width=55)
        self.tree_organisation_filieres.pack(expand=True, fill="both")

        group_toolbar = ttk.Frame(groups_frame)
        group_toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(group_toolbar, text="Ajouter", command=self.add_organisation_groupe, bootstyle="success").pack(side="left")
        ttk.Button(group_toolbar, text="Modifier", command=self.edit_selected_organisation_groupe, bootstyle="warning").pack(side="left", padx=6)
        ttk.Button(group_toolbar, text="Archiver / réouvrir", command=self.archive_selected_organisation_groupe, bootstyle="danger").pack(side="left", padx=6)
        self.tree_organisation_groupes = ttk.Treeview(groups_frame, columns=("id", "nom", "filiere", "effectif", "ordre", "statut"), show="headings", bootstyle="warning")
        for column, title in zip(("id", "nom", "filiere", "effectif", "ordre", "statut"), ("ID", "Classe", "Filière", "Effectif", "Ordre", "Statut")):
            self.tree_organisation_groupes.heading(column, text=title)
        self.tree_organisation_groupes.column("id", width=55)
        self.tree_organisation_groupes.pack(expand=True, fill="both")
        self.refresh_organisation_classes()

    def refresh_organisation(self):
        self.refresh_academic_years()
        self.refresh_academic_cycles()
        self.refresh_academic_levels()
        self.refresh_organisation_classes()

    def refresh_academic_years(self):
        if not hasattr(self, "tree_academic_years"):
            return
        self._clear_tree(self.tree_academic_years)
        for academic_year in db.session.query(AcademicYear).order_by(AcademicYear.libelle.desc()).all():
            self.tree_academic_years.insert(
                "",
                "end",
                values=(
                    academic_year.id,
                    academic_year.libelle,
                    academic_year.date_debut.isoformat() if academic_year.date_debut else "",
                    academic_year.date_fin.isoformat() if academic_year.date_fin else "",
                    "Active" if academic_year.actif else "Inactive",
                    "Oui" if academic_year.archive else "Non",
                ),
            )

    def refresh_academic_cycles(self):
        if not hasattr(self, "tree_academic_cycles"):
            return
        self._clear_tree(self.tree_academic_cycles)
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return
        cycles = db.session.query(AcademicCycle).filter_by(school_year_id=active_year.id).order_by(AcademicCycle.ordre, AcademicCycle.nom).all()
        for cycle in cycles:
            self.tree_academic_cycles.insert("", "end", values=(cycle.id, cycle.nom, cycle.code or "", cycle.ordre, self._organisation_status(cycle)))

    def refresh_academic_levels(self):
        if not hasattr(self, "tree_academic_levels"):
            return
        self._clear_tree(self.tree_academic_levels)
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return
        levels = (
            db.session.query(AcademicLevel)
            .join(AcademicCycle)
            .filter(AcademicCycle.school_year_id == active_year.id)
            .order_by(AcademicCycle.ordre, AcademicLevel.ordre, AcademicLevel.nom)
            .all()
        )
        for level in levels:
            cycle_name = level.academic_cycle.nom if level.academic_cycle else ""
            self.tree_academic_levels.insert("", "end", values=(level.id, level.nom, cycle_name, level.code or "", level.ordre, self._organisation_status(level)))

    def refresh_organisation_classes(self):
        active_year = AcademicStructureService.get_active_year()
        if hasattr(self, "tree_organisation_filieres"):
            self._clear_tree(self.tree_organisation_filieres)
        if hasattr(self, "tree_organisation_groupes"):
            self._clear_tree(self.tree_organisation_groupes)
        if active_year is None:
            return
        filieres = (
            db.session.query(Filiere)
            .join(AcademicLevel)
            .join(AcademicCycle)
            .filter(AcademicCycle.school_year_id == active_year.id)
            .order_by(AcademicLevel.ordre, Filiere.ordre, Filiere.nom)
            .all()
        )
        for filiere in filieres:
            level_name = filiere.academic_level.nom if filiere.academic_level else ""
            self.tree_organisation_filieres.insert("", "end", values=(filiere.id, filiere.nom, level_name, filiere.code or "", filiere.ordre, self._organisation_status(filiere)))
        groupes = db.session.query(Groupe).filter_by(school_year_id=active_year.id).order_by(Groupe.ordre, Groupe.nom).all()
        for groupe in groupes:
            filiere_name = groupe.filiere.nom if groupe.filiere else ""
            self.tree_organisation_groupes.insert("", "end", values=(groupe.id, groupe.nom, filiere_name, groupe.effectif, groupe.ordre, self._organisation_status(groupe)))

    def add_academic_year(self):
        label = simpledialog.askstring("Ajouter une année scolaire", "Libellé (ex: 2026-2027) :")
        if label is None:
            return
        start_text = simpledialog.askstring("Ajouter une année scolaire", "Date de début (AAAA-MM-JJ, optionnel) :", initialvalue="")
        if start_text is None:
            return
        end_text = simpledialog.askstring("Ajouter une année scolaire", "Date de fin (AAAA-MM-JJ, optionnel) :", initialvalue="")
        if end_text is None:
            return
        try:
            start_date = self._parse_organisation_date(start_text)
            end_date = self._parse_organisation_date(end_text)
            if start_date and end_date and end_date < start_date:
                raise ValueError("La date de fin doit être postérieure à la date de début.")
            academic_year = AcademicStructureService.create_year(label, start_date, end_date)
            self._record_admin_action("academic_year.created", "academic_year", academic_year.id, f"libelle={academic_year.libelle}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def activate_year(self):
        values = self._selected_tree_values(self.tree_academic_years)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez une année scolaire.")
            return
        try:
            academic_year = AcademicStructureService.set_active_year(int(values[0]))
            self._record_admin_action("academic_year.activated", "academic_year", academic_year.id, f"libelle={academic_year.libelle}")
            self.refresh_organisation()
            messagebox.showinfo("Année active", f"{academic_year.libelle} est maintenant l'année scolaire active.")
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def archive_year(self):
        values = self._selected_tree_values(self.tree_academic_years)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez une année scolaire.")
            return
        archive = str(values[5]) != "Oui"
        action = "Archiver" if archive else "Réouvrir"
        if not messagebox.askyesno("Confirmer", f"{action} l'année {values[1]} ?"):
            return
        try:
            academic_year = AcademicStructureService.archive_year(int(values[0]), archive)
            self._record_admin_action("academic_year.archived" if archive else "academic_year.reopened", "academic_year", academic_year.id, f"libelle={academic_year.libelle}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def clone_year_structure(self):
        values = self._selected_tree_values(self.tree_academic_years)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez l'année source à dupliquer.")
            return
        target_label = simpledialog.askstring("Dupliquer une année", "Libellé de la nouvelle année (ex: 2027-2028) :")
        if target_label is None:
            return
        keep_effectif = messagebox.askyesno("Effectifs", "Conserver les effectifs des classes dans la nouvelle année ?")
        try:
            result = AcademicStructureService.clone_year_structure(int(values[0]), target_label, keep_effectif)
            self._record_admin_action("academic_year.cloned", "academic_year", int(values[0]), f"cible={target_label}, {result}")
            self.refresh_organisation()
            messagebox.showinfo("Duplication terminée", f"{result['groupes_dupliques']} classe(s) dupliquée(s).")
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def add_organisation_cycle(self):
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            messagebox.showwarning("Attention", "Activez d'abord une année scolaire.")
            return
        values = self._ask_named_organisation_values("Ajouter un cycle")
        if values is None:
            return
        try:
            cycle = AcademicStructureService.create_cycle(active_year.id, *values)
            self._record_admin_action("academic_cycle.created", "academic_cycle", cycle.id, f"nom={cycle.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def edit_selected_cycle(self):
        values = self._selected_tree_values(self.tree_academic_cycles)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un cycle.")
            return
        updated_values = self._ask_named_organisation_values("Modifier le cycle", values[1], values[2], values[3])
        if updated_values is None:
            return
        try:
            cycle = AcademicStructureService.update_cycle(int(values[0]), *updated_values)
            self._record_admin_action("academic_cycle.updated", "academic_cycle", cycle.id, f"nom={cycle.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def archive_selected_cycle(self):
        self._toggle_organisation_archive(self.tree_academic_cycles, AcademicStructureService.archive_cycle, "academic_cycle")

    def add_organisation_level(self):
        choices = self._available_cycle_choices()
        if not choices:
            messagebox.showwarning("Attention", "Créez d'abord un cycle non archivé.")
            return
        choice = simpledialog.askstring("Ajouter un niveau", f"Cycle (ID) : {', '.join(choices)}")
        cycle_id = self._parse_choice_id(choice)
        if cycle_id is None:
            return
        values = self._ask_named_organisation_values("Ajouter un niveau")
        if values is None:
            return
        try:
            level = AcademicStructureService.create_level(cycle_id, *values)
            self._record_admin_action("academic_level.created", "academic_level", level.id, f"nom={level.nom}, cycle_id={cycle_id}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def edit_selected_level(self):
        values = self._selected_tree_values(self.tree_academic_levels)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un niveau.")
            return
        updated_values = self._ask_named_organisation_values("Modifier le niveau", values[1], values[3], values[4])
        if updated_values is None:
            return
        try:
            level = AcademicStructureService.update_level(int(values[0]), *updated_values)
            self._record_admin_action("academic_level.updated", "academic_level", level.id, f"nom={level.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def archive_selected_level(self):
        self._toggle_organisation_archive(self.tree_academic_levels, AcademicStructureService.archive_level, "academic_level")

    def add_organisation_filiere(self):
        choices = self._available_level_choices()
        if not choices:
            messagebox.showwarning("Attention", "Créez d'abord un niveau non archivé.")
            return
        choice = simpledialog.askstring("Ajouter une filière", f"Niveau (ID) : {', '.join(choices)}")
        level_id = self._parse_choice_id(choice)
        if level_id is None:
            return
        values = self._ask_named_organisation_values("Ajouter une filière")
        if values is None:
            return
        try:
            filiere = AcademicStructureService.create_filiere(level_id, *values)
            self._record_admin_action("filiere.created", "filiere", filiere.id, f"nom={filiere.nom}, level_id={level_id}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def edit_selected_organisation_filiere(self):
        values = self._selected_tree_values(self.tree_organisation_filieres)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez une filière.")
            return
        updated_values = self._ask_named_organisation_values("Modifier la filière", values[1], values[3], values[4])
        if updated_values is None:
            return
        try:
            filiere = AcademicStructureService.update_filiere(int(values[0]), *updated_values)
            self._record_admin_action("filiere.updated", "filiere", filiere.id, f"nom={filiere.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def archive_selected_organisation_filiere(self):
        self._toggle_organisation_archive(self.tree_organisation_filieres, AcademicStructureService.archive_filiere, "filiere")

    def add_organisation_groupe(self):
        active_year = AcademicStructureService.get_active_year()
        choices = self._available_filiere_choices()
        if active_year is None or not choices:
            messagebox.showwarning("Attention", "Créez d'abord une filière non archivée dans l'année active.")
            return
        choice = simpledialog.askstring("Ajouter une classe", f"Filière (ID) : {', '.join(choices)}")
        filiere_id = self._parse_choice_id(choice)
        if filiere_id is None:
            return
        nom = simpledialog.askstring("Ajouter une classe", "Nom de la classe :")
        if nom is None:
            return
        effectif = simpledialog.askinteger("Ajouter une classe", "Effectif :", initialvalue=0)
        if effectif is None:
            return
        ordre = simpledialog.askinteger("Ajouter une classe", "Ordre d'affichage :", initialvalue=0)
        if ordre is None:
            return
        try:
            groupe = AcademicStructureService.create_groupe(filiere_id, nom, effectif, active_year.id, ordre)
            self._record_admin_action("groupe.created", "groupe", groupe.id, f"nom={groupe.nom}, filiere_id={filiere_id}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def edit_selected_organisation_groupe(self):
        values = self._selected_tree_values(self.tree_organisation_groupes)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez une classe.")
            return
        nom = simpledialog.askstring("Modifier la classe", "Nom :", initialvalue=values[1])
        if nom is None:
            return
        effectif = simpledialog.askinteger("Modifier la classe", "Effectif :", initialvalue=int(values[3]))
        if effectif is None:
            return
        ordre = simpledialog.askinteger("Modifier la classe", "Ordre d'affichage :", initialvalue=int(values[4]))
        if ordre is None:
            return
        try:
            groupe = AcademicStructureService.update_groupe(int(values[0]), nom, effectif, ordre)
            self._record_admin_action("groupe.updated", "groupe", groupe.id, f"nom={groupe.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    def archive_selected_organisation_groupe(self):
        self._toggle_organisation_archive(self.tree_organisation_groupes, AcademicStructureService.archive_groupe, "groupe")

    def _available_cycle_choices(self):
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        return [f"{cycle.id}: {cycle.nom}" for cycle in db.session.query(AcademicCycle).filter_by(school_year_id=active_year.id, archive=False, actif=True).order_by(AcademicCycle.ordre).all()]

    def _available_level_choices(self):
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        levels = db.session.query(AcademicLevel).join(AcademicCycle).filter(AcademicCycle.school_year_id == active_year.id, AcademicCycle.archive.is_(False), AcademicLevel.archive.is_(False), AcademicCycle.actif.is_(True), AcademicLevel.actif.is_(True)).order_by(AcademicLevel.ordre).all()
        return [f"{level.id}: {level.nom}" for level in levels]

    def _available_filiere_choices(self):
        active_year = AcademicStructureService.get_active_year()
        if active_year is None:
            return []
        filieres = db.session.query(Filiere).join(AcademicLevel).join(AcademicCycle).filter(AcademicCycle.school_year_id == active_year.id, AcademicCycle.archive.is_(False), AcademicLevel.archive.is_(False), Filiere.archive.is_(False), AcademicCycle.actif.is_(True), AcademicLevel.actif.is_(True), Filiere.actif.is_(True)).order_by(Filiere.ordre, Filiere.nom).all()
        return [f"{filiere.id}: {filiere.nom}" for filiere in filieres]

    def _ask_named_organisation_values(self, title, nom="", code="", ordre=0):
        nom = simpledialog.askstring(title, "Nom :", initialvalue=nom)
        if nom is None:
            return None
        code = simpledialog.askstring(title, "Code (optionnel) :", initialvalue=code)
        if code is None:
            return None
        ordre = simpledialog.askinteger(title, "Ordre d'affichage :", initialvalue=int(ordre or 0))
        if ordre is None:
            return None
        return nom, code, ordre

    def _toggle_organisation_archive(self, tree, archive_method, entity_type):
        values = self._selected_tree_values(tree)
        if not values:
            messagebox.showwarning("Attention", "Sélectionnez un élément.")
            return
        archive = str(values[-1]) != "Archivé"
        action = "Archiver" if archive else "Réouvrir"
        if not messagebox.askyesno("Confirmer", f"{action} {values[1]} ?"):
            return
        try:
            entity = archive_method(int(values[0]), archive)
            self._record_admin_action(f"{entity_type}.archived" if archive else f"{entity_type}.reopened", entity_type, entity.id, f"nom={entity.nom}")
            self.refresh_organisation()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))

    @staticmethod
    def _clear_tree(tree):
        for row in tree.get_children():
            tree.delete(row)

    @staticmethod
    def _organisation_status(entity):
        return "Archivé" if entity.archive else "Actif" if entity.actif else "Inactif"

    @staticmethod
    def _parse_organisation_date(raw_value):
        value = (raw_value or "").strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Les dates doivent être au format AAAA-MM-JJ.") from exc

    @staticmethod
    def _parse_choice_id(choice):
        if not choice:
            return None
        try:
            return int(choice.split(":", 1)[0].strip())
        except ValueError:
            messagebox.showerror("Erreur", "L'ID sélectionné est invalide.")
            return None
