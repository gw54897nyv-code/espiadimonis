from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Perfil(models.Model):
    ROL_SOCI = 'soci'
    ROL_JUNTA = 'junta_directiva'
    ROLS = [
        (ROL_SOCI, 'Soci'),
        (ROL_JUNTA, 'Junta Directiva'),
    ]

    usuari = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLS, default=ROL_SOCI)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfils'

    def __str__(self):
        return f'{self.usuari.username} ({self.get_rol_display()})'

    def es_junta(self):
        return self.rol == self.ROL_JUNTA


class Configuracio(models.Model):
    nom_colla = models.CharField(max_length=200, default='Espiadimonis de Felanitx')
    logo = models.ImageField(upload_to='configuracio/', null=True, blank=True)
    email_contacte = models.EmailField(blank=True)
    telefon_contacte = models.CharField(max_length=30, blank=True)

    # Quotes (modificables des de l'admin)
    matricula = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('50.00'),
        verbose_name='Matrícula (1r any d\'alta, un sol cop)'
    )
    quota_anual = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('50.00'),
        verbose_name='Quota anual (tots els socis)'
    )
    mensualitat_batucada = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('15.00'),
        verbose_name='Mensualitat Batucada'
    )

    class Meta:
        verbose_name = 'Configuració'
        verbose_name_plural = 'Configuració'

    def __str__(self):
        return self.nom_colla

    cif = models.CharField(max_length=20, blank=True, verbose_name='CIF / NIF')
    adreca = models.CharField(max_length=300, blank=True, verbose_name='Adreça')
    iban = models.CharField(max_length=34, blank=True, verbose_name='IBAN bancari')

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Acta(models.Model):
    TIPUS_COLLA = 'COLLA'
    TIPUS_JUNTA = 'JUNTA'
    TIPUS_CHOICES = [
        (TIPUS_COLLA, 'Reunió de Colla'),
        (TIPUS_JUNTA, 'Reunió de Junta'),
    ]

    tipus = models.CharField(max_length=10, choices=TIPUS_CHOICES, default=TIPUS_COLLA)
    titol = models.CharField(max_length=300)
    data = models.DateField()
    fitxer = models.FileField(upload_to='actes/', null=True, blank=True)
    publicat = models.BooleanField(default=True)
    data_pujada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Acta'
        verbose_name_plural = 'Actes'
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipus_display()} – {self.titol} ({self.data})'
