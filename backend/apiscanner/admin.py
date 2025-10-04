from django.contrib import admin
from .models import APIScan

@admin.register(APIScan)
class APIScanAdmin(admin.ModelAdmin):
    list_display = ("id", "target", "status", "created_at", "finished_at")
    readonly_fields = ("progress", "results", "created_at", "finished_at")
