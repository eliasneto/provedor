from django.db import models


class Automacao(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("executando", "Executando"),
        ("parado", "Parado"),
        ("concluido", "Concluído"),
        ("falha", "Falha"),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome da Automação")

    slug_script = models.CharField(
        max_length=50,
        default="default",
        help_text="Nome da função no tasks.py",
        verbose_name="Código do Script",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        verbose_name="Status Atual",
    )

    planilha = models.FileField(
        upload_to="automacoes/planilhas/",
        null=True,
        blank=True,
        verbose_name="Arquivo Excel",
    )

    ultima_execucao = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Última Atualização",
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Automação"
        verbose_name_plural = "Automações"