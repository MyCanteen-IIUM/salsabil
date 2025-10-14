import sqlite3
from datetime import datetime
import os

DATABASE = 'salsabil.db'

def get_db_connection():
    """Créer une connexion à la base de données"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialiser la base de données avec les tables nécessaires"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table des employés
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            prenom TEXT NOT NULL,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'actif',
            date_creation TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            type TEXT NOT NULL,
            lieu TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT,
            department TEXT,
            date_limite TEXT NOT NULL,
            date_publication TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des candidatures
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            prenom TEXT NOT NULL,
            nom TEXT NOT NULL,
            email TEXT NOT NULL,
            telephone TEXT NOT NULL,
            adresse TEXT NOT NULL,
            date_naissance TEXT,
            nationalite TEXT,
            photo TEXT,
            cv TEXT NOT NULL,
            lettre_demande TEXT,
            carte_id TEXT NOT NULL,
            lettre_recommandation TEXT,
            casier_judiciaire TEXT,
            diplome TEXT,
            status TEXT DEFAULT 'en attente',
            date_soumission TEXT DEFAULT CURRENT_TIMESTAMP,
            workflow_phase TEXT DEFAULT 'phase1',
            phase1_status TEXT DEFAULT 'pending',
            phase1_date TEXT,
            phase1_notification_sent INTEGER DEFAULT 0,
            interview_date TEXT,
            interview_notes TEXT,
            interview_invitation_pdf TEXT,
            phase2_status TEXT,
            phase2_date TEXT,
            phase2_notification_sent INTEGER DEFAULT 0,
            rejection_reason TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    # Table des codes de vérification des documents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verification_code TEXT UNIQUE NOT NULL,
            application_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            pdf_path TEXT,
            status TEXT DEFAULT 'valide',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications (id)
        )
    ''')
    
    conn.commit()
    
    # Insérer les employés par défaut s'ils n'existent pas
    cursor.execute('SELECT COUNT(*) FROM employees')
    if cursor.fetchone()[0] == 0:
        default_employees = [
            ('admin', 'admin123', 'Super', 'Admin', 'admin@salsabil.com', 'admin', 'actif'),
            ('hr', 'hr123', 'Sarah', 'Martin', 'hr@salsabil.com', 'hr', 'actif'),
            ('recruteur', 'rec123', 'Pierre', 'Dupont', 'recruteur@salsabil.com', 'recruteur', 'actif')
        ]
        
        cursor.executemany('''
            INSERT INTO employees (username, password, prenom, nom, email, role, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_employees)
        
        conn.commit()
        print("✅ Employés par défaut créés")
    
    conn.close()
    print("✅ Base de données initialisée avec succès!")

def reset_db():
    """Réinitialiser complètement la base de données"""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print("🗑️  Ancienne base de données supprimée")
    init_db()

if __name__ == '__main__':
    print("Initialisation de la base de données...")
    init_db()
