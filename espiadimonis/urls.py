from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('socis/', include('socis.urls')),
    path('facturacio/', include('facturacio.urls')),
    path('dashboard/', include('accounts.dashboard_urls')),
    path('associacio/', accounts_views.dades_associacio, name='dades_associacio'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
