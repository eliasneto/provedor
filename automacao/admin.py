from django.contrib import admin
from .models import Automacao

@admin.register(Automacao)
class AutomacaoAdmin(admin.ModelAdmin):
    # Colunas que aparecerão na listagem
    list_display = ('nome', 'slug_script', 'status', 'ultima_execucao')
    
    # Filtros laterais para facilitar a busca
    list_filter = ('status', 'ultima_execucao')
    
    # Barra de busca por nome ou código
    search_fields = ('nome', 'slug_script')