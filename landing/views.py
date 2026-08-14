from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import NewsArticle, FAQ, AIKeywordResponse, ContactMessage
from .serializers import (
    NewsArticleSerializer, FAQSerializer, AIKeywordResponseSerializer,
    ContactMessageSerializer,
)


class IsAdminOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_staff:
            return True
        profile = getattr(user, "client_profile", None)
        return getattr(profile, "role", None) in ("ADMIN", "STAFF")


# ============================================================
# PUBLIC (vitrine)
# ============================================================

class NewsArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Articles d'actualité publiés, en lecture seule pour le public."""
    queryset = NewsArticle.objects.filter(published_at__lte=timezone.now())
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        featured = self.request.query_params.get("featured")
        if featured in ("1", "true", "True"):
            qs = qs.filter(is_featured=True)
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=["views"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def faq_list(request):
    faqs = FAQ.objects.filter(is_active=True)
    return Response(FAQSerializer(faqs, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def ai_assistant(request):
    """Assistant IA de la vitrine — matching par mots-clés paramétrable
    depuis l'admin, sans appel à un LLM externe."""
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response({"detail": "question requise"}, status=status.HTTP_400_BAD_REQUEST)

    question_lower = question.lower()
    answer = None
    for kr in AIKeywordResponse.objects.filter(is_active=True).order_by("priority"):
        keywords = [k.strip().lower() for k in kr.keyword.split(",") if k.strip()]
        if any(k in question_lower for k in keywords):
            answer = kr.response
            break

    if not answer:
        default_response = AIKeywordResponse.objects.filter(
            keyword__iexact="default", is_active=True
        ).first()
        answer = default_response.response if default_response else (
            "Merci pour votre question. Un conseiller LANEMA vous répondra bientôt — "
            "vous pouvez aussi nous contacter directement via la page Contact."
        )

    return Response({"answer": answer})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def contact_submit(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais."},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def search(request):
    """Recherche unifiée sur les actualités publiées et la FAQ."""
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response({"results": []})

    results = []

    articles = NewsArticle.objects.filter(published_at__lte=timezone.now()).filter(
        Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(content__icontains=q)
    )
    for article in articles:
        results.append({
            "type": "actualite",
            "title": article.title,
            "excerpt": article.excerpt,
            "url": f"/actualites/{article.slug}",
        })

    faqs = FAQ.objects.filter(is_active=True).filter(
        Q(question__icontains=q) | Q(answer__icontains=q)
    )
    for faq in faqs:
        results.append({
            "type": "faq",
            "title": faq.question,
            "excerpt": faq.answer[:180],
            "url": f"/faq?q={faq.id}",
        })

    return Response({"results": results})


# ============================================================
# ADMIN (CMS de la vitrine)
# ============================================================

class NewsArticleAdminViewSet(viewsets.ModelViewSet):
    queryset = NewsArticle.objects.all().order_by("-published_at")
    serializer_class = NewsArticleSerializer
    permission_classes = [IsAdminOrStaff]


class FAQAdminViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all().order_by("category", "order")
    serializer_class = FAQSerializer
    permission_classes = [IsAdminOrStaff]


class AIKeywordResponseAdminViewSet(viewsets.ModelViewSet):
    queryset = AIKeywordResponse.objects.all().order_by("priority", "keyword")
    serializer_class = AIKeywordResponseSerializer
    permission_classes = [IsAdminOrStaff]


class ContactMessageAdminViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by("-created_at")
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminOrStaff]
    http_method_names = ["get", "patch", "delete", "head", "options"]
