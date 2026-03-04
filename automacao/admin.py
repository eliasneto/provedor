from django.contrib import admin
from .models import Automacao


@admin.register(Automacao)
class AutomacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug_script", "status", "ultima_execucao")
    list_filter = ("status",)
    search_fields = ("nome", "slug_script")
    ordering = ("-ultima_execucao",)