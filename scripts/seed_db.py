import os
from app import create_app
from app.extensions import db, bcrypt
from app.models import Utilisateur, Salle, Matiere, Filiere, Groupe, Seance

def seed():
    app = create_app("development")
    with app.app_context():
        print("Suppression de la base de données existante...")
        db.drop_all()
        print("Création des tables...")
        db.create_all()
        
        # --- ADMIN ---
        print("Création de l'administrateur...")
        admin = Utilisateur(
            email="admin@test.com",
            nom="Admin",
            prenom="Principal",
            role="admin"
        )
        admin.set_password("password")
        db.session.add(admin)

        # --- FILIERES ---
        print("Création des filières...")
        f_smi = Filiere(nom="Sciences Mathématiques et Informatique", code="SMI")
        f_sma = Filiere(nom="Sciences Mathématiques et Applications", code="SMA")
        f_smp = Filiere(nom="Sciences de la Matière Physique", code="SMP")
        f_seg = Filiere(nom="Sciences Économiques et Gestion", code="SEG")
        
        db.session.add_all([f_smi, f_sma, f_smp, f_seg])
        db.session.flush()

        # --- GROUPES (effectifs variés pour contraindre le moteur CSP : capacité salle >= effectif) ---
        print("Création des groupes...")
        # SMI — effectifs variés : petits (TP), moyens (TD), gros (cours en amphi)
        g_smi_s1_g1 = Groupe(nom="SMI S1 G1", effectif=48, filiere=f_smi)
        g_smi_s1_g2 = Groupe(nom="SMI S1 G2", effectif=42, filiere=f_smi)
        g_smi_s1_g3 = Groupe(nom="SMI S1 G3", effectif=55, filiere=f_smi)
        g_smi_s3_g1 = Groupe(nom="SMI S3 G1", effectif=28, filiere=f_smi)
        g_smi_s3_g2 = Groupe(nom="SMI S3 G2", effectif=32, filiere=f_smi)
        g_smi_s5_il = Groupe(nom="SMI S5 Ingénierie Logicielle", effectif=18, filiere=f_smi)
        g_smi_s5_rs = Groupe(nom="SMI S5 Réseaux", effectif=22, filiere=f_smi)

        # SEG — gros effectifs (cours en amphi obligatoire)
        g_seg_s1_g1 = Groupe(nom="SEG S1 G1", effectif=72, filiere=f_seg)
        g_seg_s1_g2 = Groupe(nom="SEG S1 G2", effectif=68, filiere=f_seg)
        g_seg_s1_g3 = Groupe(nom="SEG S1 G3", effectif=58, filiere=f_seg)
        g_seg_s3_g1 = Groupe(nom="SEG S3 G1", effectif=45, filiere=f_seg)

        # SMP — effectifs moyens
        g_smp_s1_g1 = Groupe(nom="SMP S1 G1", effectif=52, filiere=f_smp)
        g_smp_s1_g2 = Groupe(nom="SMP S1 G2", effectif=38, filiere=f_smp)

        # SMA
        g_sma_s1_g1 = Groupe(nom="SMA S1 G1", effectif=40, filiere=f_sma)
        g_sma_s1_g2 = Groupe(nom="SMA S1 G2", effectif=35, filiere=f_sma)

        all_groupes = [
            g_smi_s1_g1, g_smi_s1_g2, g_smi_s1_g3, g_smi_s3_g1, g_smi_s3_g2, g_smi_s5_il, g_smi_s5_rs,
            g_seg_s1_g1, g_seg_s1_g2, g_seg_s1_g3, g_seg_s3_g1,
            g_smp_s1_g1, g_smp_s1_g2,
            g_sma_s1_g1, g_sma_s1_g2,
        ]
        db.session.add_all(all_groupes)
        db.session.flush()

        # --- SALLES (capacités variées : amphi > salles cours > TP pour contraindre l’affectation) ---
        print("Création des salles...")
        amphis = [
            Salle(nom="Amphi Al Farabi", capacite=200, type_salle="amphi", equipement_video=True),
            Salle(nom="Amphi Ibn Sina", capacite=200, type_salle="amphi", equipement_video=True),
            Salle(nom="Amphi Al Khawarizmi", capacite=150, type_salle="amphi", equipement_video=True),
        ]
        # Salles cours : 60 et 45 places (gros / moyens groupes)
        salles_60 = [
            Salle(nom="Salle A (60)", capacite=60, type_salle="cours"),
            Salle(nom="Salle B (60)", capacite=60, type_salle="cours"),
        ]
        salles_td = [Salle(nom=f"Salle {i}", capacite=45, type_salle="cours") for i in range(1, 13)]
        # Salles TP 25 places (petits groupes uniquement)
        salles_tp = [
            Salle(nom="Salle TP 1 (Linux)", capacite=25, type_salle="tp", equipement_pc=True, equipement_tp=True),
            Salle(nom="Salle TP 2 (Windows)", capacite=25, type_salle="tp", equipement_pc=True, equipement_tp=True),
            Salle(nom="Salle TP 3 (Réseaux)", capacite=25, type_salle="tp", equipement_pc=True, equipement_tp=True),
            Salle(nom="Salle TP 4", capacite=25, type_salle="tp", equipement_pc=True, equipement_tp=True),
            Salle(nom="Salle TP 5", capacite=25, type_salle="tp", equipement_pc=True, equipement_tp=True),
        ]
        db.session.add_all(amphis + salles_60 + salles_td + salles_tp)
        db.session.flush()

        # --- MATIERES ---
        print("Création des matières...")
        # Matieres SMI/SMA S1
        m_analyse1 = Matiere(nom="Analyse 1", code="MATH101", volume_horaire_cours=30, volume_horaire_td=20, filiere=f_smi)
        m_algebre1 = Matiere(nom="Algèbre 1", code="MATH102", volume_horaire_cours=30, volume_horaire_td=20, filiere=f_smi)
        m_algo = Matiere(nom="Algorithmique I", code="INFO101", volume_horaire_cours=20, volume_horaire_td=10, volume_horaire_tp=15, filiere=f_smi)
        m_langage_c = Matiere(nom="Programmation C", code="INFO102", volume_horaire_cours=15, volume_horaire_tp=20, filiere=f_smi)
        
        # Matieres SMI S3
        m_poo = Matiere(nom="POO Java", code="INFO301", volume_horaire_cours=20, volume_horaire_tp=20, filiere=f_smi)
        m_bd = Matiere(nom="Bases de Données", code="INFO302", volume_horaire_cours=20, volume_horaire_tp=15, filiere=f_smi)
        m_sys = Matiere(nom="Systèmes d'exploitation", code="INFO303", volume_horaire_cours=20, volume_horaire_tp=15, filiere=f_smi)
        
        # Matieres SEG
        m_micro = Matiere(nom="Microéconomie", code="ECO101", volume_horaire_cours=40, volume_horaire_td=15, filiere=f_seg)
        m_compta = Matiere(nom="Comptabilité Générale", code="ECO102", volume_horaire_cours=40, volume_horaire_td=20, filiere=f_seg)
        
        db.session.add_all([m_analyse1, m_algebre1, m_algo, m_langage_c, m_poo, m_bd, m_sys, m_micro, m_compta])
        db.session.flush()

        # --- ENSEIGNANTS ---
        print("Création des enseignants...")
        
        def create_prof(email, nom, prenom, matieres):
            prof = Utilisateur(email=email, nom=nom, prenom=prenom, role="enseignant")
            prof.set_password("password")
            for m in matieres:
                prof.matieres.append(m)
            return prof

        profs = [
            create_prof("benjelloun@univ.ma", "Benjelloun", "Karim", [m_analyse1, m_algebre1]),
            create_prof("elamrani@univ.ma", "El Amrani", "Fatima", [m_algo, m_langage_c]),
            create_prof("berrada@univ.ma", "Berrada", "Omar", [m_poo, m_sys]),
            create_prof("idrissi@univ.ma", "Idrissi", "Leila", [m_bd]),
            create_prof("tazi@univ.ma", "Tazi", "Ahmed", [m_micro, m_compta]),
            create_prof("ennaji@univ.ma", "Ennaji", "Samir", [m_langage_c, m_algo]), # Renfort Algo/C
        ]
        
        db.session.add_all(profs)
        db.session.flush()

        # --- SEANCES (toutes à Lundi 8h30 par défaut → le CSP les répartit sans conflit) ---
        print("Préparation des séances à planifier...")
        from datetime import time

        def add_seance_need(matiere, prof, groupe, type_s):
            return Seance(
                matiere=matiere,
                enseignant=prof,
                groupe=groupe,
                type_seance=type_s,
                jour_semaine=0,
                heure_debut=time(8, 30),
                heure_fin=time(10, 0),
            )

        seances_to_create = []

        # SMI S1 G1 (48), G2 (42), G3 (55)
        for g in [g_smi_s1_g1, g_smi_s1_g2, g_smi_s1_g3]:
            seances_to_create.extend([
                add_seance_need(m_analyse1, profs[0], g, "cours"),
                add_seance_need(m_analyse1, profs[0], g, "td"),
                add_seance_need(m_algebre1, profs[0], g, "cours"),
                add_seance_need(m_algo, profs[1], g, "cours"),
                add_seance_need(m_algo, profs[5], g, "tp"),
                add_seance_need(m_langage_c, profs[1], g, "cours"),
            ])

        # SMI S3 G1 (28), G2 (32)
        for g in [g_smi_s3_g1, g_smi_s3_g2]:
            seances_to_create.extend([
                add_seance_need(m_poo, profs[2], g, "cours"),
                add_seance_need(m_poo, profs[2], g, "tp"),
                add_seance_need(m_bd, profs[3], g, "cours"),
                add_seance_need(m_bd, profs[3], g, "tp"),
                add_seance_need(m_sys, profs[2], g, "cours"),
            ])

        # SMI S5 IL (18), S5 RS (22) — petits groupes → salles TP
        for g in [g_smi_s5_il, g_smi_s5_rs]:
            seances_to_create.extend([
                add_seance_need(m_poo, profs[2], g, "tp"),
                add_seance_need(m_bd, profs[3], g, "tp"),
                add_seance_need(m_sys, profs[2], g, "tp"),
            ])

        # SEG S1 G1 (72), G2 (68), G3 (58) — gros effectifs → amphis
        for g in [g_seg_s1_g1, g_seg_s1_g2, g_seg_s1_g3]:
            seances_to_create.extend([
                add_seance_need(m_micro, profs[4], g, "cours"),
                add_seance_need(m_micro, profs[4], g, "td"),
                add_seance_need(m_compta, profs[4], g, "cours"),
                add_seance_need(m_compta, profs[4], g, "td"),
            ])

        # SEG S3 G1 (45)
        seances_to_create.extend([
            add_seance_need(m_micro, profs[4], g_seg_s3_g1, "cours"),
            add_seance_need(m_compta, profs[4], g_seg_s3_g1, "cours"),
        ])

        # SMP S1 G1 (52), G2 (38)
        for g in [g_smp_s1_g1, g_smp_s1_g2]:
            seances_to_create.extend([
                add_seance_need(m_analyse1, profs[0], g, "cours"),
                add_seance_need(m_algebre1, profs[0], g, "cours"),
            ])

        # SMA S1 G1 (40), G2 (35)
        for g in [g_sma_s1_g1, g_sma_s1_g2]:
            seances_to_create.extend([
                add_seance_need(m_analyse1, profs[0], g, "cours"),
                add_seance_need(m_algebre1, profs[0], g, "cours"),
            ])

        db.session.add_all(seances_to_create)

        # --- ETUDIANTS (un compte par groupe pour accès démo ; tous : password) ---
        print("Création des étudiants (un par groupe)...")
        etudiants = [
            # SMI
            Utilisateur(email="etudiant.smi.s1.g1@univ.ma", nom="Alaoui", prenom="Mehdi", role="etudiant", groupe=g_smi_s1_g1),
            Utilisateur(email="etudiant.smi.s1.g2@univ.ma", nom="Benali", prenom="Fatima", role="etudiant", groupe=g_smi_s1_g2),
            Utilisateur(email="etudiant.smi.s1.g3@univ.ma", nom="Idrissi", prenom="Omar", role="etudiant", groupe=g_smi_s1_g3),
            Utilisateur(email="etudiant.smi.s3.g1@univ.ma", nom="Tazi", prenom="Lina", role="etudiant", groupe=g_smi_s3_g1),
            Utilisateur(email="etudiant.smi.s3.g2@univ.ma", nom="El Fassi", prenom="Hassan", role="etudiant", groupe=g_smi_s3_g2),
            Utilisateur(email="etudiant.smi.s5.il@univ.ma", nom="Bennani", prenom="Youssef", role="etudiant", groupe=g_smi_s5_il),
            Utilisateur(email="etudiant.smi.s5.rs@univ.ma", nom="Moussaoui", prenom="Nadia", role="etudiant", groupe=g_smi_s5_rs),
            # SEG
            Utilisateur(email="etudiant.seg.s1.g1@univ.ma", nom="Mansouri", prenom="Sara", role="etudiant", groupe=g_seg_s1_g1),
            Utilisateur(email="etudiant.seg.s1.g2@univ.ma", nom="Chraibi", prenom="Amine", role="etudiant", groupe=g_seg_s1_g2),
            Utilisateur(email="etudiant.seg.s1.g3@univ.ma", nom="Kettani", prenom="Leila", role="etudiant", groupe=g_seg_s1_g3),
            Utilisateur(email="etudiant.seg.s3.g1@univ.ma", nom="Zahir", prenom="Rachid", role="etudiant", groupe=g_seg_s3_g1),
            # SMP
            Utilisateur(email="etudiant.smp.s1.g1@univ.ma", nom="Bennani", prenom="Youssef", role="etudiant", groupe=g_smp_s1_g1),
            Utilisateur(email="etudiant.smp.s1.g2@univ.ma", nom="Berrada", prenom="Salma", role="etudiant", groupe=g_smp_s1_g2),
            # SMA
            Utilisateur(email="etudiant.sma.s1.g1@univ.ma", nom="Fahmi", prenom="Karim", role="etudiant", groupe=g_sma_s1_g1),
            Utilisateur(email="etudiant.sma.s1.g2@univ.ma", nom="Lamrani", prenom="Inès", role="etudiant", groupe=g_sma_s1_g2),
        ]
        for e in etudiants:
            e.set_password("password")
        db.session.add_all(etudiants)

        db.session.commit()
        nb_seances = len(seances_to_create)
        print(f"Données marocaines injectées avec succès ! ({len(all_groupes)} groupes, {len(profs)} enseignants, {len(etudiants)} étudiants, {nb_seances} séances.)")

if __name__ == "__main__":
    seed()
