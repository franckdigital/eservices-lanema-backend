"""Utilitaires de la fiche de devis (formulaire EN 002-PG002) : totaux,
montant en lettres, structure de donnees partagee par l'interface (service
reception et espace client) et le PDF."""
from decimal import Decimal

ACCREDITATIONS = [
    {"grandeur": "UDT", "numero": "ET-19001", "portee": "Chaîne : -20°C à 600°C / Enc : -20°C à 150°C"},
    {"grandeur": "UDP", "numero": "ET-19001-1", "portee": "Hyd : 0 bar à 1200 bar / Pne : 1 bar à 20 bars"},
    {"grandeur": "LEE", "numero": "ES 20001", "portee": "Ph, Ca, Mg, Cl-, Ip, NO2, NO3, C, Cd, Al"},
]

DESIGNATIONS_PRELEVEMENT = [
    ("INGENIEUR", "Intervention d'un ingénieur"),
    ("TECHNICIEN", "Intervention d'un technicien"),
    ("CHAUFFEUR", "Intervention d'un chauffeur"),
    ("VEHICULE", "Coût du véhicule d'intervention"),
    ("DEPLACEMENT", "Coût de déplacement"),
]

_UNITES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
           "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante"]


def _moins_de_cent(n: int) -> str:
    if n < 20:
        return _UNITES[n]
    if n < 70:
        d, u = divmod(n, 10)
        if u == 0:
            return _DIZAINES[d]
        return f"{_DIZAINES[d]} et un" if u == 1 else f"{_DIZAINES[d]}-{_UNITES[u]}"
    if n < 80:  # 70-79
        r = n - 60
        return "soixante et onze" if r == 11 else f"soixante-{_UNITES[r]}"
    # 80-99
    r = n - 80
    if r == 0:
        return "quatre-vingts"
    return f"quatre-vingt-{_UNITES[r]}"


def _moins_de_mille(n: int, final: bool) -> str:
    c, r = divmod(n, 100)
    parts = []
    if c:
        if c == 1:
            parts.append("cent")
        else:
            parts.append(f"{_UNITES[c]} cent" + ("s" if r == 0 and final else ""))
    if r:
        parts.append(_moins_de_cent(r))
    return " ".join(parts) if parts else ""


def nombre_en_lettres(n) -> str:
    """Nombre entier (>= 0) en toutes lettres, orthographe francaise."""
    n = int(Decimal(n).quantize(Decimal("1")))
    if n == 0:
        return "zéro"
    if n < 0:
        return "moins " + nombre_en_lettres(-n)
    echelles = [(10 ** 9, "milliard"), (10 ** 6, "million")]
    parts = []
    reste = n
    for valeur, nom in echelles:
        q, reste = divmod(reste, valeur)
        if q:
            parts.append(f"{_moins_de_mille(q, True) or 'un'} {nom}" + ("s" if q > 1 else ""))
    mille, reste = divmod(reste, 1000)
    if mille:
        parts.append("mille" if mille == 1 else f"{_moins_de_mille(mille, False)} mille")
    if reste:
        parts.append(_moins_de_mille(reste, True))
    texte = " ".join(p for p in parts if p).strip()
    # « quatre-vingts mille » -> « quatre-vingt mille » (invariable devant mille)
    texte = texte.replace("quatre-vingts mille", "quatre-vingt mille")
    return texte


def montant_en_lettres(montant, devise="FCFA") -> str:
    texte = nombre_en_lettres(montant)
    unite = "francs CFA" if devise.upper() in ("FCFA", "XOF") else devise
    phrase = f"{texte} {unite}"
    return phrase[0].upper() + phrase[1:]


def lignes_prestations(demande):
    return list(demande.echantillons_prevus.all().order_by("id")) if demande else []


def interventions_completes(demande):
    """Les 5 designations fixes du tableau 2, renseignees ou non."""
    existantes = {i.designation: i for i in (demande.interventions_prelevement.all() if demande else [])}
    return [(code, label, existantes.get(code)) for code, label in DESIGNATIONS_PRELEVEMENT]


def totaux(proforma):
    """Sous-totaux calcules a partir des lignes ; montants finaux (HT/TVA/TTC)
    ceux enregistres sur la proforma, pour rester coherents avec ce qui a ete
    annonce au client."""
    demande = proforma.demande_devis
    st1 = sum((Decimal(e.prix_unitaire or 0) * e.quantite for e in lignes_prestations(demande)), Decimal("0"))
    st2 = sum((i.montant for _, _, i in interventions_completes(demande) if i is not None), Decimal("0"))
    montant_ht = Decimal(proforma.montant_ht or 0)
    montant_ttc = Decimal(proforma.montant_ttc or 0)
    return {
        "sous_total_1": st1,
        "sous_total_2": st2,
        "total_ht": st1 + st2,
        "remise": Decimal(proforma.remise or 0),
        "montant_ht": montant_ht,
        "tva": montant_ttc - montant_ht,
        "montant_ttc": montant_ttc,
    }


def recalculer_montants(proforma, tva_rate):
    """Recalcule et enregistre HT / TTC a partir des lignes, interventions et remise."""
    demande = proforma.demande_devis
    st1 = sum((Decimal(e.prix_unitaire or 0) * e.quantite for e in lignes_prestations(demande)), Decimal("0"))
    st2 = sum((i.montant for _, _, i in interventions_completes(demande) if i is not None), Decimal("0"))
    ht = max(st1 + st2 - Decimal(proforma.remise or 0), Decimal("0")).quantize(Decimal("1"))
    tva = (ht * tva_rate).quantize(Decimal("1"))
    proforma.montant_ht = ht
    proforma.montant_ttc = ht + tva
    proforma.save(update_fields=["montant_ht", "montant_ttc"])


# ── Reference du devis : N° devis / annee / nom de l'editeur / Direction / Sous-Direction(s) / Laboratoire(s)
# Direction, sous-direction et laboratoire(s) sont deduits du type de prestation demande.
RATTACHEMENT_PAR_TYPE = {
    "MICROBIOLOGIE_PARASITOLOGIE": ("DEA", "SDCPA", "LMP"),
    "CHIMIE_ALIMENTAIRE_INDUSTRIELLE": ("DEA", "SDCPA", "LAI"),
    "EAUX_CONSOMMATION": ("DEA", "SDCPPI", "LEE"),
    "SOLS_ENGRAIS": ("DEA", "SDCPA", "LAI"),
    "METROLOGIE": ("DMCT", "", ""),
    "ETALONNAGE_INSTRUMENTS": ("DMCT", "", ""),
    "ETALONNAGE_VERRERIE": ("DMCT", "", "Volume"),
}
LABO_METROLOGIE_PAR_FAMILLE = {
    "MASSE": "Masse", "TEMPERATURE": "Température", "PRESSION": "Pression", "VOLUME": "Volume", "ELECTRICITE": "Électricité", "DIMENSIONNEL": "Dimensionnel",
}


def reference_devis(proforma):
    demande = proforma.demande_devis
    direction, sous_direction, labos = RATTACHEMENT_PAR_TYPE.get(getattr(demande, "type_analyse", ""), ("", "", ""))
    if direction == "DMCT":
        familles = []
        for e in lignes_prestations(demande):
            f = LABO_METROLOGIE_PAR_FAMILLE.get((e.details or {}).get("famille", ""))
            if f and f not in familles:
                familles.append(f)
        labos = ", ".join(familles) or labos or "Métrologie"
    editeur = ""
    if proforma.edite_par:
        editeur = proforma.edite_par.get_full_name() or proforma.edite_par.username
    annee = proforma.date_emission.year if proforma.date_emission else ""
    return " / ".join([proforma.numero, str(annee), editeur or "-", direction or "-", sous_direction or "-", labos or "-"])
