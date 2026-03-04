from django import forms
from .models import Provedor

class ProvedorForm(forms.ModelForm):
    class Meta:
        model = Provedor
        fields = ['nome', 'url_site', 'cidade', 'estado']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Speed Telecom'}),
            'url_site': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UF', 'maxlength': '2'}),
        }