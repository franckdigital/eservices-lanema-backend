from django.contrib import admin
from .models import NewsArticle, FAQ, AIKeywordResponse, ContactMessage


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published_at", "is_featured", "views")
    list_filter = ("category", "is_featured")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    ordering = ("category", "order")


@admin.register(AIKeywordResponse)
class AIKeywordResponseAdmin(admin.ModelAdmin):
    list_display = ("keyword", "priority", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("keyword", "question_example", "response")
    ordering = ("priority", "keyword")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject", "message")
