"""Circuit metrologie : fiche d'execution des travaux (EN 004-PG 002) transmise
par le service reception a la DMCT, travaux, puis certificat d'etalonnage
transmis au client."""
from django.db import transaction
from django.utils import timezone

from qualite.models import CompteurSequence, FicheEntreeEquipement

from .models import (
    CertificatEtalonnage, DECISIONS, EquipementFTM, FicheTravauxMetrologie, GRANDEURS, PointEtalonnage,
)

CHAMPS_REFERENCES = {
    "operations_preliminaires": ["EXIGENCES_CLIENTS", "DOCUMENTS_LANEMA", "SPECS_CONSTRUCTEUR", "DOCUMENTS_NORMATIFS"],
    "nombre_mesures_references": ["DOC_CLIENT", "DOC_LANEMA", "SPECS_CONSTRUCTEUR"],
    "erreurs_max_references": ["DOC_CLIENT", "DOC_LANEMA", "SPECS_CONSTRUCTEUR"],
    "jugement_references": ["DOC_CLIENT", "SPECS_PARTICULIERES_CONSTRUCTEUR", "DOCS_NORMATIFS"],
}
GRANDEURS_ACCREDITEES = ("TEMPERATURE", "PRESSION")  # accreditation SOAC (DMCT)
DIRECTION = "DMCT"


def _nom(u):
    return (u.get_full_name() or u.username) if u else None


def _dt(v):
    return v.isoformat() if v else None


def client_info(demande_devis):
    client = demande_devis.client
    p = getattr(client, "client_profile", None)
    return {
        "code_client": getattr(p, "code_client", "") or "",
        "raison_sociale": getattr(p, "raison_sociale", "") or client.get_full_name() or client.username,
        "adresse": getattr(p, "adresse", "") or "", "situation_geographique": getattr(p, "situation_geographique", "") or "",
        "telephone": getattr(p, "telephone", "") or "", "email": client.email,
    }


# ── Donnees ───────────────────────────────────────────────────────────────

def equipement_dict(e):
    cert = getattr(e, "certificat", None) if hasattr(e, "certificat") else None
    return {
        "id": e.id, "fiche_entree": e.fiche_entree_id, "code": e.code, "designation": e.designation, "constructeur": e.constructeur,
        "modele": e.modele, "numero_serie": e.numero_serie, "nature": e.nature, "grandeur": e.grandeur,
        "plage_mesure": e.plage_mesure, "resolution": e.resolution, "classe": e.classe, "unite": e.unite, "localisation": e.localisation,
        "decision": e.decision, "reserves": e.reserves,
        "certificat": {"id": cert.id, "numero": cert.numero, "statut": cert.statut} if cert else None,
    }


def decision_globale(fiche):
    decs = [e.decision for e in fiche.equipements.all() if e.decision]
    if not decs:
        return ""
    for d in ("NON_CONFORME", "SOUS_RESERVE"):
        if d in decs:
            return d
    return "CONFORME"


def ftm_data(fiche):
    d = {
        "id": fiche.id, "numero": fiche.numero, "annee": fiche.annee, "statut": fiche.statut, "statut_display": fiche.get_statut_display(),
        "demande_devis": {"id": fiche.demande_devis_id, "numero": fiche.demande_devis.numero, "type_analyse": fiche.demande_devis.type_analyse},
        "client": client_info(fiche.demande_devis),
        "lieu_realisation": fiche.lieu_realisation, "operations_preliminaires": fiche.operations_preliminaires or [],
        "nombre_mesures_references": fiche.nombre_mesures_references or [], "definition_points": fiche.definition_points,
        "observations_mesures": fiche.observations_mesures, "erreurs_max_references": fiche.erreurs_max_references or [],
        "jugement_references": fiche.jugement_references or [],
        "date_arrivee_materiel": fiche.date_arrivee_materiel, "date_transmission_dmct": _dt(fiche.date_transmission_dmct),
        "receptionne_par_nom": _nom(fiche.receptionne_par), "date_reception_dmct": _dt(fiche.date_reception_dmct),
        "date_debut_travaux": fiche.date_debut_travaux, "date_fin_travaux": fiche.date_fin_travaux,
        "date_arrivee_site": fiche.date_arrivee_site, "interlocuteur_site": fiche.interlocuteur_site, "visa_site": fiche.visa_site,
        "date_debut_site": fiche.date_debut_site, "date_fin_site": fiche.date_fin_site,
        "observations": fiche.observations, "decision_globale": decision_globale(fiche),
        "equipements": [equipement_dict(e) for e in fiche.equipements.select_related("certificat").all()],
        "cree_par_nom": _nom(fiche.cree_par), "created_at": _dt(fiche.created_at),
        "modifiable": fiche.statut == "BROUILLON",
    }
    return d


def ftm_resume(fiche):
    return {
        "id": fiche.id, "numero": fiche.numero, "statut": fiche.statut, "statut_display": fiche.get_statut_display(),
        "devis_numero": fiche.demande_devis.numero, "client": client_info(fiche.demande_devis)["raison_sociale"],
        "code_client": client_info(fiche.demande_devis)["code_client"], "nb_equipements": fiche.equipements.count(),
        "lieu_realisation": fiche.lieu_realisation, "date_transmission_dmct": _dt(fiche.date_transmission_dmct),
        "certificats": [{"id": c.id, "numero": c.numero, "statut": c.statut} for c in fiche.certificats.all()],
        "created_at": _dt(fiche.created_at),
    }


def certificat_data(c):
    e = c.equipement
    f = c.fiche
    cl = client_info(f.demande_devis)
    return {
        "id": c.id, "numero": c.numero, "numero_ordre": c.numero_ordre, "annee": c.annee, "statut": c.statut, "statut_display": c.get_statut_display(),
        "grandeur": c.grandeur, "grandeur_display": dict(GRANDEURS).get(c.grandeur, c.grandeur), "accredite": c.accredite,
        "date_etalonnage": c.date_etalonnage, "date_emission": c.date_emission, "conditions": c.conditions or {},
        "methode": c.methode, "etalons_utilises": c.etalons_utilises, "observations": c.observations, "directeur_nom": c.directeur_nom,
        "operateur_nom": _nom(c.operateur), "edite_par_nom": _nom(c.edite_par), "date_signature": c.date_signature, "date_transmission": c.date_transmission,
        "fiche": {"id": f.id, "numero": f.numero}, "delivre_a": cl,
        "equipement": {"id": e.id, "designation": e.designation, "constructeur": e.constructeur, "type_modele": e.modele, "numero_serie": e.numero_serie,
                       "numero_identification": e.code, "plage_mesure": e.plage_mesure, "resolution": e.resolution, "classe": e.classe,
                       "unite": e.unite, "decision": e.decision, "reserves": e.reserves, "localisation": e.localisation},
        "points": [
            {"id": p.id, "valeur_etalon": p.valeur_etalon, "valeur_instrument": p.valeur_instrument, "ecart": p.ecart,
             "incertitude": p.incertitude, "unite": p.unite, "conforme": p.conforme}
            for p in c.points.all()
        ],
        "modifiable": c.statut == "BROUILLON",
    }


# ── Fiche d'execution ──────────────────────────────────────────────────────

def _reglages(fiche, data):
    for champ in ("lieu_realisation", "definition_points", "observations_mesures", "observations", "interlocuteur_site", "visa_site"):
        if champ in data:
            setattr(fiche, champ, data[champ] or ("LABORATOIRE" if champ == "lieu_realisation" else ""))
    for champ, valides in CHAMPS_REFERENCES.items():
        if champ in data:
            setattr(fiche, champ, [x for x in (data[champ] or []) if x in valides])
    for champ in ("date_arrivee_materiel", "date_arrivee_site", "date_debut_travaux", "date_fin_travaux", "date_debut_site", "date_fin_site"):
        if champ in data:
            setattr(fiche, champ, data[champ] or None)


@transaction.atomic
def enregistrer_ftm(fiche, data, user):
    _reglages(fiche, data)
    fiche.save()
    if "equipements" in data:
        garde = set()
        for ordre, ed in enumerate(data["equipements"] or []):
            fe = None
            if ed.get("fiche_entree"):
                fe = FicheEntreeEquipement.objects.filter(pk=ed["fiche_entree"], domaine="METROLOGIE", demande_devis_id=fiche.demande_devis_id).first()
                if fe is None:
                    raise ValueError("Fiche d'entrée introuvable pour cette demande.")
                deja = EquipementFTM.objects.filter(fiche_entree=fe).exclude(fiche=fiche).first()
                if deja:
                    raise ValueError(f"L'équipement {fe.code} est déjà rattaché à la fiche {deja.fiche.numero}.")
            designation = (ed.get("designation") or (fe.designation if fe else "")).strip()
            if not designation:
                raise ValueError("Chaque équipement doit avoir une désignation.")
            champs = {
                "designation": designation[:255], "constructeur": (ed.get("constructeur") or (fe.marque if fe else ""))[:255],
                "modele": (ed.get("modele") or (fe.modele if fe else ""))[:255], "numero_serie": (ed.get("numero_serie") or (fe.numero_serie if fe else ""))[:100],
                "nature": (ed.get("nature") or "")[:100], "plage_mesure": (ed.get("plage_mesure") or "")[:100], "resolution": (ed.get("resolution") or "")[:50],
                "classe": (ed.get("classe") or "")[:50], "unite": (ed.get("unite") or "")[:30], "localisation": (ed.get("localisation") or "")[:255],
                "grandeur": ed.get("grandeur") if ed.get("grandeur") in dict(GRANDEURS) else "AUTRE", "ordre": ordre,
                "fiche_entree": fe, "code": fe.code if fe else (ed.get("code") or ""),
            }
            eq = EquipementFTM.objects.filter(pk=ed.get("id"), fiche=fiche).first()
            if eq:
                for k, v in champs.items():
                    setattr(eq, k, v)
                eq.save()
            else:
                eq = EquipementFTM.objects.create(fiche=fiche, **champs)
            garde.add(eq.id)
        fiche.equipements.exclude(id__in=garde).delete()
    return fiche


@transaction.atomic
def creer_ftm(demande_devis, data, user):
    annee = timezone.now().year
    n = CompteurSequence.suivant(f"FETM-{annee}-{DIRECTION}")
    fiche = FicheTravauxMetrologie.objects.create(
        numero=f"{annee}/{DIRECTION}/{n:04d}", annee=annee, direction=DIRECTION, demande_devis=demande_devis, cree_par=user,
        date_arrivee_materiel=timezone.now().date(), lieu_realisation=("SITE_CLIENT" if demande_devis.lieu_realisation == "SITE_CLIENT" else "LABORATOIRE"),
    )
    return enregistrer_ftm(fiche, data, user)


@transaction.atomic
def transmettre_ftm(fiche, user):
    from facturation.travaux import MESSAGE_BLOQUE, peut_demarrer

    if not peut_demarrer(fiche.demande_devis):
        raise ValueError(MESSAGE_BLOQUE)
    eqs = list(fiche.equipements.select_related("fiche_entree"))
    if not eqs:
        raise ValueError("Ajoutez au moins un équipement à la fiche avant de la transmettre.")
    fiche.statut = "TRANSMISE"
    fiche.date_transmission_dmct = timezone.now()
    fiche.save(update_fields=["statut", "date_transmission_dmct", "updated_at"])
    for e in eqs:
        if e.fiche_entree:
            e.fiche_entree.statut = "TRANSMIS_LABO"
            e.fiche_entree.save(update_fields=["statut", "updated_at"])
    return fiche


@transaction.atomic
def receptionner_dmct(fiche, user):
    if fiche.statut != "TRANSMISE":
        raise ValueError("Cette fiche n'est pas en attente de réception par la DMCT.")
    fiche.statut = "RECUE"
    fiche.receptionne_par = user
    fiche.date_reception_dmct = timezone.now()
    fiche.save(update_fields=["statut", "receptionne_par", "date_reception_dmct", "updated_at"])
    return fiche


@transaction.atomic
def demarrer_travaux(fiche, data, user):
    if fiche.statut not in ("RECUE", "EN_COURS"):
        raise ValueError("La fiche doit d'abord être réceptionnée par la DMCT.")
    _reglages(fiche, data)
    today = timezone.now().date()
    if fiche.lieu_realisation == "SITE_CLIENT":
        fiche.date_debut_site = fiche.date_debut_site or today
        fiche.date_arrivee_site = fiche.date_arrivee_site or today
    else:
        fiche.date_debut_travaux = fiche.date_debut_travaux or today
    fiche.statut = "EN_COURS"
    fiche.save()
    for e in fiche.equipements.select_related("fiche_entree"):
        if e.fiche_entree:
            e.fiche_entree.statut = "EN_COURS"
            e.fiche_entree.save(update_fields=["statut", "updated_at"])
    return fiche


@transaction.atomic
def terminer_travaux(fiche, data, user):
    if fiche.statut != "EN_COURS":
        raise ValueError("Les travaux doivent être démarrés avant d'être terminés.")
    _reglages(fiche, data)
    decisions = {d.get("id"): d for d in data.get("decisions", [])}
    for e in fiche.equipements.select_related("fiche_entree"):
        d = decisions.get(e.id) or {}
        if d.get("decision") not in dict(DECISIONS):
            raise ValueError(f"Indiquez la décision d'acceptation pour {e.designation} ({e.code or e.numero_serie or 'sans code'}).")
        if d["decision"] == "SOUS_RESERVE" and not (d.get("reserves") or "").strip():
            raise ValueError(f"Précisez les réserves pour {e.designation}.")
        e.decision, e.reserves = d["decision"], d.get("reserves") or ""
        e.save(update_fields=["decision", "reserves"])
        if e.fiche_entree:
            e.fiche_entree.statut = "TERMINE"
            e.fiche_entree.save(update_fields=["statut", "updated_at"])
    today = timezone.now().date()
    if fiche.lieu_realisation == "SITE_CLIENT":
        fiche.date_fin_site = fiche.date_fin_site or today
    else:
        fiche.date_fin_travaux = fiche.date_fin_travaux or today
    fiche.statut = "TERMINEE"
    fiche.save()
    return fiche


# ── Certificats ───────────────────────────────────────────────────────────

@transaction.atomic
def creer_certificat(equipement, user):
    fiche = equipement.fiche
    if fiche.statut not in ("EN_COURS", "TERMINEE", "CLOTUREE"):
        raise ValueError("Les travaux doivent être démarrés pour préparer un certificat.")
    if hasattr(equipement, "certificat"):
        return equipement.certificat
    return CertificatEtalonnage.objects.create(
        equipement=equipement, fiche=fiche, grandeur=equipement.grandeur,
        accredite=equipement.grandeur in GRANDEURS_ACCREDITEES,
        date_etalonnage=timezone.now().date(), operateur=user,
        methode="", etalons_utilises="", conditions={},
    )


@transaction.atomic
def enregistrer_certificat(c, data, user):
    if c.statut != "BROUILLON":
        raise ValueError("Le certificat est édité : il n'est plus modifiable.")
    for champ in ("methode", "etalons_utilises", "observations", "directeur_nom"):
        if champ in data:
            setattr(c, champ, (data[champ] or "")[:2000])
    if "grandeur" in data and data["grandeur"] in dict(GRANDEURS):
        c.grandeur = data["grandeur"]
    if "accredite" in data:
        c.accredite = bool(data["accredite"])
    if "date_etalonnage" in data:
        c.date_etalonnage = data["date_etalonnage"] or None
    if "conditions" in data and isinstance(data["conditions"], dict):
        c.conditions = {k: str(v)[:50] for k, v in data["conditions"].items() if k in ("temperature", "humidite", "pression_atmospherique")}
    c.save()
    if "points" in data:
        garde = set()
        for ordre, p in enumerate(data["points"] or []):
            if not str(p.get("valeur_etalon", "")).strip() or not str(p.get("valeur_instrument", "")).strip():
                raise ValueError("Chaque point doit avoir une valeur d'étalon et une indication de l'instrument.")
            champs = {"ordre": ordre, "valeur_etalon": str(p["valeur_etalon"])[:50], "valeur_instrument": str(p["valeur_instrument"])[:50],
                      "ecart": str(p.get("ecart") or "")[:50], "incertitude": str(p.get("incertitude") or "")[:50], "unite": str(p.get("unite") or "")[:30],
                      "conforme": p.get("conforme")}
            existant = PointEtalonnage.objects.filter(pk=p.get("id"), certificat=c).first()
            if existant:
                for k, v in champs.items():
                    setattr(existant, k, v)
                existant.save()
                garde.add(existant.id)
            else:
                garde.add(PointEtalonnage.objects.create(certificat=c, **champs).id)
        c.points.exclude(id__in=garde).delete()
    return c


@transaction.atomic
def editer_certificat(c, user):
    if c.statut != "BROUILLON":
        raise ValueError("Ce certificat est déjà édité.")
    if not c.points.exists():
        raise ValueError("Saisissez au moins un point d'étalonnage avant d'éditer le certificat.")
    if not c.directeur_nom.strip():
        raise ValueError("Renseignez le nom et prénoms du Directeur de la DMCT signataire.")
    annee = timezone.now().year
    c.annee = annee
    c.numero_ordre = CompteurSequence.suivant(f"CE-{annee}")
    c.numero = f"{c.numero_ordre:04d}/{annee}"
    c.date_emission = timezone.now().date()
    c.edite_par = user
    c.statut = "EDITE"
    c.save()
    return c


@transaction.atomic
def signer_certificat(c):
    if c.statut != "EDITE":
        raise ValueError("Le certificat doit être édité avant d'être signé.")
    c.statut = "SIGNE"
    c.date_signature = timezone.now().date()
    c.save(update_fields=["statut", "date_signature", "updated_at"])
    return c


@transaction.atomic
def transmettre_certificat(c):
    if c.statut != "SIGNE":
        raise ValueError("Le certificat doit être signé avant d'être transmis au client.")
    c.statut = "TRANSMIS"
    c.date_transmission = timezone.now().date()
    c.save(update_fields=["statut", "date_transmission", "updated_at"])
    fiche = c.fiche
    if not fiche.equipements.exclude(certificat__statut="TRANSMIS").exists():
        fiche.statut = "CLOTUREE"
        fiche.save(update_fields=["statut", "updated_at"])
        for e in fiche.equipements.select_related("fiche_entree"):
            if e.fiche_entree:
                e.fiche_entree.statut = "RESTITUE"
                e.fiche_entree.save(update_fields=["statut", "updated_at"])
    try:  # notification au client (portail labo)
        from notifications.models import creer_notification
        creer_notification(fiche.demande_devis.client, f"Certificat d'étalonnage {c.numero}", "Votre certificat d'étalonnage est disponible dans votre espace client.")
    except Exception:  # pragma: no cover
        pass
    return c
