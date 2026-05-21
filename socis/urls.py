from django.urls import path
from . import views

urlpatterns = [
    path('perfil/', views.el_meu_perfil, name='el_meu_perfil'),
    path('junta/', views.junta_organigrama, name='junta_organigrama'),
    path('junta/gestio/', views.gestionar_junta, name='gestionar_junta'),
    path('', views.llista_socis, name='llista_socis'),
    path('nou/', views.crear_soci, name='crear_soci'),
    path('importar/', views.importar_socis, name='importar_socis'),
    path('importar/plantilla/', views.descarregar_plantilla_csv, name='plantilla_csv'),
    path('pagaments/', views.pagaments_anuals, name='pagaments_anuals'),
    path('<int:pk>/', views.detall_soci, name='detall_soci'),
    path('<int:pk>/editar/', views.editar_soci, name='editar_soci'),
    path('<int:pk>/eliminar/', views.eliminar_soci, name='eliminar_soci'),
    path('<int:pk>/carnet/', views.carnet_soci, name='carnet_soci'),
    path('<int:pk>/document/', views.pujar_document, name='pujar_document'),
    path('<int:pk>/compte/', views.crear_compte, name='crear_compte'),
    path('<int:pk>/contrasenya/', views.canvi_contrasenya, name='canvi_contrasenya'),
    path('<int:pk>/rebut/quota/<int:any>/', views.rebut_quota, name='rebut_quota'),
    path('<int:pk>/rebut/matricula/', views.rebut_matricula, name='rebut_matricula'),
    path('document/<int:pk>/eliminar/', views.eliminar_document, name='eliminar_document'),
    path('pagament/<int:pk>/toggle/', views.toggle_pagament, name='toggle_pagament'),
    path('pagament/<int:pk>/rebut/', views.rebut_mensualitat, name='rebut_mensualitat'),
    path('quota/<int:pk>/toggle/', views.toggle_quota, name='toggle_quota'),
    path('matricula/<int:pk>/toggle/', views.toggle_matricula, name='toggle_matricula'),
]
