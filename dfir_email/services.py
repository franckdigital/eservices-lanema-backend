"""
Envoi (SMTP) et réception (IMAP) réels, plus une analyse "intelligente" par
mots-clés (pas de LLM) — même principe que le module courrier_intelligent de
référence, dans un périmètre volontairement réduit à SMTP+IMAP (le cas
largement majoritaire) pour rester maintenable.
"""
import email as email_lib
import imaplib
import smtplib
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, parseaddr, parsedate_to_datetime

from django.core.files.base import ContentFile
from django.utils import timezone

from .crypto import decrypt_value

# Domaine -> (serveur IMAP, port, ssl), (serveur SMTP, port, tls)
PROVIDER_PRESETS = {
    "gmail.com": {"imap": ("imap.gmail.com", 993, True), "smtp": ("smtp.gmail.com", 587, True)},
    "outlook.com": {"imap": ("outlook.office365.com", 993, True), "smtp": ("smtp.office365.com", 587, True)},
    "hotmail.com": {"imap": ("outlook.office365.com", 993, True), "smtp": ("smtp.office365.com", 587, True)},
    "office365.com": {"imap": ("outlook.office365.com", 993, True), "smtp": ("smtp.office365.com", 587, True)},
    "yahoo.com": {"imap": ("imap.mail.yahoo.com", 993, True), "smtp": ("smtp.mail.yahoo.com", 587, True)},
    "yahoo.fr": {"imap": ("imap.mail.yahoo.com", 993, True), "smtp": ("smtp.mail.yahoo.com", 587, True)},
    "zoho.com": {"imap": ("imap.zoho.com", 993, True), "smtp": ("smtp.zoho.com", 587, True)},
}


def detect_provider_config(email_address):
    domain = email_address.split("@")[-1].lower() if "@" in email_address else ""
    return PROVIDER_PRESETS.get(domain)


def _password(compte):
    return decrypt_value(compte.mot_de_passe)


def test_smtp_connection(compte):
    try:
        server = smtplib.SMTP(compte.serveur_sortant, compte.port_sortant, timeout=10)
        try:
            if compte.ssl_sortant:
                server.starttls()
            server.login(compte.identifiant or compte.adresse_email, _password(compte))
        finally:
            server.quit()
        return True, "Connexion SMTP réussie."
    except Exception as exc:
        return False, str(exc)


def test_imap_connection(compte):
    try:
        conn = (
            imaplib.IMAP4_SSL(compte.serveur_entrant, compte.port_entrant, timeout=10)
            if compte.ssl_entrant
            else imaplib.IMAP4(compte.serveur_entrant, compte.port_entrant, timeout=10)
        )
        try:
            conn.login(compte.identifiant or compte.adresse_email, _password(compte))
        finally:
            conn.logout()
        return True, "Connexion IMAP réussie."
    except Exception as exc:
        return False, str(exc)


def send_email(compte, destinataires, sujet, corps_texte, corps_html=None, cc=None, en_reponse_a=None, pieces_jointes=None):
    """Envoie un email via SMTP et renvoie son Message-ID."""
    msg = MIMEMultipart("mixed")
    msg["From"] = compte.adresse_email
    msg["To"] = ", ".join(destinataires)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = sujet
    message_id = make_msgid()
    msg["Message-ID"] = message_id
    if en_reponse_a and en_reponse_a.message_id:
        msg["In-Reply-To"] = en_reponse_a.message_id
        msg["References"] = en_reponse_a.message_id

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(corps_texte or "", "plain", "utf-8"))
    if corps_html:
        alt.attach(MIMEText(corps_html, "html", "utf-8"))
    msg.attach(alt)

    for pj in pieces_jointes or []:
        part = MIMEApplication(pj["contenu"], Name=pj["nom"])
        part["Content-Disposition"] = f'attachment; filename="{pj["nom"]}"'
        msg.attach(part)

    server = smtplib.SMTP(compte.serveur_sortant, compte.port_sortant, timeout=20)
    try:
        if compte.ssl_sortant:
            server.starttls()
        server.login(compte.identifiant or compte.adresse_email, _password(compte))
        tous = list(destinataires) + list(cc or [])
        server.sendmail(compte.adresse_email, tous, msg.as_string())
    finally:
        server.quit()

    return message_id


def _decode(value):
    if not value:
        return ""
    decoded = ""
    for text, enc in decode_header(value):
        decoded += text.decode(enc or "utf-8", errors="ignore") if isinstance(text, bytes) else text
    return decoded


def sync_compte(compte, limite=30):
    """Récupère les derniers messages de la boîte IMAP, ignore ceux déjà
    connus (message_id déjà en base pour ce compte)."""
    from .models import EmailDFIR, PieceJointeEmailDFIR

    conn = (
        imaplib.IMAP4_SSL(compte.serveur_entrant, compte.port_entrant, timeout=15)
        if compte.ssl_entrant
        else imaplib.IMAP4(compte.serveur_entrant, compte.port_entrant, timeout=15)
    )
    nb_nouveaux = 0
    try:
        conn.login(compte.identifiant or compte.adresse_email, _password(compte))
        conn.select("INBOX")
        _, data = conn.search(None, "ALL")
        ids = data[0].split()[-limite:] if data and data[0] else []

        for msg_num in ids:
            _, msg_data = conn.fetch(msg_num, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            parsed = email_lib.message_from_bytes(raw)
            message_id = (parsed.get("Message-ID") or "").strip()
            if not message_id or EmailDFIR.objects.filter(compte=compte, message_id=message_id).exists():
                continue

            sujet = _decode(parsed.get("Subject", ""))
            expediteur_nom, expediteur_email = parseaddr(parsed.get("From", ""))
            expediteur_nom = _decode(expediteur_nom)
            try:
                date_message = parsedate_to_datetime(parsed.get("Date"))
            except Exception:
                date_message = None

            corps_texte, corps_html = "", ""
            pieces = []
            if parsed.is_multipart():
                for part in parsed.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition") or "")
                    if "attachment" in disposition:
                        filename = part.get_filename()
                        if filename:
                            pieces.append((_decode(filename), content_type, part.get_payload(decode=True)))
                        continue
                    if content_type == "text/plain" and not corps_texte:
                        payload = part.get_payload(decode=True)
                        if payload:
                            corps_texte = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    elif content_type == "text/html" and not corps_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            corps_html = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
            else:
                payload = parsed.get_payload(decode=True)
                if payload:
                    corps_texte = payload.decode(parsed.get_content_charset() or "utf-8", errors="ignore")

            in_reply_to = (parsed.get("In-Reply-To") or "").strip()
            references = (parsed.get("References") or "").strip()
            thread_id = (references.split()[0] if references else (in_reply_to or message_id))
            en_reponse_a = (
                EmailDFIR.objects.filter(compte=compte, message_id=in_reply_to).first() if in_reply_to else None
            )

            email_obj = EmailDFIR.objects.create(
                compte=compte, direction="ENTRANT", message_id=message_id, thread_id=thread_id,
                en_reponse_a=en_reponse_a, sujet=sujet, expediteur_nom=expediteur_nom,
                expediteur_email=expediteur_email, destinataires=[compte.adresse_email],
                corps_texte=corps_texte, corps_html=corps_html, date_message=date_message, statut="NON_LU",
            )
            analyser_ia(email_obj)

            for nom, mime, contenu in pieces:
                if contenu:
                    pj = PieceJointeEmailDFIR(
                        email=email_obj, nom_fichier=nom or "piece-jointe", type_mime=mime or "", taille=len(contenu)
                    )
                    pj.fichier.save(nom or "piece-jointe", ContentFile(contenu), save=True)
            nb_nouveaux += 1
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    compte.derniere_synchro = timezone.now()
    compte.statut = "ACTIF"
    compte.derniere_erreur = ""
    compte.save(update_fields=["derniere_synchro", "statut", "derniere_erreur"])
    return nb_nouveaux


MOTS_URGENTS = ["urgent", "important", "délai", "delai", "deadline", "immédiat", "immediat", "asap", "critique"]
VERBES_ACTION = ["envoyer", "préparer", "preparer", "valider", "organiser", "soumettre", "confirmer", "répondre", "repondre"]


def analyser_ia(email_obj):
    """Heuristique par mots-clés (score d'urgence + détection d'actions +
    résumé tronqué) — pas d'appel à un service d'IA externe."""
    texte = f"{email_obj.sujet} {email_obj.corps_texte}".lower()
    score = min(sum(15 for mot in MOTS_URGENTS if mot in texte), 100)

    actions = []
    for ligne in (email_obj.corps_texte or "").split("\n"):
        ligne_propre = ligne.strip()
        if ligne_propre and any(v in ligne_propre.lower() for v in VERBES_ACTION):
            actions.append(ligne_propre[:200])

    email_obj.score_urgence = score
    email_obj.actions_detectees = actions[:10]
    email_obj.resume_ia = f"{email_obj.sujet}. {(email_obj.corps_texte or '')[:200]}".strip()
    email_obj.priorite = "URGENTE" if score >= 30 else ("HAUTE" if score >= 15 else "NORMALE")
    email_obj.traite_par_ia = True
    email_obj.save(update_fields=["score_urgence", "actions_detectees", "resume_ia", "priorite", "traite_par_ia"])
    return email_obj
