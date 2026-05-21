from django.contrib import admin
from .models import Soci, Pagament, DocumentSoci


class PagamentInline(admin.TabularInline):
    model = Pagament
    extra = 0
    fields = ['any', 'mes', 'pagat', 'data_pagament']


class DocumentInline(admin.TabularInline):
    model = DocumentSoci
    extra = 0
    fields = ['tipus', 'nom', 'fitxer', 'data_pujada']
    readonly_fields = ['data_pujada']


@admin.register(Soci)
class SociAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'tipus', 'email', 'telefon', 'actiu', 'data_alta']
    list_filter = ['tipus', 'actiu']
    search_fields = ['nom', 'cognoms', 'email', 'dni']
    inlines = [PagamentInline, DocumentInline]
    fieldsets = (
        ('Dades personals', {
            'fields': ('usuari', 'nom', 'cognoms', 'email', 'telefon', 'dni', 'foto')
        }),
        ('Informació de soci', {
            'fields': ('tipus', 'actiu')
        }),
    )


@admin.register(Pagament)
class PagamentAdmin(admin.ModelAdmin):
    list_display = ['soci', 'any', 'mes', 'pagat', 'data_pagament']
    list_filter = ['any', 'mes', 'pagat']
    search_fields = ['soci__nom', 'soci__cognoms']


@admin.register(DocumentSoci)
class DocumentSociAdmin(admin.ModelAdmin):
    list_display = ['soci', 'tipus', 'nom', 'data_pujada']
    list_filter = ['tipus']
    search_fields = ['soci__nom', 'soci__cognoms', 'nom']
