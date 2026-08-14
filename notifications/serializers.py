from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "titre",
            "message",
            "type_notification",
            "priorite",
            "lu",
            "date_creation",
            "lien",
        ]
        read_only_fields = ["id", "date_creation", "user"]
