"""Envoi d'e-mails (SMTP) depuis l'application pour le service reception.

Reprend le principe du module « Courrier intelligent » : un compte SMTP
configure une fois par l'utilisateur (serveur, port, SSL/STARTTLS, identifiant,
mot de passe chiffre), auto-detection du serveur pour les fournisseurs
courants, et un expediteur qui construit un message MIME avec pieces jointes.
"""
import logging
import re
import smtplib
import ssl
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from email import encoders

from dfir_email.crypto import decrypt_value

logger = logging.getLogger(__name__)

# Fournisseurs connus (auto-detection par domaine de l'adresse d'envoi)
SMTP_PROVIDERS = {
    "gmail.com": {"host": "smtp.gmail.com", "port": 587, "ssl": False},
    "googlemail.com": {"host": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.fr": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "live.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "live.fr": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "yahoo.com": {"host": "smtp.mail.yahoo.com", "port": 587, "ssl": False},
    "yahoo.fr": {"host": "smtp.mail.yahoo.fr", "port": 587, "ssl": False},
    "zoho.com": {"host": "smtp.zoho.com", "port": 587, "ssl": False},
    "ovh.net": {"host": "ssl0.ovh.net", "port": 465, "ssl": True},
    "ovh.com": {"host": "ssl0.ovh.net", "port": 465, "ssl": True},
}

EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")


def detect_smtp_config(adresse_email: str) -> dict:
    domaine = adresse_email.split("@")[-1].lower().strip() if "@" in (adresse_email or "") else ""
    return SMTP_PROVIDERS.get(domaine, {})


def parse_adresses(valeur) -> list:
    """Accepte une liste ou une chaine « a@x.com, b@y.com ; c@z.com »."""
    if not valeur:
        return []
    if isinstance(valeur, (list, tuple)):
        brut = list(valeur)
    else:
        brut = re.split(r"[,;\n]+", str(valeur))
    return [a.strip() for a in brut if a and a.strip()]


def adresses_invalides(adresses) -> list:
    return [a for a in adresses if not EMAIL_RE.match(a)]


def config_serveur(compte) -> dict:
    auto = detect_smtp_config(compte.adresse_email)
    host = compte.serveur_sortant or auto.get("host", "")
    port = compte.port_sortant or auto.get("port", 587)
    if compte.serveur_sortant:
        use_ssl = bool(compte.ssl_sortant)
    else:
        use_ssl = auto.get("ssl", False)
    # Le port prime sur le reglage SSL : 465 = SSL direct, 587 = STARTTLS
    if port == 465:
        use_ssl = True
    elif port == 587:
        use_ssl = False
    return {
        "host": host,
        "port": port,
        "ssl": use_ssl,
        "identifiant": compte.identifiant or compte.adresse_email,
        "password": decrypt_value(compte.mot_de_passe),
    }


def _message(compte, destinataires, cc, sujet, corps, pieces):
    """pieces : liste de tuples (nom_fichier, bytes, mimetype)."""
    msg = MIMEMultipart()
    msg["Subject"] = sujet or ""
    msg["From"] = formataddr((compte.nom_affichage or "", compte.adresse_email))
    msg["To"] = ", ".join(destinataires)
    if cc:
        msg["Cc"] = ", ".join(cc)
    domaine = compte.adresse_email.split("@")[-1] if "@" in compte.adresse_email else "lanema.local"
    msg["Message-ID"] = make_msgid(domain=domaine)
    corps_complet = corps or ""
    if compte.signature:
        corps_complet = f"{corps_complet.rstrip()}\n\n-- \n{compte.signature}"
    msg.attach(MIMEText(corps_complet, "plain", "utf-8"))
    for nom, contenu, mime in pieces:
        maintype, _, subtype = (mime or "application/octet-stream").partition("/")
        part = MIMEBase(maintype or "application", subtype or "octet-stream")
        part.set_payload(contenu)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=nom)
        msg.attach(part)
    return msg


def envoyer(compte, destinataires, cc, sujet, corps, pieces=()) -> dict:
    """Envoie via SMTP. Retourne {'success': bool, 'message': str}."""
    cfg = config_serveur(compte)
    if not cfg["host"]:
        return {"success": False, "message": "Serveur SMTP non configuré pour ce compte."}
    if not cfg["password"]:
        return {"success": False, "message": "Mot de passe non renseigné pour ce compte."}
    try:
        msg = _message(compte, destinataires, cc, sujet, corps, pieces)
        tous = list(destinataires) + list(cc or [])
        if cfg["ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ssl.create_default_context(), timeout=30) as srv:
                srv.login(cfg["identifiant"], cfg["password"])
                srv.sendmail(compte.adresse_email, tous, msg.as_string())
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as srv:
                srv.ehlo()
                try:
                    srv.starttls(context=ssl.create_default_context())
                    srv.ehlo()
                except smtplib.SMTPNotSupportedError:
                    # Serveur sans STARTTLS (ex. relais local de test) : on continue en clair
                    pass
                if srv.has_extn("auth"):
                    srv.login(cfg["identifiant"], cfg["password"])
                srv.sendmail(compte.adresse_email, tous, msg.as_string())
        return {"success": True, "message": "Email envoyé avec succès."}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentification SMTP échouée. Vérifiez l'identifiant et le mot de passe."}
    except (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError, OSError) as exc:
        return {"success": False, "message": f"Connexion SMTP impossible ({cfg['host']}:{cfg['port']}) : {exc}"}
    except Exception as exc:  # pragma: no cover - garde-fou
        logger.error("Erreur envoi email devis : %s", exc)
        return {"success": False, "message": str(exc)}


def tester_connexion(compte) -> dict:
    cfg = config_serveur(compte)
    if not cfg["host"]:
        return {"success": False, "message": "Serveur SMTP non renseigné."}
    try:
        if cfg["ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ssl.create_default_context(), timeout=15) as srv:
                srv.login(cfg["identifiant"], cfg["password"])
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as srv:
                srv.ehlo()
                try:
                    srv.starttls(context=ssl.create_default_context())
                    srv.ehlo()
                except smtplib.SMTPNotSupportedError:
                    pass
                if srv.has_extn("auth"):
                    srv.login(cfg["identifiant"], cfg["password"])
        return {"success": True, "message": "Connexion SMTP réussie."}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentification échouée : identifiant ou mot de passe incorrect."}
    except Exception as exc:
        return {"success": False, "message": f"Connexion impossible : {exc}"}


# ─── Contenu par defaut du message de devis ───────────────────────────────

def message_devis_par_defaut(proforma) -> tuple:
    """(sujet, corps) proposes dans le formulaire d'envoi."""
    profil = getattr(proforma.client, "client_profile", None)
    nom = (getattr(profil, "contact_nom", "") or getattr(profil, "raison_sociale", "")
           or proforma.client.get_full_name() or "").strip()
    montant = f"{proforma.montant_ttc:,.0f}".replace(",", " ")
    sujet = f"Votre devis {proforma.numero} — LANEMA"
    corps = (
        f"Bonjour{' ' + nom if nom else ''},\n\n"
        f"Suite à votre demande, veuillez trouver ci-joint votre devis {proforma.numero} "
        f"d'un montant de {montant} {proforma.devise} TTC.\n\n"
        "Pour l'accepter, connectez-vous à votre espace client LANEMA, ouvrez la fiche de devis "
        "et apposez la mention « Lu et approuvé » avec votre signature.\n\n"
        "Nous restons à votre disposition pour tout renseignement complémentaire.\n\n"
        "Cordialement,\nService Réception — LANEMA"
    )
    return sujet, corps


def normaliser_telephone_whatsapp(telephone: str, indicatif: str = "225") -> str:
    """Numero au format international sans « + » attendu par wa.me.
    Un numero ivoirien a 10 chiffres (ex. 01 23 45 67 89) recoit l'indicatif 225."""
    chiffres = re.sub(r"\D", "", telephone or "")
    if not chiffres:
        return ""
    if chiffres.startswith("00"):
        chiffres = chiffres[2:]
    elif len(chiffres) == 10:
        chiffres = indicatif + chiffres
    return chiffres
