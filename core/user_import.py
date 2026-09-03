"""
Import en masse d'utilisateurs depuis un fichier Excel (.xlsx) ou CSV.

Colonnes reconnues (insensible à la casse / aux accents, FR ou EN) :

  username*        identifiant unique, sans espace
  password*        mot de passe (min. 6 caractères)
  prenom* / first_name
  nom* / last_name
  email*           email unique
  telephone        unique ; format libre (ex: +2250700000000)
  matricule        unique ; si vide → généré automatiquement (Mxxxxx)
  role*            ADMIN | DIRECTEUR | SOUS_DIRECTEUR | CHEF_SERVICE |
                   SUPERIEUR | AGENT | SECRETAIRE | PRESTATAIRE
  cabinet          nom exact d'une Direction de type "cabinet"
  direction_generale  nom exact d'une Direction de type "direction_generale"
  direction        nom exact d'une Direction de type "direction"
  sous_direction   nom exact d'une SousDirection
  service          nom exact d'un Service
  site             nom exact d'un Site
  actif            OUI/NON (défaut OUI)

(* = obligatoire)
"""
import csv
import io
import unicodedata

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction

from .models import UserProfile, Direction, SousDirection, Service, Site


ROLES_VALIDES = {c[0] for c in UserProfile.ROLE_CHOICES}

# alias de colonnes -> nom canonique
COLONNES = {
    'username': 'username', 'identifiant': 'username', "nom d'utilisateur": 'username',
    'password': 'password', 'mot de passe': 'password', 'motdepasse': 'password',
    'first_name': 'prenom', 'prenom': 'prenom', 'prenoms': 'prenom',
    'last_name': 'nom', 'nom': 'nom', 'nom de famille': 'nom',
    'email': 'email', 'mail': 'email', 'courriel': 'email',
    'telephone': 'telephone', 'tel': 'telephone', 'phone': 'telephone', 'contact': 'telephone',
    'matricule': 'matricule',
    'role': 'role', 'rôle': 'role', 'fonction': 'role',
    'cabinet': 'cabinet',
    'direction_generale': 'direction_generale', 'direction generale': 'direction_generale',
    'dg': 'direction_generale',
    'direction': 'direction',
    'sous_direction': 'sous_direction', 'sous-direction': 'sous_direction',
    'sous direction': 'sous_direction',
    'service': 'service',
    'site': 'site', 'bureau': 'site', 'site / bureau': 'site',
    'actif': 'actif', 'active': 'actif', 'statut': 'actif',
}

CANON_HEADERS = ['username', 'password', 'prenom', 'nom', 'email', 'telephone',
                 'matricule', 'role', 'cabinet', 'direction_generale', 'direction',
                 'sous_direction', 'service', 'site', 'actif']


def _norm(s):
    if s is None:
        return ''
    s = str(s).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s


def _canon_key(header):
    return COLONNES.get(_norm(header))


def parse_import_file(django_file):
    """Retourne (rows, warnings). Chaque row = dict {canonical_col: valeur_str}."""
    name = (getattr(django_file, 'name', '') or '').lower()
    raw = django_file.read()
    warnings = []

    if name.endswith('.csv') or name.endswith('.txt'):
        text = raw.decode('utf-8-sig', errors='replace')
        # détection du séparateur
        sample = text[:2048]
        delim = ';' if sample.count(';') >= sample.count(',') else ','
        reader = csv.reader(io.StringIO(text), delimiter=delim)
        table = [list(r) for r in reader if any((c or '').strip() for c in r)]
    else:
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError(
                "Le module 'openpyxl' est requis pour les fichiers .xlsx. "
                "Installez-le (pip install openpyxl) ou utilisez un fichier .csv."
            )
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        table = []
        for r in ws.iter_rows(values_only=True):
            if r is None:
                continue
            if any((str(c).strip() if c is not None else '') for c in r):
                table.append(list(r))

    if not table:
        return [], ['Fichier vide.']

    headers = table[0]
    canon = [_canon_key(h) for h in headers]
    inconnues = [str(h) for h, c in zip(headers, canon) if h and c is None]
    if inconnues:
        warnings.append("Colonnes ignorées : " + ", ".join(inconnues))

    rows = []
    for values in table[1:]:
        row = {}
        for col, val in zip(canon, values):
            if not col:
                continue
            row[col] = ('' if val is None else str(val).strip())
        if any(row.get(k) for k in ('username', 'email', 'nom', 'prenom')):
            rows.append(row)
    return rows, warnings


def _resolve_fk(model, name, extra_filter=None, label=''):
    if not name:
        return None
    qs = model.objects.all()
    if extra_filter:
        qs = qs.filter(**extra_filter)
    obj = qs.filter(nom__iexact=name.strip()).first()
    if obj is None:
        # tolérance : recherche "contient"
        obj = qs.filter(nom__icontains=name.strip()).first()
    if obj is None:
        raise ValueError(f"{label or model.__name__} introuvable : « {name} »")
    return obj


def _row_to_error(index, message):
    return {'ligne': index + 2, 'erreur': message}  # +2 : en-tête + base 1


@transaction.atomic
def import_users(rows, *, actor=None, request=None, dry_run=False):
    """Crée les utilisateurs. Retourne un rapport.
    En cas de dry_run, tout est annulé (rollback) après validation.
    """
    from .views import _sync_fiche_agent_for_user, _audit_user_action

    crees, erreurs = [], []
    vus_username, vus_email, vus_tel = set(), set(), set()

    for i, row in enumerate(rows):
        try:
            username = (row.get('username') or '').strip()
            password = (row.get('password') or '').strip()
            prenom = (row.get('prenom') or '').strip()
            nom = (row.get('nom') or '').strip()
            email = (row.get('email') or '').strip().lower()
            telephone = (row.get('telephone') or '').strip() or None
            matricule = (row.get('matricule') or '').strip() or None
            role = (row.get('role') or 'AGENT').strip().upper()
            actif = _norm(row.get('actif') or 'oui') not in ('non', 'no', 'false', '0', 'inactif')

            # --- validations ---
            if not username:
                raise ValueError("username obligatoire")
            if ' ' in username:
                raise ValueError("username ne doit pas contenir d'espace")
            if not password or len(password) < 6:
                raise ValueError("password obligatoire (min. 6 caractères)")
            if not prenom or not nom:
                raise ValueError("prenom et nom obligatoires")
            if not email:
                raise ValueError("email obligatoire")
            try:
                validate_email(email)
            except DjangoValidationError:
                raise ValueError(f"email invalide : {email}")
            if role not in ROLES_VALIDES:
                raise ValueError(f"role invalide : {role} (attendus : {', '.join(sorted(ROLES_VALIDES))})")

            # doublons dans le fichier
            if username.lower() in vus_username:
                raise ValueError(f"username en double dans le fichier : {username}")
            if email in vus_email:
                raise ValueError(f"email en double dans le fichier : {email}")
            if telephone and telephone in vus_tel:
                raise ValueError(f"telephone en double dans le fichier : {telephone}")

            # doublons en base
            if User.objects.filter(username__iexact=username).exists():
                raise ValueError(f"username déjà utilisé : {username}")
            if User.objects.filter(email__iexact=email).exists():
                raise ValueError(f"email déjà utilisé : {email}")
            if telephone and UserProfile.objects.filter(telephone=telephone).exists():
                raise ValueError(f"telephone déjà utilisé : {telephone}")
            if matricule and UserProfile.objects.filter(matricule=matricule).exists():
                raise ValueError(f"matricule déjà utilisé : {matricule}")

            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise ValueError("; ".join(e.messages))

            # --- résolution des rattachements ---
            cabinet = _resolve_fk(Direction, row.get('cabinet'),
                                  {'type_direction': 'cabinet'}, 'Cabinet')
            dg = _resolve_fk(Direction, row.get('direction_generale'),
                             {'type_direction': 'direction_generale'}, 'Direction Générale')
            direction = _resolve_fk(Direction, row.get('direction'),
                                    {'type_direction': 'direction'}, 'Direction')
            sous_direction = _resolve_fk(SousDirection, row.get('sous_direction'),
                                         None, 'Sous-Direction')
            service = _resolve_fk(Service, row.get('service'), None, 'Service')
            site = _resolve_fk(Site, row.get('site'), None, 'Site')

            # --- création ---
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=prenom, last_name=nom, is_active=actif,
            )
            # le signal post_save a déjà créé le profil
            profile = UserProfile.objects.get(user=user)
            profile.role = role
            profile.cabinet = cabinet
            profile.direction_generale = dg
            profile.direction = direction
            profile.sous_direction = sous_direction
            profile.service = service
            profile.site = site
            if telephone:
                profile.telephone = telephone
            if matricule:
                profile.matricule = matricule
            profile.save()

            try:
                _sync_fiche_agent_for_user(user)
            except Exception:
                pass

            if request is not None and not dry_run:
                try:
                    _audit_user_action(request, 'create', user,
                                       {'source': 'import_excel', 'role': role})
                except Exception:
                    pass

            vus_username.add(username.lower())
            vus_email.add(email)
            if telephone:
                vus_tel.add(telephone)
            crees.append({'ligne': i + 2, 'username': username,
                          'matricule': profile.matricule, 'email': email})

        except Exception as e:
            erreurs.append(_row_to_error(i, str(e)))

    rapport = {
        'total': len(rows),
        'crees': len(crees),
        'erreurs': len(erreurs),
        'details_crees': crees,
        'details_erreurs': erreurs,
        'dry_run': dry_run,
    }

    if dry_run or erreurs:
        # dry-run OU au moins une erreur → on annule tout (import "tout ou rien")
        transaction.set_rollback(True)
        if erreurs and not dry_run:
            rapport['annule'] = True
            rapport['message'] = ("Import annulé : corrigez les erreurs ci-dessous "
                                  "puis réimportez le fichier complet.")

    return rapport
