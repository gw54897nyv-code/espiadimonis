from django import forms
from .models import Soci, DocumentSoci, CarrecJunta


class SociForm(forms.ModelForm):
    # ── Camps extra — junta directiva ─────────────────────────────────────────
    es_junta = forms.BooleanField(
        required=False,
        label='És membre de la Junta Directiva',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_junta_check'}),
    )
    carrec_junta = forms.ChoiceField(
        choices=[('', '— Selecciona el càrrec —')] + CarrecJunta.CARRECS,
        required=False,
        label='Càrrec',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    funcions_junta = forms.CharField(
        required=False,
        label='Funcions i responsabilitats',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Descriu les funcions i responsabilitats...',
        }),
    )
    ordre_junta = forms.IntegerField(
        required=False,
        initial=99,
        label='Ordre de visualització',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    data_inici_carrec = forms.DateField(
        required=False,
        label="Data d'inici del càrrec",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    class Meta:
        model = Soci
        fields = [
            'numero_soci',
            'nom', 'cognoms', 'email', 'telefon', 'dni', 'data_caducitat_dni', 'data_naixement', 'foto',
            'adreca', 'codi_postal', 'ciutat',
            'tipus', 'data_alta', 'data_baixa', 'actiu',
            'te_curs_pirotecnia', 'data_curs_pirotecnia',
            'proteccio_dades_firmada', 'data_proteccio_dades',
            'es_menor', 'tutor_legal', 'permis_pare_signat',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'cognoms': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'data_caducitat_dni': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_naixement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_soci': forms.NumberInput(attrs={'class': 'form-control'}),
            'adreca': forms.TextInput(attrs={'class': 'form-control'}),
            'codi_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'ciutat': forms.TextInput(attrs={'class': 'form-control'}),
            'tipus': forms.Select(attrs={'class': 'form-select'}),
            'data_alta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_baixa': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_curs_pirotecnia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_proteccio_dades': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tutor_legal': forms.Select(attrs={'class': 'form-select', 'id': 'id_tutor_legal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tutor_legal'].queryset = Soci.objects.filter(actiu=True, es_menor=False)
        self.fields['tutor_legal'].required = False
        self.fields['numero_soci'].required = False
        self.fields['data_baixa'].required = False
        self.fields['data_alta'].required = False
        self.fields['data_caducitat_dni'].required = False

        # Pre-populate junta fields when editing an existing soci
        if not self.is_bound and self.instance and self.instance.pk:
            try:
                cj = self.instance.carrec_junta
                self.initial['es_junta'] = True
                self.initial['carrec_junta'] = cj.carrec
                self.initial['funcions_junta'] = cj.funcions
                self.initial['ordre_junta'] = cj.ordre
                self.initial['data_inici_carrec'] = cj.data_inici
            except CarrecJunta.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('es_junta') and not cleaned_data.get('carrec_junta'):
            self.add_error('carrec_junta', 'Selecciona el càrrec de la junta.')
        return cleaned_data


class DocumentSociForm(forms.ModelForm):
    class Meta:
        model = DocumentSoci
        fields = ['tipus', 'nom', 'fitxer']
        widgets = {
            'tipus': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CarrecJuntaForm(forms.ModelForm):
    class Meta:
        model = CarrecJunta
        fields = ['soci', 'carrec', 'funcions', 'ordre', 'data_inici']
        widgets = {
            'soci': forms.Select(attrs={'class': 'form-select'}),
            'carrec': forms.Select(attrs={'class': 'form-select'}),
            'funcions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                              'placeholder': 'Descriu les funcions i responsabilitats...'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inici': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['soci'].queryset = Soci.objects.filter(actiu=True).order_by('cognoms', 'nom')
        self.fields['data_inici'].required = False
