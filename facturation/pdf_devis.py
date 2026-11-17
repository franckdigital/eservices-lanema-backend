"""PDF du devis, conforme au formulaire officiel LANEMA EN 002-PG002 V08 :
en-tete « DEVIS », Ref (N° devis/annee/editeur/Direction/Sous-Direction/Laboratoire),
informations client, 1-Prestations (¹ ²), 2-Prelevement (³), accreditations et
totaux, conditions (cases a cocher), montant arrete en lettres, signatures,
notes de bas de page et N.B."""
import io
from decimal import Decimal

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from qualite.pdf_circuit import GRIS, INK, S, _box, _logo, esc

from . import devis_utils

W = A4[0] - 30 * mm
PN = ParagraphStyle("pn", parent=S["n"], fontSize=7.2, leading=8.4)


def P(texte, style="n"):
    """Paragraphe compact : le devis tient sur une page comme le formulaire papier."""
    contenu = str(texte if texte not in (None, "") else "&nbsp;").replace(chr(10), "<br/>")
    return Paragraph(contenu, PN if style == "n" else S[style])



TITRE = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER, textColor=INK)
SEC = ParagraphStyle("s", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=INK)
PETIT = ParagraphStyle("pt", fontName="Helvetica", fontSize=6.8, leading=8.2, textColor=INK)
PETITB = ParagraphStyle("ptb", fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=INK)


def _fmt(v):
    try:
        return f"{float(v):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(v)


def _image(fichier, largeur, hauteur):
    if not fichier:
        return None
    try:
        fichier.open("rb")
        data = fichier.read()
        fichier.close()
        return RLImage(io.BytesIO(data), width=largeur, height=hauteur, kind="proportional")
    except Exception:
        return None


def _pied(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(INK)
    canvas.drawString(15 * mm, 26 * mm, "EN 002-PG002 V08 DU 30-07-25 AU 30-06-27")
    canvas.setStrokeColor(INK)
    canvas.line(15 * mm, 24.5 * mm, A4[0] - 15 * mm, 24.5 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawCentredString(A4[0] / 2, 20.5 * mm, "LABORATOIRE NATIONAL D'ESSAIS DE QUALITE, DE METROLOGIE ET D'ANALYSES (LANEMA)")
    canvas.setFont("Helvetica", 6.6)
    canvas.drawCentredString(A4[0] / 2, 17.5 * mm, "Siège Social : Autoroute d'Abobo, entre la Sté SONITRA et l'Université NANGUI ABROGOUA- BP V 174 Abidjan,")
    canvas.drawCentredString(A4[0] / 2, 14.5 * mm, "E-Mail : infoline@lanema.ci  Site web : www.lanema.ci")
    canvas.drawCentredString(A4[0] / 2, 11.5 * mm, "Tel. : 01 43 11 01 01- 01 43 11 02 02- 01 43 11 03 03- 01 43 11 04 04")
    canvas.setFont("Helvetica-BoldOblique", 6.8)
    canvas.drawCentredString(A4[0] / 2, 8.5 * mm, "Avant utilisation d'un document, vérifier sa validité")
    canvas.restoreState()


def devis_pdf(proforma):
    demande = proforma.demande_devis
    profil = getattr(proforma.client, "client_profile", None)
    t = devis_utils.totaux(proforma)
    devise = proforma.devise
    date_emission = proforma.date_emission.strftime("%d/%m/%Y") if proforma.date_emission else ""
    flow = []

    # ── En-tete : logo + DEVIS ─────────────────────────────────────────────
    flow.append(Table([[_logo(), Paragraph("DEVIS", TITRE), ""]], colWidths=[45 * mm, W - 90 * mm, 45 * mm]))
    flow.append(Spacer(1, 1.5 * mm))
    ref = Table([[P(f"<b>Réf:</b> {esc(devis_utils.reference_devis(proforma))}<br/><font size=6.5>N° devis/ année/nom de l'éditeur/ Direction/Sous-Direction (s)/ Laboratoire(s)</font>"),
                  P(f"Abidjan, le {date_emission}")]], colWidths=[W * 0.72, W * 0.28])
    ref.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    flow += [ref, Spacer(1, 2 * mm)]

    # ── Informations client ────────────────────────────────────────────────
    infos = [
        ("Domaine(s) d'activité(s) :", getattr(profil, "domaine_activite", "")),
        ("Raison sociale :", getattr(profil, "raison_sociale", "") or proforma.client.get_full_name() or proforma.client.username),
        ("Adresse :", getattr(profil, "adresse", "")),
        ("Situation géographique :", getattr(profil, "situation_geographique", "")),
        ("Tél :", getattr(profil, "telephone", "")),
        ("Code client :", getattr(profil, "code_client", "")),
        ("Personne à contacter :", getattr(profil, "contact_nom", "")),
        ("E-mail :", proforma.client.email),
        ("Date de la Demande :", demande.created_at.strftime("%d/%m/%Y") if demande else ""),
        ("Nature de l'objet :", demande.objet if demande else ""),
    ]
    rows = [[P("<b>INFORMATIONS CLIENT</b>", "c"), ""]] + [[P(f"<b>{lbl}</b>"), P(esc(v))] for lbl, v in infos]
    ti = Table(rows, colWidths=[55 * mm, W - 55 * mm])
    ti.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK), ("LINEBELOW", (0, 0), (-1, -1), 0.6, INK), ("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), GRIS),
                            ("TOPPADDING", (0, 0), (-1, -1), 0.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8)]))
    flow += [ti, Spacer(1, 2.5 * mm)]

    # ── 1 - Prestations ────────────────────────────────────────────────────
    flow.append(Paragraph("<u>1-Prestations d'essais/ étalonnage/ vérification</u><super>1</super>", SEC))
    flow.append(Spacer(1, 1.5 * mm))
    lignes = devis_utils.lignes_prestations(demande)
    r1 = [[P("<b>Paramètres ou Grandeurs</b><super>2</super>", "c"), P("<b>Méthodes utilisées</b>", "c"), P("<b>P.U.</b>", "c"), P("<b>Nombre</b>", "c"), P("<b>Montant</b>", "c")]]
    for e in lignes:
        pu = Decimal(e.prix_unitaire or 0)
        marques = (" (*)" if e.accredite else "") + (" ST" if e.sous_traite else "")
        r1.append([P(esc(e.nom) + marques), P(esc(e.methode_utilisee)), P(_fmt(pu), "p"), P(str(e.quantite), "p"), P(_fmt(pu * e.quantite), "p")])
    while len(r1) < 3:
        r1.append([P("&nbsp;")] * 5)
    r1.append([P("SOUS TOTAL 1 (H.T.)", "c"), "", "", "", P(_fmt(t["sous_total_1"]), "p")])
    t1 = Table(r1, colWidths=[58 * mm, 45 * mm, 22 * mm, 22 * mm, W - 147 * mm], repeatRows=1)
    t1.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.7, INK), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("SPAN", (0, -1), (3, -1)), ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]))
    flow += [t1, Spacer(1, 2 * mm)]

    # ── 2 - Prelevement ────────────────────────────────────────────────────
    flow.append(Paragraph("<u>2-Prélèvement ou Récupération de l'appareil de mesure</u><super>3</super>", SEC))
    flow.append(Spacer(1, 1.5 * mm))
    r2 = [[P(f"<b>{h}</b>", "c") for h in ("Désignation", "Durée (h)", "Km", "Nombre", "P.U.", "Montant")]]
    for code, label, ligne in devis_utils.interventions_completes(demande):
        if ligne and (ligne.nombre or ligne.prix_unitaire):
            r2.append([P(label), P(str(ligne.duree_heures or ""), "p"), P(str(ligne.km or ""), "p"), P(str(ligne.nombre), "p"), P(_fmt(ligne.prix_unitaire), "p"), P(_fmt(ligne.montant), "p")])
        else:
            r2.append([P(label)] + [P("&nbsp;", "p")] * 5)
    r2.append([P("SOUS TOTAL 2 (H.T.)", "c"), "", "", "", "", P(_fmt(t["sous_total_2"]), "p")])
    t2 = Table(r2, colWidths=[62 * mm, 25 * mm, 18 * mm, 20 * mm, 24 * mm, W - 149 * mm])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.7, INK), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("SPAN", (0, -1), (4, -1)), ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    flow += [t2, Spacer(1, 2 * mm)]

    # ── Accreditations + totaux ────────────────────────────────────────────
    acc = [[P("<b>NOS ACCREDITATIONS</b>", "c"), "", ""], [P("<b>Grandeurs</b>"), P("<b>N° Acc</b>", "c"), P("<b>Portée Acc</b>", "c")]]
    acc += [[P(a["grandeur"]), P(a["numero"]), P(a["portee"], "p")] for a in devis_utils.ACCREDITATIONS]
    ta = Table(acc, colWidths=[20 * mm, 24 * mm, 80 * mm])
    ta.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.7, INK), ("INNERGRID", (0, 1), (-1, -1), 0.5, INK), ("SPAN", (0, 0), (2, 0)), ("BACKGROUND", (0, 0), (-1, 1), GRIS)]))
    tot = [("TOTAL H.T.", _fmt(t["total_ht"])), ("Remise", _fmt(t["remise"]) if t["remise"] else ""), ("Montant H.T.", _fmt(t["montant_ht"])),
           ("T.V.A.", _fmt(t["tva"])), ("TOTAL T.T.C.", _fmt(t["montant_ttc"]) + f" {devise}")]
    tt = Table([[P(a), P(b, "p")] for a, b in tot], colWidths=[30 * mm, W - 124 * mm - 34 * mm])
    tt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.7, INK), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
    flow += [Table([[ta, "", tt]], colWidths=[126 * mm, 4 * mm, W - 130 * mm]), Spacer(1, 2.5 * mm)]

    # ── Conditions ─────────────────────────────────────────────────────────
    oui = demande.accord_sous_traitance if demande else None
    sous = ""
    if demande and demande.accord_sous_traitance:
        noms = list(demande.sous_traitants_choisis.values_list("nom", flat=True))
        if demande.sous_traitants_souhaits_libres:
            noms.append(f"autres souhaits : {demande.sous_traitants_souhaits_libres}")
        if noms:
            sous = f"<br/><font size=7>Sous-traitant(s) : {esc(', '.join(noms))}</font>"
    retour = demande.retour_materiel_gere_labo if demande else None
    lieu = demande.lieu_realisation if demande else ""
    decl = demande.declaration_conformite_souhaitee if demande else None
    delai = f"{demande.delai_realisation_jours} jours ouvrés" if demande and demande.delai_realisation_jours else ""
    cond = [
        [P("<b>Délais de réalisation</b>"), P(esc(delai))],
        [P("<b>Accord de Sous-traitance</b>"), P(f"<b>Oui {_box(oui is True)} &nbsp;&nbsp;&nbsp;&nbsp; Non {_box(oui is False)}</b>{sous}")],
        [P("<b>Le laboratoire doit-il gérer le renvoi du matériel (*)</b>"),
         P(f"<b>Oui {_box(retour is True)} &nbsp;&nbsp;&nbsp;&nbsp; Non {_box(retour is False)}</b><br/><font size=6.5><b>(*) : Si oui, le coût sera intégré dans le devis</b></font>")],
        [P("<b>Lieu de réalisation des Travaux</b>"), P(f"<b>Laboratoire {_box(lieu == 'LABORATOIRE')} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Site Client {_box(lieu == 'SITE_CLIENT')}</b>")],
        [P("<b>Observations particulières</b>"), P(esc(demande.observations_particulieres if demande else ""))],
        [P("<b>Déclaration de Conformité</b>", "c"), ""],
        [P(f"<b>Oui {_box(decl is True)} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Non {_box(decl is False)}</b>"), P(f"<b>Règle de décision :</b> {esc(demande.regle_decision if demande else '')}")],
    ]
    tc = Table(cond, colWidths=[62 * mm, W - 62 * mm])
    tc.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK), ("LINEBELOW", (0, 0), (-1, -2), 0.6, INK), ("LINEAFTER", (0, 0), (0, 4), 0.6, INK), ("LINEAFTER", (0, 6), (0, 6), 0.6, INK),
                            ("SPAN", (0, 5), (1, 5)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]))
    flow += [tc, Spacer(1, 2 * mm)]

    flow.append(P(f"Arrêté le présent devis à la somme de : <b>{esc(devis_utils.montant_en_lettres(t['montant_ttc'], devise))}</b> ({_fmt(t['montant_ttc'])} {devise} T.T.C.)"))
    flow.append(Spacer(1, 3 * mm))

    # ── Signatures ─────────────────────────────────────────────────────────
    client_cell = [P("<b><u>Le Client</u></b>")]
    if proforma.lu_approuve:
        quand = timezone.localtime(proforma.lu_approuve_le).strftime("%d/%m/%Y à %H:%M") if proforma.lu_approuve_le else ""
        client_cell.append(P(f"<b><i><font color='#166534'>Lu et approuvé</font></i></b><br/><font size=6.5>le {quand}</font>"))
        img = _image(proforma.lu_approuve_signature, 55 * mm, 22 * mm)
        if img:
            client_cell.append(img)
    resp_cell = [P("<b><u>Le Responsable Technique</u></b>")]
    if proforma.signature_responsable_appliquee and proforma.valide_par_responsable:
        rp = getattr(proforma.valide_par_responsable, "client_profile", None)
        for fichier, w, h in ((getattr(rp, "cachet_image", None), 24 * mm, 24 * mm), (getattr(rp, "signature_image", None), 40 * mm, 18 * mm)):
            img = _image(fichier, w, h)
            if img:
                resp_cell.append(img)
        resp_cell.append(P(esc(proforma.valide_par_responsable.get_full_name() or proforma.valide_par_responsable.username), "p"))
    ts = Table([[client_cell, resp_cell]], colWidths=[W * 0.5, W * 0.5], rowHeights=[24 * mm])
    ts.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "CENTER")]))
    flow += [ts, Spacer(1, 2 * mm)]

    # ── Notes de bas de page + N.B ─────────────────────────────────────────
    notes = Paragraph("<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u><br/>"
                      "<super>1</super> Barrer la mention inutile<br/>"
                      "<super>2</super> Les prestations Sous-traités sont marquées de la mention <b>\"ST\"</b>, les prestations accréditées sont marquées comme-ci (*)<br/>"
                      "<super>3</super> Cas des appareils à retourner en Métrologie", PETIT)
    nb = Paragraph("<u><b>N.B</b></u> :<br/><b>- Le LANEMA s'engage à garder confidentiel toutes informations reçues dans le cadre des présents travaux sauf injonction.</b><br/>"
                   "- La signature de ce devis avec la mention <b>\"Lu et Approuvé\"</b> atteste de votre acceptation des termes du contrat.<br/>"
                   "<b>(Voir conditions générales au verso)</b>", PETIT)
    flow.append(Table([[notes, nb]], colWidths=[W * 0.5, W * 0.5], style=[("VALIGN", (0, 0), (-1, -1), "TOP")]))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=8 * mm, bottomMargin=29 * mm, title=f"Devis {proforma.numero}")
    doc.build(flow, onFirstPage=_pied, onLaterPages=_pied)
    return buf.getvalue()
