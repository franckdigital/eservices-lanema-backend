"""Generation PDF facture DAE — meme stack que core/pdf_utils.py."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.pdf_utils import _armoirie_image


def generate_facture_dae_pdf(facture):
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
    total_style = ParagraphStyle('Total', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold', alignment=TA_RIGHT)

    story = []
    armoirie = _armoirie_image(3.0, 3.0)
    if armoirie:
        story.append(armoirie)
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("LANEMA — Direction de l'Aéronautique", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("FACTURE", title_style))
    story.append(Paragraph(f"N° {facture.reference}", center_style))
    story.append(Spacer(1, 0.8 * cm))

    infos = [
        ('Client', facture.client.nom if facture.client else '—'),
        ('Ordre de travail', facture.ordre_travail.reference if facture.ordre_travail else '—'),
        ('Date d\'émission', facture.date_emission.strftime('%d/%m/%Y') if facture.date_emission else '—'),
        ('Date de paiement', facture.date_paiement.strftime('%d/%m/%Y') if facture.date_paiement else '—'),
        ('Statut', facture.get_statut_display()),
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

    def _fcfa(v):
        return f"{v:,.0f} FCFA".replace(',', ' ')

    montants = Table(
        [
            ['Main d\'œuvre', _fcfa(facture.montant_main_oeuvre)],
            ['Pièces', _fcfa(facture.montant_pieces)],
            ['Frais supplémentaires', _fcfa(facture.frais_supplementaires)],
            ['Montant HT', _fcfa(facture.montant_ht)],
            [f'TVA ({facture.taux_tva}%)', _fcfa(facture.montant_ttc - facture.montant_ht)],
            ['Montant TTC', _fcfa(facture.montant_ttc)],
        ],
        colWidths=[13 * cm, 4 * cm],
    )
    montants.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 13),
        ('LINEABOVE', (0, 3), (-1, 3), 0.5, colors.HexColor('#CCCCCC')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#0B57A4')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(montants)

    doc.build(story)
    buffer.seek(0)
    return buffer
