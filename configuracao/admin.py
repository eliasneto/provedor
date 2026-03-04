from django.contrib import admin
from .models import EmpresaConfig

@admin.register(EmpresaConfig)
class EmpresaConfigAdmin(admin.ModelAdmin):
    # Exibe essas colunas na listagem do admin
    list_display = ('nome_fantasia', 'email_contato', 'telefone')
    
    # Impede que o usuário crie mais de uma configuração (opcional, mas recomendado)
    def has_add_permission(self, request):
        if EmpresaConfig.objects.exists():
            return False
        return True