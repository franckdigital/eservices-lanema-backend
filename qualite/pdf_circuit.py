"""PDF de la Fiche d'Execution des Travaux d'essais (EN 003-PG 002 V08) et du
Rapport d'essai (EN 001-PG019 V07), reproduisant les formulaires officiels."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import circuit

BLEU = colors.HexColor("#0B57A4")
GRIS = colors.HexColor("#d9d9d9")
INK = colors.HexColor("#111827")
W = A4[0] - 30 * mm  # largeur utile

S = {
    "n": ParagraphStyle("n", fontName="Helvetica", fontSize=8.5, leading=10.5, textColor=INK),
    "b": ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=INK),
    "p": ParagraphStyle("p", fontName="Helvetica", fontSize=7.5, leading=9, textColor=INK),
    "pb": ParagraphStyle("pb", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=INK),
    "c": ParagraphStyle("c", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=TA_CENTER, textColor=INK),
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=TA_CENTER, textColor=INK),
    "r": ParagraphStyle("r", fontName="Helvetica", fontSize=9, leading=11, alignment=TA_RIGHT, textColor=INK),
    "note": ParagraphStyle("note", fontName="Helvetica", fontSize=7.5, leading=9.5, leftIndent=12, bulletIndent=2, textColor=INK),
    "foot": ParagraphStyle("foot", fontName="Helvetica", fontSize=7, leading=8.5, textColor=INK),
}


def P(t, s="n"):
    return Paragraph(str(t if t not in (None, "") else "&nbsp;").replace("\n", "<br/>"), S[s])


def esc(t):
    return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _logo():
    t = Table([[Paragraph('<font color="white"><b>LANEMA</b></font>', ParagraphStyle("l", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER))]],
              colWidths=[40 * mm], rowHeights=[12 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2b2b2b")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def _pied_adresse(canvas, doc, avec_validite):
    canvas.saveState()
    canvas.setStrokeColor(INK)
    canvas.line(15 * mm, 22 * mm, A4[0] - 15 * mm, 22 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawCentredString(A4[0] / 2, 18.5 * mm, "LABORATOIRE NATIONAL D'ESSAIS DE QUALITE, DE METROLOGIE ET D'ANALYSES (LANEMA)")
    canvas.setFont("Helvetica", 6.5)
    canvas.drawCentredString(A4[0] / 2, 15.7 * mm, "Siège Social : Autoroute d'Abobo, entre la Sté SONITRA et l'Université NANGUI ABROGOUA- BP V 174 Abidjan,")
    canvas.drawCentredString(A4[0] / 2, 13 * mm, "E-Mail : infoline@lanema.ci  Site web : www.lanema.ci")
    canvas.drawCentredString(A4[0] / 2, 10.3 * mm, "Tel. : 01 43 11 01 01- 01 43 11 02 02- 01 43 11 03 03- 01 43 11 04 04")
    canvas.setFont("Helvetica-BoldOblique", 6.8)
    canvas.drawCentredString(A4[0] / 2, 7.5 * mm, avec_validite)
    canvas.restoreState()


def _box(ok):
    return "[X]" if ok else "[ ]"


# ═══════════════════════════════════════════════════════════════════════════
# Fiche d'execution des travaux d'essais
# ═══════════════════════════════════════════════════════════════════════════

def fet_pdf(fiche):
    data = circuit.fiche_data(fiche)
    labos_all = [("LMP", "LMP"), ("LAI", "LAI"), ("LEE", "LEE"), ("LPI", "LPI")]
    flow = []

    entete = Table(
        [[_logo(), P("FICHE<br/>D'EXECUTION<br/>DES TRAVAUX<br/>D'ESSAIS", "c"), P("CODE", "c"), P("DATE DE<br/>CREATION/<br/>REVISION", "c"),
          P("A<br/>REVISER<br/>LE", "c"), P("VERSION", "c"), P("PAGE", "c")],
         ["", "", P("EN 003-PG 002", "c"), P("<i>30/07/2025</i>", "c"), P("<i>30/06/2027</i>", "c"), P("<i>08</i>", "c"), P("1 de 1", "c")]],
        colWidths=[32 * mm, 32 * mm, 28 * mm, 26 * mm, 24 * mm, 24 * mm, 14 * mm],
    )
    entete.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.8, INK), ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow += [entete, Spacer(1, 3 * mm)]

    corps = []
    corps.append([P(f"N°FET : {esc(data['numero'])}<super>1</super>", "c")])
    corps.append([P("INFORMATIONS CLIENT", "c")])
    corps.append([Table([[P("Code Client", "b"), P(esc(data["client"]["code_client"]))]], colWidths=[40 * mm, W - 40 * mm - 4])])
    corps.append([P("INFORMATIONS OBJET(s) SOUMIS AUX ESSAIS<super>2</super>", "c")])
    nat = data["nature_objet"]
    nature = (f"Produits Alimentaires {_box(nat == 'ALIMENTAIRE')} &nbsp; Produits industriels {_box(nat == 'INDUSTRIEL')} &nbsp; "
              f"Eaux {_box(nat == 'EAUX')} &nbsp; Autres {_box(nat == 'AUTRES')}")
    if nat == "AUTRES" and data["nature_precision"]:
        nature += f"<br/>Préciser : {esc(data['nature_precision'])}"
    corps.append([Table([[P("Nature de l'objet", "b"), P(nature)]], colWidths=[40 * mm, W - 40 * mm - 4])])

    en_tete_tab = ["IDENTIFICATION<br/>ECHANTILLON", "DESCRIPTION", "QUANTITE", "DATE DE<br/>PRELEVEMENT", "ETAT DE<br/>L'ECHANTILLON", "PARAMETRES",
                   "ENTITES DU<br/>LANEMA<br/>CONCERNEES<br/>PAR LES<br/>ESSAIS"]
    lignes = [[P(t, "pb") for t in en_tete_tab]]
    ids_codes = {l["id"]: l["code"] for l in [s["laboratoire"] for s in data["suivis"]]}
    from laboratoires.models import Laboratoire
    codes_labo = {l.id: l.code for l in Laboratoire.objects.all()}
    for e in data["echantillons"]:
        etats = []
        for code, lib in circuit.ETATS:
            etats.append(f"{lib} {_box(code in e['etat'])}")
        if "AUTRES" in e["etat"] and e["etat_precision"]:
            etats.append(f"Préciser : {esc(e['etat_precision'])}")
        entites = "<br/>".join(f"{c} : {_box(any(codes_labo.get(i) == c for i in e['laboratoires']))}" for c, _ in labos_all)
        dp = e["date_prelevement"].strftime("%d/%m/%Y") if e["date_prelevement"] else ""
        lignes.append([P(f"<b>{esc(e['code_echantillon'])}</b><br/>{esc(e['designation'])}", "p"), P(esc(e["description"]), "p"), P(esc(e["quantite"]), "p"),
                       P(dp, "p"), P("<br/>".join(etats), "p"), P(esc(e["parametres"]), "p"), P(entites, "p")])
    tab = Table(lignes, colWidths=[34 * mm, 28 * mm, 16 * mm, 20 * mm, 29 * mm, 28 * mm, W - 155 * mm - 4], repeatRows=1)
    tab.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    corps.append([tab])

    d = data
    arrivee = d["date_arrivee_lanema"].strftime("%d/%m/%Y") if d["date_arrivee_lanema"] else ""
    trans = timezone_fmt(d["date_transmission_laboratoire"])
    recus = "<br/>".join(
        f"{esc(s['laboratoire']['code'])} : {esc(s['receptionne_par_nom'] or '')}" + (f" — {timezone_fmt(s['date_reception'])}" if s["date_reception"] else "")
        for s in d["suivis"] if s["date_reception"]
    ) or "&nbsp;"
    accept = "<br/>".join(
        f"{esc(s['laboratoire']['code'])} : Conforme {_box(s['acceptation'] == 'CONFORME')} &nbsp; Sous réserve {_box(s['acceptation'] == 'SOUS_RESERVE')}"
        + (f" — {esc(s['reserves'])}" if s["reserves"] else "")
        for s in d["suivis"]
    ) or f"Conforme {_box(False)} &nbsp; Sous réserve {_box(False)}"
    bloc = Table(
        [[P(f"<b>Date d'arrivée au LANEMA</b><br/>{arrivee}"), P(f"Date de transmission au laboratoire : {trans}<br/><br/>Réceptionné par : Nom et Visa :<br/>{recus}")],
         [P("Acceptation de(s)<br/>l'(des) échantillon(s)", "b"), P(accept)]],
        colWidths=[40 * mm, W - 40 * mm - 4],
    )
    bloc.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    corps.append([bloc])
    corps.append([Table([[P(f"<b>Délais de réalisation des travaux :</b> {esc(d['delai_realisation'])}")]], colWidths=[W - 4])])
    corps.append([Table([[P(f"<b>Observations particulières :</b><br/>{esc(d['observations'])}<br/>&nbsp;")]], colWidths=[W - 4])])
    re_date = timezone_fmt(d["date_reception_re"])
    sro = Table([[P(f"<b>Date de transmission du RE au SRO :</b> {_dates_re(d)}"), P(f"Réceptionné par : Nom et Visa :<br/>{esc(d['re_receptionne_par_nom'] or '')} {('— ' + re_date) if re_date else ''}")]],
                colWidths=[(W - 4) / 2, (W - 4) / 2])
    sro.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, INK), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    corps.append([sro])

    t = Table(corps, colWidths=[W])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, INK), ("LINEBELOW", (0, 0), (-1, -2), 0.6, INK),
        ("BACKGROUND", (0, 1), (0, 1), GRIS), ("BACKGROUND", (0, 3), (0, 3), GRIS),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    flow += [t, Spacer(1, 4 * mm), P("<super>1</super> Année/Direction/N° d'ordre<br/><super>2</super> A remplir par la réception", "foot")]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=26 * mm,
                            title=f"FET {data['numero']}")
    doc.build(flow, onFirstPage=lambda c, d_: _pied_adresse(c, d_, "Avant utilisation d'un document, vérifier sa validité"),
              onLaterPages=lambda c, d_: _pied_adresse(c, d_, "Avant utilisation d'un document, vérifier sa validité"))
    return buf.getvalue()


def timezone_fmt(iso):
    if not iso:
        return ""
    from datetime import datetime
    from django.utils import timezone
    dt = datetime.fromisoformat(iso) if isinstance(iso, str) else iso
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def _dates_re(d):
    dates = [timezone_fmt(s["date_transmission_resultats"]) for s in d["suivis"] if s["date_transmission_resultats"]]
    return " ; ".join(dates)


# ═══════════════════════════════════════════════════════════════════════════
# Rapport d'essai
# ═══════════════════════════════════════════════════════════════════════════

def rapport_pdf(rapport):
    data = circuit.rapport_data(rapport)
    nb_pages = 2
    for _ in range(2):  # 2 passes : la 1re compte les pages pour la mention du NB
        contenu, pages = _construire_rapport(data, nb_pages)
        if pages == nb_pages:
            break
        nb_pages = pages
    return contenu


def _construire_rapport(data, nb_pages):
    labo = data["laboratoire"]
    c = data["client"]
    i = data["info"]
    ref = esc(data["reference"]) if data["reference"] else f"<font color='#b91c1c'>(projet — non numéroté)</font>/{data['annee'] or ''}/{esc(labo['direction'])}/{esc(labo['sous_direction'])}//{esc(labo['code'])}"
    date_ed = data["date_edition"].strftime("%d/%m/%Y") if data["date_edition"] else ""
    flow = [Table([[_logo(), P("RAPPORT D'ESSAI", "title"), ""]], colWidths=[45 * mm, W - 90 * mm, 45 * mm]), Spacer(1, 4 * mm),
            P(f"Abidjan, le {date_ed}", "r"), Spacer(1, 3 * mm),
            Table([[P(f"<b><u>Réf</u></b> : <b>{ref}</b>", "n"), P(esc(labo["nom"]), "b")]], colWidths=[W * 0.52, W * 0.48]), Spacer(1, 3 * mm)]

    def ligne(lbl, val):
        return [P(f"<b>{lbl}</b>", "n"), P(esc(val) or "&nbsp;", "n")]

    rows = [
        [P("INFORMATIONS CLIENT", "c"), ""],
        ligne("Raison Sociale", c["raison_sociale"]), ligne("Adresse Postale", c["adresse"]), ligne("Situation Géographique", c["situation_geographique"]),
        ligne("Numéro Téléphone", c["telephone"]), ligne("E-mail", c["email"]), ligne("Code Client", c["code_client"]),
        [P("INFORMATIONS ECHANTILLON", "c"), ""],
        ligne("Nature échantillon(s)", i["nature"]), ligne("N° lot d'origine", i["numero_lot"]), ligne("Lieu de Prélèvement", i["lieu_prelevement"]),
        ligne("Date et heure de Prélèvement", i["date_heure_prelevement"]), ligne("Prélèvement effectué par", i["prelevement_par"]),
        ligne("Date et Heure d'arrivée au laboratoire", i["date_heure_arrivee"]), ligne("Référence(s) Echantillon(s)", i["references"]),
        [P("INFORMATIONS DIVERSES", "c"), ""],
        [P(f"<b>{esc(data['informations_diverses'] or 'R.A.S')}</b>", "n"), ""],
    ]
    t = Table(rows, colWidths=[W * 0.42, W * 0.58])
    spans = [("SPAN", (0, 0), (1, 0)), ("SPAN", (0, 7), (1, 7)), ("SPAN", (0, 15), (1, 15)), ("SPAN", (0, 16), (1, 16))]
    t.setStyle(TableStyle(spans + [("GRID", (0, 0), (-1, -1), 0.7, INK), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("BACKGROUND", (0, 7), (-1, 7), GRIS),
                                   ("BACKGROUND", (0, 15), (-1, 15), GRIS), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow += [t, Spacer(1, 4 * mm)]
    notes = ["Ce rapport ne doit pas être reproduit, sinon en entier, sans l'autorisation écrite du LANEMA.",
             "<i>Les résultats des essais sous accréditation sont marqués en gras par (**)</i>",
             "Les résultats des essais sous-traités sont identifiés par le symbole <b>\"S/T\"</b>",
             "Les résultats non conformes sont surlignés.",
             "Les résultats ne se rapportent qu'aux échantillons soumis au présent essai."]
    for n in notes:
        flow.append(Paragraph(n, S["note"], bulletText="▪"))
    flow += [Spacer(1, 8 * mm), P("<b>Le Directeur de la Direction</b>", "r"), Spacer(1, 16 * mm), P(f"<b><i>{esc(data['directeur_nom']) or 'Nom &amp; Prenoms'}</i></b>", "r"),
             Spacer(1, 6 * mm), P(f"<u>NB</u> : <i>Ce rapport comporte {nb_pages:02d} pages et est édité en un (01) exemplaire original.</i>", "n"),
             Spacer(1, 2 * mm), P("<b><i>EN 001-PG019 V07 DU 13-01-25 AU 13-12-27</i></b>", "n"), PageBreak()]

    # ── Page 2 : resultats
    flow += [P("<b>RÉSULTATS DES ESSAIS</b>", "c"), Spacer(1, 2 * mm), P(f"Réf : {ref} — {esc(labo['nom'])}", "n"), Spacer(1, 3 * mm)]
    if data["acceptation"]:
        lib = "Conforme" if data["acceptation"] == "CONFORME" else "Acceptés sous réserve"
        flow += [P(f"Acceptation des échantillons : <b>{lib}</b>" + (f" — {esc(data['reserves'])}" if data["reserves"] else ""), "n"), Spacer(1, 2 * mm)]
    for e in data["echantillons"]:
        lignes = [[P(f"<b>Échantillon {esc(e['code_echantillon'])}</b> — {esc(e['designation'])}", "n"), "", "", "", "", ""],
                  [P(t_, "pb") for t_ in ("Paramètre", "Méthode d'essai", "Unité", "Résultat", "Spécification / limite", "Conformité")]]
        style = [("GRID", (0, 0), (-1, -1), 0.5, INK), ("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), GRIS), ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eeeeee")),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
        for idx, r in enumerate(e["resultats"], start=2):
            val = f"<b>{esc(r['resultat'])} (**)</b>" if r["accredite"] else esc(r["resultat"])
            if r["sous_traite"]:
                val += " <b>S/T</b>"
            conf = "—" if r["conforme"] is None else ("Conforme" if r["conforme"] else "Non conforme")
            lignes.append([P(esc(r["parametre"]), "p"), P(esc(r["methode"]), "p"), P(esc(r["unite"]), "p"), P(val, "p"), P(esc(r["specification"]), "p"), P(conf, "p")])
            if r["conforme"] is False:
                style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#fde68a")))
        tab = Table(lignes, colWidths=[W * 0.22, W * 0.18, W * 0.13, W * 0.16, W * 0.19, W * 0.12], repeatRows=2)
        tab.setStyle(TableStyle(style))
        flow += [KeepTogether([tab]) if len(lignes) < 18 else tab, Spacer(1, 4 * mm)]
    flow += [Spacer(1, 4 * mm), P("<i>Fin du rapport d'essai.</i>", "n")]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=26 * mm, title=f"Rapport d'essai {data['reference']}")
    validite = "Avant utilisation d'un document, assurez-vous de sa validité"

    def pied(canvas, d_):
        _pied_adresse(canvas, d_, validite)
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(A4[0] - 15 * mm, 26 * mm, f"Page {d_.page}")
        canvas.restoreState()

    doc.build(flow, onFirstPage=pied, onLaterPages=pied)
    return buf.getvalue(), doc.page
