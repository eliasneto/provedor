from django.db import models

class Provedor(models.Model):
    # Campos solicitados
    nome = models.CharField(max_length=100, verbose_name="Nome do Provedor")
    url_site = models.URLField(max_length=200, verbose_name="URL do Site", blank=True, null=True)
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)")
    
    # Campo extra para controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Provedor"
        verbose_name_plural = "Provedores"