from django.contrib import admin
from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['type', 'titre', 'reference', 'utilisateur', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['titre', 'description', 'reference']
    ordering = ['-created_at']
