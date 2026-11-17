"""Catalogue metrologique : familles d'instruments, instruments pris en charge et
champs techniques specifiques a renseigner par le client dans la demande de devis.

Les champs communs (marque, modele, n° de serie, quantite, localisation) sont
toujours demandes ; ceux listes ici s'y ajoutent selon l'instrument choisi. Les
tarifs ne sont volontairement pas renseignes ici : ils restent ceux du devis,
ajustes par le service reception sur la fiche de devis."""

CHAMPS_COMMUNS = [
    {"key": "marque", "label": "Marque"},
    {"key": "modele", "label": "Modèle"},
    {"key": "numero_serie", "label": "Numéro de série"},
    {"key": "localisation", "label": "Localisation (site où se trouve l'instrument)"},
]

PRESTATIONS = [
    {"code": "ETALONNAGE", "nom": "Étalonnage d'un instrument de mesure"},
    {"code": "VERIFICATION", "nom": "Vérification métrologique"},
    {"code": "CONTROLE", "nom": "Contrôle métrologique"},
    {"code": "EXPERTISE", "nom": "Expertise métrologique"},
    {"code": "AJUSTAGE", "nom": "Ajustage ou réglage"},
    {"code": "AUTRE", "nom": "Autre prestation"},
]


def _c(key, label, placeholder=""):
    return {"key": key, "label": label, "placeholder": placeholder}


FAMILLES = [
    {"code": "MASSE", "nom": "Masse", "grandeur": "MASSE", "types": [
        {"code": "BALANCE", "nom": "Balance électronique", "champs": [
            _c("portee_max", "Portée maximale", "ex. 300 kg"), _c("echelon", "Échelon de vérification (e)", "ex. 0,01 g"), _c("classe", "Classe de précision", "I, II, III, IIII")]},
        {"code": "POIDS_ETALONS", "nom": "Poids étalons", "champs": [
            _c("valeur_nominale", "Valeur nominale", "ex. 1 kg"), _c("classe", "Classe OIML", "E2, F1, F2, M1")]},
    ]},
    {"code": "TEMPERATURE", "nom": "Température", "grandeur": "TEMPERATURE", "types": [
        {"code": "THERMOMETRE", "nom": "Thermomètre", "champs": [
            _c("plage_mesure", "Plage de mesure", "ex. 0 à 200 °C"), _c("resolution", "Résolution", "ex. 0,1 °C"), _c("unite", "Unité", "°C")]},
        {"code": "SONDE", "nom": "Sonde / capteur de température", "champs": [
            _c("plage_mesure", "Plage de mesure", "ex. -50 à 400 °C"), _c("type_sonde", "Type de sonde", "Pt100, thermocouple K…"), _c("resolution", "Résolution", "")]},
        {"code": "ENCEINTE", "nom": "Enceinte thermique (étuve, four, bain)", "champs": [
            _c("plage_mesure", "Plage de température", "ex. 20 à 250 °C"), _c("volume_utile", "Volume utile", "ex. 100 L")]},
    ]},
    {"code": "PRESSION", "nom": "Pression", "grandeur": "PRESSION", "types": [
        {"code": "MANOMETRE", "nom": "Manomètre", "champs": [
            _c("plage_mesure", "Plage de mesure", "ex. 0 à 16 bar"), _c("classe", "Classe de précision", "ex. 1,0"), _c("unite", "Unité", "bar, MPa, psi")]},
        {"code": "VACUOMETRE", "nom": "Vacuomètre", "champs": [_c("plage_mesure", "Plage de mesure", "ex. -1 à 0 bar"), _c("unite", "Unité", "")]},
    ]},
    {"code": "VOLUME", "nom": "Volume", "grandeur": "VOLUME", "types": [
        {"code": "PIPETTE", "nom": "Pipette", "champs": [_c("volume_nominal", "Volume nominal", "ex. 10 mL"), _c("classe", "Classe", "A, B")]},
        {"code": "BURETTE", "nom": "Burette", "champs": [_c("volume_nominal", "Volume nominal", "ex. 50 mL"), _c("classe", "Classe", "A, B")]},
        {"code": "EPROUVETTE", "nom": "Éprouvette / fiole / verrerie jaugée", "champs": [_c("volume_nominal", "Volume nominal", "ex. 100 mL"), _c("classe", "Classe", "A, B")]},
    ]},
    {"code": "ELECTRICITE", "nom": "Électricité", "grandeur": "ELECTRICITE", "types": [
        {"code": "MULTIMETRE", "nom": "Multimètre", "champs": [_c("plage_mesure", "Calibres / plages", "ex. 0 à 1000 V"), _c("resolution", "Résolution", "")]},
        {"code": "PINCE", "nom": "Pince ampèremétrique", "champs": [_c("plage_mesure", "Plage de mesure", "ex. 0 à 600 A"), _c("resolution", "Résolution", "")]},
    ]},
    {"code": "DIMENSIONNEL", "nom": "Dimensionnel", "grandeur": "DIMENSIONNEL", "types": [
        {"code": "PIED_COULISSE", "nom": "Pied à coulisse", "champs": [_c("plage_mesure", "Étendue de mesure", "ex. 0 à 150 mm"), _c("resolution", "Résolution", "ex. 0,01 mm")]},
        {"code": "MICROMETRE", "nom": "Micromètre", "champs": [_c("plage_mesure", "Étendue de mesure", "ex. 0 à 25 mm"), _c("resolution", "Résolution", "ex. 0,001 mm")]},
    ]},
    {"code": "AUTRE", "nom": "Autre instrument", "grandeur": "AUTRE", "types": [
        {"code": "AUTRE", "nom": "Autre instrument de mesure", "champs": [
            _c("plage_mesure", "Plage de mesure", ""), _c("resolution", "Résolution", ""), _c("classe", "Classe de précision", ""), _c("unite", "Unité de mesure", "")]},
    ]},
]


def catalogue():
    return {"familles": FAMILLES, "champs_communs": CHAMPS_COMMUNS, "prestations": PRESTATIONS}
