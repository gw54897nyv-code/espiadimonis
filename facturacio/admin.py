from django.contrib import admin
from .models import Factura, LineaFactura, Despesa


class LineaFacturaInline(admin.TabularInline):
    model = LineaFactura
    extra = 1
    fields = ['descripcio', 'quantitat', 'preu_unitari']


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tipus', 'client', 'data', 'estat', 'total']
    list_filter = ['tipus', 'estat', 'data']
    search_fields = ['numero', 'client']
    inlines = [LineaFacturaInline]

    def total(self, obj):
        return f'{obj.total():.2f} €'
    total.short_description = 'Total'


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ['data', 'categoria', 'descripcio', 'proveidor', 'import_total']
    list_filter = ['categoria', 'data']
    search_fields = ['descripcio', 'proveidor']
