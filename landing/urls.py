from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("news", views.NewsArticleViewSet, basename="news")
router.register("admin/news", views.NewsArticleAdminViewSet, basename="admin-news")
router.register("admin/faqs", views.FAQAdminViewSet, basename="admin-faqs")
router.register("admin/ai-responses", views.AIKeywordResponseAdminViewSet, basename="admin-ai-responses")
router.register("admin/contact-messages", views.ContactMessageAdminViewSet, basename="admin-contact-messages")

urlpatterns = [
    path("", include(router.urls)),
    path("faq/", views.faq_list, name="faq-list"),
    path("ai-assistant/", views.ai_assistant, name="ai-assistant"),
    path("contact/", views.contact_submit, name="contact-submit"),
    path("search/", views.search, name="search"),
]
