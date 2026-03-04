from django.db import models

class EmpresaConfig(models.Model):
    """
    Armazena as configurações globais da Ageis Sistemas / Speed.
    Permite personalizar a logo e os dados que aparecem nos relatórios.
    """
    nome_fantasia = models.CharField(max_length=100, verbose_name="Nome da Empresa")
    razao_social = models.CharField(max_length=150, verbose_name="Razão Social", blank=True, null=True)
    cnpj = models.CharField(max_length=20, verbose_name="CNPJ", blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', verbose_name="Logo do Sistema", blank=True, null=True)
    
    # Cores do Sistema (Caso queira mudar o Amarelo/Azul via painel depois)
    cor_primaria = models.CharField(max_length=7, default="#FFD700", verbose_name="Cor Primária (Hex)")
    
    email_contato = models.EmailField(verbose_name="E-mail de Suporte")
    telefone = models.CharField(max_length=20, verbose_name="Telefone de Contato")

    def __str__(self):
        return self.nome_fantasia

    class Meta:
        verbose_name = "Configuração da Empresa"
        verbose_name_plural = "Configurações da Empresa"