from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class NewsArticle(models.Model):
    """Article d'actualité publié sur la vitrine LANEMA."""

    CATEGORY_CHOICES = (
        ("COMMUNIQUE", "Communiqué"),
        ("REFORME", "Réforme / réglementation"),
        ("EVENEMENT", "Événement"),
        ("PARTENARIAT", "Partenariat"),
    )

    title = models.CharField(max_length=255, verbose_name="Titre")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(verbose_name="Extrait")
    content = models.TextField(verbose_name="Contenu")
    image = models.ImageField(upload_to="news/", null=True, blank=True, verbose_name="Image")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="COMMUNIQUE")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    is_featured = models.BooleanField(default=False, verbose_name="À la une")
    views = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "landing_news_articles"
        verbose_name = "Article d'actualité"
        verbose_name_plural = "Articles d'actualité"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:240]
            slug = base_slug
            i = 1
            while NewsArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class FAQ(models.Model):
    """Question fréquemment posée."""

    category = models.CharField(max_length=100, verbose_name="Catégorie")
    question = models.CharField(max_length=500, verbose_name="Question")
    answer = models.TextField(verbose_name="Réponse")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "landing_faqs"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["category", "order"]

    def __str__(self):
        return self.question


class AIKeywordResponse(models.Model):
    """Réponse prédéfinie de l'assistant IA de la vitrine, basée sur des
    mots-clés. `keyword` peut contenir plusieurs synonymes séparés par des
    virgules (ex: "frais, tarif, prix") : la question matche si l'un d'eux
    apparaît comme sous-chaîne. `keyword='default'` sert de réponse de repli."""

    keyword = models.CharField(max_length=150, verbose_name="Mot(s)-clé(s)")
    question_example = models.CharField(max_length=255, blank=True, verbose_name="Exemple de question")
    response = models.TextField(verbose_name="Réponse")
    priority = models.PositiveIntegerField(default=0, help_text="0 = priorité la plus haute")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "landing_ai_keyword_responses"
        verbose_name = "Réponse IA (mot-clé)"
        verbose_name_plural = "Réponses IA (mots-clés)"
        ordering = ["priority", "keyword"]

    def __str__(self):
        return f"{self.keyword} → {self.response[:40]}"


class ContactMessage(models.Model):
    """Message envoyé depuis le formulaire de contact de la vitrine."""

    name = models.CharField(max_length=150, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    subject = models.CharField(max_length=255, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "landing_contact_messages"
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"
