from django.conf import settings
from django.db import models


class CompteEmailDFIR(models.Model):
    """Compte email (boîte personnelle) configuré par un membre du personnel
    DFIR — SMTP pour l'envoi, IMAP pour la réception. Un compte par
    utilisateur (pas de partage), à l'image d'un client mail classique."""

    TYPE_CHOICES = [
        ("gmail", "Gmail"),
        ("outlook", "Outlook / Office 365"),
        ("yahoo", "Yahoo Mail"),
        ("imap", "IMAP personnalisé"),
    ]
    STATUT_CHOICES = [
        ("INACTIF", "Inactif"),
        ("ACTIF", "Actif"),
        ("ERREUR", "Erreur"),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comptes_email_dfir"
    )
    type_compte = models.CharField(max_length=10, choices=TYPE_CHOICES, default="imap")
    nom_affichage = models.CharField(max_length=255, blank=True)
    adresse_email = models.EmailField()
    identifiant = models.CharField(max_length=255, blank=True, help_text="Si différent de l'adresse email")

    # Chiffré (Fernet) avant écriture en base — cf. dfir_email/crypto.py.
    # Utiliser un mot de passe d'application dédié, jamais le mot de passe
    # principal du compte.
    mot_de_passe = models.TextField(blank=True)

    serveur_entrant = models.CharField(max_length=255, blank=True, verbose_name="Serveur IMAP")
    port_entrant = models.PositiveIntegerField(default=993)
    ssl_entrant = models.BooleanField(default=True)

    serveur_sortant = models.CharField(max_length=255, blank=True, verbose_name="Serveur SMTP")
    port_sortant = models.PositiveIntegerField(default=587)
    ssl_sortant = models.BooleanField(default=True)

    est_principal = models.BooleanField(default=False)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="INACTIF")
    derniere_synchro = models.DateTimeField(null=True, blank=True)
    derniere_erreur = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-est_principal", "adresse_email"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.adresse_email} ({self.utilisateur})"


class EmailDFIR(models.Model):
    DIRECTION_CHOICES = [
        ("ENTRANT", "Entrant"),
        ("SORTANT", "Sortant"),
    ]
    STATUT_CHOICES = [
        ("NON_LU", "Non lu"),
        ("LU", "Lu"),
        ("REPONDU", "Répondu"),
        ("ARCHIVE", "Archivé"),
    ]
    PRIORITE_CHOICES = [
        ("NORMALE", "Normale"),
        ("HAUTE", "Haute"),
        ("URGENTE", "Urgente"),
    ]

    compte = models.ForeignKey(CompteEmailDFIR, on_delete=models.CASCADE, related_name="emails")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default="ENTRANT")

    message_id = models.CharField(max_length=255, blank=True, db_index=True)
    thread_id = models.CharField(max_length=255, blank=True, db_index=True)
    en_reponse_a = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reponses"
    )

    sujet = models.CharField(max_length=500, blank=True)
    expediteur_nom = models.CharField(max_length=255, blank=True)
    expediteur_email = models.EmailField(blank=True)
    destinataires = models.JSONField(default=list, blank=True)
    destinataires_cc = models.JSONField(default=list, blank=True)
    corps_texte = models.TextField(blank=True)
    corps_html = models.TextField(blank=True)
    date_message = models.DateTimeField(null=True, blank=True)

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="NON_LU")
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default="NORMALE")

    # Analyse "intelligente" — heuristique par mots-clés (pas de LLM), cf.
    # dfir_email/services.py::analyser_ia.
    score_urgence = models.PositiveSmallIntegerField(default=0)
    resume_ia = models.TextField(blank=True)
    actions_detectees = models.JSONField(default=list, blank=True)
    traite_par_ia = models.BooleanField(default=False)

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_message", "-created_at"]
        unique_together = ("compte", "message_id")

    def __str__(self) -> str:  # pragma: no cover
        return self.sujet or f"Email #{self.pk}"


class PieceJointeEmailDFIR(models.Model):
    email = models.ForeignKey(EmailDFIR, on_delete=models.CASCADE, related_name="pieces_jointes")
    nom_fichier = models.CharField(max_length=255)
    fichier = models.FileField(upload_to="dfir_email/pieces_jointes/%Y/%m/")
    type_mime = models.CharField(max_length=100, blank=True)
    taille = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:  # pragma: no cover
        return self.nom_fichier
