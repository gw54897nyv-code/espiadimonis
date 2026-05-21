from django.urls import path
from . import views

urlpatterns = [
    path('actes/', views.actes_public, name='actes_public'),
    path('actes/gestio/', views.actes_gestio, name='actes_gestio'),
    path('actes/<int:pk>/eliminar/', views.eliminar_acta, name='eliminar_acta'),
    path('actes/<int:pk>/toggle/', views.toggle_acta_publicat, name='toggle_acta_publicat'),
]
