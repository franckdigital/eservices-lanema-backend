"""Extraction de texte des documents GED pour alimenter contenu_ocr (recherche
plein texte). Utilise PyMuPDF (fitz) pour lire le texte déjà encodé dans les
PDF texte (factures, courriers, contrats bureautiques...) — pas d'OCR image
par pixel (pas de dépendance Tesseract) : les documents scannés en image pure
ne produiront pas de texte, mais tout PDF généré numériquement (l'immense
majorité des documents administratifs) sera indexé sans nouvelle dépendance
système."""
import logging

logger = logging.getLogger(__name__)

MAX_CHARS = 200_000


def extraire_texte_document(fichier):
    """Retourne le texte extrait de `fichier` (FieldFile Django), ou une
    chaîne vide si le format n'est pas supporté ou en cas d'erreur."""
    nom = (getattr(fichier, 'name', '') or '').lower()
    if not nom.endswith('.pdf'):
        return ''
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF non installé : extraction de texte GED désactivée.")
        return ''

    try:
        fichier.seek(0)
        data = fichier.read()
        fichier.seek(0)
        texte_pages = []
        with fitz.open(stream=data, filetype='pdf') as pdf:
            for page in pdf:
                texte_pages.append(page.get_text())
        texte = '\n'.join(texte_pages).strip()
        return texte[:MAX_CHARS]
    except Exception:
        logger.exception("Échec de l'extraction de texte GED pour %s", nom)
        return ''
