from django.urls import path
from . import views

urlpatterns = [
    # Factures
    path('', views.llista_factures, name='llista_factures'),
    path('dashboard/', views.dashboard_facturacio, name='dashboard_facturacio'),
    path('nova/', views.crear_factura, name='crear_factura'),
    path('<int:pk>/', views.detall_factura, name='detall_factura'),
    path('<int:pk>/editar/', views.editar_factura, name='editar_factura'),
    path('<int:pk>/eliminar/', views.eliminar_factura, name='eliminar_factura'),
    path('<int:pk>/pdf/', views.pdf_factura, name='pdf_factura'),
    path('<int:pk>/estat/', views.canvi_estat_factura, name='canvi_estat_factura'),
    # Clients
    path('clients/', views.llista_clients, name='llista_clients'),
    path('clients/nou/', views.crear_client, name='crear_client'),
    path('clients/<int:pk>/editar/', views.editar_client, name='editar_client'),
    path('clients/<int:pk>/eliminar/', views.eliminar_client, name='eliminar_client'),
    # Productes
    path('productes/', views.llista_productes, name='llista_productes'),
    path('productes/nou/', views.crear_producte, name='crear_producte'),
    path('productes/<int:pk>/editar/', views.editar_producte, name='editar_producte'),
    path('productes/<int:pk>/eliminar/', views.eliminar_producte, name='eliminar_producte'),
    # Despeses (junta)
    path('despeses/', views.llista_despeses, name='llista_despeses'),
    path('despeses/nova/', views.crear_despesa, name='crear_despesa'),
    path('despeses/<int:pk>/editar/', views.editar_despesa, name='editar_despesa'),
    path('despeses/<int:pk>/eliminar/', views.eliminar_despesa, name='eliminar_despesa'),
    path('despeses/<int:pk>/revisar/', views.revisar_despesa, name='revisar_despesa'),
    # Despeses (socis)
    path('despeses/registrar/', views.registrar_despesa, name='registrar_despesa'),
    path('despeses/meves/', views.les_meves_despeses, name='les_meves_despeses'),
    # Factures proveïdors
    path('proveidor/', views.llista_factures_proveidor, name='llista_factures_proveidor'),
    path('proveidor/nova/', views.crear_factura_proveidor, name='crear_factura_proveidor'),
    path('proveidor/<int:pk>/editar/', views.editar_factura_proveidor, name='editar_factura_proveidor'),
    path('proveidor/<int:pk>/eliminar/', views.eliminar_factura_proveidor, name='eliminar_factura_proveidor'),
    path('proveidor/<int:pk>/estat/', views.canvi_estat_factura_proveidor, name='canvi_estat_factura_proveidor'),
]
