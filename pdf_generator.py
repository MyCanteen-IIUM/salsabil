"""
Module de génération de documents PDF pour le recrutement
Génère des convocations d'entretien officielles avec QR code de vérification
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from datetime import datetime
import os
import qrcode
from io import BytesIO
import hashlib
import hashlib
import secrets

def generate_verification_code(application_id, document_type):
    """
    Générer un code de vérification unique et sécurisé
    
    Args:
        application_id: ID de la candidature
        document_type: Type de document (convocation ou acceptation)
    
    Returns:
        str: Code de vérification unique
    """
    # Créer une chaîne unique basée sur l'ID, le type et un sel aléatoire
    timestamp = datetime.now().isoformat()
    random_salt = secrets.token_hex(16)
    data = f"{application_id}-{document_type}-{timestamp}-{random_salt}"
    
    # Générer un hash SHA256
    verification_hash = hashlib.sha256(data.encode()).hexdigest()
    
    # Retourner les 16 premiers caractères du hash (suffisant et plus lisible)
    return verification_hash[:16].upper()


def create_qr_code(verification_url):
    """
    Créer un QR code pour l'URL de vérification
    
    Args:
        verification_url: URL complète de vérification du document
    
    Returns:
        BytesIO: Image du QR code en mémoire
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    # Créer l'image du QR code
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en BytesIO pour ReportLab
    img_buffer = BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def generate_interview_invitation_pdf(application_data, interview_date, output_path, verification_code=None, base_url="http://localhost:5000"):
    """
    Générer un PDF de convocation à l'entretien
    
    Args:
        application_data: Dictionnaire contenant les infos du candidat
        interview_date: Date et heure de l'entretien (format: "2025-10-15 14:00")
        output_path: Chemin où sauvegarder le PDF
    
    Returns:
        str: Chemin du fichier PDF généré
    """
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container pour les éléments du document
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour le sous-titre
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#3498db'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour le corps
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=12
    )
    
    # Style pour les informations importantes
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Style pour la date en haut à droite
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_RIGHT,
        fontName='Helvetica'
    )
    
    # ========================================================================
    # En-tête : Logo et informations de l'entreprise
    # ========================================================================
    
    # Date d'émission
    emission_date = datetime.now().strftime('%d/%m/%Y')
    elements.append(Paragraph(f"Émis le {emission_date}", date_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Logo de l'entreprise
    logo_path = os.path.join('static', 'img', 'logo.jpeg')
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=4*cm, height=4*cm, kind='proportional')
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.3*cm))
        except Exception as e:
            print(f"Erreur lors du chargement du logo: {e}")
            # Fallback au texte si le logo ne peut pas être chargé
            elements.append(Paragraph("SALSABIL", title_style))
            elements.append(Paragraph("Entreprise de Recrutement", subtitle_style))
            elements.append(Spacer(1, 0.3*cm))
    else:
        # Si le logo n'existe pas, utiliser le texte
        elements.append(Paragraph("SALSABIL", title_style))
        elements.append(Paragraph("Entreprise de Recrutement", subtitle_style))
        elements.append(Spacer(1, 0.3*cm))
    
    # ========================================================================
    # Titre du document
    # ========================================================================
    
    title = Paragraph("CONVOCATION À UN ENTRETIEN", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*cm))
    
    # ========================================================================
    # Destinataire
    # ========================================================================
    
    recipient = f"""
    <b>À l'attention de :</b><br/>
    <b>{application_data['prenom']} {application_data['nom']}</b><br/>
    {application_data['email']}<br/>
    {application_data['telephone']}<br/>
    {application_data['adresse']}
    """
    elements.append(Paragraph(recipient, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Corps de la lettre
    # ========================================================================
    
    # Salutation
    salutation = f"Madame, Monsieur {application_data['nom']},"
    elements.append(Paragraph(salutation, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Introduction
    # For spontaneous applications, use the selected job title if available
    job_title_display = application_data.get('selected_job_title') or application_data['job_title']
    
    intro = f"""
    Suite à votre candidature pour le poste de <b>{job_title_display}</b>, 
    nous avons le plaisir de vous informer que votre profil a retenu notre attention.
    """
    elements.append(Paragraph(intro, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Convocation
    convocation = """
    Nous souhaitons vous rencontrer afin d'échanger sur votre parcours, vos compétences 
    et vos motivations. Nous vous prions de bien vouloir vous présenter à notre siège 
    aux date et heure suivantes :
    """
    elements.append(Paragraph(convocation, body_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Informations de l'entretien (Encadré)
    # ========================================================================
    
    # Parser la date de l'entretien
    try:
        interview_dt = datetime.strptime(interview_date, '%Y-%m-%dT%H:%M')
        formatted_date = interview_dt.strftime('%A %d %B %Y à %H:%M')
        formatted_day = interview_dt.strftime('%d/%m/%Y')
        formatted_time = interview_dt.strftime('%H:%M')
    except:
        formatted_date = interview_date
        formatted_day = interview_date
        formatted_time = "À confirmer"
    
    # Traduction des jours en français
    days_fr = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }
    months_fr = {
        'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
        'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
        'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
    }
    
    for eng, fr in days_fr.items():
        formatted_date = formatted_date.replace(eng, fr)
    for eng, fr in months_fr.items():
        formatted_date = formatted_date.replace(eng, fr)
    
    # Créer un tableau pour les informations
    interview_info = [
        ['📅 Date', formatted_day],
        ['🕐 Heure', formatted_time],
        ['📍 Lieu', 'Siège de SALSABIL'],
        ['💼 Poste', job_title_display],
    ]
    
    interview_table = Table(interview_info, colWidths=[5*cm, 10*cm])
    interview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    
    elements.append(interview_table)
    elements.append(Spacer(1, 0.2*cm))
    
    # ========================================================================
    # Instructions importantes
    # ========================================================================
    
    important_title = Paragraph("<b>⚠️ IMPORTANT :</b>", info_style)
    elements.append(important_title)
    elements.append(Spacer(1, 0.1*cm))
    
    instructions = """
    • <b>Merci de vous présenter 10 minutes avant l'heure prévue.</b><br/>
    • <b>Ce document est obligatoire pour accéder à nos locaux.</b> 
      Veuillez le présenter à l'accueil.<br/>
    • Veuillez vous munir d'une <b>pièce d'identité en cours de validité</b>.<br/>
    • En cas d'empêchement, merci de nous prévenir <b>au moins 24 heures à l'avance</b>.
    """
    elements.append(Paragraph(instructions, body_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # ========================================================================
    # QR Code en haut à gauche et texte code en bas de page
    # ========================================================================
    
    def add_qr_and_code(canvas, doc):
        if verification_code:
            # QR en haut à gauche
            verification_url = f"{base_url}/verify/{verification_code}"
            qr_buffer = create_qr_code(verification_url)
            from reportlab.lib.utils import ImageReader
            qr_img = ImageReader(qr_buffer)
            canvas.saveState()
            canvas.drawImage(qr_img, x=1.2*cm, y=A4[1]-4*cm, width=3*cm, height=3*cm, mask='auto')
            canvas.restoreState()
            # Texte code en bas centré
            code_text = f"Code de vérification : {verification_code}"
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 12)
            canvas.setFillColor(colors.HexColor('#2c3e50'))
            canvas.drawCentredString(A4[0]/2, 1.7*cm, code_text)
            canvas.restoreState()
    
    # ========================================================================
    
    # ========================================================================
    # Pied de page avec numéro de référence
    # ========================================================================
    
    reference = f"Référence : CONV-{application_data['id']}-{datetime.now().strftime('%Y%m%d')}"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(reference, footer_style))
    
    # ========================================================================
    # Construire le PDF
    # ========================================================================
    
    doc.build(elements, onFirstPage=add_qr_and_code, onLaterPages=add_qr_and_code)
    
    return output_path


def generate_interview_invitation_filename(candidate_name, application_id):
    """
    Générer un nom de fichier standardisé pour la convocation
    
    Args:
        candidate_name: Nom complet du candidat
        application_id: ID de la candidature
    
    Returns:
        str: Nom de fichier formaté
    """
    # Nettoyer le nom (enlever les caractères spéciaux)
    import re
    clean_name = re.sub(r'[^\w\s-]', '', candidate_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"Convocation_Entretien_{clean_name}_{application_id}_{timestamp}.pdf"


def generate_acceptance_letter_pdf(application_data, output_path, verification_code=None, base_url="http://localhost:5000"):
    """
    Générer un PDF de lettre d'acceptation finale après interview
    
    Args:
        application_data: Dictionnaire contenant les infos du candidat
        output_path: Chemin où sauvegarder le PDF
        verification_code: Code de vérification unique (optionnel)
        base_url: URL de base pour le QR code
    
    Returns:
        str: Chemin du fichier PDF généré
    """
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container pour les éléments du document
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # ========================================================================
    # En-tête avec logo
    # ========================================================================
    
    logo_path = "static/img/logo.jpeg"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3*cm, height=3*cm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 0.5*cm))
    
    # Style pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2ecc71'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    title = "🎉 LETTRE D'ACCEPTATION 🎉"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Sous-titre
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#27ae60'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("Bienvenue dans l'équipe SALSABIL !", subtitle_style))
    elements.append(Spacer(1, 1*cm))
    
    # ========================================================================
    # Date et lieu
    # ========================================================================
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    current_date = datetime.now().strftime('%d/%m/%Y')
    date_text = f"Djibouti, le {current_date}"
    elements.append(Paragraph(date_text, date_style))
    elements.append(Spacer(1, 1*cm))
    
    # ========================================================================
    # Destinataire
    # ========================================================================
    
    recipient_style = ParagraphStyle(
        'Recipient',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    recipient = f"""
    <b>À l'attention de :</b><br/>
    {application_data.get('prenom', '')} {application_data.get('nom', '')}<br/>
    {application_data.get('adresse', 'Djibouti')}<br/>
    Email : {application_data.get('email', '')}<br/>
    Tél : {application_data.get('telephone', '')}
    """
    elements.append(Paragraph(recipient, recipient_style))
    elements.append(Spacer(1, 1*cm))
    
    # ========================================================================
    # Corps de la lettre
    # ========================================================================
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_JUSTIFY,
        leading=16,
        fontName='Helvetica'
    )
    
    # Objet
    object_style = ParagraphStyle(
        'Object',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    job_title = application_data.get('job_title', 'le poste proposé')
    
    elements.append(Paragraph(f"<b>Objet : Acceptation de votre candidature - {job_title}</b>", object_style))
    elements.append(Spacer(1, 0.8*cm))
    
    # Salutation
    salutation = f"Madame, Monsieur {application_data.get('nom', '')},"
    elements.append(Paragraph(salutation, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Paragraphe 1 : Félicitations
    para1 = f"""
    C'est avec un immense plaisir que nous vous informons que votre candidature pour le poste de 
    <b>{job_title}</b> au sein de SALSABIL a été <b style="color: #27ae60;">retenue</b>.
    """
    elements.append(Paragraph(para1, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Paragraphe 2 : Qualités
    para2 = """
    Après avoir examiné attentivement votre dossier et suite à l'entretien que vous avez passé, 
    nous avons été convaincus par vos compétences, votre motivation et votre professionnalisme. 
    Vous avez démontré toutes les qualités requises pour réussir dans ce poste.
    """
    elements.append(Paragraph(para2, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Paragraphe 3 : Prochaines étapes
    para3 = """
    Nous vous invitons à prendre contact avec notre service des ressources humaines dans les 
    <b>7 jours ouvrables</b> suivant la réception de cette lettre afin de finaliser les 
    formalités administratives et convenir de votre date de prise de fonction.
    """
    elements.append(Paragraph(para3, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Encadré avec informations de contact
    contact_data = [
        ['📞 Téléphone', '+253 XXX XXX XXX'],
        ['📧 Email', 'rh@salsabil.dj'],
        ['📍 Adresse', 'SALSABIL, Djibouti']
    ]
    
    contact_table = Table(contact_data, colWidths=[5*cm, 10*cm])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(contact_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # Paragraphe 4 : Félicitations finales
    para4 = """
    Nous sommes ravis de vous accueillir au sein de notre équipe et nous sommes convaincus que 
    votre arrivée contribuera grandement au développement et au succès de SALSABIL.
    """
    elements.append(Paragraph(para4, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Clôture
    closing = """
    Dans l'attente de vous rencontrer très prochainement, nous vous prions d'agréer, 
    Madame, Monsieur, l'expression de nos salutations distinguées.
    """
    elements.append(Paragraph(closing, body_style))
    elements.append(Spacer(1, 1*cm))
    
    # Signature
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    signature = """
    <b>Le Directeur des Ressources Humaines</b><br/>
    <b>SALSABIL</b>
    """
    elements.append(Paragraph(signature, signature_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # ========================================================================
    # QR Code en haut à gauche et texte code en bas de page
    # ========================================================================
    def add_qr_and_code(canvas, doc):
        if verification_code:
            # QR en haut à gauche
            verification_url = f"{base_url}/verify/{verification_code}"
            qr_buffer = create_qr_code(verification_url)
            from reportlab.lib.utils import ImageReader
            qr_img = ImageReader(qr_buffer)
            canvas.saveState()
            canvas.drawImage(qr_img, x=1.2*cm, y=A4[1]-4*cm, width=3*cm, height=3*cm, mask='auto')
            canvas.restoreState()
            # Texte code en bas centré
            code_text = f"Code de vérification : {verification_code}"
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 12)
            canvas.setFillColor(colors.HexColor('#2c3e50'))
            canvas.drawCentredString(A4[0]/2, 1.7*cm, code_text)
            canvas.restoreState()
    # ========================================================================
    
    # ========================================================================
    # Pied de page
    # ========================================================================
    
    reference = f"Référence : ACCEPT-{application_data['id']}-{datetime.now().strftime('%Y%m%d')}"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(reference, footer_style))
    
    # ========================================================================
    # Construire le PDF
    # ========================================================================
    
    doc.build(elements, onFirstPage=add_qr_and_code, onLaterPages=add_qr_and_code)
    
    return output_path


def generate_acceptance_letter_filename(candidate_name, application_id):
    """
    Générer un nom de fichier standardisé pour la lettre d'acceptation
    
    Args:
        candidate_name: Nom complet du candidat
        application_id: ID de la candidature
    
    Returns:
        str: Nom de fichier formaté
    """
    import re
    clean_name = re.sub(r'[^\w\s-]', '', candidate_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"Lettre_Acceptation_{clean_name}_{application_id}_{timestamp}.pdf"
