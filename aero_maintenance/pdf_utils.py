"""Generation PDF pour la DAE (Direction de l'Aeronautique) — meme stack que
core/pdf_utils.py (reportlab, SimpleDocTemplate), reutilise directement
create_pdf_response(buffer, filename) pour la reponse HTTP."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.pdf_utils import _armoirie_image


def generate_certificat_ot_pdf(ordre_travail, numero_certificat=None):
    """Certificat de fin d'intervention pour un Ordre de travail TERMINE.
    numero_certificat est le numero dedie CERT-DAE-AAAA-NNNNN (cf.
    CertificatDAE) — a defaut, on retombe sur la reference de l'OT."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=11, spaceAfter=4, alignment=TA_CENTER)
    center_style = ParagraphStyle('Center', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=10)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=18, spaceAfter=12)

    aeronef = ordre_travail.aeronef
    technicien = ordre_travail.technicien
    technicien_nom = (technicien.get_full_name() or technicien.username) if technicien else 'Non renseigné'

    story = []
    armoirie = _armoirie_image(3.0, 3.0)
    if armoirie:
        story.append(armoirie)
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("RÉPUBLIQUE DE CÔTE D'IVOIRE", subtitle_style))
    story.append(Paragraph("LANEMA — Direction de l'Aéronautique", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("CERTIFICAT DE FIN D'INTERVENTION", title_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"N° {numero_certificat or ordre_travail.reference}", center_style))
    story.append(Spacer(1, 0.8 * cm))

    infos = [
        ('Aéronef', aeronef.immatriculation if aeronef else '—'),
        ('Type aéronef', (aeronef.type_aeronef or '—') if aeronef else '—'),
        ('Client', aeronef.client.nom if aeronef and aeronef.client else '—'),
        ('Type d\'intervention', ordre_travail.get_type_intervention_display()),
        ('Technicien', technicien_nom),
        ('Date de demande', ordre_travail.date_demande.strftime('%d/%m/%Y') if ordre_travail.date_demande else '—'),
        ('Date de début', ordre_travail.date_debut.strftime('%d/%m/%Y') if ordre_travail.date_debut else '—'),
        ('Date de fin', ordre_travail.date_fin.strftime('%d/%m/%Y') if ordre_travail.date_fin else '—'),
        ('Statut', ordre_travail.get_statut_display()),
    ]
    table = Table(
        [[Paragraph(l, label_style), Paragraph(v or '—', value_style)] for l, v in infos],
        colWidths=[6 * cm, 11 * cm],
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0F2FF')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0B57A4')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 1 * cm))

    texte = (
        f"Nous certifions que l'intervention <b>{ordre_travail.get_type_intervention_display()}</b> "
        f"sur l'aéronef <b>{aeronef.immatriculation if aeronef else '—'}</b> a été réalisée et clôturée "
        f"conformément aux procédures de la Direction de l'Aéronautique du LANEMA. "
        f"Le présent certificat est délivré pour servir et valoir ce que de droit."
    )
    story.append(Paragraph(texte, body_style))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("Le Responsable DAE", center_style))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("Signature et cachet", center_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
