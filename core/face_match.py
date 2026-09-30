"""Comparaison faciale auto-hébergée (face_recognition/dlib) entre la photo de
référence RH (FicheAgent.photo) et la photo capturée lors d'un pointage
assisté — empêche qu'un agent fasse valider sa présence par un collègue.
Import de face_recognition différé (lourd, dlib) : ne pénalise que les
requêtes qui l'utilisent réellement, pas le démarrage de l'app."""
import logging

logger = logging.getLogger(__name__)

# Distance euclidienne entre encodages faciaux (128-d) — 0.6 est le seuil par
# défaut recommandé par face_recognition, en dessous duquel deux visages sont
# considérés comme la même personne.
DEFAULT_TOLERANCE = 0.6


def compare_faces(reference_field, captured_field, tolerance=DEFAULT_TOLERANCE):
    """Compare le visage de deux ImageField (FicheAgent.photo vs photo de
    vérification du pointage). Retourne un dict :
        matched: bool | None (None si comparaison impossible)
        distance: float | None
        error: str | None (raison lisible si matched est None)
        stage: 'reference' | 'captured' | None — quel côté a posé problème,
               pour distinguer un souci de qualité de la photo RH (pas la
               faute de l'agent, ne doit pas bloquer le pointage) d'un souci
               sur la photo prise à l'instant (doit bloquer, l'agent peut
               reprendre la photo).
    N'échoue jamais par exception — un souci de lecture/format de photo doit
    être traité comme "comparaison impossible", pas planter le pointage.
    """
    try:
        import face_recognition
    except ImportError:
        logger.error('[face_match] face_recognition non installé — comparaison ignorée')
        return {'matched': None, 'distance': None, 'error': 'moteur de reconnaissance faciale indisponible', 'stage': 'reference'}

    try:
        reference_field.seek(0)
        reference_image = face_recognition.load_image_file(reference_field)
        reference_encodings = face_recognition.face_encodings(reference_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo de référence')
        return {'matched': None, 'distance': None, 'error': 'photo de référence illisible', 'stage': 'reference'}

    if not reference_encodings:
        return {'matched': None, 'distance': None, 'error': 'aucun visage détecté sur la photo de référence', 'stage': 'reference'}

    try:
        captured_field.seek(0)
        captured_image = face_recognition.load_image_file(captured_field)
        captured_encodings = face_recognition.face_encodings(captured_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo capturée')
        return {'matched': None, 'distance': None, 'error': 'photo capturée illisible', 'stage': 'captured'}

    if not captured_encodings:
        return {'matched': None, 'distance': None, 'error': 'aucun visage détecté sur la photo capturée', 'stage': 'captured'}

    distance = float(face_recognition.face_distance([reference_encodings[0]], captured_encodings[0])[0])
    return {'matched': distance <= tolerance, 'distance': distance, 'error': None, 'stage': None}


def extract_single_face(image_field):
    """Vérifie qu'une image contient exactement un visage détectable et
    renvoie son encodage (liste de 128 floats, sérialisable JSON) — utilisé
    à la fois pour accepter une NOUVELLE photo de référence (bootstrap d'une
    fiche agent qui n'en a pas encore) et pour mettre en cache
    FicheAgent.face_encoding. Ne lève jamais d'exception, comme compare_faces.
    Retourne {'ok': bool, 'error': str|None, 'encoding': list[float]|None}.
    """
    try:
        import face_recognition
    except ImportError:
        return {'ok': False, 'error': 'moteur de reconnaissance faciale indisponible', 'encoding': None}

    try:
        image_field.seek(0)
        image = face_recognition.load_image_file(image_field)
        encodings = face_recognition.face_encodings(image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo (extraction visage unique)')
        return {'ok': False, 'error': 'photo illisible', 'encoding': None}

    if not encodings:
        return {'ok': False, 'error': 'aucun visage détecté', 'encoding': None}
    if len(encodings) > 1:
        return {'ok': False, 'error': f'{len(encodings)} visages détectés', 'encoding': None}
    return {'ok': True, 'error': None, 'encoding': encodings[0].tolist()}


# Écart minimal exigé entre la meilleure et la 2ᵉ meilleure correspondance
# pour accepter une identification 1:N — évite de trancher entre deux agents
# qui se ressemblent au lieu de demander une sélection manuelle.
IDENTIFY_MARGIN = 0.08


def identify_face(captured_field, known_encodings, known_ids, tolerance=DEFAULT_TOLERANCE, margin=IDENTIFY_MARGIN):
    """Identification 1:N : compare le visage capturé à une liste d'encodages
    déjà en cache (FicheAgent.face_encoding), sans redécoder aucune photo de
    référence. `known_encodings`/`known_ids` doivent être alignés (même index
    = même agent). Retourne :
        status: 'matched' | 'no_match' | 'ambiguous' | 'error'
        fiche_agent_id: int | None
        distance: float | None
        error: str | None
    """
    try:
        import face_recognition
        import numpy as np
    except ImportError:
        return {'status': 'error', 'fiche_agent_id': None, 'distance': None,
                'error': 'moteur de reconnaissance faciale indisponible'}

    try:
        captured_field.seek(0)
        captured_image = face_recognition.load_image_file(captured_field)
        captured_encodings = face_recognition.face_encodings(captured_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo capturée (identification)')
        return {'status': 'error', 'fiche_agent_id': None, 'distance': None, 'error': 'photo illisible'}

    if not captured_encodings:
        return {'status': 'error', 'fiche_agent_id': None, 'distance': None, 'error': 'aucun visage détecté'}
    if len(captured_encodings) > 1:
        return {'status': 'error', 'fiche_agent_id': None, 'distance': None,
                'error': f'{len(captured_encodings)} visages détectés — cadrez un seul visage'}

    if not known_encodings:
        return {'status': 'no_match', 'fiche_agent_id': None, 'distance': None, 'error': None}

    distances = face_recognition.face_distance(np.array(known_encodings), captured_encodings[0])
    order = np.argsort(distances)
    best_idx = int(order[0])
    best_distance = float(distances[best_idx])

    if best_distance > tolerance:
        return {'status': 'no_match', 'fiche_agent_id': None, 'distance': best_distance, 'error': None}

    if len(order) > 1:
        second_distance = float(distances[int(order[1])])
        if second_distance <= tolerance and (second_distance - best_distance) < margin:
            return {'status': 'ambiguous', 'fiche_agent_id': None, 'distance': best_distance, 'error': None}

    return {'status': 'matched', 'fiche_agent_id': known_ids[best_idx], 'distance': best_distance, 'error': None}
