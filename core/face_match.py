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

# Plus grand côté (px) auquel une image est ramenée avant toute détection de
# visage. La détection HOG de dlib est ~proportionnelle au nombre de pixels.
# Descendu à 480 (depuis 720) car _detect_encodings() fait maintenant 2
# passes : une rapide à cette taille, et SEULEMENT si elle échoue, une 2e
# passe plus sensible (upsample x2) avant de conclure à l'échec — donc la
# sensibilité aux visages petits/éloignés est compensée par le fallback,
# sans payer son coût sur le cas normal (la grande majorité des captures).
MAX_IMAGE_DIM = 480


def _load_image_array(image_field):
    """Charge une image (ImageField/UploadedFile) et la redimensionne avant
    tout traitement facial — voir MAX_IMAGE_DIM."""
    from PIL import Image, ImageOps
    import numpy as np

    image_field.seek(0)
    img = Image.open(image_field)
    img = ImageOps.exif_transpose(img)  # respecte l'orientation EXIF (photo prise en portrait)
    img = img.convert('RGB')
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIM:
        scale = MAX_IMAGE_DIM / max(w, h)
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    return np.array(img)


def _detect_encodings(image_array):
    """Détecte et encode les visages d'une image, en 2 passes :
    1) détection rapide (HOG, upsample=1) — le cas normal, quasi instantané.
    2) SEULEMENT si la passe 1 n'a rien trouvé : nouvelle tentative plus
       sensible (upsample=2) avant de conclure "aucun visage" — récupère les
       visages un peu petits/éloignés/mal cadrés sans ralentir le cas normal
       (l'écrasante majorité des captures), puisque la passe 2 ne se
       déclenche que sur échec de la passe 1."""
    import face_recognition

    locations = face_recognition.face_locations(image_array)  # HOG, upsample=1 (rapide)
    if not locations:
        locations = face_recognition.face_locations(image_array, number_of_times_to_upsample=2)
    if not locations:
        return []
    return face_recognition.face_encodings(image_array, known_face_locations=locations)


def compare_faces(reference_field, captured_field, tolerance=DEFAULT_TOLERANCE):
    """Compare le visage de deux ImageField (FicheAgent.photo vs photo de
    vérification du pointage) en redécodant et ré-encodant les DEUX images.
    Préférer compare_faces_with_cache() quand un FicheAgent est disponible
    (évite de redécoder la photo de référence à chaque pointage). Retourne :
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
        reference_image = _load_image_array(reference_field)
        reference_encodings = _detect_encodings(reference_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo de référence')
        return {'matched': None, 'distance': None, 'error': 'photo de référence illisible', 'stage': 'reference'}

    if not reference_encodings:
        return {'matched': None, 'distance': None, 'error': 'aucun visage détecté sur la photo de référence', 'stage': 'reference'}

    try:
        captured_image = _load_image_array(captured_field)
        captured_encodings = _detect_encodings(captured_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo capturée')
        return {'matched': None, 'distance': None, 'error': 'photo capturée illisible', 'stage': 'captured'}

    if not captured_encodings:
        return {'matched': None, 'distance': None, 'error': 'aucun visage détecté sur la photo capturée', 'stage': 'captured'}

    distance = float(face_recognition.face_distance([reference_encodings[0]], captured_encodings[0])[0])
    return {'matched': distance <= tolerance, 'distance': distance, 'error': None, 'stage': None}


def compare_faces_with_cache(fiche_agent, captured_field, tolerance=DEFAULT_TOLERANCE):
    """Comme compare_faces, mais réutilise fiche_agent.face_encoding (calculé
    une fois pour toutes à l'enregistrement de la photo de référence) au lieu
    de redécoder ET ré-encoder cette photo à CHAQUE pointage — évite la
    moitié du travail (un seul visage à détecter/encoder : le capturé),
    optimisation principale pour la lenteur ressentie sur ProxyPresenceView.
    Retombe sur compare_faces() (recalcul complet) si le cache est absent
    (photo ajoutée avant ce cache, ou échec d'encodage précédent)."""
    try:
        import face_recognition
    except ImportError:
        logger.error('[face_match] face_recognition non installé — comparaison ignorée')
        return {'matched': None, 'distance': None, 'error': 'moteur de reconnaissance faciale indisponible', 'stage': 'reference'}

    reference_encoding = getattr(fiche_agent, 'face_encoding', None)
    if not reference_encoding:
        return compare_faces(fiche_agent.photo, captured_field, tolerance)

    try:
        captured_image = _load_image_array(captured_field)
        captured_encodings = _detect_encodings(captured_image)
    except Exception:
        logger.exception('[face_match] échec lecture/encodage photo capturée')
        return {'matched': None, 'distance': None, 'error': 'photo capturée illisible', 'stage': 'captured'}

    if not captured_encodings:
        return {'matched': None, 'distance': None, 'error': 'aucun visage détecté sur la photo capturée', 'stage': 'captured'}

    import numpy as np
    distance = float(face_recognition.face_distance([np.array(reference_encoding)], captured_encodings[0])[0])
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
        import face_recognition  # noqa: F401  (juste pour détecter l'absence du moteur)
    except ImportError:
        return {'ok': False, 'error': 'moteur de reconnaissance faciale indisponible', 'encoding': None}

    try:
        image = _load_image_array(image_field)
        encodings = _detect_encodings(image)
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
    référence — seule la photo capturée est décodée/encodée ici. Retourne :
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
        captured_image = _load_image_array(captured_field)
        captured_encodings = _detect_encodings(captured_image)
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
