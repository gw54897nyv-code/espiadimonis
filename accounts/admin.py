from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Configuracio


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilInline]


@admin.register(Configuracio)
class ConfiguracioAdmin(admin.ModelAdmin):
    fields = ['nom_colla', 'logo', 'email_contacte', 'telefon_contacte']

    def has_add_permission(self, request):
        return not Configuracio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Perfil)
