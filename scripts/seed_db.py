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
            email="admin@school.edu",
            nom="Admin",
            prenom="Principal",
            role="admin"
        )
        admin.set_password("password")
        db.session.add(admin)

        # --- FILIERES / NIVEAUX ---
        print("Création des niveaux/filières...")
        f_tc = Filiere(nom="Tronc Commun", code="TC")
        f_1bac = Filiere(nom="1ère Année Baccalauréat", code="1BAC")
        f_2bac = Filiere(nom="2ème Année Baccalauréat", code="2BAC")
        f_college = Filiere(nom="Collège (3ème Année)", code="3AC")
        
        db.session.add_all([f_tc, f_1bac, f_2bac, f_college])
        db.session.flush()

        # --- GROUPES / CLASSES ---
        print("Création des classes...")
        # 2BAC - Effectifs de terminale
        g_2bac_sm = Groupe(nom="2BAC Sciences Maths", effectif=30, filiere=f_2bac)
        g_2bac_pc = Groupe(nom="2BAC Physique Chimie", effectif=35, filiere=f_2bac)
        g_2bac_svt = Groupe(nom="2BAC SVT", effectif=38, filiere=f_2bac)

        # 1BAC
        g_1bac_sm = Groupe(nom="1BAC Sciences Maths", effectif=32, filiere=f_1bac)
        g_1bac_exp = Groupe(nom="1BAC Sciences Exp.", effectif=40, filiere=f_1bac)

        # Tronc Commun
        g_tc_sc1 = Groupe(nom="TC Sciences 1", effectif=45, filiere=f_tc)
        g_tc_sc2 = Groupe(nom="TC Sciences 2", effectif=42, filiere=f_tc)

        # Collège (3ème)
        g_3ac_1 = Groupe(nom="3ème Collège A", effectif=35, filiere=f_college)
        g_3ac_2 = Groupe(nom="3ème Collège B", effectif=36, filiere=f_college)

        all_groupes = [
            g_2bac_sm, g_2bac_pc, g_2bac_svt,
            g_1bac_sm, g_1bac_exp,
            g_tc_sc1, g_tc_sc2,
            g_3ac_1, g_3ac_2
        ]
        db.session.add_all(all_groupes)
        db.session.flush()

        # --- SALLES ---
        print("Création des salles de classe...")
        salles_cours = [Salle(nom=f"Salle {i}", capacite=40, type_salle="cours") for i in range(1, 16)]
        # Salles plus grandes
        salles_grandes = [
            Salle(nom="Grande Salle A", capacite=50, type_salle="cours", equipement_video=True),
            Salle(nom="Grande Salle B", capacite=50, type_salle="cours", equipement_video=True)
        ]
        # Salles TP/Labo
        salles_tp = [
            Salle(nom="Labo Physique", capacite=20, type_salle="tp", equipement_tp=True),
            Salle(nom="Labo SVT", capacite=20, type_salle="tp", equipement_tp=True),
            Salle(nom="Salle Informatique", capacite=20, type_salle="tp", equipement_pc=True)
        ]
        db.session.add_all(salles_cours + salles_grandes + salles_tp)
        db.session.flush()

        # --- MATIERES ---
        print("Création des matières scolaires...")
        # Matieres Lycée
        m_maths = Matiere(nom="Mathématiques", code="MATH", volume_horaire_cours=20, volume_horaire_td=10, filiere=f_2bac)
        m_physique = Matiere(nom="Physique-Chimie", code="PC", volume_horaire_cours=15, volume_horaire_tp=10, filiere=f_2bac)
        m_svt = Matiere(nom="SVT", code="SVT", volume_horaire_cours=15, volume_horaire_tp=10, filiere=f_2bac)
        m_francais = Matiere(nom="Français", code="FRA", volume_horaire_cours=15, filiere=f_tc)
        m_anglais = Matiere(nom="Anglais", code="ENG", volume_horaire_cours=10, filiere=f_tc)
        m_philo = Matiere(nom="Philosophie", code="PHILO", volume_horaire_cours=10, filiere=f_2bac)
        
        db.session.add_all([m_maths, m_physique, m_svt, m_francais, m_anglais, m_philo])
        db.session.flush()

        # --- ENSEIGNANTS ---
        print("Création des professeurs...")
        
        def create_prof(email, nom, prenom, matieres):
            prof = Utilisateur(email=email, nom=nom, prenom=prenom, role="enseignant")
            prof.set_password("password")
            for m in matieres:
                prof.matieres.append(m)
            return prof

        profs = [
            create_prof("prof.math@school.edu", "El Alaoui", "Mohamed", [m_maths]),
            create_prof("prof.math2@school.edu", "Benali", "Amina", [m_maths]),
            create_prof("prof.pc@school.edu", "Chraibi", "Youssef", [m_physique]),
            create_prof("prof.svt@school.edu", "Tazi", "Fatima", [m_svt]),
            create_prof("prof.fra@school.edu", "Lefevre", "Sophie", [m_francais]),
            create_prof("prof.eng@school.edu", "Smith", "John", [m_anglais]),
            create_prof("prof.philo@school.edu", "Ibn Sina", "Tarik", [m_philo]),
        ]
        
        db.session.add_all(profs)
        db.session.flush()

        # --- SEANCES ---
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
                heure_fin=time(10, 30), # 2 hour blocks typical for high school
            )

        seances_to_create = []

        # Affectation 2BAC
        for g in [g_2bac_sm, g_2bac_pc, g_2bac_svt]:
            seances_to_create.extend([
                add_seance_need(m_maths, profs[0], g, "cours"),
                add_seance_need(m_physique, profs[2], g, "cours"),
                add_seance_need(m_svt, profs[3], g, "cours"),
                add_seance_need(m_philo, profs[6], g, "cours"),
            ])
            # Add TPs for science groups
            if g != g_2bac_sm: # SM might have less lab time in some curricula
                seances_to_create.extend([
                    add_seance_need(m_physique, profs[2], g, "tp"),
                    add_seance_need(m_svt, profs[3], g, "tp"),
                ])

        # Affectation 1BAC
        for g in [g_1bac_sm, g_1bac_exp]:
            seances_to_create.extend([
                add_seance_need(m_maths, profs[1], g, "cours"),
                add_seance_need(m_physique, profs[2], g, "cours"),
                add_seance_need(m_francais, profs[4], g, "cours"),
            ])

        # Affectation TC
        for g in [g_tc_sc1, g_tc_sc2]:
            seances_to_create.extend([
                add_seance_need(m_maths, profs[1], g, "cours"),
                add_seance_need(m_francais, profs[4], g, "cours"),
                add_seance_need(m_anglais, profs[5], g, "cours"),
            ])

        db.session.add_all(seances_to_create)

        # --- ETUDIANTS ---
        print("Création des comptes étudiants (un par classe)...")
        etudiants = [
            Utilisateur(email="student.2bac.sm@school.edu", nom="Mansouri", prenom="Anas", role="etudiant", groupe=g_2bac_sm),
            Utilisateur(email="student.1bac.exp@school.edu", nom="Berrada", prenom="Lina", role="etudiant", groupe=g_1bac_exp),
            Utilisateur(email="student.tc.sc1@school.edu", nom="Zahir", prenom="Rachid", role="etudiant", groupe=g_tc_sc1),
            Utilisateur(email="student.3ac@school.edu", nom="Kettani", prenom="Sara", role="etudiant", groupe=g_3ac_1),
        ]
        for e in etudiants:
            e.set_password("password")
        db.session.add_all(etudiants)

        db.session.commit()
        nb_seances = len(seances_to_create)
        print(f"Base de données de l'école privée initialisée avec succès ! ({len(all_groupes)} classes, {len(profs)} professeurs, {len(etudiants)} comptes étudiants démo, {nb_seances} séances.)")

if __name__ == "__main__":
    seed()
