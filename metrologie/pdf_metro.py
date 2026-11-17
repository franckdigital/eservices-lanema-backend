"""PDF de la Fiche d'execution des travaux de metrologie (EN 004-PG 002 V06) et du
Certificat d'etalonnage (chaine nationale d'etalonnage)."""
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from qualite.pdf_circuit import GRIS, INK, P, S, W, _box, _logo, _pied_adresse, esc

from . import circuit_metro


def _fmt_dt(iso):
    if not iso:
        return ""
    from datetime import datetime
    dt = datetime.fromisoformat(iso) if isinstance(iso, str) else iso
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def _fmt_d(d):
    return d.strftime("%d/%m/%Y") if d else ""


# ═══════════════════════════════════════════════════════════════════════════
# Fiche d'execution des travaux de metrologie
# ═══════════════════════════════════════════════════════════════════════════

def ftm_pdf(fiche):
    d = circuit_metro.ftm_data(fiche)
    flow = []
    entete = Table(
        [[_logo(), P("FICHE<br/>D'EXECUTION<br/>DES TRAVAUX<br/>DE<br/>METROLOGIE", "c"), P("CODE", "c"), P("DATE DE<br/>CREATION/<br/>REVSION", "c"),
          P("A<br/>REVISER<br/>LE", "c"), P("VERSION", "c"), P("PAGE", "c")],
         ["", "", P("EN 004-PG 002", "c"), P("<i>30/07/2025</i>", "c"), P("<i>30/06/2027</i>", "c"), P("<i>06</i>", "c"), P("1 de 1", "c")]],
        colWidths=[28 * mm, 38 * mm, 26 * mm, 26 * mm, 24 * mm, 24 * mm, 14 * mm],
    )
    entete.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.8, INK), ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow += [entete, Spacer(1, 3 * mm)]

    def ligne_cases(titre, options, choisis):
        return " &nbsp; ".join(f"{lib} {_box(code in choisis)}" for code, lib in options)

    blocs = []
    blocs.append([P(f"N°FET {esc(d['numero'])}<super>1</super>", "c")])
    blocs.append([P("INFORMATIONS CLIENT", "c")])
    blocs.append([Table([[P("Code Client", "b"), P(esc(d["client"]["code_client"]) + f" <font color='#666666'>{esc(d['client']['raison_sociale'])}</font>")]], colWidths=[30 * mm, W - 34 * mm])])
    blocs.append([P("DESCRIPTION DE L'EQUIPEMENT<super>2</super>", "c")])

    lignes = [[P(t, "pb") for t in ("Désignation", "Constructeur", "Modèle/Type", "N° de Série", "Nature<br/>(Etalonnage, Vérification, ...)")]]
    for e in d["equipements"]:
        code = f"<br/><font size=6 color='#555555'>{esc(e['code'])}</font>" if e["code"] else ""
        lignes.append([P(esc(e["designation"]) + code, "p"), P(esc(e["constructeur"]), "p"), P(esc(e["modele"]), "p"), P(esc(e["numero_serie"]), "p"), P(esc(e["nature"]), "p")])
    while len(lignes) < 11:
        lignes.append([P("&nbsp;", "p")] * 5)
    tab = Table(lignes, colWidths=[40 * mm, 32 * mm, 34 * mm, 34 * mm, W - 140 * mm - 4], rowHeights=[None] + [8 * mm] * (len(lignes) - 1))
    tab.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    blocs.append([tab])

    blocs.append([P("PRESTATIONS", "c")])
    prest = [
        [P("<b><i>LIEU DE REALISATION</i></b>", "p"), P(f"Laboratoire {_box(d['lieu_realisation'] == 'LABORATOIRE')} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Site client {_box(d['lieu_realisation'] == 'SITE_CLIENT')}", "n")],
        [P("<b><i>OPERATIONS PRELIMINAIRES</i></b>", "p"),
         P(ligne_cases("", [("EXIGENCES_CLIENTS", "Exigences Clients"), ("DOCUMENTS_LANEMA", "Documents LANEMA"), ("SPECS_CONSTRUCTEUR", "Spécifications constructeur"), ("DOCUMENTS_NORMATIFS", "Documents normatifs")], d["operations_preliminaires"]), "n")],
        [P("<b><i>NOMBRE DE MESURES PAR POINT SUIVANT :</i></b>", "p"),
         P(ligne_cases("", [("DOC_CLIENT", "Document Client"), ("DOC_LANEMA", "Document LANEMA"), ("SPECS_CONSTRUCTEUR", "Spécifications Constructeur")], d["nombre_mesures_references"])
           + f"<br/>Définition des points : {esc(d['definition_points'])}<br/>Observations : {esc(d['observations_mesures'])}", "n")],
        [P("<b><i>ERREURS MAXIMALES TOLEREES SUIVANT :</i></b>", "p"),
         P(ligne_cases("", [("DOC_CLIENT", "Document Client"), ("DOC_LANEMA", "Document LANEMA"), ("SPECS_CONSTRUCTEUR", "Spécification Constructeur")], d["erreurs_max_references"]), "n")],
        [P("<b><i>JUGEMENT DE CONFORMITE SUIVANT :</i></b>", "p"),
         P(ligne_cases("", [("DOC_CLIENT", "Document Client"), ("SPECS_PARTICULIERES_CONSTRUCTEUR", "Spécifications particulières constructeur"), ("DOCS_NORMATIFS", "Documents Normatifs")], d["jugement_references"]), "n")],
    ]
    t_prest = Table(prest, colWidths=[48 * mm, W - 52 * mm])
    t_prest.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    blocs.append([t_prest])

    recu = f"{esc(d['receptionne_par_nom'] or '')} {('— ' + _fmt_dt(d['date_reception_dmct'])) if d['date_reception_dmct'] else ''}"
    trav = Table([
        [P("Travaux au Laboratoire", "c"), P("Travaux sur Site Client", "c")],
        [P(f"<i>Date d'arrivée du matériel à la réception :</i> {_fmt_d(d['date_arrivee_materiel'])}"), P(f"<i>Date d'arrivée :</i> {_fmt_d(d['date_arrivee_site'])}")],
        [P(f"<i>Date de transmission au laboratoire</i> {_fmt_dt(d['date_transmission_dmct'])}<br/><i>Réceptionné par : Nom et Visa :</i> {recu}"),
         P(f"<i>Interlocuteur :</i> {esc(d['interlocuteur_site'])}<br/><i>Visa :</i> {esc(d['visa_site'])}")],
        [P(f"<i>Date de début des travaux :</i> {_fmt_d(d['date_debut_travaux'])}"), P(f"<i>Date de début des travaux :</i> {_fmt_d(d['date_debut_site'])}")],
        [P(f"<i>Date de fin des travaux :</i> {_fmt_d(d['date_fin_travaux'])}"), P(f"<i>Date de fin des travaux :</i> {_fmt_d(d['date_fin_site'])}")],
    ], colWidths=[(W - 4) / 2, (W - 4) / 2])
    trav.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    blocs.append([trav])

    g = d["decision_globale"]
    detail = "".join(
        f"<br/><font size=7>{esc(e['code'] or e['designation'])} : {dict(circuit_metro.DECISIONS).get(e['decision'], '—')}"
        + (f" — {esc(e['reserves'])}" if e["reserves"] else "") + "</font>"
        for e in d["equipements"] if e["decision"]
    ) if len(d["equipements"]) > 1 else ""
    blocs.append([P("Décision d'acceptation de(s) l'équipement(s)", "c")])
    dec = Table([[P(f"Conforme {_box(g == 'CONFORME')}<br/>Non Conforme {_box(g == 'NON_CONFORME')}"), P(f"Sous réserve {_box(g == 'SOUS_RESERVE')}{detail}")]], colWidths=[60 * mm, W - 64 * mm])
    dec.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    blocs.append([dec])

    t = Table(blocs, colWidths=[W])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, INK), ("LINEBELOW", (0, 0), (-1, -2), 0.6, INK),
        ("BACKGROUND", (0, 1), (0, 1), GRIS), ("BACKGROUND", (0, 3), (0, 3), GRIS), ("BACKGROUND", (0, 5), (0, 5), GRIS), ("BACKGROUND", (0, 9), (0, 9), GRIS),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    flow += [t, Spacer(1, 3 * mm), P("<super>1</super> Année/Direction/N° d'ordre &nbsp;&nbsp; <super>2</super> A remplir par la réception", "foot")]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=10 * mm, bottomMargin=26 * mm, title=f"FET métrologie {d['numero']}")
    pied = lambda c, dc: _pied_adresse(c, dc, "")
    doc.build(flow, onFirstPage=pied, onLaterPages=pied)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
# Certificat d'etalonnage
# ═══════════════════════════════════════════════════════════════════════════

def certificat_pdf(cert):
    data = circuit_metro.certificat_data(cert)
    nb = 2
    for _ in range(2):
        contenu, pages = _construire_certificat(data, nb)
        if pages == nb:
            break
        nb = pages
    return contenu


def _construire_certificat(c, nb_pages):
    e = c["equipement"]
    cl = c["delivre_a"]
    big = ParagraphStyle("big", fontName="Helvetica-Bold", fontSize=17, leading=21, alignment=TA_CENTER, textColor=INK)
    lab = ParagraphStyle("lab", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=INK)
    val = ParagraphStyle("val", fontName="Helvetica", fontSize=10, leading=13, textColor=INK)

    num_aff = esc(c["numero"]) if c["numero"] else "<font color='#b91c1c'>(projet — non numéroté)</font>"
    chaine = f"CHAÎNE NATIONALE D'ÉTALONNAGE<br/>{esc(c['grandeur_display']).upper()}"
    flow = [Table([[_logo(), Paragraph(f"<b>{chaine}</b>", ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=INK))]], colWidths=[50 * mm, W - 50 * mm]),
            Spacer(1, 55 * mm),
            Paragraph("CERTIFICAT D'ETALONNAGE", big),
            Paragraph(f"CE N° {num_aff}", big),
            Spacer(1, 28 * mm),
            Paragraph("DÉLIVRÉ A :", lab),
            Paragraph(f"{esc(cl['raison_sociale'])}<br/>{esc(cl['adresse'])}{(' — ' + esc(cl['situation_geographique'])) if cl['situation_geographique'] else ''}", val),
            Spacer(1, 16 * mm),
            Paragraph("INSTRUMENT ÉTALONNÉ", lab), Spacer(1, 4 * mm),
            Paragraph(f"Désignation : {esc(e['designation'])}", val), Spacer(1, 3 * mm),
            Paragraph(f"Constructeur : {esc(e['constructeur'])}", val), Spacer(1, 3 * mm),
            Table([[Paragraph(f"Type : {esc(e['type_modele'])}", val), Paragraph(f"N° de série : {esc(e['numero_serie'])}<br/>N° d'identification : {esc(e['numero_identification'])}", val)]], colWidths=[W * 0.5, W * 0.5]),
            Spacer(1, 6 * mm),
            Paragraph(f"Ce rapport comprend {nb_pages:02d} pages", val), Spacer(1, 8 * mm),
            Table([["", Paragraph(f"<font size=8>Date d'émission : {_fmt_d(c['date_emission'])}</font><br/><br/><br/>LE DIRECTEUR<br/>DE LA METROLOGIE ET DES CONTROLES<br/>TECHNIQUES<br/><br/><br/><br/><b><i>{esc(c['directeur_nom']) or 'NOM &amp; PRENOM'}</i></b>", val)]], colWidths=[W * 0.45, W * 0.55]),
            ]
    if c["accredite"]:
        flow.append(Spacer(1, 4 * mm))
        flow.append(Paragraph("<font size=8><b>Étalonnage réalisé sous accréditation SOAC (Système Ouest Africain d'Accréditation).</b></font>", S["n"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph("<font size=7>REPRODUCTION DE CE CERTIFICAT N'EST AUTORISEE QUE SOUS LA FORME FAC-SIMILE PHOTOGRAPHIQUE INTEGRAL</font>", S["n"]))
    flow.append(PageBreak())

    # ── Page(s) de resultats
    cond = c["conditions"] or {}
    flow += [Paragraph("<b>RÉSULTATS D'ÉTALONNAGE</b>", ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=TA_CENTER)),
             Paragraph(f"CE N° {esc(c['numero']) or '(projet)'} — {esc(e['designation'])} — N° de série {esc(e['numero_serie'])} — Identification {esc(e['numero_identification'])}", S["n"]), Spacer(1, 4 * mm)]
    info = [
        [P("<b>Date d'étalonnage</b>"), P(_fmt_d(c["date_etalonnage"]))],
        [P("<b>Plage de mesure / résolution / classe</b>"), P(" — ".join(x for x in (esc(e["plage_mesure"]), esc(e["resolution"]), esc(e["classe"])) if x) or "-")],
        [P("<b>Méthode d'étalonnage</b>"), P(esc(c["methode"]) or "-")],
        [P("<b>Étalons utilisés</b>"), P(esc(c["etalons_utilises"]) or "-")],
        [P("<b>Conditions ambiantes</b>"), P(f"Température : {esc(cond.get('temperature', '-'))} &nbsp;&nbsp; Humidité : {esc(cond.get('humidite', '-'))} &nbsp;&nbsp; Pression atmosphérique : {esc(cond.get('pression_atmospherique', '-'))}")],
        [P("<b>Opérateur</b>"), P(esc(c["operateur_nom"]) or "-")],
    ]
    ti = Table(info, colWidths=[60 * mm, W - 64 * mm])
    ti.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, INK), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eeeeee")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow += [ti, Spacer(1, 5 * mm)]

    lignes = [[P(t, "pb") for t in ("N°", "Valeur de l'étalon", "Indication de l'instrument", "Écart", "Incertitude élargie U (k=2)", "Unité", "Conformité")]]
    style = [("GRID", (0, 0), (-1, -1), 0.5, INK), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i, p in enumerate(c["points"], start=1):
        conf = "—" if p["conforme"] is None else ("Conforme" if p["conforme"] else "Non conforme")
        lignes.append([P(i, "p"), P(esc(p["valeur_etalon"]), "p"), P(esc(p["valeur_instrument"]), "p"), P(esc(p["ecart"]), "p"), P(esc(p["incertitude"]), "p"), P(esc(p["unite"] or e["unite"]), "p"), P(conf, "p")])
        if p["conforme"] is False:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fde68a")))
    tp = Table(lignes, colWidths=[10 * mm, 30 * mm, 36 * mm, 24 * mm, 36 * mm, 20 * mm, W - 160 * mm - 4], repeatRows=1)
    tp.setStyle(TableStyle(style))
    flow += [tp, Spacer(1, 5 * mm)]
    dec = dict(circuit_metro.DECISIONS).get(e["decision"], "")
    if dec:
        flow.append(P(f"<b>Décision d'acceptation de l'équipement :</b> {dec}" + (f" — {esc(e['reserves'])}" if e["reserves"] else "")))
    if c["observations"]:
        flow.append(P(f"<b>Observations :</b> {esc(c['observations'])}"))
    flow += [Spacer(1, 4 * mm), P("<i>Les résultats ne se rapportent qu'à l'instrument soumis à l'étalonnage. Les incertitudes sont exprimées avec un facteur d'élargissement k = 2 (niveau de confiance d'environ 95 %).</i>", "p")]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=26 * mm, title=f"Certificat d'étalonnage {c['numero']}")

    def pied(canvas, dc):
        canvas.saveState()
        canvas.setStrokeColor(INK)
        canvas.line(15 * mm, 22 * mm, A4[0] - 15 * mm, 22 * mm)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawCentredString(A4[0] / 2, 18 * mm, "Laboratoire National d'Essais de qualité de Métrologie et d'Analyses (LANEMA)")
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0] / 2, 14.8 * mm, "Siège Social: Autoroute d'Abobo, entre la Sté SONITRA et l'Univ. NANGUI ABROGOUA- BP V 174 Abidjan")
        canvas.drawCentredString(A4[0] / 2, 11.8 * mm, "Tél.: 43 11 01 01- 43 11 02 02- 43 11 03 03- 43 11 04 04")
        canvas.drawRightString(A4[0] - 15 * mm, 8 * mm, f"CE N° {c['numero'] or 'projet'} — page {dc.page}")
        canvas.restoreState()

    doc.build(flow, onFirstPage=pied, onLaterPages=pied)
    return buf.getvalue(), doc.page
