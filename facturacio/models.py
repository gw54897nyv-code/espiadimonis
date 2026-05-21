from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Client(models.Model):
    nom = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True, verbose_name='NIF / CIF')
    adreca = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    telefon = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Producte(models.Model):
    nom = models.CharField(max_length=200)
    descripcio = models.CharField(max_length=400, blank=True)
    preu_unitari = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('21.00'))
    actiu = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producte / Servei'
        verbose_name_plural = 'Productes / Serveis'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} ({self.preu_unitari} €)'


PARTIDES = [
    ('COLLA', 'Colla'),
    ('DIMONIS', 'Dimonis'),
    ('BATUCADA', 'Batucada'),
]


class Factura(models.Model):
    TIPUS_FACTURA = 'FACTURA'
    TIPUS_PRESSUPOST = 'PRESSUPOST'
    TIPUS_CHOICES = [
        (TIPUS_FACTURA, 'Factura'),
        (TIPUS_PRESSUPOST, 'Pressupost'),
    ]

    ESTAT_PENDENT = 'PENDENT'
    ESTAT_PAGAT = 'PAGAT'
    ESTAT_CANCELAT = 'CANCELAT'
    ESTAT_CHOICES = [
        (ESTAT_PENDENT, 'Pendent'),
        (ESTAT_PAGAT, 'Pagat'),
        (ESTAT_CANCELAT, 'Cancel·lat'),
    ]

    FORMA_TRANSFERENCIA = 'TRANSFERENCIA'
    FORMA_EFECTIU = 'EFECTIU'
    FORMA_TARGETA = 'TARGETA'
    FORMA_CHOICES = [
        (FORMA_TRANSFERENCIA, 'Transferència bancària'),
        (FORMA_EFECTIU, 'Efectiu'),
        (FORMA_TARGETA, 'Targeta'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    tipus = models.CharField(max_length=15, choices=TIPUS_CHOICES, default=TIPUS_FACTURA)
    client_registrat = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='factures', verbose_name='Client (registrat)'
    )
    client = models.CharField(max_length=200, verbose_name='Nom client')
    adreca_client = models.TextField(blank=True)
    nif_client = models.CharField(max_length=20, blank=True, verbose_name='NIF / CIF client')
    data = models.DateField()
    iva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('21.00'))
    exempt_iva = models.BooleanField(
        default=False, verbose_name='Exempt d\'IVA (art. 20.1.14è LIVA)'
    )
    forma_pagament = models.CharField(
        max_length=15, choices=FORMA_CHOICES, default=FORMA_TRANSFERENCIA,
        verbose_name='Forma de pagament'
    )
    estat = models.CharField(max_length=10, choices=ESTAT_CHOICES, default=ESTAT_PENDENT)
    concepte = models.CharField(max_length=400, blank=True, verbose_name='Concepte / referència')
    partida = models.CharField(max_length=10, choices=PARTIDES, blank=True, default='', verbose_name='Partida')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Factures'
        ordering = ['-data', '-numero']

    def __str__(self):
        return f'{self.numero} - {self.client}'

    def subtotal(self):
        return sum(l.import_linia() for l in self.linies.all())

    def import_iva(self):
        if self.exempt_iva:
            return Decimal('0')
        return self.subtotal() * self.iva / Decimal('100')

    def total(self):
        return self.subtotal() + self.import_iva()


class LineaFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='linies')
    producte = models.ForeignKey(
        Producte, on_delete=models.SET_NULL, null=True, blank=True, related_name='linies_factura'
    )
    descripcio = models.CharField(max_length=300)
    quantitat = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1'))
    preu_unitari = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Línia de factura'
        verbose_name_plural = 'Línies de factura'

    def __str__(self):
        return f'{self.descripcio} x{self.quantitat}'

    def import_linia(self):
        return self.quantitat * self.preu_unitari


class Despesa(models.Model):
    CATEGORIES = [
        ('MATERIAL', 'Material'),
        ('TRANSPORT', 'Transport'),
        ('ASSEGURANCES', 'Assegurances'),
        ('LOCAL', 'Local / Lloger'),
        ('ACTIVITATS', 'Activitats'),
        ('ADMINISTRATIU', 'Administratiu'),
        ('ALTRE', 'Altre'),
    ]

    ESTAT_PENDENT = 'PENDENT'
    ESTAT_REVISAT = 'REVISAT'
    ESTATS = [
        (ESTAT_PENDENT, 'Pendent de revisar'),
        (ESTAT_REVISAT, 'Revisat'),
    ]

    soci = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='despeses', verbose_name='Soci'
    )
    data = models.DateField()
    descripcio = models.CharField(max_length=300)
    proveidor = models.CharField(max_length=200, blank=True)
    import_total = models.DecimalField(max_digits=10, decimal_places=2)
    amb_targeta_colla = models.BooleanField(
        default=False, verbose_name='Pagat amb targeta de la colla'
    )
    ticket = models.FileField(upload_to='despeses/tickets/', null=True, blank=True, verbose_name='Ticket / factura')
    estat = models.CharField(max_length=10, choices=ESTATS, default=ESTAT_PENDENT)
    # Camps assignats per la junta directiva
    categoria = models.CharField(max_length=20, choices=CATEGORIES, blank=True, default='')
    partida = models.CharField(max_length=10, choices=PARTIDES, blank=True, default='')

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despeses'
        ordering = ['-data']

    def __str__(self):
        return f'{self.data} - {self.descripcio} ({self.import_total}€)'


class FacturaProveidor(models.Model):
    ESTAT_PENDENT = 'PENDENT'
    ESTAT_PAGADA = 'PAGADA'
    ESTAT_CHOICES = [
        (ESTAT_PENDENT, 'Pendent de pagar'),
        (ESTAT_PAGADA, 'Pagada'),
    ]

    proveidor = models.CharField(max_length=200, verbose_name='Proveïdor')
    numero = models.CharField(max_length=50, blank=True, verbose_name='Núm. factura proveïdor')
    data = models.DateField(verbose_name='Data factura')
    data_venciment = models.DateField(null=True, blank=True, verbose_name='Data venciment')
    descripcio = models.CharField(max_length=400, verbose_name='Concepte')
    import_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Import total (€)')
    iva_inclou = models.BooleanField(default=True, verbose_name='Import inclou IVA')
    partida = models.CharField(max_length=10, choices=PARTIDES, blank=True, default='', verbose_name='Partida')
    estat = models.CharField(max_length=10, choices=ESTAT_CHOICES, default=ESTAT_PENDENT)
    fitxer = models.FileField(upload_to='factures_proveidor/', null=True, blank=True, verbose_name='Fitxer (PDF/imatge)')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Factura de proveïdor'
        verbose_name_plural = 'Factures de proveïdors'
        ordering = ['-data']

    def __str__(self):
        return f'{self.proveidor} - {self.descripcio} ({self.import_total}€)'
