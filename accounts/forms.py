from django import forms
from .models import Configuracio


class ConfiguracioForm(forms.ModelForm):
    class Meta:
        model = Configuracio
        fields = ['nom_colla', 'logo', 'cif', 'adreca', 'email_contacte', 'telefon_contacte', 'iban']
        widgets = {
            'nom_colla':        forms.TextInput(attrs={'class': 'form-control'}),
            'cif':              forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'G-XXXXXXXX'}),
            'adreca':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'C/ Exemple, 1 · 07200 Felanitx'}),
            'email_contacte':   forms.EmailInput(attrs={'class': 'form-control'}),
            'telefon_contacte': forms.TextInput(attrs={'class': 'form-control'}),
            'iban':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ES00 0000 0000 0000 0000 0000'}),
        }
