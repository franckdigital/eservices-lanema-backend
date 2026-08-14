from django.utils import timezone
from datetime import timedelta

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by("-date_creation")
        
        # Filter by type
        type_notification = self.request.query_params.get('type')
        if type_notification and type_notification != 'TOUS':
            queryset = queryset.filter(type_notification=type_notification)
        
        # Filter by read status
        lu = self.request.query_params.get('lu')
        if lu == 'true':
            queryset = queryset.filter(lu=True)
        elif lu == 'false':
            queryset = queryset.filter(lu=False)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="lire")
    def lire(self, request, pk=None):
        notification = self.get_object()
        notification.lu = True
        notification.save(update_fields=["lu"])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="tout_lire")
    def tout_lire(self, request):
        qs = Notification.objects.filter(user=self.request.user, lu=False)
        count = qs.count()
        qs.update(lu=True)
        return Response({"detail": f"{count} notifications marquées comme lues."})

    @action(detail=False, methods=["get"], url_path="non_lues")
    def non_lues(self, request):
        count = Notification.objects.filter(user=self.request.user, lu=False).count()
        return Response({"non_lues": count})

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Return notification statistics for the current user"""
        user_notifications = Notification.objects.filter(user=self.request.user)
        today = timezone.now().date()

        resp = Response({
            "total": user_notifications.count(),
            "non_lues": user_notifications.filter(lu=False).count(),
            "aujourd_hui": user_notifications.filter(date_creation__date=today).count(),
            "alertes": user_notifications.filter(type_notification="ALERTE", lu=False).count(),
            "par_type": {
                "INFO": user_notifications.filter(type_notification="INFO").count(),
                "ALERTE": user_notifications.filter(type_notification="ALERTE").count(),
                "STOCK": user_notifications.filter(type_notification="STOCK").count(),
                "DEMANDE": user_notifications.filter(type_notification="DEMANDE").count(),
                "QUALITE": user_notifications.filter(type_notification="QUALITE").count(),
                "FACTURATION": user_notifications.filter(type_notification="FACTURATION").count(),
            }
        })
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp["Pragma"] = "no-cache"
        return resp

    @action(detail=True, methods=["delete"], url_path="supprimer")
    def supprimer(self, request, pk=None):
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
