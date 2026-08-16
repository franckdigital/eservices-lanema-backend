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
