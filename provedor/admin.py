from django.contrib import admin
from .models import Provedor

@admin.register(Provedor)
class ProvedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'url_site')
    search_fields = ('nome', 'cidade')
    list_filter = ('estado',)