from django import forms
from django.forms import inlineformset_factory
from .models import Factura, LineaFactura, Despesa, Client, Producte, FacturaProveidor


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'nif', 'adreca', 'email', 'telefon']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'adreca': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProducteForm(forms.ModelForm):
    class Meta:
        model = Producte
        fields = ['nom', 'descripcio', 'preu_unitari', 'iva', 'actiu']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcio': forms.TextInput(attrs={'class': 'form-control'}),
            'preu_unitari': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = [
            'numero', 'tipus', 'client_registrat',
            'client', 'nif_client', 'adreca_client',
            'data', 'concepte', 'iva', 'exempt_iva',
            'forma_pagament', 'partida', 'estat', 'notes',
        ]
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'tipus': forms.Select(attrs={'class': 'form-select'}),
            'client_registrat': forms.Select(attrs={'class': 'form-select', 'id': 'id_client_registrat'}),
            'client': forms.TextInput(attrs={'class': 'form-control'}),
            'nif_client': forms.TextInput(attrs={'class': 'form-control'}),
            'adreca_client': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'concepte': forms.TextInput(attrs={'class': 'form-control'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control'}),
            'forma_pagament': forms.Select(attrs={'class': 'form-select'}),
            'partida': forms.Select(attrs={'class': 'form-select'}),
            'estat': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_registrat'].required = False
        self.fields['client_registrat'].empty_label = '— Client puntual (no registrat) —'


class LineaFacturaForm(forms.ModelForm):
    class Meta:
        model = LineaFactura
        fields = ['producte', 'descripcio', 'quantitat', 'preu_unitari']
        widgets = {
            'producte': forms.Select(attrs={'class': 'form-select form-select-sm producte-select'}),
            'descripcio': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantitat': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'preu_unitari': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producte'].required = False
        self.fields['producte'].empty_label = '— Descripció lliure —'
        self.fields['producte'].queryset = Producte.objects.filter(actiu=True)


LineaFormSet = inlineformset_factory(
    Factura, LineaFactura,
    form=LineaFacturaForm,
    extra=3,
    can_delete=True,
)


class DespesaForm(forms.ModelForm):
    """Formulari per a la junta — tots els camps."""
    class Meta:
        model = Despesa
        fields = ['data', 'categoria', 'partida', 'descripcio', 'proveidor', 'import_total', 'amb_targeta_colla', 'ticket', 'estat']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'partida': forms.Select(attrs={'class': 'form-select'}),
            'descripcio': forms.TextInput(attrs={'class': 'form-control'}),
            'proveidor': forms.TextInput(attrs={'class': 'form-control'}),
            'import_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estat': forms.Select(attrs={'class': 'form-select'}),
        }


class DespesaSociForm(forms.ModelForm):
    """Formulari per al soci — sense categoria ni partida (les assigna la junta)."""
    class Meta:
        model = Despesa
        fields = ['data', 'descripcio', 'proveidor', 'import_total', 'amb_targeta_colla', 'ticket']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descripcio': forms.TextInput(attrs={'class': 'form-control'}),
            'proveidor': forms.TextInput(attrs={'class': 'form-control'}),
            'import_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class RevisarDespesaForm(forms.ModelForm):
    """Formulari per a la junta per revisar i classificar una despesa."""
    class Meta:
        model = Despesa
        fields = ['categoria', 'partida', 'estat']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'partida': forms.Select(attrs={'class': 'form-select'}),
            'estat': forms.Select(attrs={'class': 'form-select'}),
        }


class FacturaProveidorForm(forms.ModelForm):
    class Meta:
        model = FacturaProveidor
        fields = ['proveidor', 'numero', 'data', 'data_venciment', 'descripcio',
                  'import_total', 'iva_inclou', 'partida', 'estat', 'fitxer', 'notes']
        widgets = {
            'proveidor': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_venciment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descripcio': forms.TextInput(attrs={'class': 'form-control'}),
            'import_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'partida': forms.Select(attrs={'class': 'form-select'}),
            'estat': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
