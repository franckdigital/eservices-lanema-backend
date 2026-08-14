from rest_framework import serializers
from .models import NewsArticle, FAQ, AIKeywordResponse, ContactMessage


class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = [
            "id", "title", "slug", "excerpt", "content", "image", "category",
            "published_at", "is_featured", "views", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "views", "created_at", "updated_at"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = [
            "id", "category", "question", "answer", "order", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AIKeywordResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIKeywordResponse
        fields = [
            "id", "keyword", "question_example", "response", "priority",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            "id", "name", "email", "phone", "subject", "message",
            "is_read", "created_at",
        ]
        read_only_fields = ["id", "is_read", "created_at"]
