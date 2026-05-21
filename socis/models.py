from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


def ruta_foto(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'socis/fotos/soci_{instance.pk}.{ext}'


def ruta_document(instance, filename):
    return f'socis/documents/soci_{instance.soci.pk}/{filename}'


class Soci(models.Model):
    TIPUS_DIMONIS = 'DIMONIS'
    TIPUS_BATUCADA = 'BATUCADA'
    TIPUS_CHOICES = [
        (TIPUS_DIMONIS, 'Dimonis'),
        (TIPUS_BATUCADA, 'Batucada'),
    ]

    # Identificació
    numero_soci = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name='Número de soci')
    usuari = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='soci'
    )

    # Dades personals
    nom = models.CharField(max_length=100)
    cognoms = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    telefon = models.CharField(max_length=20, blank=True)
    dni = models.CharField(max_length=20, blank=True, verbose_name='DNI / NIE')
    data_caducitat_dni = models.DateField(null=True, blank=True, verbose_name='Caducitat DNI')
    data_naixement = models.DateField(null=True, blank=True, verbose_name='Data de naixement')
    foto = models.ImageField(upload_to=ruta_foto, null=True, blank=True)

    # Adreça
    adreca = models.CharField(max_length=300, blank=True, verbose_name='Adreça')
    codi_postal = models.CharField(max_length=10, blank=True, verbose_name='Codi postal')
    ciutat = models.CharField(max_length=100, blank=True, verbose_name='Municipi')

    # Tipus i estat
    tipus = models.CharField(max_length=10, choices=TIPUS_CHOICES, default=TIPUS_DIMONIS)
    data_alta = models.DateField(null=True, blank=True, verbose_name='Data d\'alta')
    data_baixa = models.DateField(null=True, blank=True, verbose_name='Data de baixa')
    actiu = models.BooleanField(default=True)

    # Documentació obligatòria
    te_curs_pirotecnia = models.BooleanField(default=False, verbose_name='Curs pirotècnia (CREE)')
    data_curs_pirotecnia = models.DateField(null=True, blank=True, verbose_name='Data curs CREE')
    proteccio_dades_firmada = models.BooleanField(default=False, verbose_name='Protecció de dades firmada')
    data_proteccio_dades = models.DateField(null=True, blank=True, verbose_name='Data firma LOPD')

    # Menor d'edat
    es_menor = models.BooleanField(default=False, verbose_name='És menor d\'edat')
    tutor_legal = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='menors_tutelats', verbose_name='Tutor legal'
    )
    permis_pare_signat = models.BooleanField(default=False, verbose_name='Permís pare/mare signat')

    class Meta:
        verbose_name = 'Soci'
        verbose_name_plural = 'Socis'
        ordering = ['numero_soci', 'cognoms', 'nom']

    def __str__(self):
        num = f'#{self.numero_soci} ' if self.numero_soci else ''
        return f'{num}{self.cognoms}, {self.nom}'

    def nom_complet(self):
        return f'{self.nom} {self.cognoms}'

    def adreca_completa(self):
        parts = [self.adreca, self.codi_postal, self.ciutat]
        return ', '.join(p for p in parts if p)

    def al_dia(self, any, mes):
        return self.pagaments.filter(any=any, mes=mes, pagat=True).exists()

    def estat_dni(self):
        from django.utils import timezone
        if not self.data_caducitat_dni:
            return 'sense_data'
        avui = timezone.now().date()
        dies = (self.data_caducitat_dni - avui).days
        if dies < 0:
            return 'caducat'
        if dies <= 60:
            return 'aviat'
        return 'ok'

    def document_obligatori(self, tipus):
        return self.documents.filter(tipus=tipus).first()

    def documentacio_completa(self):
        ok = (
            self.dni
            and self.proteccio_dades_firmada
            and self.te_curs_pirotecnia
            and self.document_obligatori('PROTECCIO')
            and self.document_obligatori('CREE')
        )
        if self.es_menor:
            ok = ok and self.permis_pare_signat and self.tutor_legal_id and self.document_obligatori('PERMIS_PARE')
        return bool(ok)

    def save(self, *args, **kwargs):
        if not self.numero_soci:
            ultima = Soci.objects.order_by('-numero_soci').exclude(numero_soci__isnull=True).first()
            self.numero_soci = (ultima.numero_soci + 1) if ultima else 1
        super().save(*args, **kwargs)


class Pagament(models.Model):
    """Mensualitat mensual — només Batucada (15€/mes)."""
    MESOS = [
        (1, 'Gener'), (2, 'Febrer'), (3, 'Març'), (4, 'Abril'),
        (5, 'Maig'), (6, 'Juny'), (7, 'Juliol'), (8, 'Agost'),
        (9, 'Setembre'), (10, 'Octubre'), (11, 'Novembre'), (12, 'Desembre'),
    ]

    soci = models.ForeignKey(Soci, on_delete=models.CASCADE, related_name='pagaments')
    any = models.IntegerField()
    mes = models.IntegerField(choices=MESOS)
    pagat = models.BooleanField(default=False)
    data_pagament = models.DateField(null=True, blank=True)
    import_pagat = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Mensualitat'
        verbose_name_plural = 'Mensualitats'
        unique_together = ['soci', 'any', 'mes']
        ordering = ['any', 'mes']

    def __str__(self):
        estat = 'Pagat' if self.pagat else 'Pendent'
        return f'{self.soci} · {self.get_mes_display()} {self.any} ({estat})'


class PagamentMatricula(models.Model):
    """Matrícula d'entrada — un sol cop quan el soci s'apunta (50€)."""
    soci = models.OneToOneField(Soci, on_delete=models.CASCADE, related_name='matricula')
    any = models.IntegerField()
    pagat = models.BooleanField(default=False)
    data_pagament = models.DateField(null=True, blank=True)
    import_pagat = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Matrícula d\'entrada'
        verbose_name_plural = 'Matrícules d\'entrada'

    def __str__(self):
        estat = 'Pagada' if self.pagat else 'Pendent'
        return f'Matrícula {self.any} · {self.soci} ({estat})'


class PagamentQuota(models.Model):
    """Quota anual de soci — tots els membres (50€/any)."""
    soci = models.ForeignKey(Soci, on_delete=models.CASCADE, related_name='quotes')
    any = models.IntegerField()
    pagat = models.BooleanField(default=False)
    data_pagament = models.DateField(null=True, blank=True)
    import_pagat = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Quota anual'
        verbose_name_plural = 'Quotes anuals'
        unique_together = ['soci', 'any']
        ordering = ['-any']

    def __str__(self):
        estat = 'Pagada' if self.pagat else 'Pendent'
        return f'Quota {self.any} · {self.soci} ({estat})'


class CarrecJunta(models.Model):
    PRESIDENT = 'PRESIDENT'
    VICEPRESIDENT = 'VICEPRESIDENT'
    SECRETARI = 'SECRETARI'
    TRESORER = 'TRESORER'
    VOCAL = 'VOCAL'
    ALTRE = 'ALTRE'

    CARRECS = [
        (PRESIDENT, 'President/a'),
        (VICEPRESIDENT, 'Vicepresident/a'),
        (SECRETARI, 'Secretari/a'),
        (TRESORER, 'Tresorer/a'),
        (VOCAL, 'Vocal'),
        (ALTRE, 'Altre càrrec'),
    ]

    NIVELL = {
        PRESIDENT: 1,
        VICEPRESIDENT: 2,
        SECRETARI: 2,
        TRESORER: 2,
        VOCAL: 3,
        ALTRE: 3,
    }

    soci = models.OneToOneField(
        Soci, on_delete=models.CASCADE, related_name='carrec_junta'
    )
    carrec = models.CharField(max_length=20, choices=CARRECS)
    funcions = models.TextField(blank=True, verbose_name='Funcions i responsabilitats')
    ordre = models.PositiveIntegerField(default=99, verbose_name='Ordre de visualització')
    data_inici = models.DateField(null=True, blank=True, verbose_name='Data d\'inici del càrrec')

    class Meta:
        verbose_name = 'Càrrec de Junta'
        verbose_name_plural = 'Càrrecs de Junta'
        ordering = ['ordre', 'carrec']

    def __str__(self):
        return f'{self.get_carrec_display()} — {self.soci.nom_complet()}'

    def nivell(self):
        return self.NIVELL.get(self.carrec, 3)


class DocumentSoci(models.Model):
    TIPUS_DNI = 'DNI'
    TIPUS_PERMIS_PARE = 'PERMIS_PARE'
    TIPUS_PROTECCIO = 'PROTECCIO'
    TIPUS_CREE = 'CREE'
    TIPUS_ALTRE = 'ALTRE'
    TIPUS_CHOICES = [
        (TIPUS_DNI, 'DNI / NIE'),
        (TIPUS_PERMIS_PARE, 'Permís pare/mare'),
        (TIPUS_PROTECCIO, 'Protecció de dades (LOPD)'),
        (TIPUS_CREE, 'Curs pirotècnia (CREE)'),
        (TIPUS_ALTRE, 'Altre'),
    ]

    soci = models.ForeignKey(Soci, on_delete=models.CASCADE, related_name='documents')
    tipus = models.CharField(max_length=15, choices=TIPUS_CHOICES, default=TIPUS_ALTRE)
    nom = models.CharField(max_length=200)
    fitxer = models.FileField(upload_to=ruta_document)
    data_pujada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['tipus', '-data_pujada']

    def __str__(self):
        return f'{self.soci} - {self.nom}'
