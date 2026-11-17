from django.contrib.auth.models import User
from django.db import models


class ValidationResponsableMixin(models.Model):
    """Champs communs de validation par le responsable labo (signature + cachet
    appliques a partir de son ClientProfile), partages par Proforma, BonCommande
    et Facture."""

    valide_par_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    date_validation_responsable = models.DateField(null=True, blank=True)
    signature_responsable_appliquee = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Proforma(ValidationResponsableMixin):
    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("ENVOYEE", "Envoyée"),
        ("VALIDEE", "Validée"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
        ("ANNULEE", "Annulée"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="proformas",
    )
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis",
        on_delete=models.CASCADE,
        related_name="proformas",
        null=True,
        blank=True,
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")
    date_emission = models.DateField(auto_now_add=True)

    # Remise commerciale (montant HT deduit du total HT) — ligne "Remise" du
    # formulaire officiel EN 002-PG002, renseignee par le service reception.
    remise = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # « Nom de l'editeur » de la reference du devis (N° devis/annee/editeur/Direction/Sous-Direction/Laboratoire)
    edite_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    # Envoi du devis au client par le service reception (email ou WhatsApp).
    envoye_le = models.DateTimeField(null=True, blank=True)
    canal_envoi = models.CharField(max_length=10, blank=True)  # EMAIL / WHATSAPP

    # Mention manuscrite "Lu et approuve" apposee par le client sur la fiche
    # de devis (vaut acceptation des termes du contrat, cf. N.B. du formulaire).
    lu_approuve = models.BooleanField(default=False)
    lu_approuve_le = models.DateTimeField(null=True, blank=True)
    lu_approuve_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    lu_approuve_signature = models.ImageField(
        upload_to="facturation/lu_approuve/", null=True, blank=True
    )

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class CompteEmailLabo(models.Model):
    """Compte d'envoi (SMTP) utilise par le service reception pour envoyer les
    devis aux clients depuis l'application. Inspire du module « Courrier
    intelligent » : l'utilisateur configure son compte une fois (serveur,
    port, identifiant, mot de passe chiffre), puis redige et envoie ses
    messages depuis un formulaire integre."""

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comptes_email_labo")
    nom_affichage = models.CharField(max_length=200)
    adresse_email = models.EmailField()
    serveur_sortant = models.CharField(max_length=200, blank=True)
    port_sortant = models.IntegerField(default=587)
    # False -> STARTTLS (port 587), True -> SSL direct (port 465)
    ssl_sortant = models.BooleanField(default=False)
    identifiant = models.CharField(max_length=200, blank=True)
    mot_de_passe = models.CharField(max_length=500, blank=True, help_text="Chiffre (Fernet)")
    signature = models.TextField(blank=True, help_text="Signature ajoutee en bas des messages")
    est_principal = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-est_principal", "nom_affichage"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.nom_affichage} <{self.adresse_email}>"


class EmailDevis(models.Model):
    """Historique des envois de devis (email ou WhatsApp) par le service reception."""

    CANAL_CHOICES = [("EMAIL", "Email"), ("WHATSAPP", "WhatsApp")]
    STATUT_CHOICES = [("ENVOYE", "Envoyé"), ("ECHEC", "Échec")]

    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name="envois")
    canal = models.CharField(max_length=10, choices=CANAL_CHOICES, default="EMAIL")
    envoye_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    compte = models.ForeignKey(CompteEmailLabo, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    destinataires = models.JSONField(default=list, blank=True)
    destinataires_cc = models.JSONField(default=list, blank=True)
    sujet = models.CharField(max_length=500, blank=True)
    corps = models.TextField(blank=True)
    pdf_joint = models.BooleanField(default=True)
    nb_pieces_jointes = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="ENVOYE")
    erreur = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BonCommande(ValidationResponsableMixin):
    """Bon de commande emis simultanement a la facture des l'acceptation du
    devis : le client doit le signer electroniquement pour confirmer sa
    commande, condition prealable au paiement de la facture et donc au
    demarrage de la demande d'analyse."""

    STATUT_CHOICES = [
        ("EMIS", "Émis"),
        ("SIGNE_CLIENT", "Signé par le client"),
        ("ANNULE", "Annulé"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bons_commande")
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name="bons_commande")
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EMIS")
    date_emission = models.DateField(auto_now_add=True)

    # Signature electronique (dessinee) du client
    signature_client_image = models.ImageField(
        upload_to="facturation/signatures_client/", null=True, blank=True
    )
    date_signature_client = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class DemandeAnalyse(models.Model):
    STATUT_CHOICES = [
        ("EN_ATTENTE_ECHANTILLONS", "En attente d'échantillons"),
        ("ECHANTILLONS_RECUS", "Échantillons reçus"),
        ("EN_COURS", "En cours d'analyse"),
        ("TERMINEE", "Terminée"),
        ("RESULTATS_ENVOYES", "Résultats envoyés"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    demande_devis = models.ForeignKey(
        "demandes.DemandeDevis",
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    proforma = models.ForeignKey(
        Proforma,
        on_delete=models.CASCADE,
        related_name="demandes_analyses",
    )
    facture = models.ForeignKey(
        "Facture",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_analyses",
    )
    laboratoire = models.ForeignKey(
        "laboratoires.Laboratoire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_analyses",
    )
    statut = models.CharField(
        max_length=40,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE_ECHANTILLONS",
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_depot_echantillons = models.DateField(null=True, blank=True)
    date_debut_analyse = models.DateField(null=True, blank=True)
    date_fin_analyse = models.DateField(null=True, blank=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero


class Facture(ValidationResponsableMixin):
    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("EN_ATTENTE_VALIDATION", "En attente de validation comptable"),
        ("PAYEE", "Payée"),
        ("ANNULEE", "Annulée"),
    ]

    MODE_PAIEMENT_CHOICES = [
        ("CHEQUE", "Chèque"),
        ("COMPTANT", "Comptant"),
    ]

    numero = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="factures",
    )
    proforma = models.ForeignKey(
        Proforma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="factures",
    )
    bon_commande = models.ForeignKey(
        BonCommande,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="factures",
    )
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default="EN_ATTENTE")
    date_emission = models.DateField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    date_paiement = models.DateField(null=True, blank=True)

    # Informations de paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT_CHOICES,
        blank=True,
    )
    justificatif_paiement = models.FileField(
        upload_to="factures/paiements/",
        null=True,
        blank=True,
    )
    paiement_valide = models.BooleanField(default=False)
    visible_client = models.BooleanField(
        default=False,
        help_text="Quand vrai, la facture apparaît dans l'espace client",
    )
    reference_paiement = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.numero
