"""Circuit service reception <-> laboratoire : logique metier et structures de
donnees de la Fiche d'Execution des Travaux d'essais (EN 003-PG 002) et du
Rapport d'essai (EN 001-PG019)."""
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    CompteurSequence, Echantillon, Essai, FETLaboratoire, FicheExecutionTravaux, RapportEssaiLabo, ResultatEssai,
)

ETATS = [
    ("SOLIDE", "Solide"), ("LIQUIDE", "liquide"), ("POUDRE", "poudre"),
    ("PATE", "Pâte"), ("CRISTAUX", "cristaux"), ("AUTRES", "autres"),
]
DIRECTION_PAR_DEFAUT = getattr(settings, "FET_DIRECTION_DEFAUT", "DEA")


def _nom(user):
    return (user.get_full_name() or user.username) if user else None


def _dt(v):
    return v.isoformat() if v else None


# ── Numerotation ──────────────────────────────────────────────────────────

def numero_fiche(annee, direction):
    """N° FET : Année/Direction/N° d'ordre (sequence par annee et direction)."""
    n = CompteurSequence.suivant(f"FET-{annee}-{direction}")
    return f"{annee}/{direction}/{n:04d}"


def reference_rapport(numero_ordre, annee, labo):
    """Reference du rapport : 000/AN/Direction/Sous-Direction//Labo."""
    return f"{numero_ordre:03d}/{annee}/{labo.direction or '-'}/{labo.sous_direction or '-'}//{labo.code}"


# ── Fiche d'execution des travaux (FET) ───────────────────────────────────

def _client_info(demande):
    client = demande.client
    profil = getattr(client, "client_profile", None)
    return {
        "code_client": getattr(profil, "code_client", "") or "",
        "raison_sociale": getattr(profil, "raison_sociale", "") or client.get_full_name() or client.username,
        "adresse": getattr(profil, "adresse", "") or "",
        "situation_geographique": getattr(profil, "situation_geographique", "") or "",
        "telephone": getattr(profil, "telephone", "") or "",
        "email": client.email,
    }


def _resultat_dict(r):
    return {
        "id": r.id, "echantillon": r.echantillon_id, "laboratoire": r.laboratoire_id, "parametre": r.parametre,
        "methode": r.methode, "unite": r.unite, "resultat": r.resultat, "specification": r.specification,
        "conforme": r.conforme, "accredite": r.accredite, "sous_traite": r.sous_traite, "ordre": r.ordre,
    }


def echantillon_dict(e, avec_resultats=True):
    d = {
        "id": e.id, "code_echantillon": e.code_echantillon, "designation": e.designation,
        "description": e.description, "quantite": e.quantite, "statut": e.statut, "conforme": e.conforme,
        "date_reception": e.date_reception, "date_prelevement": e.date_prelevement,
        "date_heure_prelevement": _dt(e.date_heure_prelevement), "lieu_prelevement": e.lieu_prelevement,
        "prelevement_par": e.prelevement_par, "numero_lot": e.numero_lot,
        "date_heure_arrivee": _dt(e.date_heure_arrivee), "etat": e.etat or [], "etat_precision": e.etat_precision,
        "parametres": e.parametres, "laboratoires": [l.id for l in e.laboratoires.all()],
    }
    if avec_resultats:
        d["resultats"] = [_resultat_dict(r) for r in e.resultats.all()]
    return d


def fiche_data(fiche):
    suivis = []
    for s in fiche.suivis_labo.select_related("laboratoire", "receptionne_par", "transmis_par"):
        l = s.laboratoire
        suivis.append({
            "id": s.id, "laboratoire": {"id": l.id, "code": l.code, "nom": l.nom, "direction": l.direction, "sous_direction": l.sous_direction},
            "statut": s.statut, "statut_display": s.get_statut_display(), "date_reception": _dt(s.date_reception),
            "receptionne_par_nom": _nom(s.receptionne_par), "acceptation": s.acceptation, "reserves": s.reserves,
            "date_transmission_resultats": _dt(s.date_transmission_resultats), "transmis_par_nom": _nom(s.transmis_par),
        })
    return {
        "id": fiche.id, "numero": fiche.numero, "annee": fiche.annee, "direction": fiche.direction,
        "statut": fiche.statut, "statut_display": fiche.get_statut_display(),
        "nature_objet": fiche.nature_objet, "nature_precision": fiche.nature_precision,
        "date_arrivee_lanema": fiche.date_arrivee_lanema,
        "date_transmission_laboratoire": _dt(fiche.date_transmission_laboratoire),
        "delai_realisation": fiche.delai_realisation, "observations": fiche.observations,
        "demande": {"id": fiche.demande_id, "numero": fiche.demande.numero, "statut": fiche.demande.statut},
        "client": _client_info(fiche.demande),
        "echantillons": [echantillon_dict(e) for e in fiche.echantillons.prefetch_related("laboratoires", "resultats").order_by("id")],
        "suivis": suivis,
        "re_receptionne_par_nom": _nom(fiche.re_receptionne_par), "date_reception_re": _dt(fiche.date_reception_re),
        "rapports": [
            {"id": r.id, "reference": r.reference, "statut": r.statut, "laboratoire": r.laboratoire_id, "laboratoire_code": r.laboratoire.code}
            for r in fiche.rapports.select_related("laboratoire")
        ],
        "cree_par_nom": _nom(fiche.cree_par), "created_at": _dt(fiche.created_at),
        "modifiable": fiche.statut == "BROUILLON",
    }


def fiche_resume(fiche):
    return {
        "id": fiche.id, "numero": fiche.numero, "statut": fiche.statut, "statut_display": fiche.get_statut_display(),
        "demande_numero": fiche.demande.numero, "client": _client_info(fiche.demande)["raison_sociale"],
        "code_client": _client_info(fiche.demande)["code_client"],
        "nb_echantillons": fiche.echantillons.count(),
        "laboratoires": [
            {"id": s.laboratoire_id, "code": s.laboratoire.code, "statut": s.statut}
            for s in fiche.suivis_labo.select_related("laboratoire")
        ],
        "date_transmission_laboratoire": _dt(fiche.date_transmission_laboratoire),
        "rapports": [{"id": r.id, "reference": r.reference, "statut": r.statut, "laboratoire_code": r.laboratoire.code} for r in fiche.rapports.select_related("laboratoire")],
        "created_at": _dt(fiche.created_at),
    }


@transaction.atomic
def enregistrer_fiche(fiche, data, user):
    """Cree/met a jour les champs de la fiche et des echantillons (brouillon)."""
    for champ in ("nature_objet", "nature_precision", "delai_realisation", "observations"):
        if champ in data:
            setattr(fiche, champ, data[champ] or "")
    if "date_arrivee_lanema" in data:
        fiche.date_arrivee_lanema = data["date_arrivee_lanema"] or None
    fiche.save()

    from laboratoires.models import Laboratoire

    ids_actifs = set()
    for ed in data.get("echantillons", []):
        e = Echantillon.objects.filter(pk=ed.get("id"), demande_id=fiche.demande_id).first()
        if e is None:
            continue
        if e.fiche_id and e.fiche_id != fiche.id:
            raise ValueError(f"L'échantillon {e.code_echantillon} est déjà rattaché à une autre fiche.")
        e.fiche = fiche
        for champ in ("description", "quantite", "lieu_prelevement", "prelevement_par", "numero_lot", "etat_precision", "parametres"):
            if champ in ed:
                setattr(e, champ, ed[champ] or "")
        for champ in ("date_prelevement", "date_heure_prelevement", "date_heure_arrivee"):
            if champ in ed:
                setattr(e, champ, ed[champ] or None)
        if "etat" in ed:
            e.etat = [x for x in (ed["etat"] or []) if x in dict(ETATS)]
        e.save()
        if "laboratoires" in ed:
            e.laboratoires.set(Laboratoire.objects.filter(id__in=ed["laboratoires"] or []))
        ids_actifs.add(e.id)

    # echantillons retires de la fiche (brouillon uniquement)
    if "echantillons" in data:
        fiche.echantillons.exclude(id__in=ids_actifs).update(fiche=None)

    # suivi par laboratoire = laboratoires concernes par au moins un echantillon
    labos = set()
    for e in fiche.echantillons.prefetch_related("laboratoires"):
        labos.update(l.id for l in e.laboratoires.all())
    fiche.suivis_labo.exclude(laboratoire_id__in=labos).delete()
    for lid in labos:
        FETLaboratoire.objects.get_or_create(fiche=fiche, laboratoire_id=lid)
    return fiche


@transaction.atomic
def creer_fiche(demande, data, user):
    from laboratoires.models import Laboratoire

    annee = timezone.now().year
    labos_ids = {lid for ed in data.get("echantillons", []) for lid in (ed.get("laboratoires") or [])}
    labo = Laboratoire.objects.filter(id__in=labos_ids).exclude(direction="").first()
    direction = (labo.direction if labo else "") or DIRECTION_PAR_DEFAUT
    fiche = FicheExecutionTravaux.objects.create(
        numero=numero_fiche(annee, direction), annee=annee, direction=direction, demande=demande, cree_par=user,
        date_arrivee_lanema=demande.date_depot_echantillons or timezone.now().date(),
    )
    return enregistrer_fiche(fiche, data, user)


def _notifier(role, titre, message):
    try:
        from notifications.models import notifier_utilisateurs_par_role
        notifier_utilisateurs_par_role(role, titre, message)
    except Exception:  # pragma: no cover - les notifications ne doivent jamais bloquer le circuit
        pass


@transaction.atomic
def transmettre_au_laboratoire(fiche, user):
    echs = list(fiche.echantillons.prefetch_related("laboratoires"))
    if not echs:
        raise ValueError("Ajoutez au moins un échantillon à la fiche avant de la transmettre.")
    manquants = [e.code_echantillon for e in echs if not e.laboratoires.exists()]
    if manquants:
        raise ValueError(f"Indiquez l'entité du LANEMA concernée pour : {', '.join(manquants)}.")
    maintenant = timezone.now()
    fiche.statut = "TRANSMISE"
    fiche.date_transmission_laboratoire = maintenant
    fiche.save(update_fields=["statut", "date_transmission_laboratoire", "updated_at"])
    for e in echs:
        if e.date_heure_arrivee is None:
            e.date_heure_arrivee = maintenant
        e.statut = "EN_ATTENTE"
        e.save(update_fields=["date_heure_arrivee", "statut", "updated_at"])
        for l in e.laboratoires.all():
            Essai.objects.get_or_create(
                echantillon=e, laboratoire=l,
                defaults={"type_essai": l.nom[:100], "statut": "EN_ATTENTE"},
            )
    fiche.suivis_labo.update(statut="TRANSMIS")
    demande = fiche.demande
    if demande.statut in ("ECHANTILLONS_RECUS", "EN_ATTENTE_ECHANTILLONS"):
        demande.statut = "EN_COURS"
        demande.date_debut_analyse = demande.date_debut_analyse or maintenant.date()
        demande.save(update_fields=["statut", "date_debut_analyse"])
        try:
            demande.demande_devis.statut = "EN_COURS"
            demande.demande_devis.save(update_fields=["statut"])
        except Exception:  # pragma: no cover
            pass
    _notifier("TECHNICIEN", f"Fiche d'exécution {fiche.numero}", "Une nouvelle fiche d'exécution des travaux d'essais vous a été transmise par le service réception.")
    _notifier("GESTIONNAIRE", f"Fiche d'exécution {fiche.numero}", "Une nouvelle fiche d'exécution des travaux d'essais a été transmise au laboratoire.")
    return fiche


@transaction.atomic
def receptionner_labo(fiche, laboratoire_id, acceptation, reserves, user):
    suivi = fiche.suivis_labo.filter(laboratoire_id=laboratoire_id).first()
    if suivi is None or fiche.statut == "BROUILLON":
        raise ValueError("Ce laboratoire n'est pas concerné par cette fiche, ou elle n'a pas été transmise.")
    if suivi.statut != "TRANSMIS":
        raise ValueError("Cette fiche a déjà été réceptionnée par ce laboratoire.")
    if acceptation not in dict(FicheExecutionTravaux.ACCEPTATION_CHOICES):
        raise ValueError("Indiquez si les échantillons sont conformes ou acceptés sous réserve.")
    if acceptation == "SOUS_RESERVE" and not (reserves or "").strip():
        raise ValueError("Précisez les réserves (observations) pour une acceptation sous réserve.")
    suivi.statut = "RECU"
    suivi.date_reception = timezone.now()
    suivi.receptionne_par = user
    suivi.acceptation = acceptation
    suivi.reserves = reserves or ""
    suivi.save()
    for e in fiche.echantillons.filter(laboratoires__id=laboratoire_id):
        e.statut = "EN_ANALYSE"
        e.save(update_fields=["statut", "updated_at"])
        Essai.objects.filter(echantillon=e, laboratoire_id=laboratoire_id, statut="EN_ATTENTE").update(
            statut="EN_COURS", date_debut=timezone.now().date(), technicien=_nom(user) or "", technicien_user=user,
        )
    if not fiche.suivis_labo.exclude(statut__in=["RECU", "RESULTATS_TRANSMIS"]).exists():
        fiche.statut = "RECUE_LABO"
        fiche.save(update_fields=["statut", "updated_at"])
    return fiche


@transaction.atomic
def saisir_resultats(fiche, laboratoire_id, resultats, user):
    suivi = fiche.suivis_labo.filter(laboratoire_id=laboratoire_id).first()
    if suivi is None or suivi.statut != "RECU":
        raise ValueError("La fiche doit être réceptionnée par le laboratoire (et non encore transmise) pour saisir des résultats.")
    ech_ids = set(fiche.echantillons.filter(laboratoires__id=laboratoire_id).values_list("id", flat=True))
    gardes = set()
    for ordre, r in enumerate(resultats):
        if r.get("echantillon") not in ech_ids:
            raise ValueError("Résultat rattaché à un échantillon qui n'est pas confié à ce laboratoire.")
        parametre, valeur = (r.get("parametre") or "").strip(), str(r.get("resultat") if r.get("resultat") is not None else "").strip()
        if not parametre or not valeur:
            raise ValueError("Chaque ligne doit avoir un paramètre et un résultat.")
        champs = {
            "echantillon_id": r["echantillon"], "laboratoire_id": laboratoire_id, "parametre": parametre[:255],
            "methode": (r.get("methode") or "")[:255], "unite": (r.get("unite") or "")[:50], "resultat": valeur[:255],
            "specification": (r.get("specification") or "")[:255], "conforme": r.get("conforme"),
            "accredite": bool(r.get("accredite")), "sous_traite": bool(r.get("sous_traite")), "ordre": ordre,
            "analyste": user, "date_analyse": timezone.now().date(),
        }
        existant = ResultatEssai.objects.filter(pk=r.get("id"), laboratoire_id=laboratoire_id, echantillon_id__in=ech_ids).first()
        if existant:
            for k, v in champs.items():
                setattr(existant, k, v)
            existant.save()
            gardes.add(existant.id)
        else:
            gardes.add(ResultatEssai.objects.create(**champs).id)
    ResultatEssai.objects.filter(laboratoire_id=laboratoire_id, echantillon_id__in=ech_ids).exclude(id__in=gardes).delete()
    return fiche


@transaction.atomic
def transmettre_resultats(fiche, laboratoire_id, user):
    suivi = fiche.suivis_labo.filter(laboratoire_id=laboratoire_id).first()
    if suivi is None or suivi.statut != "RECU":
        raise ValueError("Les résultats ne peuvent être transmis qu'après réception de la fiche par le laboratoire.")
    echs = list(fiche.echantillons.filter(laboratoires__id=laboratoire_id))
    sans = [e.code_echantillon for e in echs if not e.resultats.filter(laboratoire_id=laboratoire_id).exists()]
    if sans:
        raise ValueError(f"Aucun résultat saisi pour : {', '.join(sans)}.")
    suivi.statut = "RESULTATS_TRANSMIS"
    suivi.date_transmission_resultats = timezone.now()
    suivi.transmis_par = user
    suivi.save()
    for e in echs:
        res = list(e.resultats.filter(laboratoire_id=laboratoire_id))
        non_conf = any(r.conforme is False for r in res)
        e.conforme = False if non_conf else (True if any(r.conforme for r in res) else e.conforme)
        e.statut = "TERMINE"
        e.save(update_fields=["conforme", "statut", "updated_at"])
        Essai.objects.filter(echantillon=e, laboratoire_id=laboratoire_id).update(statut="TERMINE", date_fin=timezone.now().date())
    if not fiche.suivis_labo.exclude(statut="RESULTATS_TRANSMIS").exists():
        fiche.statut = "RESULTATS_TRANSMIS"
        fiche.save(update_fields=["statut", "updated_at"])
        _notifier("RECEPTION", f"Résultats disponibles — fiche {fiche.numero}", "Tous les laboratoires ont transmis leurs résultats : le rapport d'essai peut être édité.")
    return fiche


@transaction.atomic
def recevoir_resultats(fiche, user):
    """Accuse de reception par le SRO (nom + visa) et preparation d'un rapport
    brouillon par laboratoire concerne."""
    if fiche.statut not in ("RESULTATS_TRANSMIS", "RESULTATS_RECUS"):
        raise ValueError("Tous les laboratoires doivent avoir transmis leurs résultats.")
    if fiche.statut == "RESULTATS_TRANSMIS":
        fiche.statut = "RESULTATS_RECUS"
        fiche.re_receptionne_par = user
        fiche.date_reception_re = timezone.now()
        fiche.save(update_fields=["statut", "re_receptionne_par", "date_reception_re", "updated_at"])
    for s in fiche.suivis_labo.select_related("laboratoire"):
        RapportEssaiLabo.objects.get_or_create(fiche=fiche, laboratoire=s.laboratoire)
    return fiche


@transaction.atomic
def editer_rapport(rapport, user):
    """Attribue le numero d'ordre chronologique et fige le rapport."""
    if rapport.statut != "BROUILLON":
        raise ValueError("Ce rapport est déjà édité.")
    if not rapport.fiche.echantillons.filter(laboratoires=rapport.laboratoire, resultats__isnull=False).exists():
        raise ValueError("Aucun résultat à rapporter pour ce laboratoire.")
    if not rapport.directeur_nom.strip():
        raise ValueError("Renseignez le nom et prénoms du Directeur signataire avant l'édition.")
    annee = timezone.now().year
    rapport.annee = annee
    rapport.numero_ordre = CompteurSequence.suivant(f"RE-{annee}")
    rapport.reference = reference_rapport(rapport.numero_ordre, annee, rapport.laboratoire)
    rapport.date_edition = timezone.now().date()
    rapport.edite_par = user
    rapport.statut = "EDITE"
    rapport.save()
    return rapport


@transaction.atomic
def remettre_rapport(rapport):
    if rapport.statut not in ("SIGNE",):
        raise ValueError("Le rapport doit être signé avant d'être remis au client.")
    rapport.statut = "REMIS"
    rapport.date_remise = timezone.now().date()
    rapport.save(update_fields=["statut", "date_remise", "updated_at"])
    fiche = rapport.fiche
    if not fiche.rapports.exclude(statut="REMIS").exists() and fiche.rapports.count() == fiche.suivis_labo.count():
        fiche.statut = "CLOTUREE"
        fiche.save(update_fields=["statut", "updated_at"])
        demande = fiche.demande
        demande.statut = "RESULTATS_ENVOYES"
        demande.date_fin_analyse = demande.date_fin_analyse or timezone.now().date()
        demande.save(update_fields=["statut", "date_fin_analyse"])
    return rapport


# ── Rapport d'essai : donnees ─────────────────────────────────────────────

def _agg(echs, fn):
    """Valeur unique si identique pour tous les echantillons, sinon « CODE : valeur »."""
    paires = [(e.code_echantillon, fn(e)) for e in echs]
    valeurs = {v for _, v in paires if v}
    if not valeurs:
        return "-"
    if len(valeurs) == 1:
        return next(iter(valeurs))
    return " ; ".join(f"{c} : {v}" for c, v in paires if v)


def _fmt_dt(v):
    return timezone.localtime(v).strftime("%d/%m/%Y à %H:%M") if v else ""


def rapport_data(rapport):
    fiche = rapport.fiche
    labo = rapport.laboratoire
    echs = list(fiche.echantillons.filter(laboratoires=labo).prefetch_related("resultats").order_by("id"))
    info = {
        "nature": "; ".join(dict.fromkeys(e.designation for e in echs)) or "-",
        "numero_lot": _agg(echs, lambda e: e.numero_lot),
        "lieu_prelevement": _agg(echs, lambda e: e.lieu_prelevement),
        "date_heure_prelevement": _agg(echs, lambda e: _fmt_dt(e.date_heure_prelevement) or (e.date_prelevement.strftime("%d/%m/%Y") if e.date_prelevement else "")),
        "prelevement_par": _agg(echs, lambda e: e.prelevement_par),
        "date_heure_arrivee": _agg(echs, lambda e: _fmt_dt(e.date_heure_arrivee)),
        "references": ", ".join(e.code_echantillon for e in echs),
    }
    suivi = fiche.suivis_labo.filter(laboratoire=labo).first()
    return {
        "id": rapport.id, "reference": rapport.reference or "", "statut": rapport.statut,
        "statut_display": rapport.get_statut_display(), "numero_ordre": rapport.numero_ordre, "annee": rapport.annee,
        "date_edition": rapport.date_edition,
        "laboratoire": {"id": labo.id, "code": labo.code, "nom": labo.nom, "direction": labo.direction, "sous_direction": labo.sous_direction},
        "fiche": {"id": fiche.id, "numero": fiche.numero, "demande_numero": fiche.demande.numero},
        "client": _client_info(fiche.demande), "info": info,
        "echantillons": [
            {"id": e.id, "code_echantillon": e.code_echantillon, "designation": e.designation,
             "resultats": [_resultat_dict(r) for r in e.resultats.filter(laboratoire=labo)]}
            for e in echs
        ],
        "acceptation": suivi.acceptation if suivi else "", "reserves": suivi.reserves if suivi else "",
        "informations_diverses": rapport.informations_diverses, "directeur_nom": rapport.directeur_nom,
        "date_signature": rapport.date_signature, "date_remise": rapport.date_remise,
        "edite_par_nom": _nom(rapport.edite_par),
        "modifiable": rapport.statut == "BROUILLON",
        "nb_non_conformes": sum(1 for e in echs for r in e.resultats.filter(laboratoire=labo) if r.conforme is False),
    }
