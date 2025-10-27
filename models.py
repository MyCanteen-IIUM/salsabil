from database import get_db_connection, is_postgresql
from datetime import datetime
import os

# ==================== UTILITY FUNCTIONS ====================

def get_placeholder():
    """Retourne le placeholder SQL approprié selon la base de données"""
    return '%s' if is_postgresql() else '?'

def convert_query_placeholders(query, num_params):
    """Convertit les placeholders ? en %s si nécessaire pour PostgreSQL"""
    if is_postgresql():
        # Remplacer tous les ? par %s
        return query.replace('?', '%s')
    return query

def delete_file_if_exists(filename):
    """Supprimer un fichier du système de fichiers s'il existe"""
    if filename:
        # Chemins possibles pour les fichiers
        paths = [
            os.path.join('static', 'uploads', filename),
            os.path.join('uploads', filename)
        ]
        
        for filepath in paths:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"✅ Fichier supprimé: {filepath}")
                    return True
                except Exception as e:
                    print(f"❌ Erreur lors de la suppression de {filepath}: {str(e)}")
                    return False
    return False

def delete_application_files(application):
    """Supprimer tous les fichiers associés à une candidature"""
    import os
    
    files_to_delete = [
        application.get('photo'),
        application.get('cv'),
        application.get('lettre_demande'),
        application.get('carte_id'),
        application.get('lettre_recommandation'),
        application.get('casier_judiciaire'),
        application.get('diplome')
    ]
    
    deleted_count = 0
    for filename in files_to_delete:
        if delete_file_if_exists(filename):
            deleted_count += 1
    
    # Supprimer le PDF de convocation s'il existe
    pdf_filename = application.get('interview_invitation_pdf')
    if pdf_filename:
        pdf_path = os.path.join('static', 'convocations', pdf_filename)
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                deleted_count += 1
                print(f"📄 PDF de convocation supprimé: {pdf_filename}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression du PDF: {e}")
    
    # Supprimer le PDF de lettre d'acceptation s'il existe
    acceptance_pdf_filename = application.get('acceptance_letter_pdf')
    if acceptance_pdf_filename:
        acceptance_pdf_path = os.path.join('static', 'acceptances', acceptance_pdf_filename)
        if os.path.exists(acceptance_pdf_path):
            try:
                os.remove(acceptance_pdf_path)
                deleted_count += 1
                print(f"✅ PDF de lettre d'acceptation supprimé: {acceptance_pdf_filename}")
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de la lettre d'acceptation: {e}")
    
    return deleted_count

# ==================== EMPLOYEES ====================

def get_all_employees():
    """Récupérer tous les employés"""
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY id').fetchall()
    conn.close()
    return [dict(emp) for emp in employees]

def get_employee_by_id(emp_id):
    """Récupérer un employé par son ID"""
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (emp_id,)).fetchone()
    conn.close()
    return dict(employee) if employee else None

def get_employee_by_username(username):
    """Récupérer un employé par son nom d'utilisateur"""
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(employee) if employee else None

def create_employee(username, password, prenom, nom, email, role, status='actif'):
    """Créer un nouvel employé"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO employees (username, password, prenom, nom, email, role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, password, prenom, nom, email, role, status))
    conn.commit()
    emp_id = cursor.lastrowid
    conn.close()
    return emp_id

def update_employee(emp_id, username, prenom, nom, email, role, status):
    """Mettre à jour un employé"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE employees 
        SET username = ?, prenom = ?, nom = ?, email = ?, role = ?, status = ?
        WHERE id = ?
    ''', (username, prenom, nom, email, role, status, emp_id))
    conn.commit()
    conn.close()

def update_employee_profile(emp_id, username, prenom, nom, email):
    """Mettre à jour le profil d'un employé"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE employees 
        SET username = ?, prenom = ?, nom = ?, email = ?
        WHERE id = ?
    ''', (username, prenom, nom, email, emp_id))
    conn.commit()
    conn.close()

def update_employee_password(emp_id, new_password):
    """Mettre à jour le mot de passe d'un employé"""
    conn = get_db_connection()
    conn.execute('UPDATE employees SET password = ? WHERE id = ?', (new_password, emp_id))
    conn.commit()
    conn.close()

def toggle_employee_status(emp_id):
    """Activer/Désactiver un employé"""
    conn = get_db_connection()
    employee = conn.execute('SELECT status FROM employees WHERE id = ?', (emp_id,)).fetchone()
    new_status = 'inactif' if employee['status'] == 'actif' else 'actif'
    conn.execute('UPDATE employees SET status = ? WHERE id = ?', (new_status, emp_id))
    conn.commit()
    conn.close()
    return new_status

def delete_employee(emp_id):
    """Supprimer un employé"""
    conn = get_db_connection()
    conn.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()

# ==================== JOBS ====================

def get_all_jobs():
    """Récupérer tous les jobs"""
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
    conn.close()
    # Convertir en dict et mapper les champs pour compatibilité avec les templates
    result = []
    for job in jobs:
        job_dict = dict(job)
        # Mapper les champs de la base de données vers les noms utilisés dans les templates
        job_dict['title'] = job_dict.get('titre', '')
        job_dict['location'] = job_dict.get('lieu', '')
        job_dict['deadline'] = job_dict.pop('date_limite')
        job_dict['posted_date'] = job_dict.get('date_publication', '')
        # Si department existe dans la BDD, l'utiliser, sinon utiliser type comme fallback
        if not job_dict.get('department'):
            job_dict['department'] = job_dict.get('type', 'Non spécifié')
        # Parser les requirements (stockées comme texte avec \n comme séparateur)
        req_text = job_dict.get('requirements', '')
        if req_text:
            job_dict['requirements'] = [r.strip() for r in req_text.split('\n') if r.strip()]
        else:
            job_dict['requirements'] = []
        result.append(job_dict)
    return result

def get_job_by_id(job_id):
    """Récupérer un job par son ID"""
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    if job:
        job_dict = dict(job)
        # Mapper les champs de la base de données vers les noms utilisés dans les templates
        job_dict['title'] = job_dict.get('titre', '')
        job_dict['location'] = job_dict.get('lieu', '')
        job_dict['deadline'] = job_dict.pop('date_limite')
        job_dict['posted_date'] = job_dict.get('date_publication', '')
        # Si department existe dans la BDD, l'utiliser, sinon utiliser type comme fallback
        if not job_dict.get('department'):
            job_dict['department'] = job_dict.get('type', 'Non spécifié')
        # Parser les requirements (stockées comme texte avec \n comme séparateur)
        req_text = job_dict.get('requirements', '')
        if req_text:
            job_dict['requirements'] = [r.strip() for r in req_text.split('\n') if r.strip()]
        else:
            job_dict['requirements'] = []
        return job_dict
    return None

def create_job(titre, type_job, lieu, description, date_limite, requirements=None, department=None, langues_requises=None):
    """Créer un nouveau job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    date_publication = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO jobs (titre, type, lieu, description, requirements, department, date_limite, date_publication, langues_requises)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (titre, type_job, lieu, description, requirements, department, date_limite, date_publication, langues_requises))
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id

def update_job(job_id, titre, type_job, lieu, description, date_limite, requirements=None, department=None, langues_requises=None):
    """Mettre à jour un job"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE jobs 
        SET titre = ?, type = ?, lieu = ?, description = ?, requirements = ?, department = ?, date_limite = ?, langues_requises = ?
        WHERE id = ?
    ''', (titre, type_job, lieu, description, requirements, department, date_limite, langues_requises, job_id))
    conn.commit()
    conn.close()

def delete_job(job_id):
    """Supprimer un job et toutes les candidatures associées avec leurs fichiers"""
    # Récupérer toutes les candidatures pour ce job
    applications = get_applications_by_job(job_id)
    
    # Supprimer les fichiers de chaque candidature
    total_files_deleted = 0
    for app in applications:
        deleted_files = delete_application_files(app)
        total_files_deleted += deleted_files
    
    if total_files_deleted > 0:
        print(f"📁 {total_files_deleted} fichier(s) supprimé(s) pour {len(applications)} candidature(s)")
    
    # Supprimer les codes de vérification et les candidatures de la base de données
    conn = get_db_connection()
    
    # Supprimer les codes de vérification pour toutes les candidatures de ce job
    verification_count = conn.execute(
        'SELECT COUNT(*) as count FROM document_verifications WHERE application_id IN (SELECT id FROM applications WHERE job_id = ?)', 
        (job_id,)
    ).fetchone()['count']
    
    if verification_count > 0:
        conn.execute(
            'DELETE FROM document_verifications WHERE application_id IN (SELECT id FROM applications WHERE job_id = ?)', 
            (job_id,)
        )
        print(f"🔐 {verification_count} code(s) de vérification supprimé(s)")
    
    # Supprimer les candidatures et le job
    conn.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()

# ==================== APPLICATIONS ====================

def get_all_applications():
    """Récupérer toutes les candidatures"""
    conn = get_db_connection()
    applications = conn.execute('SELECT * FROM applications ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(app) for app in applications]

def get_application_by_id(app_id):
    """Récupérer une candidature par son ID"""
    conn = get_db_connection()
    application = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return dict(application) if application else None

def get_applications_by_job(job_id):
    """Récupérer toutes les candidatures pour un job"""
    conn = get_db_connection()
    applications = conn.execute('SELECT * FROM applications WHERE job_id = ? ORDER BY id DESC', (job_id,)).fetchall()
    conn.close()
    return [dict(app) for app in applications]

def create_application(job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
                      sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
                      travaille_actuellement, dernier_lieu_travail, raison_depart,
                      niveau_instruction, specialisation, specialisation_autre,
                      langue_arabe, langue_anglaise, langue_francaise,
                      autre_langue_nom, autre_langue_niveau,
                      problemes_sante, nature_maladie,
                      choix_travail,
                      photo, cv, lettre_demande, carte_id, lettre_recommandation, 
                      casier_judiciaire, diplome):
    """Créer une nouvelle candidature"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        date_soumission = datetime.now().strftime('%Y-%m-%d')
        
        print("   💾 Exécution de la requête SQL INSERT...")
        
        # Utiliser le placeholder approprié
        ph = get_placeholder()
        query = f'''
            INSERT INTO applications 
            (job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
             sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
             travaille_actuellement, dernier_lieu_travail, raison_depart,
             niveau_instruction, specialisation, specialisation_autre,
             langue_arabe, langue_anglaise, langue_francaise,
             autre_langue_nom, autre_langue_niveau,
             problemes_sante, nature_maladie,
             choix_travail,
             photo, cv, lettre_demande, carte_id, lettre_recommandation, 
             casier_judiciaire, diplome, status, date_soumission)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        '''
        
        cursor.execute(query, (job_id, job_title, prenom, nom, email, telephone, adresse, pays, region,
              sexe, lieu_naissance, date_naissance, nationalite, etat_civil,
              travaille_actuellement, dernier_lieu_travail, raison_depart,
              niveau_instruction, specialisation, specialisation_autre,
              langue_arabe, langue_anglaise, langue_francaise,
              autre_langue_nom, autre_langue_niveau,
              problemes_sante, nature_maladie,
              choix_travail,
              photo, cv, lettre_demande, carte_id, lettre_recommandation,
              casier_judiciaire, diplome, 'en attente', date_soumission))
        
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        print(f"   ✅ Candidature insérée dans la BDD avec ID: {app_id}")
        return app_id
        
    except Exception as e:
        print(f"   ❌ ERREUR SQL lors de la création de la candidature:")
        print(f"      Type: {type(e).__name__}")
        print(f"      Message: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        raise  # Re-lever l'exception pour que app.py puisse la gérer

def update_application_status(app_id, status):
    """Mettre à jour le statut d'une candidature"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
    conn.commit()
    conn.close()

def delete_application(app_id):
    """Supprimer une candidature et tous ses fichiers associés"""
    # Récupérer d'abord les informations de la candidature
    application = get_application_by_id(app_id)
    
    if application:
        # Supprimer les fichiers physiques
        deleted_files = delete_application_files(application)
        print(f"📁 {deleted_files} fichier(s) supprimé(s) du système de fichiers")
    
    # Supprimer l'enregistrement de la base de données
    conn = get_db_connection()
    
    # Supprimer les codes de vérification associés
    verification_count = conn.execute(
        'SELECT COUNT(*) as count FROM document_verifications WHERE application_id = ?', 
        (app_id,)
    ).fetchone()['count']
    
    if verification_count > 0:
        conn.execute('DELETE FROM document_verifications WHERE application_id = ?', (app_id,))
        print(f"🔐 {verification_count} code(s) de vérification supprimé(s)")
    
    # Supprimer la candidature
    conn.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    conn.commit()
    conn.close()

# ==================== STATISTIQUES ====================

def get_stats():
    """Récupérer les statistiques générales"""
    conn = get_db_connection()
    
    total_jobs = conn.execute('SELECT COUNT(*) as count FROM jobs').fetchone()['count']
    total_apps = conn.execute('SELECT COUNT(*) as count FROM applications').fetchone()['count']
    pending_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'en attente'").fetchone()['count']
    accepted_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'acceptée'").fetchone()['count']
    rejected_apps = conn.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'rejetée'").fetchone()['count']
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'total_applications': total_apps,
        'pending_applications': pending_apps,
        'accepted_applications': accepted_apps,
        'rejected_applications': rejected_apps
    }

# ============================================================================
# FONCTIONS DE WORKFLOW (2 PHASES)
# ============================================================================

def update_phase1_status(app_id, decision, interview_date=None, rejection_reason=None):
    """
    Mettre à jour le statut de la Phase 1
    
    Args:
        app_id: ID de la candidature
        decision: 'selected_for_interview' ou 'rejected'
        interview_date: Date de l'entretien (si sélectionné)
        rejection_reason: Raison du rejet (si rejeté)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if decision == 'selected_for_interview':
        cursor.execute('''
            UPDATE applications 
            SET phase1_status = ?,
                phase1_date = ?,
                interview_date = ?,
                workflow_phase = 'phase1',
                status = 'interview programmé'
            WHERE id = ?
        ''', (decision, current_date, interview_date, app_id))
        
        # Générer le PDF de convocation à l'entretien
        try:
            import os
            from pdf_generator import generate_interview_invitation_pdf
            
            # Récupérer les données de la candidature
            application = cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
            
            if application:
                # Créer le dossier convocations s'il n'existe pas
                convocations_dir = os.path.join('static', 'convocations')
                os.makedirs(convocations_dir, exist_ok=True)
                
                # Nom du fichier PDF
                pdf_filename = f"convocation_{app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(convocations_dir, pdf_filename)
                
                # Générer le code de vérification
                verification_code = f"CONV-{app_id}-{datetime.now().strftime('%Y%m%d')}"
                
                # Obtenir l'URL de base (à adapter selon votre déploiement)
                base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
                
                # Convertir application en dictionnaire si nécessaire
                if hasattr(application, 'keys'):
                    # C'est déjà un dict-like object (sqlite3.Row)
                    app_data = {key: application[key] for key in application.keys()}
                else:
                    # C'est un tuple, on doit récupérer les colonnes
                    columns = [description[0] for description in cursor.description]
                    app_data = dict(zip(columns, application))
                
                # Générer le PDF
                generate_interview_invitation_pdf(
                    application_data=app_data,
                    interview_date=interview_date,
                    output_path=pdf_path,
                    verification_code=verification_code,
                    base_url=base_url
                )
                
                # Sauvegarder le nom du fichier dans la base de données
                cursor.execute('UPDATE applications SET interview_invitation_pdf = ? WHERE id = ?', 
                             (pdf_filename, app_id))
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du PDF de convocation: {e}")
            import traceback
            traceback.print_exc()
        
    elif decision == 'rejected':
        cursor.execute('''
            UPDATE applications 
            SET phase1_status = ?,
                phase1_date = ?,
                rejection_reason = ?,
                workflow_phase = 'completed',
                status = 'rejetée'
            WHERE id = ?
        ''', (decision, current_date, rejection_reason, app_id))
    
    conn.commit()
    conn.close()

def update_phase2_status(app_id, decision, rejection_reason=None):
    """
    Mettre à jour le statut de la Phase 2 (après interview)
    
    Args:
        app_id: ID de la candidature
        decision: 'accepted' ou 'rejected'
        rejection_reason: Raison du rejet (si rejeté)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if decision == 'accepted':
        cursor.execute('''
            UPDATE applications 
            SET phase2_status = ?,
                phase2_date = ?,
                workflow_phase = 'completed',
                status = 'acceptée'
            WHERE id = ?
        ''', (decision, current_date, app_id))
    elif decision == 'rejected':
        cursor.execute('''
            UPDATE applications 
            SET phase2_status = ?,
                phase2_date = ?,
                rejection_reason = ?,
                workflow_phase = 'completed',
                status = 'rejetée'
            WHERE id = ?
        ''', (decision, current_date, rejection_reason, app_id))
    
    conn.commit()
    conn.close()

def mark_notification_sent(app_id, phase):
    """Marquer qu'une notification a été envoyée"""
    conn = get_db_connection()
    
    if phase == 1:
        conn.execute('UPDATE applications SET phase1_notification_sent = 1 WHERE id = ?', (app_id,))
    elif phase == 2:
        conn.execute('UPDATE applications SET phase2_notification_sent = 1 WHERE id = ?', (app_id,))
    
    conn.commit()
    conn.close()

def add_interview_notes(app_id, notes):
    """Ajouter des notes d'entretien"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET interview_notes = ? WHERE id = ?', (notes, app_id))
    conn.commit()
    conn.close()

def save_interview_invitation_pdf(app_id, pdf_filename):
    """Sauvegarder le chemin du PDF de convocation"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET interview_invitation_pdf = ? WHERE id = ?', (pdf_filename, app_id))
    conn.commit()
    conn.close()

def get_interview_invitation_pdf(app_id):
    """Récupérer le chemin du PDF de convocation"""
    conn = get_db_connection()
    result = conn.execute('SELECT interview_invitation_pdf FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return result['interview_invitation_pdf'] if result else None

def save_acceptance_letter_pdf(app_id, pdf_filename):
    """Sauvegarder le chemin du PDF de lettre d'acceptation"""
    conn = get_db_connection()
    conn.execute('UPDATE applications SET acceptance_letter_pdf = ? WHERE id = ?', (pdf_filename, app_id))
    conn.commit()
    conn.close()

def get_acceptance_letter_pdf(app_id):
    """Récupérer le chemin du PDF de lettre d'acceptation"""
    conn = get_db_connection()
    result = conn.execute('SELECT acceptance_letter_pdf FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return result['acceptance_letter_pdf'] if result else None

# ==================== FAVORIS ====================

def toggle_favorite(app_id):
    """Basculer le statut favori d'une candidature spontanée"""
    conn = get_db_connection()
    # Récupérer l'état actuel
    result = conn.execute('SELECT is_favorite, job_id FROM applications WHERE id = ?', (app_id,)).fetchone()
    
    if result:
        current_status = result['is_favorite']
        job_id = result['job_id']
        
        # Vérifier que c'est une candidature spontanée (job_id = 0)
        if job_id == 0:
            new_status = 0 if current_status == 1 else 1
            conn.execute('UPDATE applications SET is_favorite = ? WHERE id = ?', (new_status, app_id))
            conn.commit()
            conn.close()
            return new_status
        else:
            conn.close()
            return None  # Ne pas permettre les favoris pour les candidatures normales
    
    conn.close()
    return None

def is_favorite(app_id):
    """Vérifier si une candidature est marquée comme favorite"""
    conn = get_db_connection()
    result = conn.execute('SELECT is_favorite FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    return result['is_favorite'] == 1 if result else False

def get_favorite_applications():
    """Récupérer toutes les candidatures spontanées favorites"""
    conn = get_db_connection()
    applications = conn.execute('''
        SELECT * FROM applications 
        WHERE job_id = 0 AND is_favorite = 1 
        ORDER BY date_soumission DESC
    ''').fetchall()
    conn.close()
    return [dict(app) for app in applications]

